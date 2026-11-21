# LODify 3.0.0

### Render Profiles · Safer Scene Optimization · Animation LOD
### 渲染方案 · 更可控的场景优化 · 动画 LOD

LODify 3.0.0 brings a profile-based foundation to the add-on and adds a first animation optimization workflow for final rendering. This release focuses on capturing the state before optimization, associating generated changes with a profile, and writing animation results to a separate project copy.

LODify 3.0.0 为插件引入了基于渲染方案的基础架构，并加入首版面向最终渲染的动画优化流程。本次更新重点是记录优化前状态、让生成的优化内容归属于具体方案，以及将动画优化结果写入独立工程副本。

---

## Highlights | 版本亮点

### Render Profiles | 渲染优化方案

- Create multiple named profiles in a scene.
- Assign a camera and optionally limit a profile to one collection.
- Capture object, mesh, material-slot, modifier, image-path, and related scene state before editing.
- Track generated geometry modifiers and shader variants by profile so restore operations can target the active profile.
- Use the profile's camera and collection scope in camera-aware optimization tools.

- 在同一场景中创建多个具名方案。
- 为方案指定渲染相机，并可选择将作用范围限制在某个集合。
- 在编辑前记录物体、网格、材质槽、修改器、图片路径和相关场景状态。
- 按方案跟踪生成的几何修改器和材质变体，恢复操作可针对当前方案执行。
- 相机相关优化工具可读取方案相机和集合范围。

### Animation Optimization | 动画优化

- Analyze the scene's frame range with a configurable sampling step. The default is every 5 frames.
- Always sample the range endpoints and frames immediately before and after timeline camera cuts.
- Follow timeline camera markers by default, or explicitly select one camera for the full analysis.
- Read evaluated camera transforms, evaluated object transforms, and evaluated mesh bounds at each sample.
- Select the highest sampled screen-space geometry demand per object and the highest texture demand per shared image.
- Keep one fixed geometry modifier setting and one texture resolution per image for the generated animation copy.
- Review each peak frame, geometry recommendation, texture size estimate, and skip reason in the report.
- Cancel analysis and restore the previous frame, subframe, active camera, and temporarily disabled LOD modifier visibility.
- Generate `<project>_animation_optimized.blend` with a companion `<project>_animation_textures/` directory.

- 按可调整的步长分析场景帧范围，默认每 5 帧采样一次。
- 始终检查范围首尾帧，以及时间线切镜前后的帧。
- 默认跟随时间线相机标记，也可显式指定一台相机完成全部分析。
- 每个采样点读取求值后的相机变换、物体变换和网格包围盒。
- 每个物体使用采样到的最高屏幕几何需求，每张共享贴图使用最高分辨率需求。
- 优化版动画在整段范围内使用固定几何参数和固定贴图分辨率。
- 报告可查看各项峰值帧、几何建议、贴图尺寸估算和跳过原因。
- 取消分析时恢复原帧、子帧、活动相机以及分析期间临时关闭的 LOD 修改器可见状态。
- 生成 `<工程名>_animation_optimized.blend` 和配套 `<工程名>_animation_textures/` 目录。

### Profile-aware Geometry and Materials | 方案关联的几何与材质优化

- Protect modifiers owned by another profile from unrelated update, apply, or reset operations.
- Preserve compatibility paths for older LODify-created modifiers and stored scene values.
- Read and write Geometry Nodes modifier inputs through APIs available in Blender 4.x and 5.2+.
- Keep source image references available when generated texture variants are selected or restored.

- 防止某个方案的更新、应用或重置操作误改其他方案拥有的修改器。
- 兼容旧版 LODify 创建的修改器和已保存场景参数。
- 通过 Blender 4.x 与 5.2+ 可用的接口读取和写入 Geometry Nodes 修改器输入。
- 选择或恢复生成贴图时保留原始图片引用。

### Reliability and workflow | 稳定性与工作流

- Camera optimization and image resizing continue to use worker processes for supported file-backed image tasks.
- Cancellation paths terminate active image workers where supported.
- Unrelated actions no longer trigger a global orphan-data purge.
- Generated texture-folder removal validates the selected folder name and location.
- The release package uses an explicit file list and includes bundled Pillow wheels for its supported Windows target.

- 相机优化和贴图缩放继续使用 worker 子进程处理受支持的本地图片。
- 支持取消的图片任务会终止仍在运行的 worker。
- 其他操作不会再附带执行全局孤立数据清理。
- 删除生成贴图目录前会验证目录名称和位置。
- 发布包使用明确的文件清单，并为支持的 Windows 目标附带 Pillow wheel。

---

## Animation optimization workflow | 动画优化操作流程

1. Save the source `.blend` file.
2. Open **3D View → Sidebar → Optimize → Animation Optimization**.
3. Optionally open **Sampling and camera** to change the sample step or choose a camera. The default follows timeline camera cuts.
4. Optionally open **Geometry and texture quality** to tune the geometry method, protection threshold, texture multiplier, or maximum size.
5. Click **Analyze Animation** and inspect the summary. Expand recommendations only when you need per-object or per-image details.
6. Click **Generate Optimized Copy**. The source `.blend` remains separate from the generated file.

1. 保存源 `.blend` 工程。
2. 打开 **3D View → Sidebar → Optimize → Animation Optimization**。
3. 可展开「采样与相机」调整采样步长或指定相机。默认跟随时间线切镜。
4. 可展开「几何与贴图质量」调整几何算法、保护阈值、贴图倍率或最大尺寸。
5. 点击「分析动画」并查看概要。需要逐项检查时再展开详细建议。
6. 点击「生成优化副本」。源 `.blend` 与生成文件相互独立。

The texture-size multiplier tunes a deterministic screen-space estimate. Animation texture sizing does not use a remote AI service. Changing analysis controls invalidates the current report, so run analysis again before generating the copy.

贴图倍率用于调整基于屏幕空间的规则估算。动画贴图尺寸不会调用远程 AI 服务。修改分析参数后，当前报告会失效，生成副本前需要重新分析。

---

## Support boundaries | 支持范围

### Geometry

Animation geometry optimization supports static meshes and transform-only object animation. Meshes with shape keys, armature deformation, cloth or other simulation, animated mesh data, animated non-transform properties, or unsupported modifier behavior remain unchanged and are reported. Geometry topology that changes during the timeline is not reduced by this release.

动画几何优化支持静态网格和仅有物体变换动画的网格。含形态键、骨骼变形、布料或其他模拟、动画网格数据、非变换属性动画或不受支持修改器行为的网格会保持原样并写入报告。本版不处理动画期间会改变拓扑的几何。

### Images

Regular static images with an accessible source file can be resized. HDR and EXR images are copied without resizing. Movies, image sequences, UDIM tiles, generated or viewer images, packed images, and unavailable source files are left unchanged and reported.

可以缩放能够访问源文件的普通静态图片。HDR 和 EXR 图片只复制，不缩放。视频、图片序列、UDIM、生成或 Viewer 图片、打包图片和无法访问源文件的图片会保持原样并写入报告。

### Scope of this first animation release

This workflow creates a single stable result for one timeline range. It does not create per-camera output variants or change viewport playback behavior. Texture sizing uses projected bounds, a configurable multiplier, and a maximum size. It is an automatic estimation workflow rather than AI image enhancement.

首版动画流程为一段时间线生成一套稳定结果，不会按相机分别生成多个版本，也不会改变视口播放方式。贴图尺寸根据投影包围盒、可调倍率和最大尺寸进行估算，属于自动尺寸估算，不是 AI 图像增强。

---

## Compatibility | 兼容性

- Blender 4.2 or newer.
- Release package target: Windows x64.
- Manifest version: `3.0.0`.
- Legacy add-on version in `__init__.py`: `(3, 0, 0)`.

- Blender 4.2 或更新版本。
- 发布包目标平台：Windows x64。
- Manifest 版本：`3.0.0`。
- `__init__.py` 中的旧版插件版本：`(3, 0, 0)`。

## Local test package | 本地测试包

From the repository root, run:

在仓库根目录运行：

```powershell
python scripts/build_release.py
```

The script requires Python 3.10 or newer. It validates the manifest version, `bl_info`, explicit `[build].paths`, required package files, and wheel files. It creates `dist/LODifyv3.0.0.zip`, checks the ZIP archive, and writes `dist/LODifyv3.0.0.zip.sha256`.

脚本需要 Python 3.10 或更新版本。它会检查 manifest 版本、`bl_info`、明确的 `[build].paths`、必需文件和 wheel 文件，然后生成 `dist/LODifyv3.0.0.zip`、检查 ZIP 内容，并写入 `dist/LODifyv3.0.0.zip.sha256`。

To select another output directory:

指定其他输出目录：

```powershell
python scripts/build_release.py --output-dir C:\temp\lodify-release
```

Install the generated ZIP through **Edit → Preferences → Get Extensions → Install from Disk…**. Keep the ZIP and its SHA-256 sidecar together when distributing the test build.

通过 **Edit → Preferences → Get Extensions → Install from Disk…** 安装生成的 ZIP。分发测试包时可将 ZIP 与 SHA-256 文件一并提供。

## Versioning and publishing | 版本与发布

The release version is defined in `blender_manifest.toml`. Keep it aligned with the `bl_info` tuple in `__init__.py` and the README version badge. Build and test the package before publishing. A GitHub Release and a Git tag are separate publishing actions from pushing the `main` branch.

发布版本以 `blender_manifest.toml` 为准，并与 `__init__.py` 中的 `bl_info` 版本元组和 README 版本徽章保持一致。发布前先构建并测试安装包。推送 `main` 分支与创建 Git tag、发布 GitHub Release 是不同操作。
