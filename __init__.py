import bpy
from . import properties
from . import ui 
from . import operators

# --- 1. 兼容 Legacy Add-on (Blender < 4.2) ---
# 即使是 Extension 模式，保留这个也不会报错，旧版本则依赖它识别插件。
bl_info = {
    "name": "ToOptimize Tools (LOD Edition)",
    "author": "Your Name",
    "version": (1, 3, 0),
    "blender": (3, 6, 0), # 设置为你支持的最低版本
    "location": "View3D > Sidebar > Optimize",
    "description": "全场景性能优化：贴图、减面与视窗管理",
    "warning": "",
    "doc_url": "https://help.cgoutset.com/",
    "category": "3D View",
}

# 模块列表
modules = [
    properties,
    ui.lists,
    ui.main_panels,
    operators.analyzer,
    operators.image, 
    operators.viewport,
    operators.geometry,
    operators, 
]

def register():
    for mod in modules:
        try:
            mod.register()
        except Exception as e:
            # 打印错误但不要让插件加载完全失败，方便调试
            print(f"ToOptimize Register Error in {mod}: {e}")

def unregister():
    # --- 2. 安全卸载逻辑 ---
    # 卸载的关键是：即使出错也要继续执行，不能因为一个错误卡住整个卸载过程
    for mod in reversed(modules):
        try:
            mod.unregister()
        except Exception as e:
            print(f"ToOptimize Unregister Error in {mod}: {e}")
            pass # 强制继续卸载下一个模块

    # 清理可能残留的属性 (防止下次加载报错)
    if hasattr(bpy.types.Scene, "tot_props"):
        del bpy.types.Scene.tot_props