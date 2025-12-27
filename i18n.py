# File Path: .\i18n.py

import bpy

# 翻译字典：Key 是英文原始内容，Value 是对应的中文
TRANSLATION_DICT = {
    # --- 标题与通用 ---
    "LODify": "Blender 优化工具",
    "Optimize Tools": "优化工具箱",
    "Collection Analyzer": "集合分析器",
    "View Analyzer": "视图分析器",
    "Image Resizer": "贴图缩放与管理",
    "LOD Manager": "LOD 层级管理",
    "Clean Up & Storage": "清理与存储",
    "Total": "总计",
    "Mem": "显存",
    
    # --- 按钮与操作 ---
    "Run Analyzer": "运行分析",
    "Clear Analyzer": "清除结果",
    "Scan / Refresh Images": "扫描 / 刷新图片列表",
    "Select All/None": "全选 / 反选",
    "Resize Selected Images": "缩放选中图片",
    "Original": "恢复原图",
    "Update View": "更新视图显示",
    "Reset": "重置",
    "Setup Modifiers": "安装修改器",
    "Update Geometry": "更新模型",
    "Reset Geometry": "重置模型",
    "Apply Decimate (Destructive)": "应用减面 (不可逆)",
    "Apply GeoNodes (Destructive)": "应用几何节点 (不可逆)",
    "Merge Duplicate Images (.001)": "合并重复贴图 (.001)",
    "Delete Folder": "删除文件夹",
    "Open Website": "打开官网",
    
    # --- 属性标签 (这里的 Key 必须与 properties.py 和 main_panels.py 中的英文一致) ---
    "Method": "分析方法",
    "Color Thresholds (Vertex %)": "颜色阈值 (顶点百分比)",
    "Target": "目标尺寸",
    "Pixels": "自定义像素",
    "Safe Mode (Copy Files)": "安全模式 (另存副本)",
    "Output": "输出路径",
    "Texture Switcher (Global)": "全局贴图切换器",
    "Distance Zones (Meters)": "距离区域 (米)",
    "Viewport Optimization": "视窗显示优化",
    "Hide Far Objects": "隐藏极远物体",
    "Geometry LOD": "模型几何 LOD",
    "Enable": "启用",
    "Min Faces (Safety)": "最小面数保护",
    "Min Ratio (Max Reduction)": "最小比例 (最大减面)",
    "Min Ratio Protection": "最小比例保护",
    "Data Cleanup": "数据清理",
    "Disk Storage Management": "磁盘存储管理",
    "Texture Optimization": "贴图优化",
    "See Image Resizer Panel below": "请查看下方的贴图缩放面板",
    "AI / Camera Optimization": "AI / 相机视角优化",
    "Auto-calculate size based on screen coverage": "基于屏幕占比自动计算尺寸",
    "Run Camera Optimization": "运行相机优化",
    "Auto-Opt": "自动优化组",
    "Camera Optimized: Generated": "相机优化完成：已生成",
    "LOD Distance Levels (For Viewport)": "LOD 距离分级 (仅影响视窗)",
    "Geometry LOD (Screen Ratio)": "几何体 LOD (屏幕占比模式)",
    "Min Ratio (Safety Floor)": "最小保留比例 (底限保护)",
    "Prevents breaking close-up details": "防止近景/特写细节丢失",
    
    # --- 新增的映射 (填补 properties.py 英文化的空缺) ---
    "GN Strength Factor": "节点强度因子",
    "Max Merge Distance": "最大合并距离",
    "Auto Edge Protection": "自动边缘保护 (智能)",
    "Distance-based Collapse": "基于距离的空间塌陷",
    "High <": "高精度 <",
    "Mid <": "中精度 <",
    "Low <": "低精度 <",
    "Custom Px": "自定义像素",
    "Save in Blend Dir": "存至 Blend 目录",
    "Custom Path": "自定义路径",
    "Duplicate Files": "保留副本",
    "Target Size": "目标尺寸",
    "LOD Camera": "LOD 计算相机",
    "LOD Method": "LOD 算法",
    
    # --- 提示信息 ---
    "(No resized sets found)": "(未找到已生成的尺寸组)",
    "Save file to see texture folders": "保存文件后可见贴图文件夹",
    "Found": "发现",
    "Texture Sets": "组贴图缓存",
}

def tr(text_key):
    # (逻辑同上一步，保持自动检测)
    locale = bpy.app.translations.locale
    if locale.startswith('zh'):
        return TRANSLATION_DICT.get(text_key, text_key)
    return text_key