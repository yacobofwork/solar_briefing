


# 负责把 AI输出包装成 HTML
def render_article(html_fragment):
    return f"""
    <div class="news-item">
        {html_fragment}
    </div>
    """

