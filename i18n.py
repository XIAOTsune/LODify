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
    # --- Tooltips (Properties Descriptions) ---
    "Camera used for screen coverage calculation": "用于计算屏幕占比的相机",
    "High Detail End Distance": "高精度结束距离 (LOD 0)",
    "Mid Detail End Distance": "中精度结束距离 (LOD 1)",
    "Low Detail End Distance": "低精度结束距离 (LOD 2)",
    
    # Viewport
    "Change object display mode (Solid/Wire/Bounds) based on distance": "根据距离自动切换物体显示模式 (实体/线框/边界框)",
    "Hide objects completely at far distance": "在极远距离完全隐藏物体",
    
    # Geometry LOD
    "Enable screen ratio based decimation": "启用基于屏幕占比的自动减面",
    "Use standard Decimate modifier": "使用标准减面修改器 (速度快)",
    "Use Geometry Nodes (High Quality)": "使用几何节点 (拓扑质量高)",
    "Protection: Objects with fewer faces will not be decimated": "保护：面数少于此值的物体不会被处理",
    "Strongest protection: Keep at least this ratio even at max distance": "最强保护：即使在最远距离，面数比例也不会低于此值",
    "Merge radius at furthest distance (Higher = More aggressive)": "最远距离时的顶点合并半径 (值越高减面越狠)",
    
    # Shader LOD
    "Reduce normal/displacement strength based on distance": "根据距离降低法线/置换贴图的强度",

    # --- Operators Tooltips (代码注释翻译) ---
    # Analyzer
    "Analyzes collection vertex counts and color-codes them": "分析集合顶点数量并进行颜色标记",
    "Restores original collection names and colors": "恢复原始集合名称和颜色",
    "Analyzes objects in 3D view and color-codes by density": "分析视图物体并根据密度着色",
    "Clear View Analyzer": "清除视图分析结果",

    # Image
    "Use subprocess to call an external worker.py script for image processing.": "使用子进程调用外部脚本处理图片 (防卡顿)",
    # 注意：如果你的代码里有换行符 \n，字典里的 Key 必须完全匹配，建议代码里写成单行，或者这里对应写成多行字符串

    # Geometry
    "Setup Geometry LOD Modifiers (Async Version)": "设置几何体 LOD 修改器 (异步版)",
    "Update Geometry (Async)": "更新几何体 (异步)",
    "Asynchronous Batch Application of LOD Modifiers (Prevents UI Freezing)": "异步批量应用 LOD 修改器 (防止界面冻结)",
    "Reset Geometry": "重置几何体修改器",

    # Viewport
    "Update Viewport Display Mode Based on Distance (Solid / Wire / Bounds)": "根据距离更新视窗显示模式 (实体/线框/边界框)",
    "Restore Original Display Mode": "恢复原始显示模式",

    # Shader (配合第一步修改后的英文)
    "Update shader details (Normal/Displacement) asynchronously": "异步更新材质细节 (法线/置换)",
    "Restore original shader parameters": "恢复材质原始参数",
    "Reset Shader Parameters": "重置材质参数",

    # Camera Optimization
    "Optimize by Camera (Async)": "基于相机视角优化 (异步)",
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