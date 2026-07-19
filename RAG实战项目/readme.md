# 服装商品智能客服 — RAG 实战项目文档

## 一、项目介绍

### 1.1 项目定位
本项目是一个基于 **RAG（Retrieval-Augmented Generation，检索增强生成）** 架构的**服装商品智能客服系统**。用户可通过 Streamlit Web 页面上传 TXT 知识文档，系统将其向量化存入 ChromaDB 后，即可在对话界面进行自然语言问答——大模型会先检索相关知识片段，再基于检索结果生成精准、专业的回复。

### 1.2 技术栈

| 层级 | 技术/库 | 用途 |
|---|---|---|
| **LLM 框架** | LangChain (langchain_core / langchain_community) | RAG 链编排、消息历史管理 |
| **向量数据库** | ChromaDB (langchain_chroma) | 文档向量存储与相似度检索 |
| **嵌入模型** | DashScope text-embedding-v4 | 将文本片段转为向量 |
| **对话模型** | 通义千问 qwen3-max (ChatTongyi) | 基于检索上下文生成回复 |
| **文本分割** | RecursiveCharacterTextSplitter | 长文档智能切块 |
| **Web UI** | Streamlit | 知识库上传 + 智能客服双页面 |
| **去重机制** | hashlib MD5 | 防止同一内容重复入库 |
| **会话持久化** | JSON 文件 (FileChatMessageHistory) | 多轮对话记忆跨轮保留 |

### 1.3 项目架构

```
┌──────────────────────┐      ┌───────────────────────┐
│  app_file_uploader   │      │      app_qa.py        │
│  (知识库上传页面)      │      │   (智能客服问答页面)     │
│       Streamlit      │      │       Streamlit       │
└──────────┬───────────┘      └───────────┬───────────┘
           │                              │
           ▼                              ▼
┌──────────────────────┐      ┌───────────────────────┐
│  knowledge_base.py   │      │       rag.py          │
│  - MD5 去重检查       │      │  - 检索器调度           │
│  - 文本分割           │      │  - Prompt 模板         │
│  - 向量化入库         │      │  - RunnableWithMsgHist│
└──────────┬───────────┘      └───────────┬───────────┘
           │                              │
           ▼                              ▼
┌──────────────────────┐      ┌───────────────────────┐
│   vector_stores.py   │      │ file_history_store.py │
│  - ChromaDB 封装      │◄─────│  - 会话 JSON 持久化     │
│  - 检索器返回         │      │  - 多 session 隔离      │
└──────────┬───────────┘      └───────────────────────┘
           │
           ▼
┌──────────────────────┐
│   config_data.py     │
│  - 全局配置常量       │
└──────────────────────┘
```

---

## 二、文件结构说明

```
RAG实战项目/
├── config_data.py          # 全局配置文件（路径、模型名、分块参数等）
├── knowledge_base.py       # 知识库更新服务（MD5去重 + 文本分割 + 向量入库）
├── vector_stores.py        # 向量存储服务（ChromaDB 封装，提供检索器）
├── rag.py                  # RAG 核心服务（检索→增强→生成完整链）
├── file_history_store.py   # 长期会话记忆存储服务（FileChatMessageHistory）
├── app_file_uploader.py    # Streamlit 知识库上传页面
├── app_qa.py               # Streamlit 智能客服问答页面
├── readme.md               # 原项目简要说明
├── readme1.md              # 本详细文档
├── data/
│   └── md5.txt             # 已入库内容的 MD5 记录（去重用）
├── chroma_db/              # ChromaDB 向量数据持久化目录
└── chat_history/           # 会话历史 JSON 文件存储目录
```

---

## 三、模块详细分析

### 3.1 config_data.py — 全局配置

**核心职责**：统一管理所有可调参数，避免硬编码散落各模块。

**关键配置项**：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `Base_Dir` | 项目根目录 | `os.path.dirname(os.path.abspath(__file__))` |
| `md5_path` | `{Base_Dir}/data/md5.txt` | MD5 去重记录文件路径 |
| `collection_name` | `"rag"` | ChromaDB 集合名称 |
| `persist_directory` | `{Base_Dir}/chroma_db` | 向量数据库本地持久化目录 |
| `chunk_size` | 1000 | 文本分割最大长度 |
| `chunk_overlap` | 100 | 相邻文本块重叠字符数 |
| `separators` | `["\n\n","\n",".","!","?","。","！","？"," ",""]` | 分割优先级降序排列的符号列表 |
| `max_split_chat_number` | 1000 | 触发文本分割的阈值（超过此长度才分割） |
| `similarity_threshold` | 2 | 每次检索返回的文档片段数量（top_k） |
| `embedding_model_name` | `"text-embedding-v4"` | DashScope 嵌入模型 |
| `chat_model_name` | `"qwen3-max"` | 通义千问对话模型 |
| `storage_path` | `{Base_Dir}/chat_history` | 会话历史文件存储目录 |

---

### 3.2 knowledge_base.py — 知识库更新服务

**核心职责**：接收原始文本，经过去重检查、文本分割后写入 ChromaDB 向量库。

#### 关键函数

| 函数 | 签名 | 说明 |
|---|---|---|
| `get_string_md5` | `(input_str, encoding="utf-8") -> str` | 将文本内容转为 MD5 十六进制字符串，作为内容唯一指纹 |
| `check_md5` | `(md5_str) -> bool` | 逐行比对 `md5.txt`，返回 `True` 表示已处理过（应跳过），`False` 表示新内容 |
| `save_md5` | `(md5_str) -> None` | 将 MD5 追加写入 `md5.txt`，标记该内容已入库 |

#### KnowledgeBaseService 类

| 方法 | 说明 |
|---|---|
| `__init__` | 初始化 ChromaDB 连接 + `RecursiveCharacterTextSplitter` 分割器 |
| `upload_by_str(data, filename)` | 完整入库流程：MD5 去重 → 按需分割 → 写入向量库 |

**MD5 去重机制详解**：

```
用户上传文本
      │
      ▼
 get_string_md5(data)  →  计算 MD5
      │
      ▼
 check_md5(md5_hex)   →  逐行比对 md5.txt
      │
   ┌──┴──┐
   │ 命中  │ →  return "[跳过]内容已经存在知识库中"
   └──────┘
      │ 未命中
      ▼
  len(data) > max_split_chat_number ?
   ┌──┴──┐
   │ 是   │ →  RecursiveCharacterTextSplitter.split_text(data)
   └──────┘
   │ 否   │ →  直接使用原文 [data]
      ▼
 Chroma.add_texts(texts, metadatas)
      │
      ▼
 save_md5(md5_hex)    →  持久化 MD5 记录
```

**文本分割策略**：
- 使用 `RecursiveCharacterTextSplitter`，优先按自然段落符号 `\n\n` → `\n` → 中英文标点 → 空格 → 单字符逐级拆分
- `chunk_size=1000`，`chunk_overlap=100` 确保语义连贯性
- 短于 `max_split_chat_number`(1000) 的文本不分割，直接入库

**元数据设计**：
```python
metadata = {
    "source": filename,       # 来源文件名
    "createtime": "2026-07-19 12:00:00",  # 入库时间
    "operator": "小曹"        # 操作者标识
}
```

---

### 3.3 vector_stores.py — 向量存储服务

**核心职责**：封装 ChromaDB 连接，对外提供检索器接口。

#### VectorStoreService 类

```python
class VectorStoreService:
    def __init__(self, embedding):
        # 初始化 Chroma 实例，指定集合名、嵌入函数、持久化目录
        self.vector_store = Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embedding,
            persist_directory=config.persist_directory
        )

    def get_retriever(self):
        # 返回 top_k=2 的检索器，可直接接入 LangChain Chain
        return self.vector_store.as_retriever(
            search_kwargs={"k": config.similarity_threshold}
        )
```

**设计要点**：
- `embedding` 由外部注入（依赖反转），方便切换不同嵌入模型
- `get_retriever()` 返回的检索器是 LangChain 标准 `Retriever` 接口，可直接通过 `|` 管道符接入 Runnable 链
- 每次检索返回 2 条最相关文档片段

---

### 3.4 rag.py — RAG 核心服务

**核心职责**：构建完整的「检索 → 增强 → 生成」执行链，并集成多轮对话记忆。

#### RagService 类初始化

```python
class RagService:
    def __init__(self):
        # 1. 向量存储服务（嵌入模型：text-embedding-v4）
        self.vector_service = VectorStoreService(
            embedding=DashScopeEmbeddings(model=config.embedding_model_name)
        )
        # 2. Prompt 模板
        self.prompt_template = ChatPromptTemplate([...])
        # 3. 对话模型（qwen3-max）
        self.chat_model = ChatTongyi(model=config.chat_model_name)
        # 4. 构建完整执行链
        self.chain = self.__get_chain()
```

#### Prompt 模板设计

```python
ChatPromptTemplate([
    ("system", "以我提供的已知参考资料为主简洁和专业的回答用户问题。参考资料：{context}"),
    ("system", "你需要根据会话历史回应用户问题。"),
    MessagesPlaceholder("history"),                      # 动态注入历史消息
    ("user", "请回答用户提问：{input}")
])
```

**设计特点**：
- 两条 `system` 消息：第一条约束模型以检索到的参考资料为主进行回答；第二条强调会话历史上下文
- `MessagesPlaceholder("history")` 由 `RunnableWithMessageHistory` 自动填充
- `{context}` 占位符接收向量检索结果；`{input}` 接收用户当前提问

#### RAG 链构建 — 完整数据流

```python
def __get_chain(self):
    retriever = self.vector_service.get_retriever()

    # 文档格式化函数：将检索到的 Document 列表转为结构化字符串
    def format_document(docs: list[Document]):
        if not docs:
            return "无相关参考资料"
        formatted_str = ""
        for doc in docs:
            formatted_str += f"文档片段：{doc.page_content}\n文档元数据：{doc.metadata}\n\n"
        return formatted_str

    # temp1: 从输入中提取纯文本，传给检索器
    def temp1(value):
        return value["input"]

    # temp2: 重组字典，将检索结果(context)和历史(history)合并到 prompt 所需格式
    def temp2(value):
        news_value = {}
        news_value["input"] = value["input"]["input"]
        news_value["context"] = value["context"]
        news_value["history"] = value["input"]["history"]
        return news_value

    # 第一阶段：并行获取 input 和 context
    prompt_start = {
        "input": RunnablePassthrough(),
        "context": RunnableLambda(temp1) | retriever | format_document
    }

    # 第二阶段：串联 prompt → 打印调试 → 模型生成 → 字符串解析
    chain = (
        prompt_start
        | RunnableLambda(temp2)
        | self.prompt_template
        | print_prompt          # 调试：控制台打印完整 prompt
        | self.chat_model
        | StrOutputParser()
    )

    # 第三阶段：包装为带历史记忆的对话链
    conversation_chain = RunnableWithMessageHistory(
        chain,
        get_history,                  # 会话历史工厂函数
        input_messages_key="input",
        history_messages_key="history"
    )
    return conversation_chain
```

**链执行流程（图形化）**：

```
用户输入: {"input": "怎么查看电池", "history": [...]}
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                    ▼
  RunnablePassthrough               RunnableLambda(temp1)
  直接透传整个输入                      提取 input 纯文本
        │                                    │
        │                                    ▼
        │                              retriever.invoke("怎么查看电池")
        │                                    │
        │                                    ▼
        │                              format_document(docs)
        │                              拼接为结构化字符串
        │                                    │
        └─────────────────┬──────────────────┘
                          ▼
            {"input": {原始输入}, "context": "文档片段..."}
                          │
                          ▼
                 RunnableLambda(temp2)
              重组: {input, context, history}
                          │
                          ▼
                 ChatPromptTemplate
              注入 system/user 消息
                          │
                          ▼
                    print_prompt
              控制台打印完整 Prompt
                          │
                          ▼
                    ChatTongyi
              qwen3-max 生成回复
                          │
                          ▼
                  StrOutputParser
                   输出纯文本
```

#### RunnableWithMessageHistory — 多轮对话记忆

```python
conversation_chain = RunnableWithMessageHistory(
    chain,
    get_history,              # 工厂函数: session_id → FileChatMessageHistory
    input_messages_key="input",
    history_messages_key="history"
)
```

**调用方式**：
```python
session_config = {
    "configurable": {
        "session_id": "user_001"
    }
}
res = RagService().chain.invoke({"input": "怎么查看电池"}, session_config)
```

**工作机制**：
1. 调用时从 `session_config` 中提取 `session_id`
2. 调用 `get_history(session_id)` 获得 `FileChatMessageHistory` 实例
3. 自动读取历史消息注入 `history` 占位符
4. 执行链后将本轮 Human/AI 消息写入历史
5. 下次同 `session_id` 调用即可获得完整上下文

---

### 3.5 file_history_store.py — 会话记忆存储

**核心职责**：实现 LangChain 的 `BaseChatMessageHistory` 抽象，将多轮对话持久化到本地 JSON 文件。

#### FileChatMessageHistory 类

```python
class FileChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id, storage_path):
        # 文件路径: {storage_path}/{session_id}.json
        self.file_path = os.path.join(self.storage_path, f"{self.session_id}.json")
```

| 成员 | 类型 | 说明 |
|---|---|---|
| `messages` | `@property` | 读取 JSON 文件，调用 `messages_from_dict` 反序列化为 `list[BaseMessage]` |
| `add_messages(messages)` | 方法 | 追加新消息并全量写回 JSON（先读已有 + 合并 + 序列化写入） |
| `clear()` | 方法 | 清空当前会话历史（写入空数组 `[]`） |

**序列化流程**：
```
BaseMessage 对象
      │ message_to_dict()
      ▼
   字典 (dict)
      │ json.dumps(ensure_ascii=False)
      ▼
 JSON 文件持久化
```

**读写流程**：
```
写入: add_messages(new_msgs)
  1. self.messages → 反序列化已有消息
  2. all_messages = 已有 + 新消息
  3. 逐条 message_to_dict → 转字典
  4. json.dumps 写入文件

读取: self.messages (property)
  1. 读取 JSON 文件 → list[dict]
  2. messages_from_dict → list[BaseMessage]
```

**文件格式示例**（`chat_history/user_001.json`）：
```json
[
{"type": "human", "data": {"content": "怎么查看电池"}},
{"type": "ai", "data": {"content": "请在系统设置中..."}}
]
```

#### 工厂函数

```python
def get_history(session_id):
    return FileChatMessageHistory(session_id, storage_path)
```

此函数作为 `RunnableWithMessageHistory` 的 `get_session_history` 参数，每次新会话时按 `session_id` 动态创建对应的历史存储实例，实现多用户/多会话隔离。

---

### 3.6 app_file_uploader.py — 知识库上传页面

**核心职责**：提供 Streamlit Web 页面，让用户上传 TXT 文件并入库。

**页面结构**：
```
┌──────────────────────────────┐
│     知识库更新服务             │
├──────────────────────────────┤
│  [上传 TXT 文件按钮]          │
├──────────────────────────────┤
│  文件名：xxx.txt              │
│  格式：text/plain | 大小: X KB│
│  [文件内容预览]               │
│  [载入知识库... 转圈动画]      │
│  [成功]/[跳过] 状态提示        │
└──────────────────────────────┘
```

**关键机制**：
- `st.session_state["service"]` 保持 `KnowledgeBaseService` 单例（Streamlit 重跑时不重复初始化 ChromaDB）
- 文件解码：`uploader_file.getvalue().decode("utf-8")`
- 调用 `upload_by_str(text, file_name)` 完成去重+分割+入库
- 返回状态字符串在前端展示

---

### 3.7 app_qa.py — 智能客服问答页面

**核心职责**：提供 Streamlit 对话界面，用户输入问题，系统返回 RAG 增强后的回复。

**页面结构**：
```
┌──────────────────────────────┐
│         智能客服               │
├──────────────────────────────┤
│  AI: 你好，有什么可以帮助你？   │
│  User: 怎么查看电池            │
│  AI: [RAG 增强回复...]        │
├──────────────────────────────┤
│  [用户输入框]                  │
└──────────────────────────────┘
```

**关键机制**：
- `st.session_state["message"]` 维护消息列表（用于 UI 渲染历史记录）
- `st.session_state["rag"]` 保持 `RagService` 单例（一次初始化 ChromaDB + 对话链）
- 调用链：`st.session_state["rag"].chain.invoke({"input": prompt}, config.session_config)`
- 每次对话自动通过 `RunnableWithMessageHistory` 读写历史，无需手动管理
- 使用 `st.spinner("AI思考中...")` 提供加载反馈

---

## 四、重点代码解析

### 4.1 RAG 链构建 — 分阶段数据转换

RAG 链的核心难点在于**不同阶段所需的数据结构不同**。本项目通过两个辅助函数巧妙解决：

**阶段一**：并行获取 `input` 和 `context`
```python
prompt_start = {
    "input": RunnablePassthrough(),                    # 原样穿透整个输入
    "context": RunnableLambda(temp1) | retriever | format_document  # 提取纯文本 → 检索 → 格式化
}
```
这里使用了 LangChain 的 `RunnableParallel`（字典语法），两路**同时执行**，输出一个包含 `input` 和 `context` 的字典。

**阶段二**：重组为 Prompt 模板所需格式
```python
def temp2(value):
    news_value = {}
    news_value["input"] = value["input"]["input"]     # 提取纯文本
    news_value["context"] = value["context"]           # 检索结果
    news_value["history"] = value["input"]["history"]  # 从原始输入中提取历史
    return news_value
```
因为 `RunnablePassthrough` 透传了整个原始输入（含 `history`），而 Prompt 模板需要 `input`/`context`/`history` 三个平级字段，`temp2` 完成这个**字典重组**。

### 4.2 Prompt 模板设计 — 多层次 System Message

```python
[
    ("system", "以我提供的已知参考资料为主简洁和专业的回答用户问题。参考资料：{context}"),
    ("system", "你需要根据会话历史回应用户问题。"),
    MessagesPlaceholder("history"),
    ("user", "请回答用户提问：{input}")
]
```

两条 `system` 消息形成**双重约束**：
1. **知识约束**：强制模型以检索到的参考资料为主回答（防止幻觉）
2. **上下文约束**：提醒模型参考历史对话（保持连贯性）

`MessagesPlaceholder("history")` 在最终序列中展开为所有历史 HumanMessage/AIMessage，而非简单的文本拼接，保留了消息角色信息。

### 4.3 RunnableWithMessageHistory — 对话记忆自动化

```python
RunnableWithMessageHistory(
    chain,
    get_history,
    input_messages_key="input",
    history_messages_key="history"
)
```

**自动行为**：
- **调用前**：按 `session_id` 加载历史消息 → 注入 `history` 占位符
- **调用后**：将本轮 Human + AI 消息自动写入 `FileChatMessageHistory`
- **隔离性**：不同 `session_id` 读写不同 JSON 文件，天然支持多用户

开发者无需手动管理 `messages` 列表，链的输入只需 `{"input": "用户提问"}`，搭配 `session_config` 即可。

### 4.4 MD5 去重机制

```python
def check_md5(md5_str):
    for line in open(config.md5_path, 'r', encoding="utf-8").readlines():
        if line.strip() == md5_str:
            return True
    return False
```

**设计考量**：
- 去重粒度为**内容级别**（非文件名级别）：即使改文件名、重复上传，只要内容相同即拒绝
- 逐行比对简单可靠，适合中小规模使用（大规模可用 set/hash 表优化）
- 首次运行时自动创建空的 `md5.txt`，避免 FileNotFoundError

### 4.5 Streamlit UI — 状态管理与单例模式

两个 Streamlit 页面都使用 `st.session_state` 保持对象单例：

```python
if "service" not in st.session_state:
    st.session_state["service"] = KnowledgeBaseService()
```

**原因**：Streamlit 在每次页面交互时**重新执行整个脚本**。若不缓存，ChromaDB 连接、RAG 链等重量级对象会被反复创建，导致性能极差。`st.session_state` 在脚本重跑间保持状态，确保只初始化一次。

---

## 五、数据流说明

### 5.1 知识入库流程（写入方向）

```
用户上传 TXT 文件 (app_file_uploader.py)
        │
        ▼
  uploader_file.getvalue().decode("utf-8")
        │
        ▼
  KnowledgeBaseService.upload_by_str(text, filename)
        │
        ├─ get_string_md5(data)  → 计算 MD5 指纹
        ├─ check_md5(md5_hex)   → 是否已存在？
        │    ├─ 是 → return "[跳过]"
        │    └─ 否 ↓
        ├─ len(data) > 1000 ?
        │    ├─ 是 → RecursiveCharacterTextSplitter.split_text(data)
        │    └─ 否 → [data]
        ├─ Chroma.add_texts(chunks, metadatas)  → 写入向量库
        └─ save_md5(md5_hex)  → 持久化 MD5 记录
```

### 5.2 问答流程（读取方向）

```
用户在 app_qa.py 输入问题: "怎么查看电池"
        │
        ▼
  chain.invoke({"input": "怎么查看电池"}, session_config)
        │
        ├─ RunnableWithMessageHistory 自动加载历史消息
        │
        ├─ [并行] temp1("怎么查看电池") → retriever.invoke() → ChromaDB 相似度检索
        │    → 返回 top-2 相关 Document
        │    → format_document() 拼接为文本字符串
        │
        ├─ [并行] RunnablePassthrough 保留原始输入（含 history）
        │
        ├─ temp2 重组: {input, context, history}
        │
        ├─ ChatPromptTemplate 注入 system/user 消息 + 填充占位符
        │
        ├─ print_prompt 控制台输出完整 Prompt（调试用）
        │
        ├─ ChatTongyi(qwen3-max) 生成回复
        │
        ├─ StrOutputParser → 纯文本
        │
        ├─ RunnableWithMessageHistory 自动保存本轮消息
        │
        └─ Streamlit 渲染回复到页面
```

### 5.3 对话持久化流程

```
调用 chain.invoke({"input": "xxx"}, session_config)
        │
        ▼
  RunnableWithMessageHistory
        │
        ├─ Before: get_history("user_001")
        │    → FileChatMessageHistory.messages
        │    → 读取 chat_history/user_001.json → list[BaseMessage]
        │    → 注入 history 占位符
        │
        ├─ Execute: 完整 RAG 链执行
        │
        └─ After: history.add_messages([HumanMessage, AIMessage])
             → 合并已有 + 新消息
             → message_to_dict 序列化
             → 写入 chat_history/user_001.json
```

---

## 六、调用方式和运行说明

### 6.1 环境要求

| 依赖 | 说明 |
|---|---|
| Python 3.8+ | — |
| LangChain 生态 | `langchain_core`, `langchain_community`, `langchain_chroma`, `langchain_text_splitters` |
| Streamlit | Web UI 框架 |
| ChromaDB | 向量数据库 |
| DashScope API Key | 阿里云灵积模型服务（嵌入 + 对话） |

### 6.2 安装依赖

```bash
pip install langchain langchain-core langchain-community langchain-chroma langchain-text-splitters streamlit chromadb dashscope
```

### 6.3 配置 API Key

设置阿里云 DashScope API Key：
```bash
set DASHSCOPE_API_KEY=your_api_key_here
```

或在代码中显式设置（不推荐）：
```python
import os
os.environ["DASHSCOPE_API_KEY"] = "your_api_key_here"
```

### 6.4 启动方式

**Step 1 — 启动知识库上传页面**：
```bash
streamlit run .\app_file_uploader.py
```
打开浏览器访问 `http://localhost:8501`，上传 TXT 知识文档（服装商品信息、FAQ 等）。

**Step 2 — 启动智能客服页面**：
```bash
streamlit run .\app_qa.py
```
打开浏览器访问 `http://localhost:8501`，在输入框中提问，系统将基于知识库给出 RAG 增强回复。

### 6.5 命令行测试

也可直接运行各模块的 `__main__` 块进行单元测试：

```bash
# 测试向量检索
python .\vector_stores.py

# 测试知识入库
python .\knowledge_base.py

# 测试 RAG 对话
python .\rag.py
```

### 6.6 目录结构（运行后自动生成）

```
RAG实战项目/
├── chroma_db/             ← ChromaDB 向量数据（首次运行自动创建）
├── data/
│   └── md5.txt            ← MD5 去重记录（首次上传自动创建）
├── chat_history/          ← 会话历史 JSON 文件（首次对话自动创建）
│   └── user_001.json
```

