# LODify

<div align="center">

### Make heavy Blender scenes easier to render, review, and keep working on.
### 让大型 Blender 场景更轻，也让优化过程更可控。

[![Blender](https://img.shields.io/badge/Blender-4.2%2B-E87D0D?style=for-the-badge&logo=blender&logoColor=white)](https://www.blender.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20x64-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/XIAOTsune/LODify)
[![Version](https://img.shields.io/badge/Version-3.0.0-24292F?style=for-the-badge)](https://github.com/XIAOTsune/LODify/releases)
[![License](https://img.shields.io/badge/License-GPL--3.0--or--later-6F42C1?style=for-the-badge)](https://spdx.org/licenses/GPL-3.0-or-later.html)

[Download](https://github.com/XIAOTsune/LODify/releases) · [Release notes](RELEASE.md) · [Report an issue](https://github.com/XIAOTsune/LODify/issues)

</div>

---

## Contents | 目录

- [What LODify does](#what-lodify-does--lodify-能做什么)
- [What's new in 3.0.0](#whats-new-in-300--300-版本更新)
- [Quick start](#quick-start--快速开始)
- [Animation optimization](#animation-optimization--动画优化)
- [Features](#features--功能说明)
- [Safety and supported data](#safety-and-supported-data--安全与支持范围)
- [Install](#install--安装)
- [Requirements and packaging](#requirements-and-packaging--环境与打包)
- [Credits](#credits--致谢)

## What LODify does | LODify 能做什么

LODify is a Blender add-on for analyzing and reducing scene cost. It brings collection and viewport analysis, image resizing, camera-aware texture sizing, geometry LOD, viewport display controls, material-detail controls, and cleanup tools together in the 3D View sidebar.

LODify 是一款用于分析和降低场景负载的 Blender 插件。它把集合与视图分析、贴图缩放、相机贴图优化、几何 LOD、视口显示控制、材质细节控制和数据清理整合在 3D 视图侧栏中。

The tools are designed to help with different stages of a project. Use the analyzers to locate heavy content, then choose a targeted optimization. For a final animation render, use **Animation Optimization** to analyze the whole timeline and create a separate optimized project copy.

这些工具适用于制作流程中的不同阶段。先用分析器找到高负载内容，再针对性优化。动画最终渲染可使用「动画优化」扫描整段时间线，并生成独立的优化版工程副本。

## What's new in 3.0.0 | 3.0.0 版本更新

### Render Profiles | 渲染优化方案

Create named profiles, choose a render camera and optional collection scope, and capture a snapshot before making changes. A profile tracks generated geometry modifiers and material variants so restoration can target the state recorded for that profile.

可以创建多个具名方案，为每个方案指定渲染相机和可选集合范围，并在优化前记录场景状态。生成的几何修改器和材质变体会关联到方案，恢复时按该方案记录的状态处理。

### Animation Optimization | 动画优化

Analyze a timeline range at a configurable step, including its endpoints and camera cuts. LODify finds each visible mesh's highest sampled screen-space demand, then uses a fixed geometry setting and shared-image resolution for the generated animation copy.

按可调整的步长分析指定时间范围，并额外检查首尾帧和切镜帧。LODify 记录每个网格物体在采样帧中的最高屏幕需求，再以固定几何参数和共享贴图分辨率生成动画优化副本。

### Safer optimization workflow | 更可控的优化流程

- Geometry and shader changes can be associated with the active profile.
- Generated texture sets keep source images available for switching back.
- Image processing uses worker processes for supported file-based images.
- Destructive cleanup is no longer run automatically as a side effect of unrelated actions.
- Blender 5.2 Geometry Nodes modifier inputs use the newer socket API when available.

- 几何与材质优化可以关联到当前方案。
- 生成贴图集保留原图路径，便于切回原始贴图。
- 支持的本地图片由 worker 子进程处理。
- 不会再因为其他操作而自动执行破坏性的全局清理。
- Blender 5.2 几何节点修改器输入在可用时使用新版接口。

See [RELEASE.md](RELEASE.md) for the detailed 3.0.0 release notes.

## Quick start | 快速开始

1. Install LODify and open a project in Blender.
2. In the 3D View, open the sidebar with `N`, then select **Optimize**.
3. Create or select a render profile. Set its camera and optional collection scope.
4. Use the relevant analyzer or optimization panel for the work you need.
5. For animation, save the project first, then follow the three steps below.

1. 安装 LODify 并在 Blender 中打开工程。
2. 在 3D 视图按 `N` 展开侧栏，选择 **Optimize** 标签。
3. 新建或选择渲染方案，设置相机和可选集合范围。
4. 根据当前需求使用对应的分析器或优化面板。
5. 动画优化需要先保存工程，再按下方三步操作。

```text
Save the project → Analyze Animation → Generate Optimized Copy
保存工程       → 分析动画       → 生成优化副本
```

The generated `.blend` is a separate file. The source project remains available, and the optimized file uses a companion texture folder beside it.

生成的 `.blend` 是单独的文件。源工程仍可继续使用，优化版工程会引用旁边生成的贴图目录。

## Animation optimization | 动画优化

Animation Optimization is intended for **final rendering**. It analyzes one camera path across the scene timeline and produces one stable optimization for the whole range. Per-camera versions and viewport playback acceleration are outside this first release.

「动画优化」面向**最终渲染**。它沿场景时间线分析相机路径，并为整段范围生成一套稳定的优化结果。按镜头拆分方案和视口播放加速不属于本版功能。

### Use it in three steps | 三步完成

1. **Save the source `.blend`.** The operator writes the optimized copy beside this file.
2. **Analyze Animation.** Review the frame, object, image, and skipped-item counts. Expand the recommendation details only when you need to inspect individual items.
3. **Generate Optimized Copy.** LODify writes `<project>_animation_optimized.blend` and `<project>_animation_textures/` next to the source project.

1. **先保存源 `.blend`。** 优化副本会写到源文件旁边。
2. **点击「分析动画」。** 查看采样帧、物体、贴图和跳过项目的数量，需要检查单项时再展开建议详情。
3. **点击「生成优化副本」。** LODify 会在源文件旁边生成 `<工程名>_animation_optimized.blend` 和 `<工程名>_animation_textures/`。

### Defaults and controls | 默认值与可调参数

The scene's start and end frames are used by default. Sampling defaults to every 5 frames. Set the sample step to `1` for every-frame analysis. The first frame, last frame, and each timeline camera marker's neighboring frames are always included.

默认使用场景起止帧，每 5 帧采样一次。将采样步长设为 `1` 可逐帧分析。首帧、尾帧和每个时间线相机标记的前后帧始终会加入采样。

The collapsed **Sampling and camera** controls let you change the sample step or explicitly select one camera. Leave the camera override empty to follow the active camera and timeline camera markers.

展开「采样与相机」可调整采样步长或指定单台相机。相机留空时会跟随场景当前相机和时间线相机标记。

The collapsed **Geometry and texture quality** controls let you choose the geometry method, set the minimum retained geometry ratio and face-count threshold, tune Geometry Nodes merge distance, and adjust the automatic texture-size estimate with a multiplier and maximum size. Change these controls before analysis, then analyze again to refresh the recommendations.

展开「几何与贴图质量」可选择几何算法，设置最低几何保留比例和面数门槛，调整几何节点合并距离，并用倍率和最大尺寸调节贴图自动估算结果。修改这些设置后，需要重新分析以刷新建议。

Texture sizing is automatic and rule-based. It estimates the required long edge from the object's projected screen-space bounds, applies the multiplier, and respects the configured resolution limit. It does not call an AI service.

贴图尺寸采用自动规则估算：根据物体包围盒投影后的屏幕尺寸计算长边需求，再应用倍率和分辨率上限。当前估算不调用 AI 服务。

### What the analysis measures | 分析内容

- At each sampled frame, Blender's evaluated scene is used for camera transforms, object transforms, and mesh bounds.
- Each mesh receives the maximum normalized screen ratio found during the sampled range and the frame where that peak occurred.
- A shared image receives the highest estimated resolution required by any sampled user of that image.
- Objects outside the camera view for the entire sampled range keep their existing geometry settings, since they may still contribute to reflections or shadows.
- Recommendations can be expanded to inspect peak frames, retained geometry factors, texture source and target sizes, and skip reasons.

- 每个采样帧都会读取 Blender 求值后的相机变换、物体变换和网格包围盒。
- 每个网格物体记录采样范围内的最大归一化屏幕占比及对应峰值帧。
- 共享贴图按所有使用物体中的最高估算需求确定尺寸。
- 整段采样都位于镜头外的物体会保留原几何设置，因为它们仍可能参与反射或投影阴影。
- 展开分析建议后，可以查看峰值帧、几何保留比例、贴图原尺寸和目标尺寸，以及跳过原因。

## Features | 功能说明

| Module | English | 中文 |
| --- | --- | --- |
| Render Profiles | Store a camera, optional collection scope, and captured scene state for restoration. | 记录渲染相机、可选集合范围和可恢复的场景状态。 |
| Collection Analyzer | Compare vertex load across collections and optionally display heatmap colors. | 对比各集合的顶点负载，并可用热力色标显示。 |
| View Analyzer | Highlight relatively dense mesh objects in the current view layer. | 在当前视图层中标出相对高密度的网格物体。 |
| Image Resizer | Resize selected images to a target long-edge size and optionally save copies. | 将选中的图片缩放到目标长边尺寸，并可另存副本。 |
| Camera Optimization | Estimate image sizes from one profile camera and generate a camera-specific texture set. | 根据方案相机估算贴图需求，并生成相机专用贴图集。 |
| Geometry LOD | Use Decimate or Geometry Nodes with screen-ratio-driven settings and safety limits. | 使用 Decimate 或 Geometry Nodes，依据屏幕占比调整强度并提供保护阈值。 |
| Animation Optimization | Use peak demand over sampled frames to generate one fixed LOD and texture set. | 按采样帧峰值需求为整段动画生成固定 LOD 和贴图集。 |
| Viewport LOD | Change distant objects' display mode or optionally hide them. | 切换远景物体的显示模式，也可选择隐藏。 |
| Shader Detail LOD | Adjust supported normal, bump, and displacement node values by distance. | 按距离调整受支持的法线、凹凸和置换节点数值。 |
| Cleanup and Storage | Merge duplicate image references, remove unused material slots, and manage generated texture folders. | 合并重复图片引用、清理无用材质槽并管理生成的贴图目录。 |

### Geometry LOD | 几何 LOD

The regular Geometry LOD panel updates profile-owned Decimate or Geometry Nodes modifiers from screen coverage and the selected camera. It offers setup, update, reset, and apply operations. **Apply** is destructive to the current mesh data, so use a profile snapshot or save a copy before applying.

普通「几何 LOD」面板会根据屏幕占比和所选相机更新归属于方案的 Decimate 或 Geometry Nodes 修改器，并提供创建、更新、重置和应用操作。「应用」会直接改写当前网格数据，建议先记录方案或另存工程。

### Image and camera tools | 贴图与相机工具

Image Resizer handles selected images with a target maximum size and copy options. Camera Optimization uses the active profile camera to estimate texture demand for the current scene view and writes a generated texture set. The original images remain available for switching back through the image controls.

「贴图缩放」按目标最大尺寸处理所选图片，并提供副本选项。「相机优化」使用当前方案相机估算当前场景视角下的贴图需求，并生成贴图集。图片控制项保留切回原图的入口。

## Safety and supported data | 安全与支持范围

### Animation geometry | 动画几何

Animation Optimization supports static meshes and meshes animated only through object location, rotation, or scale. These meshes receive one fixed modifier value derived from their peak sampled screen ratio.

动画优化支持静态网格，以及仅通过物体位置、旋转或缩放进行动画的网格。此类网格会按采样到的最高屏幕占比获得一组固定修改器参数。

Meshes with shape keys, armature deformation, cloth or other simulation, animated mesh data, animated non-transform properties, or unsupported modifier behavior are kept unchanged and listed in the report. Geometry that changes topology over time is not reduced by this first version.

含形态键、骨骼变形、布料或其他模拟、动画网格数据、非变换属性动画或不受支持修改器行为的网格会保留原样，并在报告中列出。拓扑随时间变化的几何不由首版减面。

### Animation images | 动画贴图

Regular file-backed static images are eligible for resizing. The source image is kept, and the optimized project points to a generated copy. HDR and EXR files are copied without resizing to preserve their high-dynamic-range data.

普通的本地静态图片文件可以缩放。原图会保留，优化版工程改为引用生成的副本。HDR 和 EXR 文件为保护高动态范围数据只复制，不缩放。

Image sequences, movies, UDIM tiles, generated or viewer images, packed images, and files whose source path cannot be resolved remain unchanged. The analysis report lists images it could not process.

图片序列、视频、UDIM、生成或 Viewer 图片、打包图片以及无法定位源文件的图片会保持原样。分析报告会列出未处理的图片。

### Project files | 工程文件

Animation generation requires the source `.blend` to be saved. It writes a separate optimized `.blend` and a companion texture directory. Review the generated copy and its texture folder together when moving or archiving the result.

生成动画优化副本前必须先保存源 `.blend`。功能会另写优化版 `.blend` 和配套贴图目录。移动或归档结果时，请同时保留工程文件与贴图目录。

## Install | 安装

### Blender Extension | Blender 扩展安装

1. Download the ZIP package from [GitHub Releases](https://github.com/XIAOTsune/LODify/releases).
2. In Blender, open **Edit → Preferences → Get Extensions**.
3. Select **Install from Disk…** and choose the downloaded ZIP.
4. In the 3D View, press `N` and open the **Optimize** tab.

1. 从 [GitHub Releases](https://github.com/XIAOTsune/LODify/releases) 下载 ZIP 安装包。
2. 在 Blender 中打开 **Edit → Preferences → Get Extensions**。
3. 点击 **Install from Disk…**，选择下载的 ZIP。
4. 在 3D 视图按 `N`，打开 **Optimize** 标签。

### Install a local test build | 安装本地测试包

Python 3.10 or newer can build the deterministic test package from the repository root:

在仓库根目录使用 Python 3.10 或更新版本构建本地测试包：

```powershell
python scripts/build_release.py
```

The package is written to `dist/LODifyv3.0.0.zip`; a `.sha256` checksum file is written beside it. Install it using the same **Install from Disk…** command.

安装包会生成在 `dist/LODifyv3.0.0.zip`，旁边会附带 `.sha256` 校验文件。使用同一个 **Install from Disk…** 菜单安装即可。

## Requirements and packaging | 环境与打包

- Blender 4.2 or newer.
- Windows x64 is the packaged target for 3.0.0.
- The extension manifest bundles Pillow wheels for supported Windows Blender Python versions. Image operations that require Pillow depend on the bundled runtime being available.
- Animation sampling and Blender data access run in Blender's main thread. Supported image resizing is dispatched to worker processes.

- Blender 4.2 或更新版本。
- 3.0.0 的预打包目标为 Windows x64。
- 扩展清单附带面向受支持 Blender Python 版本的 Pillow wheel。需要 Pillow 的贴图操作依赖扩展环境正确加载该组件。
- 动画采样和 Blender 数据访问在 Blender 主线程执行，支持的图片缩放由 worker 子进程处理。

The local package builder uses the explicit file list in `[build].paths`, validates the Blender manifest and legacy `bl_info` version, checks the archive contents, and writes a SHA-256 sidecar. See [RELEASE.md](RELEASE.md) for version notes and the local build workflow.

本地打包脚本根据 `[build].paths` 中的文件清单构建，检查 Blender manifest 与旧版 `bl_info` 的版本一致性、ZIP 内容完整性，并生成 SHA-256 文件。版本说明和打包流程见 [RELEASE.md](RELEASE.md)。

## Credits | 致谢

Core analysis ideas and parts of the UI layout were inspired by Rodrigo Gama's **ToOptimize Tools**. LODify adds its own profile workflow, Geometry Nodes integration, asynchronous image processing, and camera-based optimization tools.

核心分析思路与部分界面布局参考了 Rodrigo Gama 的 **ToOptimize Tools**。LODify 在此基础上加入了渲染方案、Geometry Nodes 集成、异步图片处理和相机优化工具。
