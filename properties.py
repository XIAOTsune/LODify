import bpy
from bpy.props import (
    StringProperty, BoolProperty, IntProperty, FloatProperty, 
    EnumProperty, CollectionProperty, PointerProperty
)

# --- 数据项类 (Collection Items) ---
class TOT_ImageItem(bpy.types.PropertyGroup):
    tot_image_name: StringProperty()
    image_size: StringProperty()
    image_selected: BoolProperty(default=False)
    packed_img: IntProperty(default=0) # 0:File, 1:Packed, 2:Linked

# --- 主属性组 ---
class TOT_Props(bpy.types.PropertyGroup):
    language: EnumProperty(
        name="Language",
        description="Switch Interface Language",
        items=[
            ('EN', "EN", "English"),
            ('CN', "中", "中文")
        ],
        default='CN'
    )
    # ==========================================================
    # 1. 全局开关与分析器
    # ==========================================================
    CA_Toggle: BoolProperty(default=False, name="Collection Analyzer Toggle")
    AA_Toggle: BoolProperty(default=False, name="Scene Analyzer Toggle")
    
    colA_Method: EnumProperty(
        name="Method", 
        items=[('m1', 'Default', ''), ('m2', 'Advanced', '')],
        default='m1'
    )
    # 分析器阈值
    mult_veryhigh: FloatProperty(default=0.9, min=0, max=1)
    mult_high: FloatProperty(default=0.8, min=0, max=1)
    mult_medium: FloatProperty(default=0.6, min=0, max=1)
    mult_low: FloatProperty(default=0.2, min=0, max=1)
    mult_very_low: FloatProperty(default=0.0, min=0, max=1)
    
    default_col_colors: StringProperty() 
    last_shading: StringProperty()

    # 贴图管理
    image_list: CollectionProperty(type=TOT_ImageItem)
    custom_index_image_list: IntProperty()
    
    # 缩放相关
    resize_size: EnumProperty(
        name="Target Size",
        items=[
            ('128', '128 px', ''), ('256', '256 px', ''), ('512', '512 px', ''),
            ('1024', '1024 px', ''), ('2048', '2048 px', ''), ('c', 'Custom', '')
        ],
        default='1024'
    )
    custom_resize_size: IntProperty(default=1024, min=4, name="Custom Px")
    use_same_directory: BoolProperty(default=True, name="Save in Blend Dir")
    custom_output_path: StringProperty(subtype='DIR_PATH', name="Custom Path")
    duplicate_images: BoolProperty(default=True, name="Duplicate Files") # 是否另存为副本

    # 统计信息
    r_total_images: IntProperty(name="Total Images")
    total_image_memory: StringProperty(name="Total Memory")
    # ==========================================================
    # 2. LOD 管理器核心设置 (LOD Manager Core)
    # ==========================================================
    # 用于计算距离的相机
    lod_camera: PointerProperty(
        name="LOD Camera",
        description="用于计算距离的相机，不设置则使用场景主相机",
        type=bpy.types.Object,
    )

    # 三个距离阈值 (定义 High / Mid / Low 区域)
    # Zone 1 (High): 0 ~ dist_0
    # Zone 2 (Mid):  dist_0 ~ dist_1
    # Zone 3 (Low):  dist_1 ~ dist_2
    # Zone 4 (Far):  > dist_2
    lod_dist_0: FloatProperty(name="Distance L0 (High)", default=10.0, min=0.0, unit='LENGTH')
    lod_dist_1: FloatProperty(name="Distance L1 (Mid)", default=30.0, min=0.0, unit='LENGTH')
    lod_dist_2: FloatProperty(name="Distance L2 (Low)", default=60.0, min=0.0, unit='LENGTH')

    # ==========================================================
    # 3. 维度三：视窗优化 (Viewport Optimization)
    # ==========================================================
    view_lod_enabled: BoolProperty(
        name="Enable Viewport LOD",
        description="根据距离改变物体显示模式 (Solid/Wire/Bounds)",
        default=False,
    )
    
    # 定义显示模式枚举
    display_items = (
        ('TEXTURED', "Textured", "完整材质"),
        ('SOLID',    "Solid",    "实体显示"),
        ('WIRE',     "Wire",     "线框显示"),
        ('BOUNDS',   "Bounds",   "包围盒 (最快)"),
    )

    view_lod0_display: EnumProperty(name="L0 Display", items=display_items, default='TEXTURED')
    view_lod1_display: EnumProperty(name="L1 Display", items=display_items, default='SOLID')
    view_lod2_display: EnumProperty(name="L2 Display", items=display_items, default='WIRE')
    view_lod3_display: EnumProperty(name="L3 Display", items=display_items, default='BOUNDS')
    view_lod3_hide: BoolProperty(name="Hide at L3", description="在极远距离直接隐藏物体", default=False)

    # ==========================================================
    # 4. 维度二：模型减面 (Geometry LOD)
    # ==========================================================
    geo_lod_enabled: BoolProperty(
        name="Enable Geometry LOD",
        description="启用基于距离的自动减面系统",
        default=False,
    )
    
    geo_lod_method: EnumProperty(
        name="LOD Method",
        items=[
            ("DECIMATE", "Decimate Modifier", "使用传统 Decimate 修改器 (破坏性较小，兼容性好)"),
            ("GNODES", "Geometry Nodes", "使用几何节点 (计算更快，功能更现代)"),
        ],
        default="DECIMATE",
    )
    
    geo_lod_min_faces: IntProperty(
        name="Min Faces", 
        default=1000, 
        min=0, 
        description="保护机制：面数少于此值的物体将不会被减面"
    )
    
    # 这个参数同时控制 Decimate 的 ratio 和 GN 的 Factor
    geo_lod_min_ratio: FloatProperty(
        name="Max Reduction Strength", 
        default=0.1, 
        min=0.01, 
        max=1.0, 
        description="最远距离时的压缩比例 (Decimate Ratio) 或 强度因子"
    )

# 注册列表
classes = (
    TOT_ImageItem,
    TOT_Props,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.tot_props = PointerProperty(type=TOT_Props)

def unregister():
    del bpy.types.Scene.tot_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)