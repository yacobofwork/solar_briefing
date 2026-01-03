

# 负责把 AI输出包装成 HTML
def render_price_insight(html_fragment):
    return f"""
    <div class="price-insight">
        {html_fragment}
    </div>
    """