import hashlib
import os
from utils.logger_handler import logger
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader,TextLoader

#获取文件的md5的十六进制字符串
def get_file_md5_hex(file_path:str):
    if not os.path.exists(file_path):
        logger.error(f"[md5计算]文件{file_path}不存在")
        return
    if not os.path.isfile(file_path):
        logger.error(f"[md5计算]路径P{file_path}不是文件")
        return
    md5_obj = hashlib.md5()
    chunk_size = 4096               #4KB分片，避免文件过大爆内存
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)

            """
            chunk = f.read(chunk_size)
            while chunk:
                md5_obj.update(chunk)
                chunk = f.read(chunk_size)
            """
            md5_hex =md5_obj.hexdigest()
            return md5_hex
    except Exception as e:
        logger.error(f"计算文件{file_path}md5失败.{str(e)}")

#返回文件夹内文件列表（允许的文件后缀）
def listdir_with_allowed_type(path:str,allowed_type:tuple[str]):
    files = []
    if not os.path.isdir(path):
        logger.error(f"[获取文件失败]{path}不是文件夹")
        return []
    for f in os.listdir(path):
        #enswith()  以什么结尾，是则返回True
        if f.endswith(allowed_type):
            files.append(os.path.join(path,f))
    #返回元组，可以不允许修改
    return tuple(files)

def pdf_loader(file_path:str,passwd=None) -> list[Document]:
    return PyPDFLoader(file_path).load()

def txt_loader(file_path:str,passwd=None) -> list[Document]:
    return TextLoader(file_path,encoding="utf-8").load()