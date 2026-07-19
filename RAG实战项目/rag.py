from langchain_core.output_parsers import StrOutputParser
from vector_stores import VectorStoreService
from langchain_community.embeddings import DashScopeEmbeddings
import config_data as config
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.runnables import RunnablePassthrough,  RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.documents import Document
from file_history_store import get_history

def print_prompt(prompt):
    print("-"*50)
    print(prompt.to_string())
    print("-" * 50)
    return prompt



class RagService:
    def __init__(self):
        self.vector_service = VectorStoreService(
            embedding=DashScopeEmbeddings(model=config.embedding_model_name),
        )
        self.prompt_template = ChatPromptTemplate(
            [
                ("system","以我提供的已知参考资料为主"
                 "简洁和专业的回答用户问题。参考资料：{context}"),
                ("system", "你需要根据会话历史回应用户问题。"),
                MessagesPlaceholder("history"),
                ("user","请回答用户提问：{input}")
            ]
        )
        self.chat_model = ChatTongyi(model=config.chat_model_name,streaming=True)
        self.chain = self.__get_chain()

    def __get_chain(self):
        """获取最终的执行链"""
        retriever =self.vector_service.get_retriever()

        def format_document(docs:list[Document]):
            if not docs:
                return "无相关参考资料"
            formatted_str = ""
            for doc in docs:
                formatted_str += f"文档片段：{doc.page_content}\n文档元数据：{doc.metadata}\n\n"
            return formatted_str

        def temp1(value):
            return value["input"]
        def temp2(value):
            news_value = {}
            news_value["input"] = value["input"]["input"]
            news_value["context"] = value["context"]
            news_value["history"] = value["input"]["history"]
            return news_value

        prompt_start = {"input":RunnablePassthrough(),"context":RunnableLambda(temp1) | retriever | format_document}
        chain = (
            prompt_start | RunnableLambda(temp2) | self.prompt_template | print_prompt | self.chat_model | StrOutputParser()
        )
        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key="input",
            history_messages_key="history"
        )
        return conversation_chain



if __name__ == "__main__":
    session_config = {
        "configurable":{
            "session_id":"user_001"
        }
    }
    res = RagService().chain.stream({"input":"怎么查看电池"},session_config)
    for doc in res:
        print(doc)
