import os

# 设置要生成的合并文件名
output_file = 'project_context.txt'

# 设置需要忽略的文件夹（例如 git 目录，编译目录等）
ignore_dirs = {'.git', 'node_modules', '__pycache__', 'dist', 'build', '.idea', '.vscode'}
# 设置需要读取的文件后缀（根据您的项目调整）
valid_extensions = {'.js', '.ts', '.vue', '.html', '.css', '.py', '.java', '.json', '.xml', '.go'}
# 设置需要忽略的文件名
ignore_files = {'.gitignore', 'README.md'}  # 新增：要忽略的文件

with open(output_file, 'w', encoding='utf-8') as outfile:
    for root, dirs, files in os.walk('.'):
        # 过滤掉不需要的文件夹
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            # 新增：排除忽略的文件 + 保留合法后缀的文件
            if file not in ignore_files and any(file.endswith(ext) for ext in valid_extensions):
                file_path = os.path.join(root, file)
                
                # 写入文件路径作为分隔符（这对 AI 理解结构至关重要）
                outfile.write(f"\n{'='*50}\n")
                outfile.write(f"File Path: {file_path}\n")
                outfile.write(f"{'='*50}\n\n")
                
                # 写入文件内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                        outfile.write("\n")
                except Exception as e:
                    outfile.write(f"Error reading file: {e}\n")

print(f"完成！所有代码已合并到 {output_file}.")