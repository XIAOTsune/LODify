# File Path: .\worker.py

import sys
import os
import argparse
import shutil

# 尝试导入 Pillow
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

def run_worker():
    # 1. 解析命令行参数
    parser = argparse.ArgumentParser(description="LODify Image Worker")
    parser.add_argument("--src", required=True, help="Source image path")
    parser.add_argument("--dst", required=True, help="Destination image path")
    parser.add_argument("--size", type=int, default=1024, help="Target size in pixels")
    parser.add_argument("--action", default="RESIZE", choices=["RESIZE", "COPY"], help="Action to perform")
    
    # 解析 args
    args = parser.parse_args()
    
    src_path = args.src
    dst_path = args.dst
    target_size = args.size
    action = args.action

    # 2. 检查 PIL 环境
    # 如果是 RESIZE 任务但没有 PIL，直接报错退出
    if action == "RESIZE" and not HAS_PIL:
        print(f"ERROR: PIL not found in {sys.executable}")
        sys.exit(2) # 退出码 2 表示缺少依赖

    try:
        # --- 逻辑分支 A: 直接复制 (COPY) ---
        # 用于 HDR/EXR 或其他不需要缩放的情况
        if action == "COPY":
            if os.path.normpath(src_path) != os.path.normpath(dst_path):
                shutil.copy2(src_path, dst_path)
            print("SUCCESS")
            return

        # --- 逻辑分支 B: 缩放处理 (RESIZE) ---
        with Image.open(src_path) as img:
            # 1. 针对 PNG 强制转 RGBA (防止 Alpha 丢失)
            ext = os.path.splitext(dst_path)[1].lower()
            if ext == '.png':
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

            # 2. 检查尺寸，防止无效缩放 (如果原图比目标还小，直接复制)
            width, height = img.size
            if width <= target_size and height <= target_size:
                if os.path.normpath(src_path) != os.path.normpath(dst_path):
                    shutil.copy2(src_path, dst_path)
                print("SUCCESS")
                return

            # 3. 计算新尺寸
            ratio = min(target_size / width, target_size / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)

            # 4. 执行缩放 (LANCZOS 质量最好)
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 5. 保存
            if ext in ('.jpg', '.jpeg'):
                # JPG 不支持透明，转 RGB 并加白底 (防止透明变黑)
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
                # 其他格式 (bmp, tiff etc)
                resized_img.save(dst_path)

        print("SUCCESS")

    except Exception as e:
        # 捕获所有错误并打印
        print(f"ERROR: {str(e)}")
        sys.exit(1) # 退出码 1 表示通用错误

if __name__ == "__main__":
    run_worker()