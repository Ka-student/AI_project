from langchain.agents import AgentState
from langchain.agents.middleware import wrap_tool_call, dynamic_prompt, ModelRequest, before_model
from typing import Callable
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.runtime import Runtime
from langgraph.types import Command
from utils.logger_handler import logger
from utils.prompt_loader import load_system_prompts,load_report_prompts

@wrap_tool_call
def monitor_tool(
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:                 #工具执行的监控
    """"
    request  请求的数据封装
    handler  执行的函数本身
    ToolCallRequest:工具调用请求体
    Callable[[入参类型列表], 返回值类型]
    """
    logger.info(f"[tool monitor]执行工具：{request.tool_call['name']}")
    logger.info(f"[tool monitor]传入参数：{request.tool_call['args']}")
    try:
        result = handler(request)
        logger.info(f"[tool monitor]工具{request.tool_call['name']}调用成功")
        if request.tool_call['name'] == "fill_context_for_report":
            request.runtime.context["report"] = True
        return result
    except Exception as e:
        logger.error(f"工具{request.tool_call['name']}调用失败，原因：{str(e)}")
        raise

@before_model
def log_before_model(
        state: AgentState,
        runtime: Runtime,
):              #在模型执行前输出日志
    """
    state  整个agent智能体中的状态记录
    runtime  记录了整个执行过程中的上下文信息
    """
    logger.info(f"[log_before_model]即将调用模型，带有{len(state['messages'])}条信息")
    logger.debug(f"[log_before_model]{type(state['messages'][-1]).__name__} | {state['messages'][-1].content.strip()}")
    return None

@dynamic_prompt     #每一次在生成提示词之前，调用此函数
def report_prompt_switch(request:ModelRequest):         #动态切换提示词
    #获取runtime的context中report，若获取不到则返回False
    is_report = request.runtime.context.get("report",False)
    if is_report:           #是报告场景，返回报告生成提示词内容
        return load_report_prompts()
    return load_system_prompts()