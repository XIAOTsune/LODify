import bpy
import os

# =============================================================================
# Acknowledgements / 致谢
# =============================================================================
# Core analysis concepts and UI layout inspired by "ToOptimize Tools" by Rodrigo Gama.
# This plugin (LODify) is a derivative work that refactors the codebase and introduces 
# new features such as Geometry Nodes integration, Async processing, and Camera Optimization.
# 核心分析逻辑与UI布局参考了 Rodrigo Gama 的 "ToOptimize Tools"。
# 本插件 (LODify) 在此基础上进行了重构，并新增了几何节点集成、异步处理及相机优化等功能。
# =============================================================================


ADDON_WEBSITE_URL = "https://github.com/XIAOTsune/LODify" # 默认值
AUTHOR_NAME = "小T_sune" # 你想要显示在标题栏的名字

from . import properties
from . import ui 
from . import operators
from . import i18n



try:
    import tomllib
except ImportError:
    # 兼容低版本 Python (虽然 Blender 5.0 不会进这里)
    import pip
    # 这里不做自动安装逻辑，仅作防错
    tomllib = None


def load_manifest_info():
    """读取 manifest.toml 中的 website 字段"""
    global ADDON_WEBSITE_URL
    
    # 获取当前文件的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    manifest_path = os.path.join(current_dir, "blender_manifest.toml")
    
    if os.path.exists(manifest_path) and tomllib:
        try:
            with open(manifest_path, "rb") as f:
                data = tomllib.load(f)
                # 读取 [information] 下的 website
                if "information" in data and "website" in data["information"]:
                    ADDON_WEBSITE_URL = data["information"]["website"]
                # 也可以顺便读取 maintainer 或 name
        except Exception as e:
            print(f"LOD Warning: Could not read manifest: {e}")


# --- 1. 兼容 Legacy Add-on (Blender < 4.2) ---
# 即使是 Extension 模式，保留这个也不会报错，旧版本则依赖它识别插件。
bl_info = {
    "name": "LODify",
    "author": "小T_sune",
    "version": (2, 2, 0),
    "blender": (4, 2, 0), # 设置为你支持的最低版本
    "location": "View3D > Sidebar > Optimize",
    "description": "Full-Scenario Perf Opt: Textures, Decimation & Viewport Mgmt",
    "warning": "",
    "doc_url": "https://github.com/XIAOTsune/LODify",
    "category": "3D View",
}

# 模块列表
modules = [
    i18n,
    properties,
    ui.lists,
    ui.main_panels,
    operators.analyzer,
    operators.image, 
    operators.viewport,
    operators.geometry,
    operators.shader_lod,
]

def register():
    
    load_manifest_info()

    for mod in modules:
        try:
            mod.register()
        except Exception as e:
            # 打印错误但不要让插件加载完全失败，方便调试
            print(f"LODify Register Error in {mod}: {e}")

def unregister():
    # --- 2. 安全卸载逻辑 ---
    # 卸载的关键是：即使出错也要继续执行，不能因为一个错误卡住整个卸载过程
    for mod in reversed(modules):
        try:
            mod.unregister()
        except Exception as e:
            print(f"LODify Unregister Error in {mod}: {e}")
            pass # 强制继续卸载下一个模块

    # 清理可能残留的属性 (防止下次加载报错)
    if hasattr(bpy.types.Scene, "lod_props"):
        del bpy.types.Scene.lod_props