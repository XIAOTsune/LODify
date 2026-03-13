# LODify 2.9.0 更新报告 / Update Report

日期 Date: 2026-03-03  
目标 Target: Blender Extensions (blender.org)

## 1. 版本更新 / Version Update

- 中文: 插件清单文件 `blender_manifest.toml` 的版本号已更新为 `2.9.0`。  
  English: The extension manifest version in `blender_manifest.toml` has been updated to `2.9.0`.
- 中文: 兼容旧版的 `bl_info` 版本号已更新为 `(2, 9, 0)`。  
  English: The legacy compatibility `bl_info` version has been updated to `(2, 9, 0)`.

## 2. 改动概览 / Change Summary

- 中文: 本次为“最小修复”版本，仅修复已确认的正确性与交互问题，不做架构重构。  
  English: This release is a minimal-fix update focused on confirmed correctness and UX issues, without architectural refactors.

### 2.1 P0 关键修复 / P0 Critical Fixes

1. 中文: 修复异步图片处理进度统计不准确的问题。  
   English: Fixed inaccurate progress counting in async image processing.
2. 中文: 清理 View Analyzer 时不再覆盖未分析对象颜色。  
   English: Clean View Analyzer no longer overwrites colors of untouched objects.
3. 中文: Viewport Reset 不再错误取消无快照对象的隐藏状态。  
   English: Viewport Reset no longer unhides objects when no hide snapshot exists.
4. 中文: 原生兜底缩放改为保持宽高比，避免拉伸。  
   English: Native fallback resize now preserves aspect ratio to prevent distortion.

### 2.2 P1 重要体验与正确性 / P1 Important UX & Correctness

1. 中文: 补充输出目录模式 UI 控件（`use_same_directory`）。  
   English: Added the missing UI control for output directory mode (`use_same_directory`).
2. 中文: 屏幕占比归一化加入 `resolution_percentage`。  
   English: Screen-ratio normalization now respects `resolution_percentage`.
3. 中文: 文件夹删除路径判断从前缀匹配升级为可靠目录包含判断。  
   English: Folder-delete path validation now uses robust directory containment instead of prefix matching.

### 2.3 P2 低风险清理 / P2 Low-Risk Cleanup

1. 中文: 清单网站字段读取逻辑改为优先读取顶层 `website`，再回退旧结构。  
   English: Manifest website lookup now reads top-level `website` first, then falls back to legacy structure.

## 3. 变更文件 / Files Changed

- `__init__.py`
- `blender_manifest.toml`
- `operators/image.py`
- `operators/analyzer.py`
- `operators/viewport.py`
- `ui/main_panels.py`
- `utils.py`

## 4. 已执行验证 / Validation Performed

1. 中文: 语法检查通过：`python -m compileall -q .`。  
   English: Syntax check passed: `python -m compileall -q .`.
2. 中文: 版本字段检查通过：  
   English: Version field verification passed:
   - `blender_manifest.toml` contains `version = "2.9.0"`.
   - `__init__.py` contains `"version": (2, 9, 0)`.

## 5. 提交说明 / Submission Notes

1. 中文: 本报告覆盖代码改动与静态检查结果。  
   English: This report covers code changes and static checks.
2. 中文: 提交前建议在 Blender 4.2+ 完成运行态冒烟测试。  
   English: Before submission, run Blender 4.2+ runtime smoke tests.
3. 中文: 建议测试项包括：插件注册/卸载、图片缩放流程（异步与原生兜底）、View Analyzer 运行/清理、Viewport LOD 更新/重置。  
   English: Recommended tests: add-on register/unregister, image resize flow (async + native fallback), View Analyzer run/clear, Viewport LOD update/reset.
