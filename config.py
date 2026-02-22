import os
import chromadb
from chromadb.config import Settings

# ========================= 路径配置 =========================
# 项目根路径（自动获取，避免绝对路径）
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 原始/处理后数据路径
RAW_DOCS_PATH = os.path.join("data", "raw_docs")
PROCESSED_DOCS_PATH = os.path.join("data", "processed")
CHUNKS_JSON_PATH = os.path.join("data", "chunks.json")

# 日志/失败文件路径
VECTOR_DB_LOG_PATH = "vector_db_build.log"
FAILED_CHUNKS_PATH = "failed_chunks.json"

# ========================= 数据流水线配置 =========================
# 文本清洗配置
CHAPTER_TITLES = {
    "2": "===== 第2章 基本规定 =====",
    "3": "===== 第3章 宿舍 =====",
    "4": "===== 第4章 旅馆 ====="
}  # 章标题映射（可按不同规范扩展）

# 文本切分配置
MAX_CHUNK_LENGTH = 400  # 每个chunk最大字符数
# CHUNKS_OUTPUT_JSON = os.path.join(PROJECT_ROOT, "data", "chunks.json")  # 切分后输出文件
# CHUNKS_CLEANED_JSON = os.path.join(PROJECT_ROOT, "data", "chunks_cleaned.json")  # 清洗后chunk文件
CHUNKS_JSON_PATH = os.path.join(PROJECT_ROOT, "data", "chunks.json")
CHROMA_DB_PATH = os.path.join(PROJECT_ROOT, "vector_store", "chroma_db_new")  # 用新目录名
VECTOR_DB_LOG_PATH = os.path.join(PROJECT_ROOT, "vector_db.log")
FAILED_CHUNKS_PATH = os.path.join(PROJECT_ROOT, "failed_chunks.json")

# 批量处理规范文件配置（替换原硬编码路径）
SPEC_FILES = {
    "GB50016_2014_建筑设计防火规范": (
        os.path.join(PROJECT_ROOT, "data", "processed", "GB50016_2014_建筑设计防火规范.txt"), 
        "jzsj"
    ),
    "GB50352_2019_民用建筑设计统一标准": (
        os.path.join(PROJECT_ROOT, "data", "processed", "GB50352_2019_民用建筑设计统一标准.txt"), 
        "myjz"
    ),
    "GB50067_2014_汽车库、修车库、停车场设计防火规范": (
        os.path.join(PROJECT_ROOT, "data", "processed", "GB50067_2014_汽车库、修车库、停车场设计防火规范.txt"), 
        "qck"
    ),
    "GB50038_2025_住宅项目规范": (
        os.path.join(PROJECT_ROOT, "data", "processed", "GB50038_2025_住宅项目规范.txt"), 
        "zzxm"
    ),
    "GB50025_2022_宿舍、旅馆建筑项目规范": (
        os.path.join(PROJECT_ROOT, "data", "processed", "GB50025_2022_宿舍、旅馆建筑项目规范.txt"), 
        "sslg"
    )
}

# 清洗示例文件路径（替换原硬编码绝对路径）
CLEAN_INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "raw_docs", "GB50016_2014_建筑设计防火规范.txt")
CLEAN_OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "clean_text_example_GB50016_2014_建筑设计防火规范.txt")

# ========================= API & 模型配置 =========================
EMBEDDING_MODEL = "text-embedding-v2"  # 嵌入模型
GENERATION_MODEL = "qwen-turbo"  # 生成式模型
EMBEDDING_DIMENSION = 1536  # 向量维度

# ========================= Chroma配置 =========================
CHROMA_COLLECTION_NAME = "chroma_collection_name"
CHROMA_SETTINGS = Settings(
    persist_directory=CHROMA_DB_PATH,  # 和CHROMA_DB_PATH完全一致
    anonymized_telemetry=False,
    allow_reset=True
)
CHROMA_COLLECTION_METADATA = {"hnsw:space": "cosine"}

# ========================= 批量处理配置 =========================
BATCH_SIZE = 100
RETRY_MAX_ATTEMPTS = 3
RETRY_WAIT_MULTIPLIER = 1
RETRY_WAIT_MIN = 2
RETRY_WAIT_MAX = 10

# ========================= RAG配置 =========================
QUERY_EXPAND_TEMPERATURE = 0.3  # 查询扩展温度
ANSWER_GENERATE_TEMPERATURE = 0.2  # 回答生成温度
RETRIEVE_N_RESULTS = 5  # 初始检索条数
RETRIEVE_TOP_K = 3  # 最终返回条数
SIMILARITY_THRESHOLD = 0.6  # 相似度阈值