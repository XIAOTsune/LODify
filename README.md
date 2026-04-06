# LODify

> Blender large-scene optimizer for textures, geometry, viewport display, and scene cleanup.  
> 面向 Blender 大场景的综合优化插件，覆盖贴图、几何、视口显示与场景清理。

<p align="center">
  <a href="https://github.com/XIAOTsune/LODify/releases">Releases</a> ·
  <a href="https://github.com/XIAOTsune/LODify">GitHub</a>
</p>

---

## EN | What Is LODify?

LODify is a practical optimization toolkit for Blender scenes that are getting too heavy to edit smoothly.

Instead of focusing on only one bottleneck, it gives you a full workflow:

- find heavy collections and objects fast
- batch resize textures safely
- generate geometry LOD by screen importance
- reduce viewport cost for distant objects
- simplify shader detail at distance
- clean duplicated image data and unused material slots

It is designed for artists and technical users who want faster iteration without manually rebuilding an optimization pipeline from scratch.

## 中文 | LODify 是什么？

LODify 是一个面向 Blender 大场景的实用优化工具集，适合处理“场景太重、编辑卡顿、视口吃力、贴图太大”的工作场景。

它不是只解决单一问题，而是把常见优化流程整合到一个插件里：

- 快速找出高负载 Collection 和高负载物体
- 安全地批量缩放贴图
- 按屏幕占比生成几何 LOD
- 按距离降低视口显示开销
- 远距离降低材质细节强度
- 清理重复图片数据和未使用材质槽

目标很直接：让你更快定位瓶颈，更快优化，更少手工重复劳动。

---

## EN | Why It Stands Out

- One add-on, multiple optimization layers  
  Texture, geometry, viewport, shader, and cleanup tools live in one workflow.

- Built for real production friction  
  The tools target the things that usually slow Blender down first: oversized textures, dense meshes, distant objects, and messy scene data.

- Async where it matters  
  Expensive image operations and several batch updates are processed in a non-blocking way to keep the UI responsive.

- Safer than brute-force optimization  
  LODify stores original states where needed and offers reset flows for viewport, shader, and geometry operations.

- Camera-aware decisions  
  Instead of optimizing blindly, several features estimate on-screen importance and adjust output accordingly.

## 中文 | 它的优势是什么？

- 一个插件覆盖多层优化  
  贴图、几何、视口、材质、清理工具集中在同一套工作流里。

- 面向真实的大场景痛点  
  它优先解决最常见的性能瓶颈：大贴图、高面数、远景物体、混乱的数据引用。

- 关键流程采用异步处理  
  图片处理和部分批量更新不会粗暴卡死 Blender 界面，交互体验更稳定。

- 比“硬砍性能”更安全  
  多个模块都保留原始状态或提供重置入口，适合边看效果边调整。

- 带有相机感知能力  
  部分优化不是盲目统一降级，而是基于物体在屏幕中的实际重要性做判断。

---

## EN | Core Features

### 1. Collection Analyzer

- analyzes vertex weight across collections
- can append percentage labels to collection names
- can also use heatmap colors for a quick visual scan

Useful for understanding which part of a scene is actually heavy before changing anything.

### 2. 3D View Analyzer

- colors mesh objects by relative density in the current view layer
- makes heavy objects obvious at a glance
- restores original object colors safely

### 3. Async Texture Resizer

- scans scene images and shows estimated memory usage
- batch resizes selected textures
- supports safe copy mode instead of overwriting originals
- can write resized files to the blend directory or a custom output path
- supports switching between original and generated texture sets

### 4. Camera Optimization

- estimates on-screen texture demand from the active camera
- generates a camera-optimized texture set automatically
- avoids wasting resolution on objects that barely occupy pixels

### 5. Geometry LOD

- supports two workflows:
  - Decimate Modifier
  - Geometry Nodes based LOD
- updates LOD by screen ratio instead of only raw distance
- includes safety floors such as minimum face count and minimum retained ratio
- can batch setup, update, reset, or destructively apply results

### 6. Viewport LOD

- changes object display mode by distance
- supports textured, solid, wire, and bounds display
- can optionally hide very distant objects
- restores original display and hidden state safely

### 7. Shader Detail LOD

- reduces Normal Map, Bump, and Displacement intensity by distance
- keeps close-up detail where it matters
- lowers shading cost on distant assets

### 8. Cleanup and Storage Tools

- merges duplicate image references such as `.001`
- removes unused material slots
- manages generated `textures_*` folders from inside Blender

## 中文 | 核心功能

### 1. Collection Analyzer

- 统计各 Collection 的顶点负载占比
- 可把占比直接写到 Collection 名称后缀
- 也可使用热力色标快速查看密度分布

适合在正式优化前先定位“到底哪一组最重”。

### 2. 3D View Analyzer

- 按相对顶点密度给物体着色
- 一眼看出当前视图里谁最重
- 可安全恢复原始颜色

### 3. 异步贴图缩放

- 扫描场景贴图并显示估算内存占用
- 批量缩放选中的图片
- 支持安全模式，生成副本而不是覆盖原图
- 可输出到 `.blend` 目录或自定义目录
- 可在原图与生成后的多个贴图集之间切换

### 4. 相机视角优化

- 基于当前相机估算贴图在屏幕上的实际需求
- 自动生成相机专用优化贴图集
- 避免把分辨率浪费在几乎看不见的物体上

### 5. 几何 LOD

- 支持两种工作流：
  - Decimate Modifier
  - 基于 Geometry Nodes 的 LOD
- 根据屏幕占比而不是纯距离更新几何细节
- 提供最小面数保护、最小保留比例等安全阈值
- 支持批量 setup、update、reset 和最终应用

### 6. 视口 LOD

- 按距离自动切换物体显示模式
- 支持 `Textured`、`Solid`、`Wire`、`Bounds`
- 可选择隐藏极远物体
- 可安全恢复原始显示与隐藏状态

### 7. 材质细节 LOD

- 按距离降低 `Normal`、`Bump`、`Displacement` 强度
- 近景保留细节，远景降低开销
- 适合大型环境场景和重复资产

### 8. 清理与存储管理

- 合并 `.001` 这类重复图片引用
- 清理未使用的材质槽
- 在 Blender 内直接管理生成的 `textures_*` 文件夹

---

## EN | How It Works

LODify uses a mix of scene analysis, distance-based rules, and screen-space estimation:

- Collection and object analyzers measure scene density and expose hotspots visually.
- Texture tools scan image data, estimate memory cost, and batch-generate resized copies.
- Camera optimization calculates approximate screen coverage from object bounds and camera projection.
- Geometry LOD converts screen importance into reduction strength, using either Decimate or a generated Geometry Nodes group.
- Viewport and shader LOD downgrade only when objects move farther away, while keeping reset paths available.
- Heavy image processing is delegated to a subprocess worker so Blender stays more responsive during batch tasks.

## 中文 | 它是怎么实现的？

LODify 的实现思路是把“分析”和“执行优化”分开：

- 先通过 Collection / 物体分析找出高负载区域。
- 再通过贴图扫描、屏幕占比估算、距离分级等方式决定优化强度。
- 相机优化会根据包围盒投影到屏幕后的占比，估算贴图真正需要的像素级别。
- 几何 LOD 会把屏幕重要性映射成减面强度，可走 `Decimate`，也可走自动构建的 `Geometry Nodes`。
- 视口 LOD 和 Shader LOD 则按距离逐级降级，尽量把性能节省在远景对象上。
- 大批量贴图处理交给独立 worker 子进程执行，以减少 Blender 主线程卡顿。

---

## EN | Typical Workflow

1. Run the analyzers to find the real hotspots.
2. Resize textures or generate a camera-optimized texture set.
3. Configure Geometry LOD and update it from the chosen camera.
4. Enable Viewport LOD for smoother scene navigation.
5. Optionally reduce shader detail on distant assets.
6. Clean duplicate images and unused material slots.

## 中文 | 推荐使用流程

1. 先运行分析器，确认真正的性能热点。
2. 批量缩放贴图，或生成相机专用优化贴图集。
3. 设置 Geometry LOD，并基于相机更新几何细节。
4. 开启 Viewport LOD，提升场景浏览流畅度。
5. 需要时再开启 Shader LOD，进一步压低远景材质成本。
6. 最后清理重复图片和未使用材质槽。

---

## EN | Installation

1. Download the latest package from [Releases](https://github.com/XIAOTsune/LODify/releases).
2. Open Blender.
3. Go to `Edit -> Preferences -> Get Extensions`.
4. Choose `Install from Disk...` and select the downloaded zip.
5. Open the `Optimize` tab in the 3D View sidebar.

## 中文 | 安装方式

1. 从 [Releases](https://github.com/XIAOTsune/LODify/releases) 下载最新版本。
2. 打开 Blender。
3. 进入 `Edit -> Preferences -> Get Extensions`。
4. 使用 `Install from Disk...` 选择下载好的 zip 包。
5. 安装后，在 3D View 侧边栏打开 `Optimize` 标签页。

---

## EN | Requirements

- Blender `4.2+`
- Windows `x64`

Current extension packaging includes bundled Pillow wheels for Windows.

## 中文 | 环境要求

- Blender `4.2+`
- Windows `x64`

当前发布包内置的 Pillow wheel 主要面向 Windows。

---

## EN | Repository Structure

- `blender_manifest.toml`: Blender Extensions manifest
- `core/image_worker.py`: subprocess worker for async image tasks
- `operators/`: feature operators for analyzers, image tools, geometry, viewport, and shader LOD
- `ui/`: Blender panels and list UI
- `wheels/`: bundled Pillow wheels for supported Windows Python versions

## 中文 | 仓库结构

- `blender_manifest.toml`：Blender Extensions 清单文件
- `core/image_worker.py`：异步图片处理使用的子进程 worker
- `operators/`：分析、贴图、几何、视口、材质 LOD 等功能实现
- `ui/`：Blender 面板与列表界面
- `wheels/`：发布包附带的 Windows Pillow 依赖

---

## EN | Credits

Core analysis ideas and parts of the UI layout were inspired by Rodrigo Gama's "ToOptimize Tools".  
LODify extends that direction with a refactored structure and added workflows such as Geometry Nodes integration, async image processing, and camera-based optimization.

## 中文 | 致谢

核心分析思路与部分界面布局参考了 Rodrigo Gama 的 "ToOptimize Tools"。  
LODify 在此基础上进行了结构重构，并扩展了 `Geometry Nodes` 集成、异步图片处理、相机视角优化等工作流。
