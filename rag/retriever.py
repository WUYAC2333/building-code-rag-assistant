import dashscope
import os
from dashscope import Generation
import chromadb
from config import (
    CHROMA_DB_PATH,
    CHROMA_COLLECTION_NAME,
    GENERATION_MODEL,
    QUERY_EXPAND_TEMPERATURE,
    RETRIEVE_N_RESULTS,
    RETRIEVE_TOP_K,
    SIMILARITY_THRESHOLD,
    CHROMA_COLLECTION_METADATA
)
from rag.embedding import get_embedding

# 初始化API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

# 初始化Chroma客户端（和原代码一致）
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection(
    name=CHROMA_COLLECTION_NAME,
    embedding_function=None,
    metadata=CHROMA_COLLECTION_METADATA
)

def expand_query(question):
    """查询扩展（LLM自动生成关键词）- 核心逻辑不变"""
    prompt = f"""
请为以下建筑规范问题生成5个用于语义检索的关键词，
只返回关键词，用空格分隔，不要解释。

问题：
{question}
"""

    response = Generation.call(
        model=GENERATION_MODEL,  # 替换为配置中的模型名
        prompt=prompt,
        temperature=QUERY_EXPAND_TEMPERATURE  # 替换为配置中的温度
    )

    keywords = response.output.text.strip()
    return question + " " + keywords

def retrieve(question):
    """检索相关条文 - 核心逻辑不变，仅替换硬编码参数"""
    expanded_query = expand_query(question)
    query_embedding = get_embedding(expanded_query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=RETRIEVE_N_RESULTS,  # 替换为配置中的初始检索条数
        include=["documents", "metadatas", "distances"]
    )

    structured = []
    for doc, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        # 相似度计算（和原代码一致）
        similarity = 1 - distance if distance <= 1 else 0
        # 替换阈值为配置中的值
        if similarity < SIMILARITY_THRESHOLD:
            continue
        structured.append({
            "similarity": similarity,
            "article_id": metadata.get("article_id"),
            "spec_name": metadata.get("spec_name"),
            "spec_abbr": metadata.get("spec_abbr"),
            "content": doc
        })

    # 排序（和原代码一致）
    structured.sort(key=lambda x: x["similarity"], reverse=True)
    # 替换返回条数为配置中的值
    return structured[:RETRIEVE_TOP_K]