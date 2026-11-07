# Release workflow

The release version is defined in `blender_manifest.toml`. Keep the legacy `bl_info` version in `__init__.py` and the README badge in sync.

## Build a test package

Run this from the project root with Python 3.10 or newer:

```powershell
python scripts/build_release.py
```

The script validates the version and manifest build paths, creates a Blender-installable zip at `dist/LODifyv<version>.zip`, checks the archive, and writes a `.sha256` sidecar. Build paths come from `[build].paths`, so the zip contains only the add-on, README, and bundled wheels, not Git metadata or design documents. Run the command again after code changes to replace the package for the same version.

To choose another output directory:

```powershell
python scripts/build_release.py --output-dir C:\temp\lodify-release
```

Install the generated zip in Blender through **Edit > Preferences > Get Extensions > Install from Disk...** and test it before publishing.

## Publish a release

After testing, commit the release changes, create a version tag such as `v3.0.0`, and publish a GitHub Release for that tag. Attach the generated `.zip` and `.sha256` files. For the next release, update the manifest version, `bl_info`, and README badge before rebuilding.
