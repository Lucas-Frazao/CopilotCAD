"""Spec compliance tests for F-018 — Assembly creation."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import yaml

from rpc_helpers import call_rpc, assert_rpc_success
from spec_fixtures import assembly_create_ir


def _assembly_module():
    try:
        return importlib.import_module("project.assembly_folder")
    except ImportError as exc:
        pytest.fail(f"F-018 requires project.assembly_folder: {exc}")


def test_assembly_folder_create_and_read(workspace):
    asm = _assembly_module()
    create_asm = getattr(asm, "create_assembly", None)
    read_asm = getattr(asm, "read_assembly", None)
    assert create_asm and read_asm

    create_asm(
        workspace,
        "demo_asm",
        {
            "id": "demo_asm",
            "name": "Demo Assembly",
            "instances": [
                {"instance_id": "inst_plate", "part_id": "mounting_plate"},
                {"instance_id": "inst_bracket", "part_id": "bracket"},
            ],
        },
    )
    path = workspace / "assemblies" / "demo_asm.yaml"
    assert path.is_file()
    data = read_asm(workspace, "demo_asm")
    assert data["id"] == "demo_asm"
    assert len(data["instances"]) == 2


def test_assembly_create_execution_scaffolds_missing_parts(workspace):
    asm = _assembly_module()
    execute_asm = getattr(asm, "execute_assembly_create", None)
    if execute_asm is None:
        from engine.executor import execute_intent_ir
        from ir.validator import validate_intent_ir

        intent = validate_intent_ir(assembly_create_ir())
        result = execute_intent_ir(intent, workspace_path=workspace)
        assert result.success, getattr(result, "error", result)
    else:
        execute_asm(workspace, assembly_create_ir())

    assert (workspace / "parts" / "mounting_plate").is_dir()
    assert (workspace / "parts" / "bracket").is_dir()
    assert (workspace / "assemblies" / "demo_asm.yaml").is_file()


def test_assembly_yaml_mvp_fields(workspace):
    asm = _assembly_module()
    create_asm = getattr(asm, "create_assembly")
    create_asm(
        workspace,
        "demo_asm",
        {
            "id": "demo_asm",
            "name": "Demo",
            "instances": [{"instance_id": "i1", "part_id": "p1"}],
        },
    )
    raw = yaml.safe_load((workspace / "assemblies" / "demo_asm.yaml").read_text(encoding="utf-8"))
    assert "instances" in raw
    inst = raw["instances"][0]
    assert "part_id" in inst
    assert "instance_id" in inst


def test_assembly_create_jsonrpc_or_execute(workspace):
    ir = assembly_create_ir()
    response = call_rpc("execute_intent", {"ir": ir, "workspace_path": str(workspace)})
    payload = response.get("result") or response.get("error", {}).get("data", {})
    if not payload.get("success"):
        pytest.fail(f"assembly_create execute must succeed: {response}")
    assert (workspace / "assemblies" / "demo_asm.yaml").is_file()


def test_explorer_lists_assembly_file(workspace):
    asm = _assembly_module()
    asm.create_assembly(
        workspace,
        "demo_asm",
        {"id": "demo_asm", "name": "Demo", "instances": []},
    )
    response = call_rpc("list_workspace_tree", {"workspace_path": str(workspace)})
    tree = assert_rpc_success(response)

    def _find(nodes, path):
        for n in nodes:
            if n.get("path") == path:
                return True
            if _find(n.get("children") or [], path):
                return True
        return False

    assert _find(tree, "assemblies/demo_asm.yaml")


def test_problems_engine_flags_assembly_issues():
    from ir.validator import validate_intent_ir
    from problems.engine import evaluate_problems

    ir = assembly_create_ir()
    ir["constraints"] = {"interfaces": ["dup", "dup"]}
    intent = validate_intent_ir(ir)
    problems = evaluate_problems(intent)
    assert any(p.type == "interface_conflict" for p in problems)
