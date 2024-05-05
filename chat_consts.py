import os


def qdrant_path(path: str = "local_qdrant") -> str:
    """获取 qdrant向量数据库的绝对路径 """

    # 获取当前工作目录的绝对路径
    current_dir = os.getcwd()

    # 将目录路径组合起来
    dir_path = os.path.join(current_dir, path)
    print("目录路径:", dir_path)

    # 获取目录的绝对路径
    absolute_dir_path = os.path.abspath(dir_path)
    print("绝对路径:", absolute_dir_path)

    return absolute_dir_path
