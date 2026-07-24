# 扫地机器人智能客服 Agent 🤖

基于 **LangChain + Chroma + Streamlit + 通义千问** 构建的扫地/扫拖机器人智能客服系统。支持知识库问答（RAG）与个性化使用报告生成。

---

## 功能概览

| 功能 | 说明 |
|------|------|
| **知识库问答** | 基于扫地机器人 100 问、故障排除、维护保养、选购指南等文档，通过 RAG 精准回复用户问题 |
| **个性化报告** | 动态切换提示词，结合用户历史使用数据生成专属机器人使用报告与保养建议 |
| **流式对话** | 基于 Streamlit 实现流式打字机效果，前端实时展示模型输出 |
| **工具扩展** | 7 个可扩展 Agent 工具（天气查询、用户定位、使用记录检索等） |
| **日志监控** | 完整的工具调用日志 + 模型调用日志，支持调试与审计 |

## 技术栈

| 类别 | 选型 |
|------|------|
| 前端 | Streamlit |
| Agent 框架 | LangChain `create_agent`（ReAct 模式） |
| 对话模型 | 通义千问 `qwen3-max`（通过 `ChatTongyi` 调用） |
| 嵌入模型 | 通义 `text-embedding-v4`（通过 `DashScopeEmbeddings` 调用） |
| 向量数据库 | Chroma（本地持久化） |
| 文档切分 | RecursiveCharacterTextSplitter |
| 配置文件 | YAML 多文件 |
| 日志系统 | 自定义 Logger（控制台 + 文件双输出） |

## 项目结构

```
Agent项目/
├── app.py                          # Streamlit 入口，启动聊天界面
├── agent/                          # Agent 核心模块
│   ├── react_agent.py              # ReAct Agent 封装（流式输出）
│   └── tools/
│       ├── agent_tools.py          # 7 个 Tool 定义
│       └── middleware.py           # 3 个中间件（监控/日志/动态提示词）
├── rag/                            # RAG 模块
│   ├── vector_store.py             # 向量库构建与加载（含 MD5 去重）
│   └── rag_service.py             # 检索 + LLM 总结链
├── model/
│   └── factory.py                  # 抽象工厂：生成聊天模型 & 嵌入模型
├── config/                         # 配置文件目录
│   ├── rag.yml                     # 模型名称配置
│   ├── chroma.yml                  # 向量库参数（chunk_size, k 值等）
│   ├── prompts.yml                 # 提示词文件路径映射
│   └── agent.yml                   # Agent 配置（外部数据路径）
├── prompts/                        # 提示词模板
│   ├── main_prompt.txt             # 主系统提示词（ReAct 思考 + 工具说明）
│   ├── rag_summarize.txt           # RAG 总结提示词
│   └── report_prompt.txt           # 报告生成提示词
├── data/                           # 知识库数据
│   ├── 扫地机器人100问.pdf
│   ├── 扫地机器人100问2.txt
│   ├── 扫拖一体机器人100问.txt
│   ├── 故障排除.txt
│   ├── 维护保养.txt
│   ├── 选购指南.txt
│   └── external/
│       └── records.csv             # 用户使用记录（用于报告生成）
├── chroma_db/                      # Chroma 向量库持久化目录
│   └── chroma.sqlite3
├── utils/                          # 工具模块
│   ├── config_handler.py           # YAML 配置加载
│   ├── file_handler.py             # 文件加载（txt / pdf）+ MD5 计算
│   ├── path_tools.py               # 项目路径工具
│   ├── prompt_loader.py            # 提示词文件加载
│   └── logger_handler.py           # 日志管理器
├── log/                            # 运行日志
├── md5.txt                         # 已入库文件的 MD5 记录（去重）
└── requirements.txt                # （建议自行生成）
```

## 快速开始

### 1. 环境要求

- Python >= 3.10
- 通义千问 API Key（环境变量 `DASHSCOPE_API_KEY`）

### 2. 安装依赖

```bash
pip install langchain langchain-community langchain-chroma chromadb streamlit
pip install langchain-core langgraph pyyaml
pip install dashscope
pip install pypdf
```

### 3. 配置 API Key

```bash
# Windows PowerShell
$env:DASHSCOPE_API_KEY="your-api-key-here"

# 或写入 .env 文件
```

### 4. 启动知识库（首次运行）

```bash
python -m rag.vector_store
```

这会扫描 `data/` 目录下的 txt/pdf 文件，计算 MD5 去重后存入 Chroma。

### 5. 启动应用

```bash
streamlit run app.py
```

访问 `http://localhost:8501` 即可开始对话。

## 核心架构

### Agent 工作流程（ReAct）

```
用户输入
    │
    ├─ 系统提示词（main_prompt.txt）指导 Agent：
    │     思考 → 判断是否需要工具 → 调用工具 → 观察结果 → 再思考 → 回答
    │
    ├─ 7 个可用工具（见下方工具表）
    │
    └─ 3 个中间件拦截器
           ├─ monitor_tool      # 工具调用前后打日志，监听报告标记
           ├─ log_before_model  # 模型调用前记录状态
           └─ report_prompt_switch  # 动态切换系统提示词
```

### 动态提示词切换

系统实现了**场景自适应提示词切换**机制：

1. 用户请求「生成使用报告」
2. Agent 调用 `fill_context_for_report` 工具
3. 中间件 `monitor_tool` 检测到该调用 → 设置 `runtime.context["report"] = True`
4. 下一次模型调用前，`report_prompt_switch` 中间件检测到标记
5. 系统提示词从 `main_prompt.txt` 自动切换为 `report_prompt.txt`
6. Agent 切换到报告生成模式，拉取数据生成报告

### 工具清单

| 工具名 | 作用 | 入参 |
|--------|------|------|
| `rag_summarize` | 基于向量知识库检索并总结回答 | `query: str` |
| `get_weather` | 查询指定城市天气 | `city: str` |
| `get_user_location` | 获取用户所在城市（Mock） | 无 |
| `get_user_id` | 获取当前用户 ID（Mock） | 无 |
| `get_current_month` | 获取当前月份（Mock） | 无 |
| `fetch_external_data` | 从 CSV 拉取用户使用记录 | `user_id, month` |
| `fill_context_for_report` | 触发报告场景（切换提示词） | 无 |

### RAG 检索流程

```
用户提问
    │
    ├─ RecursiveCharacterTextSplitter 切分文档（chunk_size=200, overlap=20）
    │
    ├─ DashScopeEmbeddings 向量化 → Chroma 存储
    │
    ├─ 检索 top-k=3 相似片段
    │
    └─ 拼接 context → LLM 总结生成回答
```

## 配置说明

### `config/chroma.yml` 向量库参数

```yaml
collection_name: agent           # 集合名称
k: 3                            # 检索返回条数
data_path: data                 # 知识库数据目录
md5_hex_store: md5.txt          # MD5 记录文件
allow_knowledge_file_type: ["txt","pdf"]
chunk_size: 200                 # 切片大小
chunk_overlap: 20               # 切片重叠
separators: ["\n\n","\n",","]   # 分割符
```

### `config/rag.yml` 模型配置

```yaml
chat_model_name: qwen3-max
embedding_model_name: text-embedding-v4
```

## 典型对话示例

### 场景一：知识问答

```
用户：扫地机器人迷路了怎么办？
Agent：调用 rag_summarize("扫地机器人 迷路")
Agent：根据知识库，建议检查以下几点：1. 传感器是否被遮挡...
```

### 场景二：生成使用报告

```
用户：帮我生成本月的使用报告
Agent：调用 get_user_id → 获取用户ID
Agent：调用 get_current_month → 获取当前月份
Agent：调用 fill_context_for_report → 触发提示词切换
Agent：调用 fetch_external_data(uid, month) → 拉取记录
Agent：切换为报告提示词 → 生成完整报告
```

## 日志系统

日志分为两个输出通道：

| 通道 | 级别 | 存储位置 |
|------|------|---------|
| 控制台 | INFO 及以上 | 终端 |
| 文件 | DEBUG 及以上 | `log/agent_YYYYMMDDHH.log` |

日志格式：
```
2025-07-24 13:00:00 - agent - INFO - agent_tools.py:42 - [tool monitor]执行工具：rag_summarize
```

## 注意事项

- `get_weather` / `get_user_id` / `get_user_location` / `get_current_month` 均为 **Mock 实现**，返回随机值，接入真实服务需替换
- CSV 数据解析依赖固定列索引，扩充数据格式时需同步更新 `agent_tools.py` 中的 `generate_external_data()`
- 首次运行前必须先执行 `python -m rag.vector_store` 构建向量库
- 中间件 `langchain.agents.middleware` 需要 LangChain >= 1.0 版本

---

## 扩展开发指南

### 如何添加新工具

1. 在 `agent/tools/agent_tools.py` 中使用 `@tool` 装饰器定义新工具：

```python
from langchain_core.tools import tool

@tool(description="工具功能描述，Agent 会根据描述决定何时调用")
def my_new_tool(param1: str, param2: str) -> str:
    """实现工具逻辑"""
    # 你的代码
    return f"结果：{param1} - {param2}"
```

2. 在 `agent/react_agent.py` 的 `create_agent` 调用中注册新工具：

```python
tools=[
    rag_summarize,
    get_weather,
    # ... 其他已有工具
    my_new_tool,        # 加入新工具
]
```

3. 如需在子提示词（如 `report_prompt.txt`）中使用，需同步更新提示词中的工具说明。

### 如何接入真实接口替换 Mock 工具

当前 `get_weather`、`get_user_id`、`get_user_location`、`get_current_month` 返回随机模拟数据。替换为真实接口的示例：

```python
# 替换前（Mock）
@tool(description="获取指定城市的天气")
def get_weather(city: str) -> str:
    return f"城市{city}天气为晴天，30℃，体感 37℃，湿度高"

# 替换后（真实 API）
import requests

@tool(description="获取指定城市的天气")
def get_weather(city: str) -> str:
    api_url = f"https://weather-api.example.com/v1/{city}"
    resp = requests.get(api_url, timeout=10)
    data = resp.json()
    return f"{city}天气：{data['condition']}，{data['temp']}℃，湿度{data['humidity']}%"
```

### 如何添加新知识文档

1. 将新的 `.txt` 或 `.pdf` 文件放入 `data/` 目录
2. 重新运行向量库加载脚本：

```bash
python -m rag.vector_store
```

脚本会自动计算新文件 MD5，跳过已入库文件，仅处理新增文档。

### 调整检索参数

编辑 `config/chroma.yml`：

- **提高检索精度**：减小 `chunk_size`（如 150），增大 `k`（如 5）
- **降低 API 成本**：减小 `k`（如 2）
- **减少断句**：增大 `chunk_overlap`（如 50）

修改后需重建向量库：

```bash
# 删除旧库
Remove-Item -Recurse -Force chroma_db/*

# 重建
python -m rag.vector_store
```

### 切换底层模型

只需修改 `config/rag.yml`：

```yaml
# 切换到 qwen-plus（更快但能力稍弱）
chat_model_name: qwen-plus

# 或用其他兼容 OpenAI 接口的模型，需同步修改 model/factory.py
```

---

## 环境变量

| 变量名 | 必须 | 说明 |
|--------|:--:|------|
| `DASHSCOPE_API_KEY` | ✅ | 通义千问 API Key [申请地址](https://dashscope.console.aliyun.com/) |
| `LANGCHAIN_TRACING_V2` | ❌ | LangSmith 链路追踪（调试用，可选） |
| `LANGCHAIN_API_KEY` | ❌ | LangSmith API Key（可选） |

---

## 故障排查

### 启动报错 `ModuleNotFoundError`

```bash
pip install langchain langchain-community langchain-chroma chromadb streamlit dashscope pypdf pyyaml langgraph
```

### 向量库加载报错 `No such collection`

表示尚未构建向量库，请先执行：

```bash
python -m rag.vector_store
```

### Streamlit 界面空白

检查 `prompts/` 目录下的三个提示词文件是否存在且编码为 UTF-8。

### 工具调用失败

查看 `log/` 目录下的日志文件，搜索 `ERROR` 关键字定位问题：

```bash
# PowerShell
Select-String -Path "log/agent_*.log" -Pattern "ERROR"
```

### 切换模型后报错

确保 `model/factory.py` 中导入的模型类与 `config/rag.yml` 配置一致：

```python
# ChatTongyi 对应通义千问系列
from langchain_community.chat_models.tongyi import ChatTongyi

# 换用其他模型时修改工厂类和 config 同步调整
```

---

## 常见问题 FAQ

### Q: 为什么天气/位置/用户ID每次都不同？
A: 这几个工具是 Mock 实现，返回随机值用于演示。接入真实生产环境时需替换为实际 API。

### Q: 同一个文件放两次会不会重复入库？
A: 不会。系统用 MD5 做去重，已在 `md5.txt` 中记录的文件会自动跳过。

### Q: 如何清空知识库重新构建？
A: 删除 `chroma_db/` 和 `md5.txt` 后重新运行 `python -m rag.vector_store`。

### Q: 如何让 Agent 支持更多文件格式（如 Word、Excel）？
A: 在 `utils/file_handler.py` 中添加对应的 loader，在 `rag/vector_store.py` 的 `get_file_documents()` 中增加分支，并在 `config/chroma.yml` 的 `allow_knowledge_file_type` 中加入扩展名。

### Q: 报告和普通问答用的是同一套提示词吗？
A: 不同。系统通过中间件 `report_prompt_switch` 实现动态切换：普通问答用 `main_prompt.txt`，报告场景自动切到 `report_prompt.txt`。

### Q: 支持流式输出吗？
A: 支持。`app.py` 使用 `st.write_stream()` 实现打字机效果，`react_agent.py` 通过 `agent.stream(stream_mode="values")` 逐 token 输出。

### Q: 能部署到服务器供多人使用吗？
A: 可以。Streamlit 支持 `streamlit run app.py --server.port 8501 --server.address 0.0.0.0` 部署为 Web 服务。生产环境建议加 Nginx 反向代理和认证层。

---

## 设计模式

本项目应用了以下设计模式，便于理解和扩展：

| 模式 | 应用位置 | 说明 |
|------|---------|------|
| **抽象工厂** | `model/factory.py` | `BaseModelFactory` 定义接口，`ChatModelFactory` / `EmbeddingsFactory` 分别创建实例 |
| **模板方法** | `rag/vector_store.py` → `load_document()` | 固定的加载流程（MD5 检查 → 加载 → 切分 → 入库），各步骤可独立替换 |
| **责任链** | `agent/tools/middleware.py` | 三个中间件按序拦截，各自处理独立关注点 |
| **策略模式** | `report_prompt_switch` 中间件 | 根据运行时上下文动态选择提示词策略 |
| **适配器** | `utils/file_handler.py` | `txt_loader` / `pdf_loader` 为不同文件格式提供统一 `list[Document]` 接口 |

---
