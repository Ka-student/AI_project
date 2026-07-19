import os
"""项目的绝对路径"""
Base_Dir = os.path.dirname(os.path.abspath(__file__))


#存储md5文件路径
md5_path = os.path.join(Base_Dir,"data","md5.txt")
#数据库的表名
collection_name = "rag"
#数据库本地存储文件夹
persist_directory = os.path.join(Base_Dir,"chroma_db")
#分割后的文本段最大长度
chunk_size = 1000
#连续文本段之间的字符重叠数量
chunk_overlap = 100
#自然段落划分的符号
separators = ["\n\n","\n",".","!","?","。","！","？"," ",""]
#文本分割的阈值
max_split_chat_number = 1000

#每次检索返回多少个检索记录
similarity_k = 2
#RAG的嵌入模型
embedding_model_name = "text-embedding-v4"
#RAG的聊天模型
chat_model_name = "qwen3-max"
#聊天历史记录
storage_path = os.path.join(Base_Dir,"chat_history")
#用户ID
session_config = {
        "configurable":{
            "session_id":"user_001"
        }
    }


