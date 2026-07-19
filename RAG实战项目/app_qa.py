import time
import streamlit as st
from rag import RagService
import config_data as config
#标题
st.title("智能客服")
st.divider()                #分隔符

if "message" not in st.session_state:
    st.session_state["message"] = [{"role": "assistant", "content": "你好，有什么可以帮助你？"}]
#创建RAG对象
if "rag" not in st.session_state:
    st.session_state["rag"] = RagService()

for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

#在页面最下方提供用户输入栏
prompt = st.chat_input()
if prompt:
    #在页面输出用户的提问
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role":"user","content":prompt})

    with st.spinner("AI思考中..."):
        time.sleep(1)

        res_stream = st.session_state["rag"].chain.stream({"input":prompt},config.session_config)

        #本质就是一个 tee 分叉——数据流一份给 UI 渲染，一份给内存收集。
        def capture(generator,cache_list):
            for chunk in generator:
                cache_list.append(chunk)
                yield chunk
        ai_res = []
        #流式输出
        st.chat_message("assistant").write_stream(capture(res_stream,ai_res))
        st.session_state["message"].append({"role": "assistant", "content": "".join(ai_res)})



