# LODify 2.9.0 Release Notes

From `v2.8.0` to `v2.9.0`  
Release Date: `2026-03-13`

## English

LODify 2.9.0 is a maintenance and stabilization release focused on improving reliability, cleanup safety, and workflow consistency in large-scene optimization.

This update does not introduce a major new feature set. Instead, it refines several existing systems to make everyday use more predictable and production-friendly, especially in image-processing and viewport-optimization workflows.

### Highlights

- Improved async image-processing progress reporting so long-running texture batches now reflect completion more accurately.
- Fixed native fallback image resizing to preserve aspect ratio and avoid unintended stretching.
- Refined View Analyzer cleanup behavior so only objects with stored color snapshots are restored, preventing accidental color overrides on untouched objects.
- Corrected Viewport Reset behavior so objects without saved hide-state snapshots are no longer unintentionally unhidden.
- Restored the missing output-directory workflow control in the image-resize UI, making save-location behavior clearer and easier to manage.
- Updated camera-based texture optimization calculations to respect Blender's `resolution_percentage`, improving screen-coverage estimation.
- Strengthened generated-folder deletion checks with safer directory containment validation.
- Improved extension manifest website lookup compatibility for release metadata handling.

### Release Positioning

LODify 2.9.0 is recommended as a stability-focused update for users working with heavy Blender scenes, large texture sets, and repeated optimization passes. The release is intended to reduce workflow friction and improve confidence in cleanup and reset operations.

## 中文

LODify 2.9.0 是一次以维护和稳定性为核心的正式更新，重点提升大型场景优化流程中的可靠性、清理安全性，以及整体工作流一致性。

这一版本并未引入大规模的新功能模块，而是针对现有系统进行了多项打磨与修正，使插件在日常使用中更加稳定、可控，也更适合持续投入到实际生产环境中，尤其是贴图处理与视口优化相关流程。

### 更新亮点

- 优化了异步图片处理的进度反馈逻辑，使长时间运行的贴图批处理在完成统计上更加准确。
- 修复了原生兜底图片缩放会破坏宽高比的问题，避免输出结果出现拉伸。
- 调整了 View Analyzer 的清理逻辑，现在只会恢复确实保存过颜色快照的对象，避免误改未参与分析对象的颜色。
- 修复了 Viewport Reset 对无隐藏状态快照对象的误恢复问题，不再错误取消隐藏无关对象。
- 补回了图片缩放界面中缺失的输出目录控制项，使输出位置选择更加清晰直观。
- 更新了基于相机的贴图优化计算逻辑，现已正确考虑 Blender 的 `resolution_percentage` 参数，提升屏幕占比估算准确度。
- 强化了生成目录删除时的路径校验逻辑，进一步提升清理操作的安全性。
- 改进了扩展清单中 `website` 字段的读取兼容性，提升发布元数据处理的稳定性。

### 版本说明

LODify 2.9.0 推荐给处理高负载 Blender 场景、大量贴图资源以及频繁执行优化回合的用户使用。该版本的目标，是在不改变原有核心工作流的前提下，减少使用阻力，提升清理与重置操作的可信度，并让整体优化体验更加稳定。

## Notes / 备注

English:
This release note is based on the actual code changes between Git tags `v2.8.0` and `v2.9.0`.

中文：
本发版说明基于 Git 标签 `v2.8.0` 到 `v2.9.0` 之间的实际代码变更整理。
