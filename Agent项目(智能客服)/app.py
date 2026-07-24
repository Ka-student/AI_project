import streamlit as st
from agent.react_agent import ReactAgent
import time

st.title("机器人智能客服")
st.divider()

if "agent" not in st.session_state:
    st.session_state["agent"] = ReactAgent()

if "message" not in st.session_state:
    st.session_state["message"] = []

#输出历史记录
for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

#用户输入提示词
prompt = st.chat_input()

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role":"user","content":prompt})

    #流式输出后respinse_message才会有内容，即执行write_stream()后
    response_messages = []
    with st.spinner("智能客服思考中..."):
        res_stream = st.session_state["agent"].execute_stream(prompt)

        #一边缓存完整的流式输出，一边把流式片段逐个给前端实现打字机效果。
        #遍历 Agent 返回的每个事件块
        def capture(generator,cache_list):
            for chunk in generator:
                cache_list.append(chunk)    #把整个块原封不动存进缓存
                for c in chunk:
                    time.sleep(0.01)        #每次 10ms，制造打字机节奏
                    yield c                 #再把块里的字符逐个 yield 出去
        #st.write_stream()  一边后端产出文字，一边前端实时刷新
        st.chat_message("assistant").write_stream(capture(res_stream,response_messages))
        #只返回最后一条消息，真正需要的消息
        st.session_state["message"].append({"role":"assistant","content":response_messages[-1]})
        #刷新网页
        st.rerun()

