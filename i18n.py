import bpy

# 关键修改 1: 使用包名作为域名，确保全插件通用
DOMAIN = __package__

# 翻译字典
ZH_DICT = {
    # --- Header ---
    "LODify": "LODify 优化工具",

    # --- Properties (这些是我们在 Step 2 中恢复为英文的属性值) ---
    "Custom": "自定义",
    "Textured": "纹理",
    "Full Material": "完整材质",
    "Solid": "实体",
    "Solid Shading": "实体着色",
    "Wire": "线框",
    "Wireframe": "线框模式",
    "Bounds": "边界框",
    "Bounding Box (Fastest)": "边界框 (最快)",
    "Decimate Modifier": "减面修改器",
    "Use standard Decimate modifier": "使用标准减面修改器",
    "Geometry Nodes": "几何节点",
    "Use Geometry Nodes (High Quality)": "使用几何节点 (高质量)",
    "Collection Analyzer Toggle": "集合分析器开关",
    "Scene Analyzer Toggle": "场景分析器开关",
    "Target Size": "目标尺寸",

    # --- Panels (原有翻译保持不变) ---
    "1. Collection Analyzer": "1. 集合分析器",
    "2. View Analyzer": "2. 视图分析器",
    "3. Image Resizer": "3. 贴图缩放管理",
    "4. LOD Manager": "4. LOD 层级管理",
    "5. Clean Up & Storage": "5. 清理与存储",
    "6. Experimental Features": "6. 实验性功能",

    # --- General Buttons & Labels ---
    "Method": "算法/方法",
    "Target": "目标",
    "Output": "输出",
    "Total": "总计",
    "Mem": "显存",
    "Default": "默认",
    "Advanced": "高级",

    # --- Collection Analyzer ---
    "Collection Analyzer": "集合分析器",
    "Run Analyzer": "运行分析",
    "Clear Analyzer": "清除结果",
    "Color Thresholds (Vertex %)": "颜色阈值 (顶点百分比)",

    # --- View Analyzer ---
    "View Analyzer": "视图分析器",
    "Run 3D View Analyzer": "运行视图分析",
    "Clear View Analyzer": "清除视图分析",

    # --- Image Resizer ---
    "Scan / Refresh Images": "扫描 / 刷新图片列表",
    "Select All/None": "全选 / 反选",
    "Resize Selected Images": "缩放选中图片",
    "Original": "原图",
    "Auto-Opt": "自动",
    "Pixels": "像素",
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
    "Texture Switcher (Global)": "全局贴图切换",
    "Switch to": "切换到",
    "Resize Options:": "缩放选项:",
    "Total Images": "图片总数",
    "Total Memory": "总显存占用",
    "(No resized sets found)": "(未找到已生成的尺寸组)",

    # --- LOD Manager ---
    "LOD Camera": "LOD 计算相机",
    "LOD Distance Levels (For Viewport)": "LOD 距离分级 (仅影响视窗)",
    "High <": "高精度 <",
    "Mid <": "中精度 <",
    "Low <": "低精度 <",

    # --- Viewport Optimization ---
    "Viewport Optimization": "视窗显示优化",
    "Enable Viewport LOD": "启用视窗 LOD",
    "Update View": "更新视图",
    "Reset": "重置",
    "Hide Far Objects": "隐藏极远物体",
    "Hide objects completely at far distance": "在极远距离完全隐藏物体",

    # --- Geometry LOD ---
    "Geometry LOD (Screen Ratio)": "几何体 LOD (屏幕占比模式)",
    "Enable": "启用",
    "Enable Geometry LOD": "启用几何体 LOD",
    "Setup Modifiers": "安装修改器",
    "Update Geometry": "更新模型",
    "Update Geometry (Async)": "更新模型 (异步)",
    "Reset Geometry": "重置模型",
    "Apply Decimate (Destructive)": "应用减面 (不可逆)",
    "Apply GeoNodes (Destructive)": "应用几何节点 (不可逆)",

    # Parameters
    "Min Faces (Safety)": "最小面数保护",
    "Min Ratio (Safety Floor)": "最小比例保护",
    "Prevents breaking close-up details": "防止近景或特写时的细节丢失",
    "GN Strength Factor": "节点强度因子",
    "Max Merge Distance": "最大合并距离",
    "Auto Edge Protection": "自动边缘保护 (智能)",
    "Distance-based Collapse": "基于距离的空间塌陷",

    # --- Cleanup ---
    "Data Cleanup": "数据清理",
    "Disk Storage Management": "磁盘存储管理",
    "Merge Duplicate Images (.001)": "合并重复贴图 (.001)",
    "Clear Duplicate Images": "清理重复贴图",
    "Delete Folder": "删除文件夹",
    "Save file to see texture folders": "保存文件后可见贴图文件夹",
    "Found": "发现",
    "Texture Sets": "组贴图缓存",
    "No generated folders found.": "未找到已生成的贴图文件夹。",

    # --- Experimental ---
    "Shader Detail LOD": "材质细节 LOD",
    "Enable Shader LOD": "启用材质 LOD",
    "Normal Map Strength Multipliers": "法线强度倍率",
    "Displacement Scale Multipliers": "置换强度倍率",
    "Update Shaders": "更新材质",
    "Reset Shader Parameters": "重置材质参数",
}

translations = {
    "zh_CN": {
        ("*", k): v for k, v in ZH_DICT.items()
    },
    "zh_HANS": {
        ("*", k): v for k, v in ZH_DICT.items()
    },
}

def register():
    # 使用 __package__ 注册
    try:
        bpy.app.translations.register(DOMAIN, translations)
    except ValueError:
        pass # 防止重载报错

def unregister():
    bpy.app.translations.unregister(DOMAIN)

# def i18n(msg):
#     # 关键修改 2: 上下文必须匹配 "*"
#     return bpy.app.translations.pgettext_iface(msg, msgctxt="*")

def i18n(msg):
    # 使用 pgettext_iface，它是 Blender 暴露的正确 API
    return bpy.app.translations.pgettext_iface(msg, msgctxt="*")