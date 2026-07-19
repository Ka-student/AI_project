from langchain_core.chat_history import BaseChatMessageHistory
import os
from typing import Sequence
import json
from langchain_core.messages import message_to_dict, messages_from_dict, BaseMessage
from config_data import storage_path


def get_history(session_id):
        return FileChatMessageHistory(session_id,storage_path)

class FileChatMessageHistory(BaseChatMessageHistory):
    def __init__(self,session_id,storage_path):
        self.session_id = session_id            #会话ID
        self.storage_path = storage_path        #不同会话ID的存储文件，所在的文件夹路径
        #完整的文件路径
        self.file_path = os.path.join(self.storage_path, f"{self.session_id}.json")
        #确保文件夹存在
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    @property                   #@property装饰器将messages方法变成成员属性用
    def messages(self) -> list[BaseMessage]:
        #当前文件内：list[字典] 需要转为 list[BaseMessage]
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                messages_data = json.load(f)
                return messages_from_dict(messages_data)
        except FileNotFoundError:
            return []

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        all_messages = list(self.messages)          #已有的消息列表
        all_messages.extend(messages)               #新的和已有的融合成一个list
        """"
        将数据同步写入到本地文件中
        类对象写入文件 -> 一堆二进制
        为了方便，可以将BaseMessage消息转为字典（借助json模块以json字符串写入文件）
        官方message_to_dict：单个消息对象（BaseMessage类实例） ->字典
        """
        news_messages = []
        for message in all_messages:
            d = message_to_dict(message)
            news_messages.append(d)
        #[message_to_dict(message) for message in all_messages]

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("[\n")
            for i, msg in enumerate(news_messages):
                line = json.dumps(msg, ensure_ascii=False)  # 转成json字符串写入文件,ensure_ascii=False一定要有，否则中文无法正常显示
                if i < len(news_messages) - 1:
                    f.write(f"{line},\n")
                else:
                    f.write(f"{line}\n")
            f.write("]")

    def clear(self) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump([], f,ensure_ascii=False)


