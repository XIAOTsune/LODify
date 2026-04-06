# LODify

<div align="center">

### Optimize heavy Blender scenes with a workflow that actually feels usable.
### 用一套真正顺手的工作流，优化沉重的 Blender 大场景。

[![Blender](https://img.shields.io/badge/Blender-4.2%2B-E87D0D?style=for-the-badge&logo=blender&logoColor=white)](https://www.blender.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20x64-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/XIAOTsune/LODify)
[![Version](https://img.shields.io/badge/Version-2.9.0-111111?style=for-the-badge)](https://github.com/XIAOTsune/LODify/releases)

[Download Release](https://github.com/XIAOTsune/LODify/releases) · [View Repository](https://github.com/XIAOTsune/LODify)

</div>

---

## Overview | 简介

**LODify** is a Blender optimization add-on for large and complex scenes.  
It helps you find bottlenecks, reduce texture cost, simplify geometry, lighten viewport display, and clean messy scene data in one place.

**LODify** 是一个面向大型复杂场景的 Blender 优化插件。  
它把性能定位、贴图优化、几何 LOD、视口降载和数据清理整合到同一套工作流里。

### Built for scenes that feel like this | 它适合这样的场景

- viewport navigation is getting slow
- textures are oversized
- geometry is too dense for iteration
- distant assets are wasting detail
- scene data is duplicated or messy

- 视口操作越来越卡
- 贴图分辨率明显过高
- 模型面数太重，不方便继续制作
- 远景物体浪费了大量细节
- 场景里有重复贴图和混乱数据

---

## Why LODify | 为什么用它

<table>
  <tr>
    <td width="33%">
      <strong>Find problems first</strong><br/>
      Analyze collections and objects before you touch anything.
      <br/><br/>
      <strong>先找问题</strong><br/>
      在真正动手优化前，先找出最重的区域和物体。
    </td>
    <td width="33%">
      <strong>Optimize by importance</strong><br/>
      Use distance and screen coverage instead of blind global reduction.
      <br/><br/>
      <strong>按重要性优化</strong><br/>
      不是全局一刀切，而是按距离和屏幕占比来决定强度。
    </td>
    <td width="33%">
      <strong>Keep iteration smooth</strong><br/>
      Async processing and reset flows make experimentation safer.
      <br/><br/>
      <strong>更适合迭代</strong><br/>
      异步处理和重置机制让你可以边试边调，不容易把场景搞乱。
    </td>
  </tr>
</table>

---

## At a Glance | 一眼看懂

| Module | What it does | 模块 | 它做什么 |
|---|---|---|---|
| Collection Analyzer | Finds heavy collections with labels or heatmap colors | Collection Analyzer | 用百分比和热力色标找出高负载 Collection |
| 3D View Analyzer | Highlights dense objects directly in the viewport | 3D View Analyzer | 在视口里直接标出高密度物体 |
| Image Resizer | Batch resizes textures with safe-copy options | Image Resizer | 批量缩放贴图，支持安全副本模式 |
| Camera Optimization | Generates texture sets based on camera screen coverage | Camera Optimization | 按相机视角生成更合理的贴图集 |
| Geometry LOD | Reduces mesh cost with Decimate or Geometry Nodes | Geometry LOD | 通过 Decimate 或 Geometry Nodes 降低几何成本 |
| Viewport LOD | Downgrades display mode for distant objects | Viewport LOD | 让远景物体以更轻量的方式显示 |
| Shader Detail LOD | Lowers normal, bump, displacement strength at distance | Shader Detail LOD | 在远距离降低法线、凹凸、置换强度 |
| Cleanup Tools | Merges duplicate images and cleans material slots | Cleanup Tools | 清理重复图片引用和无用材质槽 |

---

## Core Advantages | 核心优势

### 1. One add-on, full optimization workflow

You do not need separate tools for analysis, texture reduction, geometry simplification, viewport management, and scene cleanup.

### 1. 一个插件，覆盖完整优化链路

不需要再把分析、贴图压缩、减面、视口降载、数据清理拆到多个工具里做。

### 2. Camera-aware, not blind optimization

LODify does not just reduce everything globally.  
It uses distance and screen-space importance so large close objects keep detail while tiny far assets get lighter treatment.

### 2. 基于相机和屏幕占比，而不是盲目降级

LODify 不会简单粗暴地全局统一减配。  
它会根据距离和屏幕占比判断谁应该保留细节，谁应该被优先优化。

### 3. Safer for real production scenes

Several tools preserve original states and provide reset actions, so you can test optimization strategies without immediately committing to destructive changes.

### 3. 更适合真实生产场景

多个模块都保留原始状态并提供重置入口，你可以先试效果，再决定是否应用不可逆操作。

### 4. Better responsiveness for batch tasks

Heavy image work is pushed into a subprocess worker, and several batch operations run in async-style modal flows to reduce UI freezing.

### 4. 批处理时更流畅

高负载图片处理会交给子进程 worker，部分批量任务也采用异步式流程，尽量减少 Blender 主界面卡顿。

---

## Feature Breakdown | 功能拆解

### Collection Analyzer

**EN**
- measures vertex load across collections
- adds percentage suffixes to names
- can apply heatmap colors for quick scanning

**中文**
- 统计各 Collection 的顶点负载
- 自动在名称后追加占比信息
- 可用热力色标快速定位重区

### 3D View Analyzer

**EN**
- colors mesh objects by relative density
- instantly reveals heavy objects in the current view layer
- restores original object colors safely

**中文**
- 根据相对密度给 Mesh 物体着色
- 一眼看出当前视图层里谁最重
- 可安全恢复原始颜色

### Image Resizer

**EN**
- scans all scene textures
- estimates memory usage
- resizes selected textures in batch
- supports safe-copy output instead of overwriting originals
- supports switching between original and generated texture sets

**中文**
- 扫描场景贴图
- 估算贴图内存占用
- 批量缩放选中的图片
- 支持输出副本而不是覆盖原图
- 支持在原图和生成贴图集之间切换

### Camera Optimization

**EN**
- estimates required texture size from active camera coverage
- creates a camera-optimized texture set automatically
- reduces waste on barely visible assets

**中文**
- 根据当前相机估算贴图真正需要的尺寸
- 自动生成相机专用优化贴图集
- 避免把分辨率浪费在几乎看不见的物体上

### Geometry LOD

**EN**
- supports both `Decimate` and `Geometry Nodes`
- updates geometry detail by normalized screen ratio
- includes safety limits like minimum faces and minimum retained ratio
- supports setup, update, reset, and destructive apply

**中文**
- 同时支持 `Decimate` 和 `Geometry Nodes`
- 按归一化屏幕占比更新几何细节
- 提供最小面数保护和最低保留比例
- 支持 setup、update、reset 和最终应用

### Viewport LOD

**EN**
- switches distant objects to lighter display modes
- supports `Textured`, `Solid`, `Wire`, and `Bounds`
- can hide very distant objects
- restores original display and hidden state safely

**中文**
- 自动把远景物体切换成更轻量的显示模式
- 支持 `Textured`、`Solid`、`Wire`、`Bounds`
- 可选隐藏极远物体
- 可安全恢复原始显示和隐藏状态

### Shader Detail LOD

**EN**
- reduces `Normal Map`, `Bump`, and `Displacement` intensity by distance
- preserves close-up detail where it matters
- cuts material overhead for large environments

**中文**
- 按距离降低 `Normal Map`、`Bump`、`Displacement` 强度
- 近景保留细节，远景减少浪费
- 适合大型环境场景和重复资产

### Cleanup and Storage

**EN**
- merges duplicate image references like `.001`
- removes unused material slots
- manages generated `textures_*` folders from inside Blender

**中文**
- 合并 `.001` 这类重复图片引用
- 清理未使用材质槽
- 可直接管理生成的 `textures_*` 文件夹

---

## Typical Workflow | 推荐使用流程

```text
Analyze scene
   ↓
Find heavy collections / objects
   ↓
Resize textures or run Camera Optimization
   ↓
Set up Geometry LOD
   ↓
Enable Viewport LOD
   ↓
Optionally reduce Shader Detail
   ↓
Clean duplicate data and storage folders
```

```text
分析场景
   ↓
找出高负载 Collection / 物体
   ↓
缩放贴图或运行相机优化
   ↓
设置 Geometry LOD
   ↓
启用 Viewport LOD
   ↓
按需降低 Shader Detail
   ↓
清理重复数据和贴图目录
```

---

## How It Works | 实现方式

### EN

LODify combines scene analysis, screen-space estimation, distance rules, and non-blocking batch processing:

- collection and object analyzers expose hotspots visually
- texture tools scan image data and generate resized copies
- camera optimization projects object bounds into screen space to estimate required texture size
- geometry LOD maps screen importance to reduction strength
- viewport and shader LOD downgrade distant assets while keeping reset paths
- heavy image processing is delegated to `core/image_worker.py` through a subprocess

### 中文

LODify 的实现思路是把“先分析，再执行”做成可控工作流：

- Collection 和物体分析器先把热点直观标出来
- 贴图工具会扫描图片并生成缩放后的贴图副本
- 相机优化通过物体包围盒投影估算屏幕占比，决定贴图实际需求
- 几何 LOD 会把屏幕重要性映射成减面强度
- 视口 LOD 和材质 LOD 主要针对远景对象做降级
- 高负载图片处理交给 `core/image_worker.py` 子进程执行

---

## Installation | 安装方式

1. Download the latest zip from [Releases](https://github.com/XIAOTsune/LODify/releases).
2. Open Blender.
3. Go to `Edit -> Preferences -> Get Extensions`.
4. Click `Install from Disk...`.
5. Select the downloaded package.
6. Open the `Optimize` tab in the 3D View sidebar.

1. 从 [Releases](https://github.com/XIAOTsune/LODify/releases) 下载最新 zip。
2. 打开 Blender。
3. 进入 `Edit -> Preferences -> Get Extensions`。
4. 点击 `Install from Disk...`。
5. 选择下载好的安装包。
6. 在 3D View 侧边栏打开 `Optimize` 标签页。

---

## Requirements | 环境要求

- Blender `4.2+`
- Windows `x64`
- Bundled Pillow wheels are currently prepared for Windows builds

- Blender `4.2+`
- Windows `x64`
- 当前发布包附带的 Pillow 依赖主要面向 Windows

---

## Repository Structure | 仓库结构

| Path | Purpose |
|---|---|
| `blender_manifest.toml` | Blender Extensions manifest |
| `core/image_worker.py` | subprocess worker for image processing |
| `operators/` | analyzers, texture tools, geometry, viewport, shader operators |
| `ui/` | Blender panels and list UI |
| `wheels/` | bundled Pillow wheels |

| 路径 | 说明 |
|---|---|
| `blender_manifest.toml` | Blender Extensions 清单文件 |
| `core/image_worker.py` | 图片处理子进程 worker |
| `operators/` | 分析、贴图、几何、视口、材质等功能实现 |
| `ui/` | Blender 面板和列表界面 |
| `wheels/` | 打包附带的 Pillow 依赖 |

---

## Credits | 致谢

Core analysis ideas and parts of the UI layout were inspired by Rodrigo Gama's **ToOptimize Tools**.  
LODify extends that direction with a refactored structure and added workflows such as Geometry Nodes integration, async image processing, and camera-based optimization.

核心分析思路与部分界面布局参考了 Rodrigo Gama 的 **ToOptimize Tools**。  
LODify 在此基础上进行了结构重构，并扩展了 Geometry Nodes 集成、异步图片处理和相机视角优化等工作流。

---

## Final Pitch | 收尾文案

**LODify is for the moment when your Blender scene still needs to grow, but your viewport already wants to give up.**  
**LODify 适合那种“项目还要继续做，但视口已经快撑不住”的时刻。**
