import bpy
from bpy.props import (
    StringProperty, BoolProperty, IntProperty, FloatProperty, 
    EnumProperty, CollectionProperty, PointerProperty
)


# --- 数据项类 (Collection Items) ---
class LOD_ImageItem(bpy.types.PropertyGroup):
    lod_image_name: StringProperty()
    image_size: StringProperty()
    image_selected: BoolProperty(default=False)
    packed_img: IntProperty(default=0) # 0:File, 1:Packed, 2:Linked

# --- 主属性组 ---
class LOD_Props(bpy.types.PropertyGroup):

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
    image_list: CollectionProperty(type=LOD_ImageItem)
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
        description="Camera used for screen coverage calculation",
        type=bpy.types.Object,
    )
    
    lod_dist_0: FloatProperty(name="LOD 0 Distance", default=10.0, min=0.0, description="High Detail End Distance")
    lod_dist_1: FloatProperty(name="LOD 1 Distance", default=25.0, min=0.0, description="Mid Detail End Distance")
    lod_dist_2: FloatProperty(name="LOD 2 Distance", default=50.0, min=0.0, description="Low Detail End Distance")
    # ==========================================================
    # 3. 维度三：视窗优化 (Viewport Optimization)
    # ==========================================================
    view_lod_enabled: BoolProperty(
        name="Enable Viewport LOD",
        description="Change object display mode (Solid/Wire/Bounds) based on distance",
        default=False,
    )
    
    # 定义显示模式枚举
    display_items = (
        ('TEXTURED', "Textured", "Full Material"),
        ('SOLID',    "Solid",    "Solid Shading"),
        ('WIRE',     "Wire",     "Wireframe"),
        ('BOUNDS',   "Bounds",   "Bounding Box (Fastest)"),
    )

    view_lod0_display: EnumProperty(name="L0 Display", items=display_items, default='TEXTURED')
    view_lod1_display: EnumProperty(name="L1 Display", items=display_items, default='SOLID')
    view_lod2_display: EnumProperty(name="L2 Display", items=display_items, default='WIRE')
    view_lod3_display: EnumProperty(name="L3 Display", items=display_items, default='BOUNDS')
    view_lod3_hide: BoolProperty(name="Hide at L3", description="Hide objects completely at far distance", default=False)

    # ==========================================================
    # 4. 维度二：模型减面 (Geometry LOD)
    # ==========================================================
    geo_lod_enabled: BoolProperty(
            name="Enable Geometry LOD",
            description="Enable screen ratio based decimation",
            default=False,
        )
    geo_lod_method: EnumProperty(
            name="LOD Method",
            items=[
                ("DECIMATE", "Decimate Modifier", "Use standard Decimate modifier"),
                ("GNODES", "Geometry Nodes", "Use Geometry Nodes (High Quality)"),
            ],
            default="GNODES",
        )
    
    geo_lod_min_faces: IntProperty(
        name="Min Faces", 
        default=1000, 
        min=0, 
        description="Protection: Objects with fewer faces will not be decimated"
    )
    
    # 这个参数同时控制 Decimate 的 ratio 和 GN 的 Factor
    geo_lod_min_ratio: FloatProperty(
            name="Min Ratio Protection", 
            default=0.1, 
            min=0.01, 
            max=1.0, 
            description="Strongest protection: Keep at least this ratio even at max distance"
        )
    # 最大合并距离
    geo_lod_max_dist: FloatProperty(
        name="Max Merge Distance",
        default=0.5,   # 默认 0.5m
        min=0.001,
        max=100.0,     # 给一个足够大的上限，应对巨型场景
        description="Merge radius at furthest distance (Higher = More aggressive)"
    )    

    # ==========================================================
    # 5. 实验性功能：Shader LOD (Shader Detail)
    # ==========================================================
    exp_shader_lod_enabled: BoolProperty(
        name="Enable Shader LOD",
        description="Reduce normal/displacement strength based on distance",
        default=False,
    )
    
    # 法线强度乘数 (LOD 0 默认为 1.0 即原始强度)
    exp_normal_mult_1: FloatProperty(name="L1 Normal %", default=0.7, min=0.0, max=1.0, subtype='FACTOR')
    exp_normal_mult_2: FloatProperty(name="L2 Normal %", default=0.3, min=0.0, max=1.0, subtype='FACTOR')
    exp_normal_mult_3: FloatProperty(name="L3 Normal %", default=0.0, min=0.0, max=1.0, subtype='FACTOR') # 极远处完全关闭法线

    # 置换强度乘数
    exp_disp_mult_1: FloatProperty(name="L1 Disp %", default=0.5, min=0.0, max=1.0, subtype='FACTOR')
    exp_disp_mult_2: FloatProperty(name="L2 Disp %", default=0.0, min=0.0, max=1.0, subtype='FACTOR') # 远距离通常不需要置换
    exp_disp_mult_3: FloatProperty(name="L3 Disp %", default=0.0, min=0.0, max=1.0, subtype='FACTOR')    



# 注册列表
classes = (
    LOD_ImageItem,
    LOD_Props,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.lod_props = PointerProperty(type=LOD_Props)

def unregister():
    del bpy.types.Scene.lod_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)