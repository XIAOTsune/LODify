# LODify 2.9.0 Release Report

Release Date: 2026-03-13  
Target: Blender Extensions, Blender 4.2+

## Version

- `blender_manifest.toml`: `version = "2.9.0"`
- `__init__.py`: `"version": (2, 9, 0)`

## Highlights

### P0 Critical Fixes

1. Fixed inaccurate progress counting in async image processing.
2. Fixed View Analyzer cleanup so untouched object colors are no longer overwritten.
3. Fixed Viewport Reset so objects without hide snapshots are not incorrectly unhidden.
4. Fixed native fallback resizing to preserve aspect ratio.

### P1 Important UX and Correctness

1. Added the missing UI control for output directory mode.
2. Updated screen-ratio normalization to respect `resolution_percentage`.
3. Hardened generated-folder deletion checks with robust directory containment validation.

### P2 Low-Risk Cleanup

1. Manifest website lookup now prefers the top-level `website` field with legacy fallback.

## Files Updated

- `__init__.py`
- `blender_manifest.toml`
- `operators/analyzer.py`
- `operators/image.py`
- `operators/viewport.py`
- `ui/main_panels.py`
- `utils.py`
- `README.md`

## Documentation Sync

- Updated `README.md` for the `v2.9.0` release.
- Kept `RELEASE_REPORT_2.9.0.md` as the release-specific notes file.
- Removed `EXECUTION_CHECKLIST.md` to avoid duplicate process documentation in the release package.

## Validation

1. Static syntax check: `python -m compileall -q .`
2. Version field verification:
   - `blender_manifest.toml` is `2.9.0`
   - `__init__.py` is `(2, 9, 0)`

## Notes

- This release is a stabilization and release-packaging update, not a large architectural refactor.
- A runtime smoke test in Blender 4.2+ is still recommended before shipping the final zip package.
