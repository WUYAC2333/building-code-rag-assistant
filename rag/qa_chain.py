import dashscope
import os
from dashscope import Generation
from config import (
    GENERATION_MODEL,
    ANSWER_GENERATE_TEMPERATURE
)
from .retriever import retrieve
from .prompt_builder import build_prompt

# 初始化API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

def qa_chain(question):
    """RAG主流程：检索 → 构建Prompt → 生成回答"""
    # 1. 检索相关条文
    docs = retrieve(question)
    if not docs:
        return "未检索到相关条文", []
    
    # 2. 构建Prompt
    prompt = build_prompt(docs, question)
    
    # 3. 生成回答（和原代码一致）
    response = Generation.call(
        model=GENERATION_MODEL,
        prompt=prompt,
        temperature=ANSWER_GENERATE_TEMPERATURE
    )
    answer = response.output.text
    
    return answer, docs