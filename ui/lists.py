import bpy

class LOD_OT_ImageInfoTooltip(bpy.types.Operator):
    """显示图片尺寸信息的 tooltip operator"""
    bl_idname = "lod.image_info_tooltip"
    bl_label = ""
    bl_options = {'INTERNAL'}
    
    dimensions: bpy.props.StringProperty()
    
    @classmethod
    def description(cls, context, properties):
        return f"尺寸: {properties.dimensions}"
    
    def execute(self, context):
        return {'CANCELLED'}  # 什么都不做，只是显示 tooltip


class LOD_UL_ImageStats(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # 绘制列表的每一行
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            
            # 选择框
            row.prop(item, "image_selected", text="")
            
            # 图片名 + 信息图标
            split = row.split(factor=0.6)
            name_row = split.row(align=True)
            name_row.label(text=item.lod_image_name, icon='IMAGE_DATA')
            
            # 信息图标 (悬停显示尺寸)
            op = name_row.operator("lod.image_info_tooltip", text="", icon='INFO', emboss=False)
            op.dimensions = item.image_dimensions
            
            # 状态图标 (打包/链接)
            r = split.row()
            if item.packed_img == 1:
                r.label(text="", icon='PACKAGE')
            elif item.packed_img == 2:
                r.label(text="", icon='LINKED')
            
            # 大小
            r.label(text=f"{item.image_size} MB")

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='IMAGE_DATA')

classes = (
    LOD_OT_ImageInfoTooltip,
    LOD_UL_ImageStats,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)