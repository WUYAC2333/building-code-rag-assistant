def build_prompt(docs, question):
    """构建问答Prompt - 核心逻辑完全不变"""
    context = ""
    for item in docs:
        context += (
            f"【规范名称：{item['spec_name']} "
            f"| 条文编号：{item['article_id']}】\n"
            f"{item['content']}\n\n"
        )

    prompt = f"""
你是一名建筑设计规范助手。
请严格依据以下规范条文回答问题，不允许编造。

{context}

问题：
{question}

要求：
1. 必须明确写出“规范名称 + 条文编号”
2. 回答中必须标注引用来源，例如：
   （依据《规范名称》第X.X.X条）
3. 若规范未明确说明，回答“规范中未明确规定”
"""
    return prompt