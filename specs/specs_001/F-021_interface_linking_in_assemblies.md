# F-021 — Interface linking in assemblies

## Summary

When parts are **mated in an assembly**, automatically **link interface definitions** across part specs — updating `connects_to` fields — and run **interface conflict** detection across the project.

**Status:** Pending approval.

## Why this matters

Interfaces (F-016) describe connection intent. Mates (F-019) describe physical connection. Linking them keeps **documentation aligned with geometry** — a core PDD promise.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **`connects_to`** | Field in a part’s interface entry pointing to another part’s interface id. |
| **Auto-link** | When a mate is created, infer which interfaces are involved and cross-reference specs. |
| **Interface conflict** | Problem when two linked interfaces disagree (size, type, position). |
| **Propagation** | Updating one spec triggers re-check of related parts. |

## What the user will experience

1. User mates bracket to plate via chat.
2. `spec.yaml` on both parts updates: interface entries reference each other.
3. Interfaces panel (F-016) shows status **linked**.
4. Conflicting interface definitions surface as problems in chat and Problems panel.

## What we will build

### Backend

- Post-mate hook in executor: map mate step → interface ids (from IR `links` or heuristics).
- Update both `parts/<a>/spec.yaml` and `parts/<b>/spec.yaml` `connects_to`.
- Extend `evaluate_problems` to compare linked interface parameters.
- Idempotent updates — re-running mate doesn’t duplicate links.

### Intent IR

- Optional `links.interface_refs` on mate steps for explicit interface pairing.

## Acceptance criteria

1. Successful mate between two parts with defined interfaces updates both specs.
2. Interfaces panel reflects linked status after mate.
3. Deliberate conflict (mismatched bolt pattern) triggers `interface_conflict` problem.
4. Unit tests with fixture specs and mate IR.

## Dependencies

- **F-016** — Interface definitions and panel.
- **F-019** — Mate execution hook point.
- **F-006** — `interface_conflict` problem type.
- **F-002** — spec.yaml writes.

## Out of scope (not in F-021)

- Verified status automation (may remain manual/stub).
- Suggesting interfaces from geometry auto-detection.
- More than pairwise links in one mate (MVP: one mate → one interface pair).

## Notes for reviewers

This is **traceability glue** between PDD metadata and assembly geometry — high value for solo engineers maintaining many connections.
