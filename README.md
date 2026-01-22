<div align="center">
 
  <h1>🚀 LODify</h1>
  
  <h3>Full-Scenario Performance Optimization | 全场景性能优化大师</h3>
  <p>
    <b>v2.7</b> • <i>Non-Blocking Architecture</i> • <i>Bundled Dependencies</i> • <i>Color-Safe Analysis</i>
  </p>

  <p>
    <a href="https://www.blender.org/">
      <img src="https://img.shields.io/badge/Blender-4.2%2B-orange?logo=blender&style=for-the-badge" alt="Blender Version">
    </a>
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/License-GPL%20v3-blue.svg?style=for-the-badge" alt="License">
    </a>
    <a href="https://github.com/XIAOTsune/LODify/releases">
      <img src="https://img.shields.io/badge/Download-Latest-green.svg?style=for-the-badge" alt="Download">
    </a>
  </p>

  <br>
  
  <p>
    👇 <b>Select Language / 选择语言</b> 👇
  </p>
  <p>
    <a href="#-english-version">🇺🇸 English Version</a> • 
    <a href="#-cn-中文介绍">🇨🇳 中文介绍</a>
  </p>
</div>

<br>
<hr>

<a name="-english-version"></a>

# 🇺🇸 LODify: Unchain Your Viewport

**LODify** is a comprehensive performance optimization suite designed for massive Blender scenes. The latest version introduces a **Non-Blocking Architecture** and **Smart Worker Processes**, solving UI freezing and VRAM overflow issues in complex architectural or game environment projects.

> **Batteries Included:** This add-on comes with all necessary dependencies (Pillow) bundled. **No manual `pip install` is required.** Just install and optimize.

<br>

## 🔥 Key Features

### 1. 📊 Scene Analyzers (New)
* **Collection Analyzer with Safe Mode:** Instantly calculates vertex count weights for all collections.
    * **Heatmap Mode:** Color-codes collections (Red to Blue) based on density to identify "performance killers."
    * **Non-Destructive Mode (New in v2.7):** Toggle off heatmap colors to simply add percentage suffixes (e.g., `Furniture | 15.3%`) without altering your original collection color organization.
* **View Analyzer:** Visualizes heavy objects directly in the 3D Viewport using a heatmap overlay.
* **Smart Restoration:** The new restoration system ensures that cleaning up the analyzer only reverts changes if valid backup data exists, preventing accidental color resets.

### 2. ⚡ Asynchronous Image Optimization
* **True Background Processing:** LODify spawns a separate system process (subprocess) to resize images, bypassing the Python GIL. You can continue working in Blender while it optimizes 500 textures in the background. **Zero UI freezing.**
* **Hybrid Engine:** Automatically switches between Blender's native API and the bundled, high-performance PIL engine.
* **Camera AI Optimization:** One-click analysis calculates exactly how many pixels an object occupies in the active camera view. Far objects get smaller textures; close-ups stay sharp.
* **Disk Storage Management:** Scan and clean up generated texture folders directly from the addon panel.

### 3. 📉 Geometry LOD System
* **Dual Algorithms:** Choose between the fast **Decimate Modifier** or the high-quality **Geometry Nodes** workflow.
* **Safety Floor:** Includes "Min Ratio" and "Min Faces" protection to prevent close-up objects from losing essential silhouette details.
* **Async Batch Processing:** Setup, update, and apply modifiers on thousands of objects using a non-blocking modal operator.
* **Destructive Apply:** One-click apply for all LOD modifiers to bake optimizations for export (Unity/UE5).

### 4. 👁️ Viewport & Shader Management
* **Distance Culling:** Automatically downgrades display modes (Textured → Solid → Wire → Bounds) based on distance to significantly boost viewport FPS.
* **Shader LOD (Experimental):** Dynamically reduces Normal and Displacement strength for distant objects to save render resources and reduce noise.
* **Snapshot Restoration:** Remembers the original display state of every object, ensuring a perfect reset when optimization is disabled.

<br>

## 🛠️ Installation (Blender 4.2+)

1.  Download the latest `.zip` file from the [Releases](https://github.com/XIAOTsune/LODify/releases) page.
2.  Open Blender, go to **Edit -> Preferences -> Get Extensions**.
3.  Click the arrow icon (top right) -> **Install from Disk...** and select the zip file.
4.  Find the **Optimize** tab in the 3D View Sidebar (N key).

---
<br>
<br>

<a name="-cn-中文介绍"></a>

# 🇨🇳 LODify: 让你的 Blender 飞起来！

**LODify** 是一套工业级的 Blender 场景优化解决方案。最新版本引入了全新的**全异步架构**和**智能子进程 Worker**，彻底解决了大场景优化时 Blender 界面卡死、显存爆炸的痛点。

> **开箱即用：** 新版插件已内置高性能图像处理库 (Pillow)，**无需再手动运行脚本安装依赖**，安装插件即可直接享受极速模式。

<br>

## 🔥 核心功能

### 1. 📊 场景分析器 (新功能)
* **集合分析器 (Collection Analyzer)**：一键统计所有 Collection 的顶点数。
    * **热力图模式**：用红-蓝渐变色标记出哪些集合是“性能杀手”。
    * **无损模式 (v2.7 新增)**：你可以关闭“使用热力图颜色”开关，仅在集合名称后添加百分比后缀（如 `家具 | 15.3%`），**完全保留你原有的集合颜色标记**，不破坏整理习惯。
* **视图分析器 (View Analyzer)**：在 3D 视图中直接通过颜色显示物体密度，直观定位高面数模型。
* **智能恢复**：改进的清理逻辑确保只在有备份时还原颜色，避免误操作导致集合颜色丢失。

### 2. ⚡ 异步图像优化 (Async Image Resizer)
* **真正的后台处理**：LODify 启动独立的系统进程 (subprocess) 来缩放图片，绕过 Python GIL 锁。你可以在优化 500 张贴图的同时，继续在 Blender 里雕刻或建模，**界面绝不卡顿**。
* **混合引擎**：智能识别环境，在 Blender 原生 API 和内置的高性能 PIL 引擎之间自动切换。
* **相机视锥优化 (Camera AI)**：点击一下，插件会自动计算物体在相机视角里到底占了多少像素。远处的物体贴图会被自动缩小，近处的保持高清。
* **磁盘管理**：直接在面板中扫描和清理生成的贴图缓存文件夹，管理硬盘空间。

### 3. 📉 几何体 LOD 系统 (Geometry LOD)
* **双重算法**：支持传统的**减面修改器**（速度快）或**几何节点**（拓扑质量高）。
* **细节保护**：内置“安全底限” (Min Ratio) 和“最小面数保护”，防止近景物体过度减面导致崩坏。
* **异步批量处理**：支持对数千个物体进行异步设置、更新和应用 (Apply)，方便导出到游戏引擎 (Unity/UE5)。
* **一键应用**：支持批量应用所有 LOD 修改器，永久固化优化结果。

### 4. 👁️ 视窗与材质管理
* **视窗分级显示**：根据距离自动将物体显示切换为 材质 -> 实体 -> 线框 -> 边界框，极大提升视窗 FPS。
* **材质 LOD (实验性)**：根据距离自动降低法线 (Normal) 和置换 (Displacement) 的强度，减少渲染时的噪点和显存压力。
* **快照恢复**：自动记录优化前的物体状态，确保一键重置时完美复原。

<br>

## 🛠️ 安装方法 (Blender 4.2+)

1.  在 [Releases](https://github.com/XIAOTsune/LODify/releases) 页面下载最新的 `.zip` 文件。
2.  打开 Blender，顶部菜单 **Edit -> Preferences -> Get Extensions**。
3.  点击右上角箭头 -> **Install from Disk...** 选择下载的压缩包。
4.  在 3D 视图按 **N** 键打开侧边栏，找到 **Optimize** 标签页。
