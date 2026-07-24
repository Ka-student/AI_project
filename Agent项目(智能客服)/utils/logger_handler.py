import logging
import os
from utils.path_tools import get_abs_path
from datetime import datetime

#日志保存的根目录
LOG_ROOT = get_abs_path("log")

#确保日志的目录存在(exist_ok=True 存在就跳过，不存在则创建)
os.makedirs(LOG_ROOT, exist_ok=True)

#日志的格式配置
DEFAULT_LOG_FORMAT = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
)
"""
asctime：时间
name：名字
levelname：级别
filename：文件名
lineno：文件的哪一行
message：日志正文
"""

def get_logger(
        name:str = "agent",
        console_level:int = logging.INFO,
        file_level:int = logging.DEBUG,
        log_file = None
) -> logging.Logger:
    """
    console_level=logging.INFO：控制台打印最低等级，INFO 及以上才会在终端显示
    file_level=logging.DEBUG：日志文件写入最低等级，DEBUG 及以上全部存本地文件
    log_file=None：自定义日志文件路径，不传则自动按时间生成文件名
    """

    #日志对象
    logger = logging.getLogger(name)
    #日志器接收所有等级日志
    logger.setLevel(logging.DEBUG)

    #避免重复添加Handler
    if logger.handlers:
        return logger

    #控制台Handler
    console_handler = logging.StreamHandler()
    #控制台只输出 ≥INFO 的日志
    console_handler.setLevel(console_level)
    #绑定定义好的日志格式
    console_handler.setFormatter(DEFAULT_LOG_FORMAT)
    #挂载在日志对象上
    logger.addHandler(console_handler)

    #文件Handler(写入本地log文件)
    if not log_file:            #日志文件的存放路径
        log_file = os.path.join(LOG_ROOT, f"{name}_{datetime.now().strftime('%Y%m%d%H')}.log")
    file_handler = logging.FileHandler(log_file,encoding="utf-8")
    #保存所有debug及以上日志
    file_handler.setLevel(file_level)
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)
    logger.addHandler(file_handler)

    return logger

#快捷获取日志管理器
logger = get_logger()

if __name__=="__main__":
    logger.info("信息日志")
    logger.error("错误日志")
    logger.warning("警告日志")
    logger.debug("调试日志")
