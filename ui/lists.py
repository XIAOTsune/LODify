import bpy

class TOT_UL_ImageStats(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # 绘制列表的每一行
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            
            # 选择框
            row.prop(item, "image_selected", text="")
            
            # 图片名
            split = row.split(factor=0.6)
            split.label(text=item.tot_image_name, icon='IMAGE_DATA')
            
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

def register():
    bpy.utils.register_class(TOT_UL_ImageStats)

def unregister():
    bpy.utils.unregister_class(TOT_UL_ImageStats)