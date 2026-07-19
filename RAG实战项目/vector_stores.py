from langchain_chroma import Chroma
import config_data as config


class VectorStoreService:
    def __init__(self,embedding):
        """"
        :param embedding: 嵌入模型的传入
        """
        self.embedding = embedding
        self.vector_store = Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embedding,
            persist_directory=config.persist_directory
        )

    def get_retriever(self):
        """返回向量检索器，方便加入chain"""
        #每次检索返回similarity_threshold个检索记录
        return self.vector_store.as_retriever(search_kwargs={"k":config.similarity_k})

if __name__ == "__main__":
    from langchain_community.embeddings import DashScopeEmbeddings
    retriever = VectorStoreService(
        embedding=DashScopeEmbeddings(model="text-embedding-v4")
    ).get_retriever()
    #VectorStoreService对象，用invoke传参，是str
    res = retriever.invoke("查看电池")
    for item in res:
        print(item.page_content)
        print("-"*50)

