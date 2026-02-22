# rag/__init__.py
"""
RAG 模块：检索增强生成。
"""
# 导入核心函数和变量
from .embedding import get_embedding
from .retriever import retrieve
from .qa_chain import qa_chain
from .prompt_builder import build_prompt

# 明确对外暴露的接口
__all__ = ["get_embedding", "retrieve", "qa_chain", "build_prompt"]