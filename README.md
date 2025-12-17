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
    <a href="#-cn-中文介绍">🇨🇳 中文介绍 (及极速模式教程)</a> • 
    <a href="#-us-english-version">🇺🇸 English Version (Turbo Mode Guide)</a>
  </p>
</div>

<br>
<hr>

<a name="-cn-中文介绍"></a>

# 🇨🇳 让你的 Blender 飞起来！

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
```


---

#功能介绍
🔥 核心功能介绍
1. ⚡ 永不卡顿的异步内核 (Async Core)
别再忍受点击优化后的“白屏”和“无响应”。LODify 采用 时间片 (Time-Slicing) 技术，即使在处理上万个物体或数百张贴图时，你的界面依然可以自由操作。

2. 🧠 屏幕占比算法 (Screen Coverage)
传统的“距离法”已过时。LODify 实时计算物体在画面中的像素占比：只有物体在镜头里真的变小了，才会降低精度。完美适配广角与长焦镜头，真正做到“所见即所得”。

3. 🛡️ 智能几何节点流 (支持 Apply)
使用非破坏性的 Geometry Nodes 代替原始的减面修改器：

智能护边：保护锐利边缘、倒角与轮廓不崩坏。

一键固化：支持一键 Apply (应用) 结果，将程序化模型转为普通网格，方便导出 FBX/GLTF。

4. 📸 资产管理的“后悔药”
状态快照 (Snapshot)：在进行视窗优化（改变物体显示为线框/包围盒）前自动保存状态，一键还原，绝不弄乱你的源文件。

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

Run Blender as Administrator:

Right-click the Blender icon -> "Run as Administrator".

Steam users: Right-click Blender in Library -> Manage -> Browse local files -> Right-click blender.exe -> Run as Admin.

Go to the Scripting tab in Blender.

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
        print("\n✅ SUCCESS! Turbo Mode activated. Restart Blender to enjoy 5x-10x speed boost!")
        success = True
        break
    except Exception:
        continue

if not success:
    print(f"\n❌ Error: Installation failed. Please ensure you are running Blender as Administrator.")
```
---


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
