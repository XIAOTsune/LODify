<div align="center">

  <h1>🚀 LODify</h1>
  
  <h3>The Blender Performance Savior | Blender 性能救星</h3>
  <p>
    <b>LOD Edition v3.0</b> • <i>Async Core</i> • <i>Screen Coverage Algorithm</i> • <i>Turbo Ready</i>
  </p>

  <p>
    <a href="https://www.blender.org/">
      <img src="https://img.shields.io/badge/Blender-4.2%2B%20%7C%205.0-orange?logo=blender&style=for-the-badge" alt="Blender Version">
    </a>
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/License-GPL%20v3-blue.svg?style=for-the-badge" alt="License">
    </a>
    <a href="https://github.com/XIAOTsune/LODify/releases">
      <img src="https://img.shields.io/badge/Download-v3.0-green.svg?style=for-the-badge" alt="Download">
    </a>
  </p>

  <br>
  
  <p>
    👇 <b>选择语言 / Select Language</b> 👇
  </p>
  <p>
    <a href="#-cn-中文介绍">🇨🇳 中文介绍 (及加速教程)</a> • 
    <a href="#-us-english-version">🇺🇸 English Version (Turbo Mode Guide)</a>
  </p>
</div>

<br>
<hr>

<a name="-cn-中文介绍"></a>

# 让你的 Blender 飞起来！

**LODify** 是一套工业级的 Blender 场景优化解决方案。我们引入了**异步时间片技术**和**屏幕占比算法**，解决了大场景优化时 Blender 界面卡死、显存爆炸的痛点。

> **v3.0 核心更新：** 大幅优化了贴图缩放算法速度，改进了减面拓扑效果，并支持一键应用（Apply）几何节点以便快速导出到游戏引擎。

<br>

## 🚀 必读：如何开启 5-10 倍速“极速模式”？

LODify 默认使用**原生模式**，无需安装任何库即可流畅运行。但如果你需要处理 **数百张 4K/8K 贴图**，强烈建议开启 **极速模式 (Turbo Mode)** 以激活多线程并行加速。

**开启步骤 (仅需操作一次)：**

1.  **以管理员身份运行 Blender**：
    * **普通版**：右键 Blender 图标 -> 选择“以管理员身份运行”。
    * **Steam 版**：在库中右键 Blender -> 管理 -> 浏览本地文件 -> 右键 `blender.exe` -> 以管理员运行。
2.  进入顶部 **Scripting (脚本)** 工作区。
3.  新建一个文本，**复制粘贴**下方代码，点击 **运行 (Run Script)** 按钮。
4.  等待控制台显示成功后，**重启 Blender** 即可。

```python
import subprocess, sys

# 自动安装加速库 (使用清华源加速下载)
print("🚀 正在安装极速模式依赖 (Pillow)...")

cmds = [
    # 方案 A: 全局安装
    [sys.executable, "-m", "pip", "install", "pillow", "-i", "[https://pypi.tuna.tsinghua.edu.cn/simple](https://pypi.tuna.tsinghua.edu.cn/simple)"],
    # 方案 B: 用户目录安装 (备用)
    [sys.executable, "-m", "pip", "install", "pillow", "--user", "-i", "[https://pypi.tuna.tsinghua.edu.cn/simple](https://pypi.tuna.tsinghua.edu.cn/simple)"]
]

success = False
for cmd in cmds:
    try:
        subprocess.check_call(cmd)
        print("\n✅ 成功！极速模式已激活，重启 Blender 后 LODify 将获得 5-10 倍加速！")
        success = True
        break
    except Exception:
        continue

if not success:
    print("\n❌ 安装失败。请确保您是以【管理员身份】运行的 Blender 且网络连接正常。")
🔥 核心功能
1. ⚡ 永不卡顿的异步核心 (Async Core)
别再忍受点击优化后的“白屏”和“无响应”。LODify 采用 时间片 (Time-Slicing) 技术，即使在处理上万个物体或数百张贴图时，你的界面依然可以自由操作。

2. 🧠 屏幕占比算法 (Screen Coverage)
传统的“距离法”已过时。LODify 实时计算物体在画面中的像素占比：只有物体在镜头里真的变小了，才会降低精度。完美适配广角与长焦镜头，真正做到“所见即所得”。

3. 🛡️ 智能几何节点流 (支持 Apply)
使用非破坏性的 Geometry Nodes 代替原始的减面修改器：

智能护边：保护锐利边缘、倒角与轮廓不崩坏。

一键固化：支持一键 Apply (应用) 结果，将程序化模型转为普通网格，方便导出 FBX/GLTF。

4. 📸 资产管理的“后悔药”
智能快照：优化视窗显示（线框/隐藏）前自动保存状态，一键还原，绝不弄乱你的源文件。

智能缓存：缩放过的贴图会被自动记录，第二次运行实现“瞬时”优化。

🛠️ 安装方法
在本页面的 Releases 下载最新的 .zip 文件。

打开 Blender，顶部菜单 Edit -> Preferences -> Get Extensions。

点击右上角箭头 -> Install from Disk... 选择下载的压缩包。

<a name="-us-english-version"></a>

🇺🇸 US: Unchain Your Viewport!
LODify is a pro-grade optimization suite for Blender. Powered by Async Time-Slicing and Screen Coverage Algorithms, it solves the UI freezing and VRAM overflow issues in complex scenes.

v3.0 Highlights: Significantly faster texture resizing, improved decimation topology, and "Apply to Mesh" support for game engine export.

🚀 PRO TIP: Unlock "Turbo Mode" (5x-10x Speed)
By default, LODify runs in Native Mode (Zero dependencies). However, for heavy scenes with hundreds of textures, we highly recommend unlocking Turbo Mode to enable multi-threaded parallel processing.

How to Enable (One-time setup):

Run Blender as Administrator (Right-click -> Run as Administrator).

For Steam users: Right-click Blender in Library -> Manage -> Browse local files -> Right-click blender.exe -> Run as Admin.

Go to the Scripting tab in Blender.

Create a new text block, paste the script below, and click Run Script.

Restart Blender.

Python

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
        print("\n✅ SUCCESS! Turbo Mode activated. Restart Blender to enjoy 5x-10x speed boost!")
        success = True
        break
    except Exception:
        continue

if not success:
    print(f"\n❌ Error: Installation failed. Please ensure you are running Blender as Administrator.")
🔥 Key Features
1. ⚡ The "Zero-Freeze" Async Core
Stop waiting for the spinning wheel of death. Our Time-Slicing tech ensures your UI remains 100% responsive even during massive batch operations. Cancel anytime with ESC.

2. 🧠 Smart Algorithm: Screen Coverage LOD
Distance-based LOD is obsolete. LODify projects every object into 2D screen space to calculate its actual Pixel Ratio. What you see is exactly what gets optimized.

3. 🛡️ Geometry Nodes Guardian (Export Ready)
LODify dynamically builds smart Geometry Nodes instead of destructive modifiers:

Edge Protection: Intelligently preserves sharp edges and silhouettes.

Non-Destructive: Tweak or revert anytime.

Bake Support: One-click Apply to bake procedural optimizations into mesh for game engine exports.

4. 📸 Asset Management & Snapshot
Smart Caching: Texture resizing is instant if already processed.

Snapshot Reset: Automatically takes a snapshot of your original scene state before viewport optimization. Revert anytime with no data loss.

🛠️ Installation
Download the latest .zip from Releases.

Open Blender Edit -> Preferences -> Get Extensions.

Click the arrow icon (top right) -> Install from Disk... and select the zip file.

<div align="center"> <p> <b>Developed with ❤️ for the Blender Community</b>




🛠️ LODify 核心功能详解 | Feature Deep Dive
1. ⚡ 异步调度内核 (Async & Multi-threading)
LODify 彻底解决了 Blender 插件在处理大数据量时的“假死”痛点。

混合动力架构：自动检测环境，若安装 Pillow 库则启用 真·多线程 (Multi-threading) 并行加速；若无，则自动回退至 时间分片 (Time-Slicing) 异步调度。

非阻塞交互：无论后台是在缩放 300 张贴图还是计算 10,000 个物体的 LOD，Blender 界面始终保持 60FPS 响应。你可以随时旋转视图、调整参数，甚至按 ESC 键安全终止任务。

2. 🧠 智能屏幕占比算法 (Screen Coverage LOD)
区别于传统的、基于绝对距离的优化，LODify 采用类似 Unreal Engine 5 的屏幕占比逻辑。

像素级评估：通过将物体的包围盒投影至当前相机的 2D 屏幕空间，精确计算物体在最终画面中所占的像素比例。

透视自适应：自动适配广角与长焦镜头。长焦拉近时，即使距离很远，插件也会识别到物体占据了大量像素从而保留高精度，避免了传统优化中“远景模糊”的尴尬。

优化由感性转理性：插件会根据计算结果自动匹配最合适的贴图分辨率（如：仅占 100 像素的物体不需要 4K 贴图）。

3. 🛡️ 几何节点 LOD 系统 (Procedural Geometry Nodes)
放弃破坏性的 Decimate 修改器，LODify 构建了一套基于 Geometry Nodes 的动态减面管线。

边缘保护算法：节点组内部集成了边缘检测，能够自动识别并锁定模型的 锐利边缘 (Sharp Edges) 和 轮廓线 (Silhouettes)，仅对平坦区域进行塌陷。

距离感应塌陷：随着物体离开相机，模型面数会平滑降低，且支持自定义过渡曲线。

一键固化 (Apply to Mesh)：专为游戏导出设计，可一键将程序化减面结果“烘焙”为真实网格。

4. 📸 资产管理与快照 (Asset & Viewport Management)
针对大型场景资产混乱的问题，提供了一套非破坏性的管理方案。

状态快照 (Snapshot)：在进行视窗优化（改变物体显示为线框/包围盒）前，插件会自动记录所有物体的原始状态。用户可以反复试验，随时一键重置。

贴图智能缓存：贴图缩放过程会生成专属缓存，二次运行无需重新计算，实现“零秒”加载。

冗余清理：一键扫描并清理场景中因为反复导入产生的 .001、.002 冗余贴图数据块，压缩项目体积。

5. 📊 深度分析器 (Diagnostics)
在优化前，先看清性能瓶颈。

集合分析 (Collection Analyzer)：递归扫描集合，列出最消耗显存的“显存杀手”。

视窗分析 (Viewport Analyzer)：基于实时视窗状态，高亮显示面数异常的对象，让优化有的放矢。

🇬🇧 Technical Features (English)
🚀 Async Performance Engine
LODify features a sophisticated Time-Slicing scheduler combined with Optional Threading. It prevents Blender from freezing during heavy I/O or geometry operations, maintaining a responsive UI and allowing real-time cancellation.

📐 Pixel-Perfect Screen Coverage
Utilizing Screen Space Projection to determine LOD levels. Instead of simple distance, LODify calculates the object's pixel density in the current camera view, ensuring visual fidelity even with extreme focal lengths.

🔗 Non-Destructive Geo-Nodes Pipeline
Unlike standard decimation, LODify generates a Procedural Geometry Node Tree.

Silhouette Preservation: Intelligently locks sharp edges and boundary loops.

Bake-Ready: Includes a dedicated operator to "Apply" procedural results to static meshes for FBX/GLTF export.

📦 Asset Integrity & Snapshot
Viewport Snapshot: Takes a "memory photo" of your scene before optimization, allowing for 100% reversible workflows.

Smart Texture Deduplication: Scans and merges redundant image data-blocks created by repeated appending.


<i>Open Source under GPL-3.0-or-later</i> </p> <p> <a href="https://github.com/XIAOTsune/LODify/issues">Report Bug</a> • <a href="https://github.com/XIAOTsune/LODify/pulls">Contribute</a> </p> </div>
