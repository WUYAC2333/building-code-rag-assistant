import streamlit as st
from rag import qa_chain

# ========================= 页面UI（核心逻辑完全不变） =========================
st.title("📘 建筑规范智能问答系统")

question = st.text_input("请输入问题：")

if st.button("查询"):
    if not question:
        st.warning("请输入问题")
    else:
        with st.spinner("正在检索与生成回答..."):
            # 调用封装后的RAG主流程
            answer, docs = qa_chain(question)
            
            st.subheader("📌 回答")
            st.write(answer)

            st.subheader("📚 参考条文")
            for item in docs:
                st.write(
                    f"""
                    **📘 规范名称：** {item['spec_name']}  
                    **📌 条文编号：** {item['article_id']}  
                    **📊 相似度：** {item['similarity']:.2%}
                    """
                )