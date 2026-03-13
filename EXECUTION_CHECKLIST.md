# LODify Minimal-Fix Execution Checklist

This checklist tracks the agreed "minimal change" fixes only.
Do not include refactors in this pass.

## Scope

- Goal: Fix confirmed bugs and UX gaps with minimal code changes.
- Out of scope: architecture rewrite, API redesign, feature expansion.

## Status Legend

- [ ] Not started
- [~] In progress
- [x] Done
- [!] Blocked

## Phase A - Critical Fixes (P0)

### A1. Async image progress count is incorrect
- [x] ID: P0-A1
- Files:
  - `operators/image.py`
- Change:
  - Increment `self._processed` when PIL worker finishes successfully.
- Why:
  - Current progress/report can undercount completed tasks.
- Acceptance:
  - Progress bar reaches 100% for all-worker runs.
  - Final report count matches the number of processed images.

### A2. Clean View Analyzer overwrites colors of untouched objects
- [x] ID: P0-A2
- Files:
  - `operators/analyzer.py`
- Change:
  - Remove fallback branch that forces `(1, 1, 1, 1)` for objects without backup key.
- Why:
  - Objects never analyzed should not have their display color altered.
- Acceptance:
  - Only objects with `_lod_orig_color` are restored.
  - Unanalyzed object colors remain unchanged.

### A3. Viewport reset can wrongly unhide objects
- [x] ID: P0-A3
- Files:
  - `operators/viewport.py`
- Change:
  - Remove fallback `obj.hide_viewport = False` when no `_lod_orig_hide` snapshot exists.
- Why:
  - User-hidden objects must not be unhidden by reset.
- Acceptance:
  - Objects hidden before LOD update remain hidden after reset unless snapshot says otherwise.

### A4. Native fallback image resize distorts aspect ratio
- [x] ID: P0-A4
- Files:
  - `operators/image.py`
- Change:
  - Replace square `img.scale(target_size, target_size)` with aspect-ratio-preserving dimensions.
- Why:
  - Non-square textures are currently stretched.
- Acceptance:
  - A 2:1 texture remains 2:1 after resize.
  - Long edge clamps to target size.

## Phase B - Important UX/Correctness (P1)

### B1. Missing UI control for output directory mode
- [x] ID: P1-B1
- Files:
  - `ui/main_panels.py`
  - `properties.py` (verify existing property usage only)
- Change:
  - Expose `use_same_directory` toggle in the image panel.
  - Show `custom_output_path` only when custom directory mode is active.
- Why:
  - Current branch logic depends on a control not visible in UI.
- Acceptance:
  - User can switch between blend-dir output and custom-dir output.

### B2. Screen ratio normalization ignores render percentage
- [x] ID: P1-B2
- Files:
  - `utils.py`
- Change:
  - Apply `resolution_percentage` to normalization denominator.
- Why:
  - LOD trigger strength drifts when render percentage is not 100%.
- Acceptance:
  - LOD behavior remains consistent when changing render percentage.

### B3. Folder delete path check is too weak
- [x] ID: P1-B3
- Files:
  - `operators/image.py`
- Change:
  - Replace simple `startswith` path check with robust path containment check.
- Why:
  - Prefix-based matching can misclassify similar paths.
- Acceptance:
  - Only images actually under the target folder are treated as in-folder.

## Phase C - Low-Risk Cleanup (P2)

### C1. Manifest website lookup mismatch
- [x] ID: P2-C1
- Files:
  - `__init__.py`
  - `blender_manifest.toml` (reference only)
- Change:
  - Read top-level `website` first, then fallback to legacy structure if needed.
- Why:
  - Current logic checks a nested key that may not exist.
- Acceptance:
  - Website URL resolves correctly from manifest.

## Implementation Order

1. Phase A (all P0 items)
2. Phase B (all P1 items)
3. Phase C (P2 item)

## Validation Checklist

- [ ] Add-on registers/unregisters without errors.
- [x] No syntax errors (`python -m compileall -q .`).
- [ ] P0 acceptance checks completed.
- [ ] P1 acceptance checks completed.
- [ ] Manual smoke test in Blender 4.2+ completed.

## Sign-off

- [x] Scope confirmed by user
- [x] Ready to implement
