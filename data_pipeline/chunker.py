import json
import re
import os
from collections import Counter
from config import MAX_CHUNK_LENGTH, SPEC_FILES, CHUNKS_OUTPUT_JSON

def split_text_to_chunks(text, max_length=None):
    """
    将文本按最大长度切分，尽量按句子/标点分割（避免生硬截断）
    Args:
        text: 待切分的文本
        max_length: 每个chunk的最大字符数（默认使用配置中的值）
    Returns:
        list: 切分后的文本片段列表
    """
    # 使用配置中的默认值
    if max_length is None:
        max_length = MAX_CHUNK_LENGTH
    
    chunks = []
    # 先去除多余换行/空格，统一格式
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 文本长度未超限制，直接返回
    if len(text) <= max_length:
        return [text]
    
    # 按标点（。；！？）分割句子，优先整句切分
    sentences = re.split(r'(。|；|！|？)', text)
    # 重组句子（把分割符拼回去）
    sentences = [s1 + s2 for s1, s2 in zip(sentences[0::2], sentences[1::2])]
    if len(sentences) == 0:
        sentences = [text]
    
    # 逐句拼接，直到接近max_length
    current_chunk = ""
    for sentence in sentences:
        # 如果当前chunk+新句子超过限制，先保存当前chunk
        if len(current_chunk + sentence) > max_length and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += sentence
    
    # 添加最后一个chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # 极端情况（单句超过max_length字）：强制按字符截断
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_length:
            final_chunks.append(chunk)
        else:
            for i in range(0, len(chunk), max_length):
                final_chunks.append(chunk[i:i+max_length])
    
    return final_chunks

def parse_construction_code(file_path):
    """
    解析单份规范txt文件，生成条文列表
    """
    articles_list = []
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按空行分割段落，过滤空段落和纯空白字符的段落
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    # 用于追踪当前上下文
    current_article_id = None  # 当前条款ID
    current_table_id = None    # 当前表格ID
    note_counter = 0           # 注释计数器
    
    # 正则表达式模式（仅匹配三位小数的条款ID）
    article_pattern = r'^(\d+\.\d+\.\d+[A-Z]?)'  
    table_pattern = r'^===== 表格：表([\d\.]+)'      
    note_pattern = r'^注：'                          
    
    for para in paragraphs:
        # 1. 识别条款（仅三位小数的编号）
        article_match = re.match(article_pattern, para)
        if article_match:
            current_article_id = article_match.group(1)
            # 添加条款到列表
            articles_list.append({
                'id': current_article_id,
                'type': 'article',
                'content': para
            })
            # 重置表格和注释状态
            current_table_id = None
            note_counter = 0
            continue
        
        # 2. 识别表格
        table_match = re.match(table_pattern, para)
        if table_match:
            table_num = table_match.group(1)
            current_table_id = f'table_{table_num}'
            # 添加表格到列表
            articles_list.append({
                'id': current_table_id,
                'type': 'table',
                'related_to': table_num,
                'content': para
            })
            # 重置注释计数器
            note_counter = 0
            continue
        
        # 3. 识别表格注释
        if re.match(note_pattern, para) and current_table_id:
            note_id = f'note_{current_table_id.split("_")[1]}'
            # 添加注释到列表
            articles_list.append({
                'id': note_id,
                'type': 'note',
                'related_to': current_table_id,
                'content': para
            })
            continue
    
    return articles_list

def articles_to_chunks(articles_list, spec_name, spec_abbr, max_chunk_length=None):
    """
    将单份规范的条文列表转换为chunk列表（新增规范名字段）
    """
    if max_chunk_length is None:
        max_chunk_length = MAX_CHUNK_LENGTH
    
    chunks_list = []
    
    for item in articles_list:
        # 提取基础信息
        original_id = item['id']
        content = item['content']
        item_type = item['type']
        
        # 提取章节号（从article_id/related_to中解析）
        chapter = ""
        if item_type == "article":
            chapter = original_id.split('.')[0] if '.' in original_id else ""
        elif item_type in ["table", "note"]:
            related_num = item['related_to']
            chapter = related_num.split('.')[0] if '.' in related_num else ""
        
        # 切分文本为chunks
        content_chunks = split_text_to_chunks(content, max_chunk_length)
        
        # 为每个chunk生成完整信息
        for idx, chunk_content in enumerate(content_chunks, 1):
            # 生成chunk_id（规范缩写_原ID_序号），避免不同规范同ID冲突
            chunk_id = f"{spec_abbr}_{original_id}_{idx}"
            
            # 构建chunk字典（新增spec_name字段）
            chunk = {
                "chunk_id": chunk_id,          # 全局唯一ID
                "content": chunk_content,      # 切分后的内容
                "article_id": original_id,     # 关联原条文ID
                "type": item_type,             # 内容类型（article/table/note）
                "chapter": chapter,            # 章节号
                "spec_name": spec_name,        # 规范全称
                "spec_abbr": spec_abbr         # 规范缩写（便于检索）
            }
            
            # 表格/注释补充related_to字段
            if item_type in ["table", "note"] and "related_to" in item:
                chunk["related_to"] = item["related_to"]
            
            chunks_list.append(chunk)
    
    return chunks_list

def batch_process_specs(spec_files=None, max_chunk_length=None, output_file=None):
    """
    批量处理多份规范文件，生成统一的chunk列表并导出JSON
    """
    # 使用配置中的默认值
    if spec_files is None:
        spec_files = SPEC_FILES
    if max_chunk_length is None:
        max_chunk_length = MAX_CHUNK_LENGTH
    if output_file is None:
        output_file = CHUNKS_OUTPUT_JSON
    
    # 存储所有规范的chunk
    all_chunks = []
    
    # 遍历处理每份规范
    for spec_name, (file_path, spec_abbr) in spec_files.items():
        print(f"正在处理：{spec_name} | 文件：{file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"警告：文件 {file_path} 不存在，跳过该规范")
            continue
        
        # 1. 解析单份规范生成条文列表
        articles_list = parse_construction_code(file_path)
        print(f"  - 解析出 {len(articles_list)} 条条文")
        
        # 2. 转换为chunk列表
        spec_chunks = articles_to_chunks(articles_list, spec_name, spec_abbr, max_chunk_length)
        print(f"  - 生成 {len(spec_chunks)} 个chunk")
        
        # 3. 添加到总列表
        all_chunks.extend(spec_chunks)
    
    # 4. 导出所有chunk到JSON文件
    os.makedirs(os.path.dirname(output_file), exist_ok=True)  # 确保目录存在
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=4)
    
    print(f"\n批量处理完成！")
    print(f"总计生成 {len(all_chunks)} 个chunk")
    print(f"文件已导出到：{output_file}")
    
    return all_chunks

def validate_embedding_chunks(json_file_path=None, max_content_length=None):
    """
    校验embedding用的chunk JSON文件，输出详细校验报告
    """
    # 使用配置中的默认值
    if json_file_path is None:
        json_file_path = CHUNKS_OUTPUT_JSON
    if max_content_length is None:
        max_content_length = MAX_CHUNK_LENGTH
    
    # 初始化校验报告
    report = {
        "total_chunks": 0,          # 总chunk数
        "valid_chunks": 0,          # 有效chunk数
        "error_count": 0,           # 错误总数
        "warning_count": 0,         # 警告总数
        "errors": [],               # 错误详情（严重，需修复）
        "warnings": [],             # 警告详情（轻微，可优化）
        "duplicate_chunk_ids": [],  # 重复的chunk_id
        "empty_content_chunks": [], # 空内容的chunk
        "field_check": {            # 字段完整性统计
            "missing_chunk_id": 0,
            "missing_content": 0,
            "missing_article_id": 0,
            "missing_type": 0,
            "missing_chapter": 0,
            "missing_spec_name": 0,
            "missing_spec_abbr": 0,
            "table_note_missing_related_to": 0,
            "article_has_related_to": 0
        }
    }

    try:
        # 1. 读取并解析JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            try:
                chunks = json.load(f)
            except json.JSONDecodeError as e:
                report["errors"].append(f"JSON文件解析失败：{str(e)}")
                report["error_count"] += 1
                return report

        # 检查是否为数组格式
        if not isinstance(chunks, list):
            report["errors"].append(f"JSON文件内容不是数组格式，当前类型：{type(chunks)}")
            report["error_count"] += 1
            return report

        report["total_chunks"] = len(chunks)
        if report["total_chunks"] == 0:
            report["errors"].append("JSON文件中无任何chunk数据")
            report["error_count"] += 1
            return report

        # 2. 提取所有chunk_id，检查重复
        chunk_ids = [chunk.get("chunk_id", "") for chunk in chunks]
        duplicate_ids = [cid for cid, count in Counter(chunk_ids).items() if count > 1 and cid]
        if duplicate_ids:
            report["duplicate_chunk_ids"] = duplicate_ids
            report["errors"].append(f"发现重复的chunk_id：{', '.join(duplicate_ids)}")
            report["error_count"] += len(duplicate_ids)

        # 3. 遍历每个chunk进行详细校验
        for idx, chunk in enumerate(chunks):
            chunk_id = chunk.get("chunk_id", f"第{idx+1}个chunk")
            is_valid = True

            # ========== 字段完整性校验（必选字段） ==========
            # 检查chunk_id
            if not chunk.get("chunk_id") or not isinstance(chunk["chunk_id"], str):
                report["field_check"]["missing_chunk_id"] += 1
                report["errors"].append(f"{chunk_id}：缺失chunk_id字段或字段类型非字符串")
                report["error_count"] += 1
                is_valid = False

            # 检查content
            content = chunk.get("content", "").strip()
            if not content:
                report["field_check"]["missing_content"] += 1
                report["empty_content_chunks"].append(chunk_id)
                report["errors"].append(f"{chunk_id}：content字段为空或纯空白字符")
                report["error_count"] += 1
                is_valid = False
            else:
                # 检查content长度是否超限
                if len(content) > max_content_length:
                    report["warnings"].append(f"{chunk_id}：content长度({len(content)})超过设定阈值({max_content_length})")
                    report["warning_count"] += 1

                # 检查特殊字符/乱码（简单检测非中文字符+数字+标点的异常字符）
                abnormal_chars = re.findall(r'[^\u4e00-\u9fa50-9a-zA-Z\s。，；：！？""''（）【】《》、·%@#￥&*+-=<>]', content)
                if abnormal_chars and len(set(abnormal_chars)) > 3:  # 避免少量特殊符号误判
                    report["warnings"].append(f"{chunk_id}：content包含异常特殊字符，可能影响embedding")
                    report["warning_count"] += 1

            # 检查其他必选字段
            required_fields = [
                ("article_id", "missing_article_id"),
                ("type", "missing_type"),
                ("chapter", "missing_chapter"),
                ("spec_name", "missing_spec_name"),
                ("spec_abbr", "missing_spec_abbr")
            ]
            for field, key in required_fields:
                if not chunk.get(field) or not isinstance(chunk[field], str):
                    report["field_check"][key] += 1
                    report["errors"].append(f"{chunk_id}：缺失{field}字段或字段类型非字符串")
                    report["error_count"] += 1
                    is_valid = False

            # ========== 类型相关字段校验 ==========
            chunk_type = chunk.get("type", "")
            has_related_to = "related_to" in chunk

            # 1. table/note类型必须有related_to
            if chunk_type in ["table", "note"] and not has_related_to:
                report["field_check"]["table_note_missing_related_to"] += 1
                report["errors"].append(f"{chunk_id}：类型为{chunk_type}，但缺失related_to字段")
                report["error_count"] += 1
                is_valid = False

            # 2. article类型不能有related_to
            if chunk_type == "article" and has_related_to:
                report["field_check"]["article_has_related_to"] += 1
                report["warnings"].append(f"{chunk_id}：类型为article，但包含related_to字段（建议移除）")
                report["warning_count"] += 1

            # ========== 统计有效chunk ==========
            if is_valid:
                report["valid_chunks"] += 1

        # 4. 生成最终报告摘要
        report["summary"] = (
            f"校验完成 | 总chunk数：{report['total_chunks']} | 有效chunk数：{report['valid_chunks']} | "
            f"错误数：{report['error_count']} | 警告数：{report['warning_count']}"
        )

    except FileNotFoundError:
        report["errors"].append(f"未找到JSON文件：{json_file_path}")
        report["error_count"] += 1
    except Exception as e:
        report["errors"].append(f"校验过程中发生未知错误：{str(e)}")
        report["error_count"] += 1

    return report

def print_validate_report(report):
    """格式化打印校验报告，便于阅读"""
    print("="*80)
    print("              Chunk JSON文件校验报告（Embedding前校验）")
    print("="*80)
    print(f"\n【总览】")
    print(f"  总chunk数：{report['total_chunks']}")
    print(f"  有效chunk数：{report['valid_chunks']}")
    print(f"  错误总数：{report['error_count']}")
    print(f"  警告总数：{report['warning_count']}")

    if report["errors"]:
        print(f"\n【错误详情】（需修复后再进行embedding）")
        for i, error in enumerate(report["errors"], 1):
            print(f"  {i}. {error}")

    if report["warnings"]:
        print(f"\n【警告详情】（可优化，不影响基础embedding）")
        for i, warning in enumerate(report["warnings"], 1):
            print(f"  {i}. {warning}")

    if report["duplicate_chunk_ids"]:
        print(f"\n【重复的chunk_id】")
        print(f"  共{len(report['duplicate_chunk_ids'])}个重复ID：{', '.join(report['duplicate_chunk_ids'])}")

    if report["empty_content_chunks"]:
        print(f"\n【空内容的chunk】")
        print(f"  共{len(report['empty_content_chunks'])}个空内容chunk：{', '.join(report['empty_content_chunks'])}")

    print(f"\n【字段完整性统计】")
    field_check = report["field_check"]
    print(f"  缺失chunk_id：{field_check['missing_chunk_id']}")
    print(f"  缺失content：{field_check['missing_content']}")
    print(f"  缺失article_id：{field_check['missing_article_id']}")
    print(f"  缺失type：{field_check['missing_type']}")
    print(f"  缺失chapter：{field_check['missing_chapter']}")
    print(f"  缺失spec_name：{field_check['missing_spec_name']}")
    print(f"  缺失spec_abbr：{field_check['missing_spec_abbr']}")
    print(f"  table/note缺失related_to：{field_check['table_note_missing_related_to']}")
    print(f"  article包含related_to：{field_check['article_has_related_to']}")

    print("\n" + "="*80)

def chunker():
    # 1. 批量处理所有规范
    all_chunks = batch_process_specs()

    # 打印前3个chunk示例
    print("\n前3个chunk示例（含规范名字段）：")
    for i, chunk in enumerate(all_chunks[:3]):
        print(f"\nChunk {i+1}:")
        for k, v in chunk.items():
            print(f"  {k}: {v}")

    # 2. 执行校验
    validate_report = validate_embedding_chunks()
    print_validate_report(validate_report)

    return