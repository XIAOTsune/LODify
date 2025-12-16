  
  <h1>🚀 LODify</h1>
  
  <h3>The Blender Performance Savior | Blender 性能救星</h3>
  <p>
    <b>LOD Edition v3.0</b> • <i>Async Core</i> • <i>Screen Coverage Algorithm</i>
  </p>

  <p>
    <a href="https://www.blender.org/">
      <img src="https://img.shields.io/badge/Blender-4.2%2B%20%7C%205.0-orange?logo=blender&style=for-the-badge" alt="Blender Version">
    </a>
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/License-GPL%20v3-blue.svg?style=for-the-badge" alt="License">
    </a>
    <a href="https://github.com/XIAOTsune/LODify/releases">
      <img src="https://img.shields.io/badge/Release-v3.0-green.svg?style=for-the-badge" alt="Download">
    </a>
  </p>

  <br>
  
  <p>
    👇 <b>选择语言 / Select Language</b> 👇
  </p>
  <p>
    <a href="#-cn-中文介绍让你的-blender-飞起来">🇨🇳 中文介绍</a> • 
    <a href="#-us-english-version-unchain-your-viewport">🇺🇸 English Version</a>
  </p>
</div>

<br>
<hr>

<a name="-cn-中文介绍让你的-blender-飞起来"></a>

#  让你的 Blender 飞起来！

> **"受够了点击‘优化’后界面卡死、转圈圈、甚至白屏崩溃？"** > **"受够了单纯按‘距离’减面，长焦一拉远景全变马赛克？"**

**LODify (Blender优化工具)** 就是为了结束这一切而生的！这不是一个简单的脚本，这是一套**工业级、非破坏性、永不卡顿**的场景优化解决方案。我们把 3A 游戏引擎的核心优化逻辑搬进了 Blender！

<br>

## 🔥 核心卖点：为什么它无可替代？

### 1. ⚡ 革命性的“零阻塞”异步核心 (Async Core)
**别再让 Blender 假死了！** LODify 采用了先进的 `时间片（Time-Slicing）技术`。
* 哪怕你有 **10,000 个物体** 需要计算 LOD；
* 哪怕你要批量缩放 **500 张 8K 贴图**；
* 你的界面 **永远是活的**！你可以看着进度条丝般顺滑地滚动，随时可以按 `ESC` 叫停。这就是 2025 年该有的体验！

### 2. 🧠 降维打击：屏幕占比算法 (Screen Coverage)
**忘掉落后的“距离法”吧！** 传统的 LOD 只看距离，简直是长焦镜头的噩梦。LODify 引入了 **屏幕占比算法**：
* 它将物体投影到 2D 屏幕空间，计算它在画面里到底占了几个像素。
* **只有当它在画面里真的变小了，我们才减面。**
* 无论广角还是长焦，画质与性能的完美平衡，**所见即所得**！

### 3. 🛡️ 几何节点流：硬表面守护神
**拒绝一键毁模型！** 我们不使用破坏性的 Decimate 修改器。LODify 会动态构建一套智能的 **Geometry Nodes (几何节点)**。
* ✅ 识别 **锐利的边缘** 和 **倒角**，死死护住你的模型轮廓。
* ✅ 只对平坦的、无关紧要的面进行“核打击”。
* ✅ 全程 **非破坏性**，随时调整参数，随时反悔！

### 4. 📸 资产管理的“后悔药”
* **智能缓存**：贴图缩放过一次？第二次运行 **0秒完成**！它记得一切。
* **时光倒流**：优化视窗显示（线框/隐藏）前，它会自动拍摄 **状态快照**。无论你折腾多少次，一键 Reset，所有物体乖乖回到你最初设置的样子。


<img width="912" height="810" alt="1" src="https://github.com/user-attachments/assets/1d2fd224-30ec-4ae1-ab53-754950d93dd6" width="300"/>

<img width="884" height="845" alt="2" src="https://github.com/user-attachments/assets/24bd17cf-e9b0-4b8e-81ab-6145f0b2171d" width="300"/>

<img width="894" height="709" alt="3" src="https://github.com/user-attachments/assets/7819a88d-2074-47c2-b547-cb6a4d35212c" width="300"/>

<img width="891" height="265" alt="4" src="https://github.com/user-attachments/assets/a1fcaf6d-b58e-4fe2-9482-83b4fafa0e0b" width="300"/>



<br>

## 🛠️ 如何安装

1. 在本页面的 [Releases](https://github.com/YourUsername/LODify/releases) 下载最新的 `.zip` 文件。
2. 打开 Blender，顶部菜单 `Edit` -> `Preferences` -> `Get Extensions`。
3. 点击右上角箭头 -> `Install from Disk...` 选择压缩包即可。

<br>
<br>
<hr>

<a name="-us-english-version-unchain-your-viewport"></a>

# 🇺🇸 US: Unchain Your Viewport!

> **"Sick of Blender freezing, hanging, or crashing when you try to optimize a scene?"** > **"Tired of 'Distance-based' LOD ruining your telephoto shots?"**

Meet **LODify**. This isn't just a script; it's a **pro-grade, non-blocking, non-destructive** optimization suite. We brought AAA game engine optimization logic directly into Blender!

<br>

## 🔥 Killer Features

### 1. ⚡ The "Zero-Freeze" Async Engine
**Stop waiting for the spinning wheel of death.** Powered by `Async Modal Operators` and Time-Slicing tech.
* Process **10,000 objects** for LOD updates?
* Batch resize **500 textures**?
* Your UI remains **100% responsive**. Watch the real-time progress bar glide smoothly. Cancel anytime. 

### 2. 🧠 Smart Algorithm: Screen Coverage LOD
**Distance-based LOD is obsolete.** LODify projects every object's bounding box into 2D screen space to calculate its actual **Pixel Ratio**.
* We only decimate mesh when it *actually* occupies less screen space.
* Perfect details for both wide-angle and telephoto lenses. **What you see is what you optimize.**

### 3. 🛡️ Geometry Nodes: The Hard-Surface Guardian
**Don't ruin your topology.** Instead of the destructive Decimate modifier, LODify dynamically builds a smart **Geometry Nodes** graph.
* ✅ It intelligently protects **sharp edges** and **silhouettes**.
* ✅ It aggressively reduces flat surfaces.
* ✅ **Non-Destructive**: Tweak parameters or revert changes anytime!

### 4. 📸 Smart Asset Management
* **Smart Caching**: Resizing textures? LODify checks for existing optimized files. Re-runs are **instant**.
* **Snapshot Reset**: Before optimizing the viewport (Wire/Bounds), it takes a **Snapshot** of your original state. Reset anytime, and your scene returns exactly to how you left it—no data loss.

<br>

## 🛠️ Installation

1. Download the latest `.zip` from [Releases](https://github.com/XIAOTsune/LODify/releases).
2. Open Blender `Edit` -> `Preferences` -> `Get Extensions`.
3. Click the arrow icon (top right) -> `Install from Disk...` and select the zip file.

<br>
<hr>

<div align="center">
  <p>
    <b>Developed with ❤️ for the Blender Community</b><br>
    <i>Open Source under GPL-3.0-or-later</i>
  </p>
  <p>
    <a href="https://github.com/XIAOTsune/LODify/issues">Report Bug</a> • 
    <a href="https://github.com/XIAOTsune/LODify/pulls">Contribute</a>
  </p>
</div>
