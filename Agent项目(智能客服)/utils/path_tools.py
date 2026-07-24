""""
为整个工程提供统一的绝对路径
"""

import os
def get_project_root() -> str:
    """获取工程所在的根目录"""
    #当前文件的绝对路径
    base_file = os.path.abspath(__file__)
    #获取当前文件所在的文件夹绝对路径
    utils_dir = os.path.dirname(base_file)
    # 获取工程的根目录
    project_dir = os.path.dirname(utils_dir)
    return project_dir

def get_abs_path(relative_path:str) -> str:
    #传递相对路径，得到绝对路径
    project_dir = get_project_root()
    return os.path.join(project_dir, relative_path)

if __name__ == '__main__':
    print(get_project_root())
    print(get_abs_path("data\\选购指南.txt"))