# File Path: .\properties.py

import bpy
from bpy.props import (
    StringProperty, BoolProperty, IntProperty, FloatProperty, 
    EnumProperty, CollectionProperty, PointerProperty
)
from .i18n import i18n


def get_display_type_items():
    enum_items = bpy.types.Object.bl_rna.properties["display_type"].enum_items
    available = {item.identifier for item in enum_items}
    labels = {
        'TEXTURED': ("Textured", "Full Material"),
        'SOLID': ("Solid", "Solid Shading"),
        'WIRE': ("Wire", "Wireframe"),
        'BOUNDS': ("Bounds", "Bounding Box (Fastest)"),
    }
    ordered = ['TEXTURED', 'SOLID', 'WIRE', 'BOUNDS']
    items = []

    for identifier in ordered:
        if identifier in available:
            label, description = labels[identifier]
            items.append((identifier, label, description))

    if not items:
        for item in enum_items:
            items.append((item.identifier, item.name, item.description))

    return items


DISPLAY_TYPE_ITEMS = get_display_type_items()
DEFAULT_NEAR_DISPLAY = 'TEXTURED' if any(item[0] == 'TEXTURED' for item in DISPLAY_TYPE_ITEMS) else DISPLAY_TYPE_ITEMS[0][0]
DEFAULT_MID_DISPLAY = 'SOLID' if any(item[0] == 'SOLID' for item in DISPLAY_TYPE_ITEMS) else DISPLAY_TYPE_ITEMS[0][0]
DEFAULT_LOW_DISPLAY = 'WIRE' if any(item[0] == 'WIRE' for item in DISPLAY_TYPE_ITEMS) else DISPLAY_TYPE_ITEMS[-1][0]
DEFAULT_FAR_DISPLAY = 'BOUNDS' if any(item[0] == 'BOUNDS' for item in DISPLAY_TYPE_ITEMS) else DISPLAY_TYPE_ITEMS[-1][0]
# --- Collection Items ---
class LOD_ImageItem(bpy.types.PropertyGroup):
    lod_image_name: StringProperty()
    image_size: StringProperty()
    image_dimensions: StringProperty()  # 存储图片尺寸 (如 "1024 x 1024")
    image_selected: BoolProperty(default=False)
    packed_img: IntProperty(default=0) # 0:File, 1:Packed, 2:Linked

# --- Main Properties ---
class LOD_Props(bpy.types.PropertyGroup):

    # ==========================================================
    # 1. Global & Analyzers
    # ==========================================================
    CA_Toggle: BoolProperty(default=False, name="Collection Analyzer Toggle")
    AA_Toggle: BoolProperty(default=False, name="Scene Analyzer Toggle")
    CA_use_heatmap: BoolProperty(
        default=True, 
        name="Use Heatmap Colors",
        description="If disabled, analyzer will only add percentage suffix without changing collection colors"
    )
    
    colA_Method: EnumProperty(
        name="Method", 
        items=[
            ('m1', 'Default', ''),
            ('m2', 'Advanced', '')
        ],
        default='m1'
    )
    # Analyzer Thresholds
    mult_veryhigh: FloatProperty(default=0.9, min=0, max=1)
    mult_high: FloatProperty(default=0.8, min=0, max=1)
    mult_medium: FloatProperty(default=0.6, min=0, max=1)
    mult_low: FloatProperty(default=0.2, min=0, max=1)
    mult_very_low: FloatProperty(default=0.0, min=0, max=1)
    
    default_col_colors: StringProperty() 
    last_shading: StringProperty()

    # Image Management
    image_list: CollectionProperty(type=LOD_ImageItem)
    custom_index_image_list: IntProperty()
    
    # Resize Options
    resize_size: EnumProperty(
        name="Target Size",
        items=[
            ('128', '128 px', ''), ('256', '256 px', ''), ('512', '512 px', ''),
            ('1024', '1024 px', ''), ('2048', '2048 px', ''), ('c','Custom', '')
        ],
        default='1024'
    )
    custom_resize_size: IntProperty(default=1024, min=4, name="Custom Px")
    use_same_directory: BoolProperty(default=True, name="Save in Blend Dir")
    custom_output_path: StringProperty(subtype='DIR_PATH', name="Custom Path")
    duplicate_images: BoolProperty(default=True, name="Duplicate Files")

    # Stats
    r_total_images: IntProperty(name="Total Images")
    total_image_memory: StringProperty(name="Total Memory")
    
    # ==========================================================
    # 2. LOD Manager Core
    # ==========================================================
    lod_camera: PointerProperty(
        name="LOD Camera",
        description="Camera used for screen coverage calculation",
        type=bpy.types.Object,
    )
    
    lod_dist_0: FloatProperty(name="LOD 0 Distance", default=10.0, min=0.0, description="High Detail End Distance")
    lod_dist_1: FloatProperty(name="LOD 1 Distance", default=25.0, min=0.0, description="Mid Detail End Distance")
    lod_dist_2: FloatProperty(name="LOD 2 Distance", default=50.0, min=0.0, description="Low Detail End Distance")

    # ==========================================================
    # 3. Viewport Optimization
    # ==========================================================
    view_lod_enabled: BoolProperty(
        name="Enable Viewport LOD",
        description="Change object display mode (Solid/Wire/Bounds) based on distance",
        default=False,
    )
    
    view_lod0_display: EnumProperty(name="L0 Display", items=DISPLAY_TYPE_ITEMS, default=DEFAULT_NEAR_DISPLAY)
    view_lod1_display: EnumProperty(name="L1 Display", items=DISPLAY_TYPE_ITEMS, default=DEFAULT_MID_DISPLAY)
    view_lod2_display: EnumProperty(name="L2 Display", items=DISPLAY_TYPE_ITEMS, default=DEFAULT_LOW_DISPLAY)
    view_lod3_display: EnumProperty(name="L3 Display", items=DISPLAY_TYPE_ITEMS, default=DEFAULT_FAR_DISPLAY)
    view_lod3_hide: BoolProperty(name="Hide at L3", description="Hide objects completely at far distance", default=False)

    # ==========================================================
    # 4. Geometry LOD
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
    
    geo_lod_min_ratio: FloatProperty(
            name="Min Ratio Protection", 
            default=0.1, 
            min=0.01, 
            max=1.0, 
            description="Strongest protection: Keep at least this ratio even at max distance"
        )

    geo_lod_max_dist: FloatProperty(
        name="Max Merge Distance",
        default=0.5,   
        min=0.001,
        max=100.0,     
        description="Merge radius at furthest distance (Higher = More aggressive)"
    )    

    # ==========================================================
    # 5. Experimental: Shader LOD
    # ==========================================================
    exp_shader_lod_enabled: BoolProperty(
        name="Enable Shader LOD",
        description="Reduce normal/displacement strength based on distance",
        default=False,
    )
    
    exp_normal_mult_1: FloatProperty(name="L1 Normal %", default=0.7, min=0.0, max=1.0, subtype='FACTOR')
    exp_normal_mult_2: FloatProperty(name="L2 Normal %", default=0.3, min=0.0, max=1.0, subtype='FACTOR')
    exp_normal_mult_3: FloatProperty(name="L3 Normal %", default=0.0, min=0.0, max=1.0, subtype='FACTOR') 

    exp_disp_mult_1: FloatProperty(name="L1 Disp %", default=0.5, min=0.0, max=1.0, subtype='FACTOR')
    exp_disp_mult_2: FloatProperty(name="L2 Disp %", default=0.0, min=0.0, max=1.0, subtype='FACTOR') 
    exp_disp_mult_3: FloatProperty(name="L3 Disp %", default=0.0, min=0.0, max=1.0, subtype='FACTOR')    


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
