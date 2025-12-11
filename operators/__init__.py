from . import analyzer
from . import image
from . import viewport  # 新增
from . import geometry  # 新增
import bpy

# --- 定义宏 Operator：一键执行所有优化 ---
class TOT_OT_RunAllOptimization(bpy.types.Operator):
    """依次运行所有启用的优化流程 (Texture, Geo, Viewport)"""
    bl_idname = "tot.run_all_optimization"
    bl_label = "Run All Optimizations"
    
    def execute(self, context):
        scn = context.scene.tot_props
        
        # 1. Viewport
        if scn.view_lod_enabled:
            bpy.ops.tot.viewport_lod_update()
            
        # 2. Geometry
        if scn.geo_lod_enabled:
            # 自动 Setup (如果还没加修改器)
            bpy.ops.tot.geo_lod_setup()
            # 更新参数
            bpy.ops.tot.geo_lod_update()
            
        # 3. Texture (未来扩展：这里可以加基于距离的贴图缩放逻辑)
        # currently mostly manual in the other panel
        
        self.report({'INFO'}, "All optimizations updated based on camera distance.")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(TOT_OT_RunAllOptimization)

def unregister():
    bpy.utils.unregister_class(TOT_OT_RunAllOptimization)