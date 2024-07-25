import os
import glob
import importlib
import inspect
import sys

def takepatch():
    # 获取当前文件的路径
    current_file = os.path.abspath(__file__)
    
    # 获取当前文件的目录
    current_dir = os.path.dirname(current_file)
    
    # 获取当前目录的父目录
    parent_dir = os.path.dirname(current_dir)
    
    # 获取项目根目录的路径（父目录的父目录）
    project_root = os.path.dirname(parent_dir)
    
    # 将项目根目录添加到 Python 路径中，以便能够导入模块
    sys.path.insert(0, project_root)
    
    # 构建 core/patch 目录的路径
    patch_dir = os.path.join(project_root, 'core', 'patch')
    
    # 确保 core/patch 目录存在
    if not os.path.exists(patch_dir):
        print(f"Warning: Directory {patch_dir} does not exist.")
        return
    
    # 遍历 core/patch 目录中的所有 Python 文件
    for filename in os.listdir(patch_dir):
        if filename.endswith('_patch.py'):
            module_name = f'core.patch.{filename[:-3]}'  # 使用完整的模块路径
            
            try:
                # 动态导入模块
                module = importlib.import_module(module_name)
                
                # 获取模块中所有的函数
                functions = inspect.getmembers(module, inspect.isfunction)
                
                # 执行所有以 _patch 结尾的函数
                for name, func in functions:
                    if name.endswith('_patch'):
                        #print(f"Executing {name} from {filename}")
                        func()
            
            except ImportError as e:
                print(f"Error importing {filename}: {e}")
            except Exception as e:
                print(f"Error executing patches in {filename}: {e}")

