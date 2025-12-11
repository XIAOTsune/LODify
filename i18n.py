# File Path: .\i18n.py

import bpy

# 翻译字典：Key 是英文原始内容，Value 是对应的中文
# 你可以在这里随意添加更多翻译
TRANSLATION_DICT = {
    # --- 标题与通用 ---
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
    
    # --- 属性标签 ---
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
    "GN Strength Factor": "几何节点强度因子",
    "Data Cleanup": "数据清理",
    "Disk Storage Management": "磁盘存储管理",
    "Texture Optimization": "贴图优化",
    "See Image Resizer Panel below": "请查看下方的贴图缩放面板",
    "AI / Camera Optimization": "AI / 相机视角优化",
    "Auto-calculate size based on screen coverage": "基于屏幕占比自动计算尺寸",
    "Run Camera Optimization": "运行相机优化",
    "Auto-Opt": "自动优化组",
    "Camera Optimized: Generated": "相机优化完成：已生成",
    
    # --- 提示信息 ---
    "(No resized sets found)": "(未找到已生成的尺寸组)",
    "Save file to see texture folders": "保存文件后可见贴图文件夹",
    "Found": "发现",
    "Texture Sets": "组贴图缓存",
}

def tr(text_key):
    """
    翻译核心函数：
    根据当前场景的语言设置，返回对应的中文或英文
    """
    # 获取上下文中的语言设置
    # 注意：为了防止在注册阶段报错，加个 try-except
    try:
        scn = bpy.context.scene.tot_props
        if scn.language == 'CN':
            return TRANSLATION_DICT.get(text_key, text_key) # 如果找不到翻译，返回原文
    except:
        pass
    
    return text_key # 默认为英文 (原文)