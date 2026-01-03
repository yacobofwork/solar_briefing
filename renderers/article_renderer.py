# renderers/article_renderer.py

def render_article(data):
    """
    输入：AI 输出的 JSON dict
    输出：HTML 字符串（新闻卡片）
    """

    title = data.get("title", "News")
    cn_summary = data.get("cn_summary", "")
    en_summary = data.get("en_summary", "")
    cn_insights = data.get("cn_insights", [])
    en_insights = data.get("en_insights", [])
    supply_chain = data.get("supply_chain", "")
    nigeria_impact = data.get("nigeria_impact", "")
    recommendation = data.get("recommendation", "")

    html = f"""
    <div class="news-item">
        <h3>{title}</h3>

        <p><strong>中文摘要：</strong></p >
        <p>{cn_summary}</p >

        <p><strong>English Summary:</strong></p >
        <p>{en_summary}</p >

        <p><strong>中文核心洞察：</strong></p >
        <ul>
            {''.join(f'<li>{x}</li>' for x in cn_insights)}
        </ul>

        <p><strong>English Key Insights:</strong></p >
        <ul>
            {''.join(f'<li>{x}</li>' for x in en_insights)}
        </ul>

        <p><strong>Supply Chain Impact:</strong></p >
        <p>{supply_chain}</p >

        <p><strong>Impact on Nigeria Microgrid Projects:</strong></p >
        <p>{nigeria_impact}</p >

        <p><strong>Procurement Recommendation:</strong></p >
        <p>{recommendation}</p >
    </div>
    """

    return html