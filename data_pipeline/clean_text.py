import re
from config import CLEAN_INPUT_FILE, CLEAN_OUTPUT_FILE, CHAPTER_TITLES

def standardize_construction_code(txt_content):
    """
    标准化建筑规范TXT文本：
    1. 清理多余空格、空行（仅针对非表格内容）
    2. 识别条款/表格/注释，按模板重组
    3. 块间仅保留一行空行
    特别说明：表格内容（标题+表格体）完全保留原始格式，不做任何修改
    """
    # ========== 第一步：拆分文本为不同块（重点：识别表格块并保留原始格式） ==========
    lines = txt_content.split('\n')  # 不提前strip，保留表格原始格式
    blocks = []
    current_block = []
    in_table = False  # 标记是否在表格块中

    for line in lines:
        # 检测表格开始标记
        if line.strip().startswith('===== 表格：'):
            # 如果之前有非表格内容，先处理并加入blocks
            if current_block and not in_table:
                blocks.append(('normal', '\n'.join(current_block)))
                current_block = []
            in_table = True
            current_block.append(line)  # 保留表格行原始格式
        # 检测表格结束（遇到条款编号/注：/下一个表格开始，且当前在表格中）
        elif in_table and (
            re.match(r'^\s*\d+\.\d+(\.\d+[A-Z]?)?', line.strip()) or  # 条款编号
            line.strip().startswith('注：') or                        # 注释开头
            line.strip().startswith('===== 表格：')                  # 下一个表格
        ):
            # 表格块结束，加入blocks（类型为table，保留原始内容）
            blocks.append(('table', '\n'.join(current_block)))
            current_block = [line]
            in_table = False
        else:
            current_block.append(line)  # 继续收集当前块内容

    # 处理最后一个块
    if current_block:
        if in_table:
            blocks.append(('table', '\n'.join(current_block)))
        else:
            blocks.append(('normal', '\n'.join(current_block)))

    # ========== 第二步：分别处理不同类型的块 ==========
    processed_blocks = []
    for block_type, block_content in blocks:
        if block_type == 'table':
            # 表格块：完全保留原始格式，仅去除首尾空行（避免多余空行影响块间分隔）
            table_content = block_content.strip()
            processed_blocks.append(table_content)
        else:
            # 非表格块（条款/注释）：执行原有的标准化逻辑
            # 1. 基础清理
            content = block_content.replace('　', ' ')
            lines_normal = [line.strip() for line in content.split('\n')]
            lines_normal = [line for line in lines_normal if line]  # 过滤空行
            
            # 2. 合并连续行
            merged_lines = []
            for line in lines_normal:
                if not merged_lines:
                    merged_lines.append(line)
                else:
                    last_line = merged_lines[-1]
                    is_new_block = (
                        re.match(r'^\d+\.\d+(\.\d+[A-Z]?)?', line) or
                        line.startswith('注：')
                    )
                    if is_new_block:
                        merged_lines.append(line)
                    else:
                        merged_lines[-1] = last_line + ' ' + line
            
            # 3. 拆分回独立块（条款/注释）
            sub_blocks = []
            current_sub_block = None
            for line in merged_lines:
                if re.match(r'^\d+\.\d+(\.\d+[A-Z]?)?', line) or line.startswith('注：'):
                    if current_sub_block:
                        sub_blocks.append(current_sub_block)
                    current_sub_block = line
                else:
                    if current_sub_block:
                        current_sub_block += ' ' + line
            if current_sub_block:
                sub_blocks.append(current_sub_block)
            
            # 4. 清理多余空格并加入结果
            for sub_block in sub_blocks:
                cleaned_sub_block = re.sub(r'\s+', ' ', sub_block).strip()
                processed_blocks.append(cleaned_sub_block)

    # ========== 第三步：块间加一行空行分隔 ==========
    final_content = '\n\n'.join(processed_blocks)
    return final_content

def normalize_table_spacing(text):
    """统一表格间距，清理多余空行"""
    # 统一换行符
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 匹配整个表格块
    table_pattern = r"\n*===== 表格：.*?=====\n(?:.*?\n)*?(?=\n\S|\Z)"

    def fix_spacing(match):
        table_block = match.group(0)

        # 去掉前后所有空行
        table_block = table_block.strip("\n")

        # 强制前后各加一个空行
        return "\n\n" + table_block + "\n\n"

    text = re.sub(table_pattern, fix_spacing, text, flags=re.S)

    # 清理连续 3 行以上空行 → 统一成 2 行（正文之间最多允许1空行）
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip() + "\n"

def add_chapter_titles(text, chapter_titles=None):
    """
    为文本添加章标题：
    - 章标题前后各 1 行空行
    - 文件开头不允许有空行
    - 文件结尾不允许有空行
    """
    # 使用配置中的章标题（默认）
    if chapter_titles is None:
        chapter_titles = CHAPTER_TITLES

    lines = text.split('\n')
    new_lines = []
    current_chapter = None

    for line in lines:
        stripped_line = line.strip()

        # 判断是否为节标题（如 5.1 xxx、5.1.1 xxx）
        if stripped_line and '.' in stripped_line:
            chapter_num = stripped_line.split('.')[0]

            if chapter_num.isdigit() and chapter_num in chapter_titles:
                if chapter_num != current_chapter:
                    current_chapter = chapter_num

                    # -------- 控制标题前空行 --------
                    # 删除 new_lines 末尾所有空行
                    while new_lines and new_lines[-1].strip() == '':
                        new_lines.pop()

                    # 如果不是文件开头，添加一个空行
                    if new_lines:
                        new_lines.append('')

                    # 添加章标题
                    new_lines.append(chapter_titles[chapter_num])

                    # 标题后加一个空行
                    new_lines.append('')

        new_lines.append(line)

    # ---------- 全局空行规范 ----------
    result = '\n'.join(new_lines)

    # 压缩连续 3 行以上空行为 2 行
    result = re.sub(r'\n{3,}', '\n\n', result)

    # 删除文件开头空行
    result = result.lstrip('\n')

    # 删除文件结尾空行
    result = result.rstrip('\n')

    return result

# 集成以上函数
def clean_text():
    # 读取原始文件
    with open(CLEAN_INPUT_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        raw_content = f.read()

    # 标准化处理
    standardized_content = standardize_construction_code(raw_content)
    new_content = normalize_table_spacing(standardized_content)
    final_text = add_chapter_titles(new_content)

    # 保存结果
    with open(CLEAN_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_text)

    print(f"文本清洗完成！输出文件：{CLEAN_OUTPUT_FILE}")

    return