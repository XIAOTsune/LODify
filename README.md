# LODify v2.9.0

LODify is a Blender optimization add-on for large scenes, focused on texture workflows, geometry simplification, and viewport performance management.

LODify 是一个面向大型 Blender 场景的优化插件，核心覆盖贴图优化、几何减面、视口性能管理，以及批量化场景分析工具。

## Highlights / 功能亮点

- Collection Analyzer: analyze collection density, apply heatmap coloring, or use non-destructive percentage labels only. / 集合分析器：可分析 Collection 密度、使用热力图着色，或仅以非破坏方式追加百分比标记。
- 3D View Analyzer: quickly identify heavy objects in the viewport and clean up safely. / 3D 视图分析器：快速定位高负载物体，并可安全清理分析结果。
- Async Image Optimization: resize textures in the background through a worker process. / 异步图片优化：通过独立 worker 在后台批量缩放贴图。
- Camera-Based Optimization: estimate on-screen texture demand from the active camera and generate more reasonable output resolutions. / 相机视角优化：基于当前相机估算贴图实际屏幕占比，自动生成更合理的输出分辨率。
- Geometry LOD: support both Decimate and Geometry Nodes based workflows for batch LOD generation. / 几何 LOD：同时支持 Decimate 和 Geometry Nodes 两种批量 LOD 工作流。
- Viewport / Shader LOD: reduce display cost for distant objects and restore original state safely. / 视口 / Shader LOD：降低远处物体的显示与材质开销，并可安全恢复原始状态。

## What's New in 2.9.0 / 2.9.0 更新内容

- Fixed inaccurate progress counting during async image processing. / 修复异步图片处理时进度统计不准确的问题。
- Fixed View Analyzer cleanup so untouched object colors are no longer overwritten. / 修复清理 View Analyzer 时误覆盖未分析对象颜色的问题。
- Fixed Viewport Reset so objects without hide-state snapshots are not incorrectly unhidden. / 修复 Viewport Reset 在没有隐藏状态快照时错误取消隐藏对象的问题。
- Fixed native fallback image resizing to preserve aspect ratio. / 修复原生兜底缩放会拉伸图片的问题，现已保持宽高比。
- Added the missing output-directory mode UI control for image processing. / 补回图片处理输出目录模式的 UI 控件。
- Updated screen-ratio normalization to respect `resolution_percentage`. / 更新屏幕占比归一化逻辑，使其正确考虑 `resolution_percentage`。
- Hardened generated-folder deletion checks to use proper directory containment validation. / 强化生成目录删除校验，改为可靠的目录包含关系判断。
- Improved manifest website lookup compatibility for Blender extension metadata. / 改进 Blender Extension manifest 网站字段的兼容读取逻辑。

## Platform Support / 平台支持

- Blender Extensions platform: `windows-x64`
- Bundled Pillow wheels are currently maintained for Windows only. / 当前仅维护 Windows 对应的 Pillow wheel。
- Current package targets Blender `4.2+` with bundled Windows wheels for Python `3.11` and `3.13`. / 当前扩展包面向 Blender `4.2+`，内置适配 Python `3.11` 与 `3.13` 的 Windows wheels。

## Requirements / 环境要求

- Blender `4.2+`
- Windows `x64`

## Installation / 安装方式

1. Download the latest release package from the [Releases](https://github.com/XIAOTsune/LODify/releases) page. / 从 [Releases](https://github.com/XIAOTsune/LODify/releases) 页面下载最新发布包。
2. Open Blender and go to `Edit -> Preferences -> Get Extensions`. / 打开 Blender，进入 `Edit -> Preferences -> Get Extensions`。
3. Use `Install from Disk...` and select the downloaded zip package. / 使用 `Install from Disk...` 并选择下载好的 zip 包。
4. Open the `Optimize` tab in the 3D View sidebar. / 安装后在 3D 视图侧边栏中打开 `Optimize` 标签页。

## Repository Notes / 仓库说明

- `blender_manifest.toml` is the Blender Extensions manifest. / `blender_manifest.toml` 是 Blender Extensions 的清单文件。
- `core/image_worker.py` is the subprocess worker used by async texture operations. / `core/image_worker.py` 是异步贴图处理使用的子进程 worker。
- The `wheels/` directory is part of the extension package and currently only ships the Windows wheel. / `wheels/` 目录属于扩展发布内容，当前仅附带 Windows wheel。
