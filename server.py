# 导入环境变量，必须放在最顶部
import load_envs

# 调试模式配置
from langchain.globals import set_debug

# 导入app实例
from router import app

from utils.db import init_db

import os

redis_host = os.getenv("REDIS_HOST")

if redis_host == '192.168.50.10':
    import tracemalloc

    tracemalloc.start()

    # 设置调试模式
    set_debug(False)


# 创建数据库表, 如果表不存在的话
init_db()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
