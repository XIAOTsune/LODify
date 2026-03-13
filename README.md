# LODify v2.9.0

LODify is a Blender optimization add-on for large scenes, focused on texture workflows, geometry simplification, and viewport performance management.

LODify 是一个面向大型 Blender 场景的优化插件，核心覆盖贴图优化、几何减面、视口性能管理，以及批量化的场景分析工具。

## Highlights

- Collection Analyzer: analyze collection density, apply heatmap coloring, or use non-destructive percentage labels only.
- 3D View Analyzer: quickly identify heavy objects in the viewport and clean up safely.
- Async Image Optimization: resize textures in the background through a worker process, with bundled Pillow support on Windows x64.
- Camera-Based Optimization: estimate on-screen texture demand from the active camera and generate more reasonable output resolutions.
- Geometry LOD: support both Decimate and Geometry Nodes based workflows for batch LOD generation.
- Viewport / Shader LOD: reduce display cost for distant objects and restore original state safely.

## What's New in 2.9.0

- Fixed inaccurate progress counting during async image processing.
- Fixed View Analyzer cleanup so untouched object colors are no longer overwritten.
- Fixed Viewport Reset so objects without hide-state snapshots are not incorrectly unhidden.
- Fixed native fallback image resizing to preserve aspect ratio.
- Added the missing output-directory mode UI control for image processing.
- Updated screen-ratio normalization to respect `resolution_percentage`.
- Hardened generated-folder deletion checks to use proper directory containment validation.
- Improved manifest website lookup compatibility for Blender extension metadata.

## Requirements

- Blender `4.2+`
- Windows `x64` for the bundled Pillow wheel in the current extension package

## Installation

1. Download the latest release package from the [Releases](https://github.com/XIAOTsune/LODify/releases) page.
2. Open Blender and go to `Edit -> Preferences -> Get Extensions`.
3. Use `Install from Disk...` and select the downloaded zip package.
4. Open the `Optimize` tab in the 3D View sidebar.

## Release Notes

- Current release: [RELEASE_REPORT_2.9.0.md](RELEASE_REPORT_2.9.0.md)

## Repository Notes

- `blender_manifest.toml` is the Blender Extensions manifest.
- `__init__.py` keeps the legacy `bl_info` metadata for compatibility.
- `core/image_worker.py` is the subprocess worker used by async texture operations.

## 中文简介

LODify 适合用于建筑可视化、关卡搭建、资产整合等高负载场景。当前版本以“稳定修复 + 发布整理”为主，重点提升了图片处理、视图分析恢复、视口重置和文档一致性。

如果你准备提交到 Blender Extensions 或 GitHub Releases，建议优先查阅本次版本说明文件：
[RELEASE_REPORT_2.9.0.md](RELEASE_REPORT_2.9.0.md)
