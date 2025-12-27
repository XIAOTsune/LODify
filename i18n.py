
import bpy

# =============================================================================
# 翻译字典 (Translation Dictionary)
# =============================================================================
# 格式: {locale: {key: translation, ...}}
# key (英文原文) 必须与 properties.py 和 UI 中的英文完全一致
# =============================================================================

translations = {
    "zh_CN": {
        # --- Header & General ---
        "LODify": "LODify 优化工具",
        "Optimize Tools": "优化工具箱",
        "Total": "总计",
        "Mem": "显存",
        "Method": "算法/方法",
        "Target": "目标",
        "Output": "输出",
        
        # --- Collection Analyzer ---
        "Collection Analyzer": "集合分析器",
        "Run Analyzer": "运行分析",
        "Clear Analyzer": "清除结果",
        "Color Thresholds (Vertex %)": "颜色阈值 (顶点百分比)",
        "Analyzes collection vertex counts and color-codes them": "分析集合的顶点数量并进行颜色标记",
        "Restores original collection names and colors": "恢复原始的集合名称和颜色",
        
        # --- View Analyzer ---
        "View Analyzer": "视图分析器",
        "Run 3D View Analyzer": "运行视图分析",
        "Analyzes objects in 3D view and color-codes by density": "分析3D视图中的物体并按密度着色",
        "Clear View Analyzer": "清除视图分析",
        
        # --- Image Resizer ---
        "Image Resizer": "贴图缩放管理",
        "Scan / Refresh Images": "扫描 / 刷新图片列表",
        "Select All/None": "全选 / 反选",
        "Resize Selected Images": "缩放选中图片",
        "Original": "原图",
        "Auto-Opt": "自动",
        "Target Size": "目标尺寸",
        "Custom Px": "自定义像素",
        "Safe Mode (Copy Files)": "安全模式 (另存副本)",
        "Duplicate Files": "保留副本",
        "Save in Blend Dir": "存至 Blend 目录",
        "Custom Path": "自定义路径",
        "Resize selected images to target resolution": "将选中的图片缩放到目标分辨率",
        "Calculates optimal texture size based on camera view": "根据相机视角自动计算最佳贴图尺寸",
        "Run Camera Optimization": "运行相机优化",
        "AI / Camera Optimization": "AI / 相机视角优化",
        "Auto-calculate size based on screen coverage": "基于屏幕占比自动计算尺寸",
        "Switch Texture Resolution": "切换贴图分辨率",
        "Switch to": "切换到",
        
        # --- LOD Manager ---
        "LOD Manager": "LOD 层级管理",
        "LOD Camera": "LOD 计算相机",
        "Camera used for screen coverage calculation": "用于计算屏幕占比的参考相机",
        "LOD Distance Levels (For Viewport)": "LOD 距离分级 (仅影响视窗)",
        "High <": "高精度 <",
        "Mid <": "中精度 <",
        "Low <": "低精度 <",
        "High Detail End Distance": "高精度显示的结束距离",
        "Mid Detail End Distance": "中精度显示的结束距离",
        "Low Detail End Distance": "低精度显示的结束距离",
        
        # --- Viewport Optimization ---
        "Viewport Optimization": "视窗显示优化",
        "Enable Viewport LOD": "启用视窗 LOD",
        "Change object display mode (Solid/Wire/Bounds) based on distance": "根据距离更改物体显示模式 (实体/线框/包围盒)",
        "Update View": "更新视图",
        "Update viewport display modes based on current camera": "根据当前相机更新视窗显示模式",
        "Reset": "重置",
        "Reset Viewport": "重置视窗",
        "Restore objects to original display mode": "将物体恢复为原始显示模式",
        "Hide at L3": "L3 级隐藏",
        "Hide objects completely at far distance": "在极远距离完全隐藏物体",
        
        # --- Geometry LOD ---
        "Geometry LOD (Screen Ratio)": "几何体 LOD (屏幕占比模式)",
        "Geometry LOD": "几何体 LOD",
        "Enable Geometry LOD": "启用几何体 LOD",
        "Enable screen ratio based decimation": "启用基于屏幕占比的自动减面",
        "Setup Modifiers": "安装修改器",
        "Add LOD modifiers to eligible objects": "为符合条件的物体添加 LOD 修改器",
        "Update Geometry": "更新模型",
        "Update Geometry (Async)": "更新模型 (异步)",
        "Recalculate LOD ratios based on current camera": "根据当前相机重新计算 LOD 比例",
        "Reset Geometry": "重置模型",
        "Remove all LOD modifiers": "移除所有 LOD 修改器",
        "Apply Decimate (Destructive)": "应用减面 (不可逆)",
        "Apply GeoNodes (Destructive)": "应用几何节点 (不可逆)",
        "Apply modifiers permanently": "永久应用修改器",
        
        # Parameters
        "Min Faces (Safety)": "最小面数保护",
        "Protection: Objects with fewer faces will not be decimated": "保护：面数少于此值的物体不会被减面",
        "Min Ratio (Safety Floor)": "最小比例保护",
        "Prevents breaking close-up details": "防止近景或特写时的细节丢失",
        "GN Strength Factor": "节点强度因子",
        "Strongest protection: Keep at least this ratio even at max distance": "最强保护：即使在最远距离也至少保留此比例",
        "Max Merge Distance": "最大合并距离",
        "Merge radius at furthest distance (Higher = More aggressive)": "最远距离时的顶点合并半径 (值越大减面越狠)",
        "Auto Edge Protection": "自动边缘保护 (智能)",
        "Distance-based Collapse": "基于距离的空间塌陷",
        
        # --- Cleanup ---
        "Clean Up & Storage": "清理与存储",
        "Data Cleanup": "数据清理",
        "Disk Storage Management": "磁盘存储管理",
        "Merge Duplicate Images (.001)": "合并重复贴图 (.001)",
        "Clear Duplicate Images": "清理重复贴图",
        "Replaces .001, .002 duplicates with the original image": "将 .001, .002 等重复图片替换为原始图片",
        "Delete Folder": "删除文件夹",
        "Permanently delete this texture folder": "永久删除此贴图文件夹",
        "Save file to see texture folders": "保存文件后可见贴图文件夹",
        "Found": "发现",
        "Texture Sets": "组贴图缓存",
        "(No resized sets found)": "(未找到已生成的尺寸组)",
        
        # --- Experimental ---
        "Experimental Features": "实验性功能",
        "Shader Detail LOD": "材质细节 LOD",
        "Enable Shader LOD": "启用材质 LOD",
        "Reduce normal/displacement strength based on distance": "根据距离降低法线/置换强度",
        "Normal Map Strength Multipliers": "法线强度倍率",
        "Displacement Scale Multipliers": "置换强度倍率",
        "Update Shaders": "更新材质",
        "Reset Shader Parameters": "重置材质参数",
        
        # --- Common Enums & Status ---
        "Default": "默认",
        "Advanced": "高级",
        "Solid Shading": "实体显示",
        "Wireframe": "线框显示",
        "Bounding Box (Fastest)": "包围盒 (最快)",
        "Textured": "材质预览",
        "Full Material": "完整材质",
        "Decimate Modifier": "减面修改器",
        "Geometry Nodes": "几何节点 (高质量)",
        "Use standard Decimate modifier": "使用标准减面修改器",
        "Use Geometry Nodes (High Quality)": "使用几何节点 (高质量)",
    }
}

def register():
    # 注册翻译
    bpy.app.translations.register(__name__, translations)

def unregister():
    bpy.app.translations.unregister(__name__)

def tr(msg):
    """
    辅助函数：在 UI 代码中手动调用翻译
    """
    return bpy.app.translations.pgettext_iface(msg)