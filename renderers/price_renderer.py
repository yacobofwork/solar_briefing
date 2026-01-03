# renderers/price_renderer.py

def render_price_insight(data):
    """
    输入：AI 输出的 JSON dict
    输出：HTML 字符串（价格影响分析）
    """

    title = data.get("title", "Price Impact Analysis")
    sections = data.get("sections", [])

    html = f"<h2>{title}</h2>"

    for sec in sections:
        subtitle = sec.get("subtitle", "")
        content = sec.get("content", "")

        html += f"""
        <h3>{subtitle}</h3>
        <p>{content}</p >
        """

    return html