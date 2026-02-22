# data_pipeline/__init__.py
"""
Data Pipeline 模块：数据清洗与拆分。
"""
# 导入核心函数和变量
from .clean_text import clean_text
from .chunker import chunker
from .metadata_builder import find_abnormal_unicode

# 明确对外暴露的接口
__all__ = ["clean_text", "chunker", "find_abnormal_unicode"]