import os
import json
import re
from config import CHUNKS_OUTPUT_JSON, CHUNKS_CLEANED_JSON

def find_abnormal_unicode(json_file_path=None, raw_data_path=None):
    """
    定位并清理JSON文件中的异常unicode字符
    :param json_file_path: 清理后文件的保存路径
    :param raw_data_path: 原始待清理数据的文件路径
    :return: 清理后的chunk列表
    """
    # 使用配置中的默认路径
    if json_file_path is None:
        json_file_path = CHUNKS_CLEANED_JSON
    if raw_data_path is None:
        raw_data_path = CHUNKS_OUTPUT_JSON

    # 优化正则：修复单双引号转义问题，补充常见符号
    abnormal_pattern = r'[^\u4e00-\u9fa5a-zA-Z0-9\s。，；：！？"（）【】《》、·%@#￥&*+-=<>|—～_\.\-]'
    abnormal_re = re.compile(abnormal_pattern)

    # ========================
    # 步骤1：读取原始待清理数据（增强调试）
    # ========================
    print(f"\n🔍 开始处理：")
    print(f"   原始文件路径: {raw_data_path}")
    print(f"   输出文件路径: {json_file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(raw_data_path):
        error_msg = f"❌ 原始数据文件 {raw_data_path} 不存在，请检查路径！"
        print(error_msg)
        # 即使文件不存在，也写入空列表（避免文件缺失）
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return []
    
    # 读取文件（增强异常捕获）
    try:
        with open(raw_data_path, 'r', encoding='utf-8') as f:
            raw_chunks = json.load(f)
        
        # 检查数据类型
        if not isinstance(raw_chunks, list):
            error_msg = f"❌ 原始数据格式错误，必须是列表类型！当前类型：{type(raw_chunks)}"
            print(error_msg)
            # 尝试转换为列表（容错处理）
            raw_chunks = [raw_chunks]
            print(f"⚠️  已自动将数据转换为列表，继续处理...")
        
        print(f"✅ 成功读取原始数据，共 {len(raw_chunks)} 个chunk")
        
        # 检查原始数据是否为空
        if len(raw_chunks) == 0:
            print(f"⚠️  原始数据文件是空列表，清理后也会是空列表")
            
    except json.JSONDecodeError as e:
        error_msg = f"❌ 读取原始数据失败：JSON格式错误 - {e}"
        print(error_msg)
        return []
    except UnicodeDecodeError as e:
        error_msg = f"❌ 读取原始数据失败：文件编码错误 - {e}"
        print(error_msg)
        return []
    except Exception as e:
        error_msg = f"❌ 读取原始数据失败：{e}"
        print(error_msg)
        return []

    # ========================
    # 步骤2：定位并清理异常字符
    # ========================
    cleaned_chunks = []  # 存储清理后的数据
    ablist = []          # 存储所有异常字符
    print("\n=== 异常unicode字符定位结果 ===")
    
    for idx, chunk in enumerate(raw_chunks):
        # 容错：处理chunk不是字典的情况
        if not isinstance(chunk, dict):
            print(f"\n⚠️  第{idx+1}个chunk不是字典类型，跳过处理：{chunk}")
            continue
            
        chunk_id = chunk.get("chunk_id", f"第{idx+1}个chunk")
        content = str(chunk.get("content", ""))  # 确保是字符串
        
        # 查找异常字符
        abnormal_chars = abnormal_re.findall(content)
        ablist.extend(abnormal_chars)  # 修复：用extend而不是append，避免嵌套列表
        
        if abnormal_chars:
            # 去重并显示编码
            unique_chars = list(set(abnormal_chars))
            char_codes = [f"{c} (\\u{ord(c):04x})" for c in unique_chars]
            print(f"\n{chunk_id} 包含异常字符：{char_codes}")
            print(f"清理前内容片段：{content[:200]}...")
            
            # 清理异常字符（核心：移除所有匹配的异常字符）
            cleaned_content = abnormal_re.sub("", content)
            print(f"清理后内容片段：{cleaned_content[:200]}...")
        else:
            cleaned_content = content  # 无异常字符，直接保留
        
        # 保存清理后的chunk
        cleaned_chunks.append({
            "chunk_id": chunk_id,
            "content": cleaned_content,
            "original_content": content  # 可选：保留原始内容用于对比
        })

    # ========================
    # 步骤3：将清理后的数据写入目标文件
    # ========================
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(json_file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_chunks, f, ensure_ascii=False, indent=4)
        
        print(f"\n✅ 清理完成！结果已保存到 {json_file_path}")
        print(f"📊 处理统计：")
        print(f"   - 原始chunk数量：{len(raw_chunks)}")
        print(f"   - 清理后chunk数量：{len(cleaned_chunks)}")
        print(f"   - 发现异常字符总数：{len(ablist)}")
        print(f"   - 唯一异常字符：{list(set(ablist)) if ablist else '无'}")
        
    except PermissionError:
        print(f"❌ 写入文件失败：没有写入 {json_file_path} 的权限")
        return []
    except Exception as e:
        print(f"❌ 写入清理后文件失败：{e}")
        return []

    return cleaned_chunks