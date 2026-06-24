"""Direct pythonOCC calls — sole OCCT entry point for CopilotCAD (F-003).

All Open CASCADE / pythonOCC imports must live in this module only.
Requires pythonocc-core on Python 3.11+; some platforms (e.g. Windows ARM64)
may not have wheels — tests skip when OCC is unavailable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakeWire,
)
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakePrism
from OCC.Core.GeomAbs import GeomAbs_Plane
from OCC.Core.gp import gp_Ax2, gp_Dir, gp_Pnt, gp_Vec
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.IGESControl import IGESControl_Writer
from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Reader, STEPControl_Writer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.TopoDS import TopoDS_Face, TopoDS_Shape, topods

PathLike = Union[str, Path]

SUPPORTED_PLANES = frozenset({"XY"})
SUPPORTED_DIRECTIONS = frozenset({"+Z"})
SUPPORTED_SKETCH_MODES = frozenset({"center"})
SUPPORTED_EXTRUDE_MODES = frozenset({"add"})


class GeometryError(Exception):
    """Raised when geometry parameters are invalid or OCCT operations fail."""


def _require_positive(name: str, value: float) -> None:
    if value <= 0:
        raise GeometryError(f"{name} must be positive, got {value}")


def _require_in(name: str, value: str, allowed: frozenset[str]) -> None:
    if value not in allowed:
        allowed_list = ", ".join(sorted(allowed))
        raise GeometryError(f"{name} must be one of {allowed_list}, got {value!r}")


def _require_shape(name: str, shape: TopoDS_Shape) -> None:
    if shape is None or shape.IsNull():
        raise GeometryError(f"{name} must be a non-null TopoDS_Shape")


def _shape_bbox(shape: TopoDS_Shape) -> tuple[float, float, float, float, float, float]:
    box = Bnd_Box()
    brepbndlib.Add(shape, box)
    return box.Get()


def sketch_rectangle(
    length: float,
    width: float,
    plane: str,
    mode: str,
) -> TopoDS_Shape:
    """Build a rectangular sketch profile on the requested plane."""
    _require_positive("length", length)
    _require_positive("width", width)
    _require_in("plane", plane, SUPPORTED_PLANES)
    _require_in("mode", mode, SUPPORTED_SKETCH_MODES)

    half_length = length / 2.0
    half_width = width / 2.0

    if plane == "XY":
        p1 = gp_Pnt(-half_length, -half_width, 0.0)
        p2 = gp_Pnt(half_length, -half_width, 0.0)
        p3 = gp_Pnt(half_length, half_width, 0.0)
        p4 = gp_Pnt(-half_length, half_width, 0.0)
    else:
        raise GeometryError(f"unsupported plane: {plane}")

    wire_builder = BRepBuilderAPI_MakeWire()
    wire_builder.Add(BRepBuilderAPI_MakeEdge(p1, p2).Edge())
    wire_builder.Add(BRepBuilderAPI_MakeEdge(p2, p3).Edge())
    wire_builder.Add(BRepBuilderAPI_MakeEdge(p3, p4).Edge())
    wire_builder.Add(BRepBuilderAPI_MakeEdge(p4, p1).Edge())

    if not wire_builder.IsDone():
        raise GeometryError("failed to build rectangle wire")

    face_builder = BRepBuilderAPI_MakeFace(wire_builder.Wire())
    if not face_builder.IsDone():
        raise GeometryError("failed to build rectangle face")

    return face_builder.Face()


def extrude(
    profile: TopoDS_Shape,
    distance: float,
    direction: str,
    mode: str,
) -> TopoDS_Shape:
    """Extrude a profile shape into a solid."""
    _require_shape("profile", profile)
    _require_positive("distance", distance)
    _require_in("direction", direction, SUPPORTED_DIRECTIONS)
    _require_in("mode", mode, SUPPORTED_EXTRUDE_MODES)

    face = _as_face(profile)
    if direction == "+Z":
        vec = gp_Vec(0.0, 0.0, distance)
    else:
        raise GeometryError(f"unsupported direction: {direction}")

    prism = BRepPrimAPI_MakePrism(face, vec)
    if not prism.IsDone():
        raise GeometryError("extrude failed")

    solid = prism.Shape()
    _require_shape("extruded solid", solid)
    return solid


def hole_pattern_corners(
    solid: TopoDS_Shape,
    diameter: float,
    offset: float,
) -> TopoDS_Shape:
    """Cut four corner holes into a rectangular plate solid."""
    _require_shape("solid", solid)
    _require_positive("diameter", diameter)
    _require_positive("offset", offset)

    xmin, ymin, zmin, xmax, ymax, zmax = _shape_bbox(solid)
    length = xmax - xmin
    width = ymax - ymin
    thickness = zmax - zmin

    if length <= 2 * offset or width <= 2 * offset:
        raise GeometryError("offset too large for plate dimensions")

    radius = diameter / 2.0
    cut_height = thickness + 2e-4
    cylinder_base_z = zmin - 1e-4

    centers = [
        (xmax - offset, ymax - offset),
        (xmin + offset, ymax - offset),
        (xmax - offset, ymin + offset),
        (xmin + offset, ymin + offset),
    ]

    result = solid
    for x, y in centers:
        axis = gp_Ax2(gp_Pnt(x, y, cylinder_base_z), gp_Dir(0.0, 0.0, 1.0))
        cylinder = BRepPrimAPI_MakeCylinder(axis, radius, cut_height)
        cylinder_shape = cylinder.Shape()
        _require_shape("hole cylinder", cylinder_shape)

        cut = BRepAlgoAPI_Cut(result, cylinder_shape)
        cut.Build()
        if not cut.IsDone():
            raise GeometryError("hole boolean cut failed")

        result = cut.Shape()
        _require_shape("cut result", result)

    return result


def export_step(shape: TopoDS_Shape, path: PathLike) -> None:
    """Write a TopoDS shape to a STEP file."""
    _require_shape("shape", shape)

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    writer = STEPControl_Writer()
    transfer_result = writer.Transfer(shape, STEPControl_AsIs)
    if transfer_result != IFSelect_RetDone:
        raise GeometryError(f"STEP transfer failed with status {transfer_result}")

    write_status = writer.Write(str(output_path))
    if write_status != IFSelect_RetDone:
        raise GeometryError(f"STEP write failed with status {write_status}")


def read_step(path: PathLike) -> TopoDS_Shape:
    """Read a STEP file and return the first transferred shape (for tests)."""
    input_path = Path(path)
    reader = STEPControl_Reader()
    read_status = reader.ReadFile(str(input_path))
    if read_status != IFSelect_RetDone:
        raise GeometryError(f"STEP read failed with status {read_status}")

    reader.TransferRoots()
    shape = reader.OneShape()
    _require_shape("imported STEP shape", shape)
    return shape


def build_mounting_plate_golden() -> TopoDS_Shape:
    """Build the F-001 golden mounting plate solid (100x50x6 mm, corner holes)."""
    profile = sketch_rectangle(100.0, 50.0, "XY", "center")
    solid = extrude(profile, 6.0, "+Z", "add")
    return hole_pattern_corners(solid, 6.0, 8.0)


def fuse_shapes(shape_a: TopoDS_Shape, shape_b: TopoDS_Shape) -> TopoDS_Shape:
    """Fuse two solids into one combined shape."""
    _require_shape("shape_a", shape_a)
    _require_shape("shape_b", shape_b)
    fuse = BRepAlgoAPI_Fuse(shape_a, shape_b)
    fuse.Build()
    if not fuse.IsDone():
        raise GeometryError("boolean fuse failed")
    return fuse.Shape()


def make_box(length: float, width: float, height: float) -> TopoDS_Shape:
    """Build a simple box solid centered on XY at z=0."""
    _require_positive("length", length)
    _require_positive("width", width)
    _require_positive("height", height)
    box = BRepPrimAPI_MakeBox(length, width, height)
    shape = box.Shape()
    _require_shape("box solid", shape)
    return shape


def tessellate_shape(shape: TopoDS_Shape, deflection: float = 0.5) -> dict[str, list]:
    """Triangulate a shape for viewport rendering."""
    _require_shape("shape", shape)

    mesh = BRepMesh_IncrementalMesh(shape, deflection)
    mesh.Perform()
    if not mesh.IsDone():
        raise GeometryError("mesh tessellation failed")

    vertices: list[float] = []
    normals: list[float] = []
    indices: list[int] = []
    face_ids: list[int] = []

    vertex_offset = 0
    face_index = 0
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        face = topods.Face(explorer.Current())
        location = TopLoc_Location()
        triangulation = BRep_Tool.Triangulation(face, location)
        if triangulation is None:
            explorer.Next()
            continue

        transform = location.Transformation()
        node_count = triangulation.NbNodes()
        for node_index in range(1, node_count + 1):
            point = triangulation.Node(node_index)
            point.Transform(transform)
            vertices.extend([point.X(), point.Y(), point.Z()])

        has_normals = triangulation.HasNormals()
        if has_normals:
            for node_index in range(1, node_count + 1):
                normal = triangulation.Normal(node_index)
                normal.Transform(transform)
                normals.extend([normal.X(), normal.Y(), normal.Z()])
        else:
            # OCCT 7.9 removed Poly_Triangulation.ComputeNormal; use a stable fallback.
            face_normal = gp_Dir(0.0, 0.0, 1.0)
            adaptor = BRepAdaptor_Surface(face)
            if adaptor.GetType() == 0:  # GeomAbs_Plane
                face_normal = adaptor.Plane().Axis().Direction()
            for _ in range(node_count):
                normals.extend([face_normal.X(), face_normal.Y(), face_normal.Z()])

        triangle_count = triangulation.NbTriangles()
        for triangle_index in range(1, triangle_count + 1):
            triangle = triangulation.Triangle(triangle_index)
            n1, n2, n3 = triangle.Get()
            indices.extend(
                [
                    vertex_offset + n1 - 1,
                    vertex_offset + n2 - 1,
                    vertex_offset + n3 - 1,
                ]
            )
            face_ids.append(face_index)

        vertex_offset += node_count
        face_index += 1
        explorer.Next()

    return {
        "vertices": vertices,
        "normals": normals,
        "indices": indices,
        "face_ids": face_ids,
    }


def export_iges(shape: TopoDS_Shape, path: PathLike) -> None:
    """Write a TopoDS shape to an IGES file."""
    _require_shape("shape", shape)

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    writer = IGESControl_Writer()
    writer.AddShape(shape)
    status = writer.Write(str(output_path))
    if status != IFSelect_RetDone:
        raise GeometryError(f"IGES write failed with status {status}")


def _as_face(profile: TopoDS_Shape) -> TopoDS_Face:
    if profile.ShapeType() == TopAbs_FACE:
        return topods.Face(profile)

    explorer = TopExp_Explorer(profile, TopAbs_FACE)
    if explorer.More():
        return topods.Face(explorer.Current())

    raise GeometryError("profile must be a face or contain a face")
