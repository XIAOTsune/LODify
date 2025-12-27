<div align="center">
 
  <h1>🚀 LODify</h1>
  
  <h3>The Blender Performance Savior | Blender 性能救星</h3>
  <p>
    <b>LOD Edition v3.0</b> • <i>Multi-Process Image System</i> • <i>Screen Coverage Algorithm</i> • <i>Geometry Nodes</i>
  </p>

  <p>
    <a href="https://www.blender.org/">
      <img src="https://img.shields.io/badge/Blender-4.2%2B%20%7C%205.0-orange?logo=blender&style=for-the-badge" alt="Blender Version">
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
    👇 <b>选择语言 / Select Language</b> 👇
  </p>
  <p>
    <a href="#-cn-中文介绍">🇨🇳 中文介绍 (及极速模式教程)</a> • 
    <a href="#-us-english-version">🇺🇸 English Version (Turbo Mode Guide)</a>
  </p>
</div>

<br>
<hr>

<a name="-cn-中文介绍"></a>

# 🇨🇳 让你的 Blender 飞起来！

**LODify** 是一套工业级的 Blender 场景优化解决方案。v3.0 最新版本引入了全新的**多进程架构**和**屏幕占比算法**，彻底解决了大场景优化时 Blender 界面卡死、显存爆炸的痛点。

> **核心特性：** 真正的后台多进程贴图处理、基于相机视角的智能分辨率计算、非破坏性几何节点 LOD、以及材质细节动态调节。

<br>

## 🚀 必读：开启“极速模式” (多进程加速)

LODify 内置了 `worker.py` 子系统。默认情况下它使用 Blender 内部 API 处理图片。为了处理**数百张 4K/8K 贴图**而不阻塞界面，你需要安装 Python `Pillow` 库来激活**独立进程加速**。

**开启步骤 (仅需操作一次)：**

1.  **以管理员身份运行 Blender** (权限用于安装 pip 库)。
2.  进入顶部 **Scripting (脚本)** 工作区。
3.  新建一个文本，**复制粘贴**下方代码，点击 **运行 (Run Script)** 按钮。
4.  等待控制台显示“成功”后，**重启 Blender**。

```python
import subprocess, sys, os

# 自动安装极速模式依赖 (使用清华源加速)
print("🚀 正在安装极速模式依赖 (Pillow)...")

# 尝试为 Blender 的 Python 环境安装 Pillow
cmds = [
    [sys.executable, "-m", "pip", "install", "pillow", "-i", "[https://pypi.tuna.tsinghua.edu.cn/simple](https://pypi.tuna.tsinghua.edu.cn/simple)"],
    [sys.executable, "-m", "pip", "install", "pillow", "--user", "-i", "[https://pypi.tuna.tsinghua.edu.cn/simple](https://pypi.tuna.tsinghua.edu.cn/simple)"]
]

success = False
for cmd in cmds:
    try:
        subprocess.check_call(cmd)
        print("\n✅ 成功！极速模式已激活。LODify 现在将使用独立进程处理贴图，不会卡住界面！")
        success = True
        break
    except Exception as e:
        print(f"尝试安装失败: {e}")
        continue

if not success:
    print("\n❌ 安装失败。请确保您是以【管理员身份】运行的 Blender 且网络连接正常。")
```


---

🔥 功能详解
1. ⚡ 多进程图像优化 (Multi-Process Image Resizer)
真正的后台处理：不同于传统的插件，LODify 启动独立的系统进程 (subprocess) 来缩放图片。你可以在优化 500 张贴图的同时，继续在 Blender 里雕刻或建模，界面绝不卡顿。

智能缓存：自动识别已处理过的图片，二次运行实现“秒开”。

相机视锥优化 (AI Camera Opt)：点击一下，插件会自动计算物体在相机视角里到底占了多少像素。远处的物体贴图会被自动缩小，近处的保持高清。

2. 🧠 屏幕占比几何 LOD (Screen Ratio Geometry)
所见即所得：抛弃过时的“距离法”。LODify 计算物体在屏幕上的实际像素覆盖率。

几何节点驱动：使用 Geometry Nodes 进行非破坏性减面，支持智能护边 (Edge Protection)，确保模型轮廓不崩坏。

异步应用：支持批量 Apply (应用) 修改器，方便导出到游戏引擎 (Unity/UE5)。

3. 📊 场景分析器 (Analyzers)
集合分析器：一键统计所有 Collection 的顶点数，并用颜色热力图标记出哪些集合是“性能杀手”。

视图分析器：在 3D 视图中直接通过颜色显示物体密度，直观定位高面数模型。

4. 🎨 视窗与材质管理
视窗 LOD：根据距离自动将物体显示切换为 实体 -> 线框 -> 边界框，极大提升视窗 FPS。

材质 LOD (实验性)：根据距离自动降低法线 (Normal) 和置换 (Displacement) 的强度，减少渲染时的噪点和显存压力。

🛠️ 安装方法 (Blender 4.2+)
在 Releases 页面下载最新的 .zip 文件。

打开 Blender，顶部菜单 Edit -> Preferences -> Get Extensions。

点击右上角箭头 -> Install from Disk... 选择下载的压缩包。

在 3D 视图按 N 键打开侧边栏，找到 Optimize 标签页。

<a name="-us-english-version"></a>

🇺🇸 US: Unchain Your Viewport!
LODify is a pro-grade optimization suite for Blender. v3.0 introduces a brand new Multi-Process Architecture and Screen Coverage Algorithm, solving UI freezing and VRAM overflow issues in complex scenes.

Key Features: True background image processing, Camera-based texture optimization, Non-destructive Geometry Nodes LOD, and Dynamic Shader adjustment.

🚀 PRO TIP: Unlock "Turbo Mode" (Multi-Process)
LODify includes a worker.py subsystem. By default, it uses Blender's internal API. To process hundreds of textures without freezing the UI, you need to install the Pillow library to activate Process Isolation.

How to Enable (One-time setup):

Run Blender as Administrator.

Go to the Scripting tab.

Create a new text block, paste the script below, and click Run Script.

Restart Blender.

```Python

import subprocess, sys

# Auto-install Turbo Mode dependencies (Pillow)
print("🚀 Installing Turbo Mode dependencies...")

cmds = [
    [sys.executable, "-m", "pip", "install", "pillow"],
    [sys.executable, "-m", "pip", "install", "pillow", "--user"]
]

success = False
for cmd in cmds:
    try:
        subprocess.check_call(cmd)
        print("\n✅ SUCCESS! Turbo Mode activated. Image processing now runs in a separate process!")
        success = True
        break
    except Exception:
        continue

if not success:
    print(f"\n❌ Error: Installation failed. Please ensure you are running Blender as Administrator.")
```
---


🔥 Feature Highlights
1. ⚡ Multi-Process Image Optimization
True Background Processing: LODify spawns separate system processes (subprocess) to resize images. You can continue working in Blender while optimizing 500 textures. Zero UI freezing.

Camera Optimization: One-click analysis calculates exactly how many pixels an object occupies in the active camera view. Far objects get smaller textures; close-ups stay sharp.

2. 🧠 Screen Ratio Geometry LOD
Visual Accuracy: Deprecated "Distance-based" LODs are gone. We calculate actual Screen Pixel Coverage.

Geometry Nodes Powered: Uses non-destructive Geometry Nodes for decimation with Edge Protection to preserve silhouettes.

Async Apply: Batch apply modifiers asynchronously for exporting to Game Engines (Unity/UE5).

3. 📊 Scene Analyzers
Collection Analyzer: identifying "heavy" collections with a color-coded heatmap based on vertex count.

View Analyzer: Visualizes object density directly in the 3D viewport.

4. 🎨 Viewport & Shader Management
Viewport LOD: Automatically switches display modes (Solid -> Wire -> Bounds) based on distance to boost FPS.

Shader LOD (Experimental): Dynamically reduces Normal and Displacement strength based on distance to save render resources.

🛠️ Installation (Blender 4.2+)
Download the latest .zip from Releases.

Open Blender Edit -> Preferences -> Get Extensions.

Click the arrow icon (top right) -> Install from Disk... and select the zip file.

Find the Optimize tab in the 3D View Sidebar (N key).