# LODify 2.9.0 Release Notes

From `v2.8.0` to `v2.9.0`  
Release Date: `2026-03-13`

## English

LODify 2.9.0 is a stability-focused update for large-scene optimization workflows in Blender.

### Highlights

- Improved async image-processing progress reporting.
- Fixed native fallback resizing to preserve aspect ratio.
- Fixed View Analyzer cleanup so untouched objects are no longer overwritten.
- Fixed Viewport Reset so objects without saved hide snapshots are no longer unintentionally unhidden.
- Restored the missing output-directory control in the image resize workflow.
- Improved camera-based texture optimization by respecting `resolution_percentage`.
- Hardened generated-folder deletion checks.

### Compatibility

- Supported platform: Windows `x64`
- Supported Blender versions: Blender `4.2+`
- Added support for Blender `5.1.0`
- Bundled Pillow wheels now cover Python `3.11` and `3.13`

## 中文

LODify 2.9.0 是一次以稳定性为核心的更新，主要面向 Blender 大场景优化工作流。

### 更新亮点

- 优化了异步图片处理的进度反馈。
- 修复了原生兜底缩放破坏宽高比的问题。
- 修复了 View Analyzer 清理时误覆盖未处理对象颜色的问题。
- 修复了 Viewport Reset 误取消隐藏无快照对象的问题。
- 补回了图片缩放流程中缺失的输出目录控制项。
- 改进了基于相机的贴图优化计算，现已正确考虑 `resolution_percentage`。
- 强化了生成目录删除时的安全校验。

### 兼容性

- 支持平台：Windows `x64`
- 支持 Blender 版本：Blender `4.2+`
- 新增 Blender `5.1.0` 支持
- 内置 Pillow wheels 现已覆盖 Python `3.11` 与 `3.13`
