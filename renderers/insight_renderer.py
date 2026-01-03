# renderers/insight_renderer.py

def render_daily_insight(data):
    """
    输入：AI 输出的 JSON dict
    输出：HTML 字符串（Daily Insight）
    """

    title = data.get("title", "Daily Insight")
    points = data.get("points", [])

    html = f"<h2>{title}</h2><ul>"

    for p in points:
        html += f"<li>{p}</li>"

    html += "</ul>"

    return html