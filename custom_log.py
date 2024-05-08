import logging
from logging.handlers import TimedRotatingFileHandler
from pytz import timezone
from datetime import datetime, time
import os

from dotenv import load_dotenv
# 加载环境变量
load_dotenv()


# 创建日志记录器
log = logging.getLogger('ai')
log.setLevel(logging.INFO)


# 创建一个用于控制台输出的处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 创建一个处理器，用于写入日志文件，同时按周分割日志文件，每周一0点0分1秒切换
handler = TimedRotatingFileHandler(
    filename=os.getenv("LOG_PATH"),
    when="W0",
    interval=1,
    atTime=time(0, 0, 1)
)
handler.suffix = "%Y-%m-%d"
handler.setLevel(logging.INFO)


class CustomFormatter(logging.Formatter):
    """ 
    # 设置日志格式
    # 注意：这里我们自定义了一个格式化函数，以北京时间显示时间
    """
    converter = datetime.fromtimestamp

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created, timezone('Asia/Shanghai'))
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]  # 切片操作获取到毫秒级别的前三位


# 设置日志格式
fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 创建一个自定义格式化器
formatter = CustomFormatter(fmt=fmt)

# 给处理器设置格式化器
handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 给日志记录器添加处理器
log.addHandler(handler)
log.addHandler(console_handler)
