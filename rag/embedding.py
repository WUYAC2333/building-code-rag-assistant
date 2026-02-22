import logging
import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import dashscope
from dashscope import TextEmbedding
from config import (
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    RETRY_MAX_ATTEMPTS,
    RETRY_WAIT_MULTIPLIER,
    RETRY_WAIT_MIN,
    RETRY_WAIT_MAX
)

# 初始化API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
if not dashscope.api_key:
    raise ValueError("API Key不能为空！")

# 日志
logger = logging.getLogger(__name__)

# 新增：嵌入缓存（和原代码一致）
embedding_cache = {}

# 保留原重试逻辑，补充缓存
@retry(
    stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),
    wait=wait_exponential(multiplier=RETRY_WAIT_MULTIPLIER, min=RETRY_WAIT_MIN, max=RETRY_WAIT_MAX),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: logger.warning(
        f"API调用失败，即将重试（第{retry_state.attempt_number}次）：{retry_state.outcome.exception()}"
    )
)
def get_embedding(text: str) -> list[float]:
    """生成文本向量（带重试+缓存机制）"""
    # 新增：缓存逻辑（和原代码一致）
    if text in embedding_cache:
        return embedding_cache[text]
    
    if not text or text.strip() == "":
        logger.warning("空文本，跳过生成向量")
        return []
    
    try:
        response = TextEmbedding.call(
            model=EMBEDDING_MODEL,
            input=text,
            result_format="float"
        )
        embedding = response.output["embeddings"][0]["embedding"]
        if len(embedding) != EMBEDDING_DIMENSION:
            logger.error(f"向量维度异常：{len(embedding)}，预期{EMBEDDING_DIMENSION}")
            return []
        
        # 新增：存入缓存
        embedding_cache[text] = embedding
        return embedding
    except Exception as e:
        logger.error(f"生成向量失败（文本：{text[:20]}...）：{e}")
        raise