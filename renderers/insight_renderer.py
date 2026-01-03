


# 负责把 AI输出包装成 HTML
def render_daily_insight(html_fragment):
    return f"""
    <div class="daily-insight">
        {html_fragment}
    </div>
    """