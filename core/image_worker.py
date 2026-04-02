import sys
import os
import argparse
import shutil
# =============================================================================
# LODify Internal Component: Image Worker Process
# =============================================================================
# IMPORTANT:
# This file is a critical RUNTIME COMPONENT of the LODify add-on.
# It is executed via subprocess.Popen() to handle computationally expensive
# image processing tasks (Resizing/Format Conversion) asynchronously.
#
# Segregating this logic into a separate process allows LODify to bypass 
# Blender's Global Interpreter Lock (GIL) and prevents the UI from freezing
# when processing hundreds of high-resolution textures.
#
# This is NOT a development script. DO NOT REMOVE.
# =============================================================================
# =============================================================================
# Library Check (由 Blender 扩展环境自动提供)
# =============================================================================
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

def run_worker():
    # 参数切片处理
    # 如果 sys.argv 中包含 "--"，则只取它后面的部分
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    # 1. 解析命令行参数
    parser = argparse.ArgumentParser(description="LODify Image Worker")
    parser.add_argument("--src", required=True, help="Source image path")
    parser.add_argument("--dst", required=True, help="Destination image path")
    parser.add_argument("--size", type=int, default=1024, help="Target size in pixels")
    parser.add_argument("--action", default="RESIZE", choices=["RESIZE", "COPY"], help="Action to perform")
    
    args = parser.parse_args()
    
    src_path = args.src
    dst_path = args.dst
    target_size = args.size
    action = args.action

    # 2. 检查 PIL 环境
    if action == "RESIZE" and not HAS_PIL:
        # 如果是 RESIZE 任务但没有 PIL，报错并返回特定错误码
        print(f"ERROR: PIL not found in {sys.executable}")
        sys.exit(2) 

    try:
        # --- 逻辑分支 A: 直接复制 (COPY) ---
        if action == "COPY":
            if os.path.normpath(src_path) != os.path.normpath(dst_path):
                shutil.copy2(src_path, dst_path)
            print("SUCCESS")
            return

        # --- 逻辑分支 B: 缩放处理 (RESIZE) ---
        with Image.open(src_path) as img:
            ext = os.path.splitext(dst_path)[1].lower()
            
            # 1. PNG 透明度保护
            if ext == '.png' and img.mode != 'RGBA':
                img = img.convert('RGBA')

            # 2. 尺寸检查：如果原图已经很小，则直接复制
            width, height = img.size
            if width <= target_size and height <= target_size:
                if os.path.normpath(src_path) != os.path.normpath(dst_path):
                    shutil.copy2(src_path, dst_path)
                print("SUCCESS")
                return

            # 3. 计算缩放比例
            ratio = min(target_size / width, target_size / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)

            # 4. 执行缩放
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 5. 保存处理
            if ext in ('.jpg', '.jpeg'):
                if resized_img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', resized_img.size, (255, 255, 255))
                    background.paste(resized_img, mask=resized_img.split()[3])
                    resized_img = background
                elif resized_img.mode != 'RGB':
                    resized_img = resized_img.convert('RGB')
                resized_img.save(dst_path, quality=95, optimize=True)

            elif ext == '.png':
                resized_img.save(dst_path, optimize=True)
            else:
                resized_img.save(dst_path)

        print("SUCCESS")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_worker()
