import bpy
from .. import utils

class TOT_OT_CollectionAnalyzer(bpy.types.Operator):
    """Run Collection Analyzer"""
    bl_idname = "tot.collectionanalyzer"
    bl_label = "Run Analyzer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene.tot_props
        
        # 1. 清理旧状态
        bpy.ops.tot.cleancolors()

        self.report({'INFO'}, "Analyzing Collections...")
        
        # 备份当前颜色状态，以便 Clear 时恢复
        backup = {}
        
        # 获取基础阈值 (假设基准是 100万面，你可以调整这个基数)
        BASE_COUNT = 1000000 
        
        # 遍历所有集合
        for col in bpy.data.collections:
            # 记录原始颜色
            backup[col.name] = col.color_tag
            
            # 计算该集合的顶点数
            v_count = utils.get_collection_vertex_count(col)
            
            # 逻辑判定：根据顶点数赋予颜色
            # COLOR_01: Red (Very High)
            # COLOR_02: Orange (High)
            # COLOR_03: Yellow (Medium)
            # COLOR_04: Green (Low)
            # COLOR_05: Blue (Very Low/Safe)
            
            if v_count > (BASE_COUNT * scn.mult_veryhigh): # 0.9
                col.color_tag = 'COLOR_01'
            elif v_count > (BASE_COUNT * scn.mult_high):   # 0.8
                col.color_tag = 'COLOR_02'
            elif v_count > (BASE_COUNT * scn.mult_medium): # 0.6
                col.color_tag = 'COLOR_03'
            elif v_count > (BASE_COUNT * scn.mult_low):    # 0.2
                col.color_tag = 'COLOR_04'
            else:
                col.color_tag = 'NONE' # 或者 'COLOR_05'

        # 保存备份数据到字符串属性中
        scn.default_col_colors = str(backup)
        
        # 更新 UI 状态
        scn.CA_Toggle = True 
        
        return {'FINISHED'}
    
class TOT_OT_CleanColors(bpy.types.Operator):
    """Clear Analysis Results"""
    bl_idname = "tot.cleancolors"
    bl_label = "Clear Analyzer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene.tot_props
        
        if scn.default_col_colors:
            try:
                data = eval(scn.default_col_colors)
                for col in bpy.data.collections:
                    # 只有当集合还在时才恢复
                    if col.name in data:
                        col.color_tag = data[col.name]
            except Exception as e:
                print(f"Restore Error: {e}")
        
        # 归零状态
        scn.CA_Toggle = False
        scn.default_col_colors = ""
        
        return {'FINISHED'}

# --- 3D View Analyzer (同理) ---
class TOT_OT_ViewAnalyzer(bpy.types.Operator):
    bl_idname = "tot.viewanalyzer"
    bl_label = "Run 3D View Analyzer"
    
    def execute(self, context):
        scn = context.scene.tot_props
        # 备份当前显示模式
        if context.space_data.type == 'VIEW_3D':
            scn.last_shading = context.space_data.shading.color_type
            # 切换为 Object Color 显示
            context.space_data.shading.type = 'SOLID'
            context.space_data.shading.color_type = 'OBJECT'
        
        # [核心修复]
        scn.AA_Toggle = True
        return {'FINISHED'}

class TOT_OT_CleanViewAnalyzer(bpy.types.Operator):
    bl_idname = "tot.cleanviewanalyzer"
    bl_label = "Clear View Analyzer"
    
    def execute(self, context):
        scn = context.scene.tot_props
        # 还原
        if context.space_data.type == 'VIEW_3D':
             # 防止出错，如果有备份则用备份，否则默认 MATERIAL
            target = scn.last_shading if scn.last_shading else 'MATERIAL'
            context.space_data.shading.color_type = target
        
        # [核心修复]
        scn.AA_Toggle = False
        return {'FINISHED'}

classes = (
    TOT_OT_CollectionAnalyzer,
    TOT_OT_CleanColors,
    TOT_OT_ViewAnalyzer,
    TOT_OT_CleanViewAnalyzer,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)