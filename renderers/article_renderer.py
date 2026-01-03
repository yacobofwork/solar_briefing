def render_article(data):
    """
    Render a single news article card in English.
    """

    title = data.get("title", "News")
    source = data.get("source", "Unknown")
    link = data.get("link", "")
    pub_date = data.get("pub_date", "")

    cn_summary = data.get("cn_summary", "")
    en_summary = data.get("en_summary", "")
    cn_insights = data.get("cn_insights", [])
    en_insights = data.get("en_insights", [])
    supply_chain = data.get("supply_chain", "")
    nigeria_impact = data.get("nigeria_impact", "")
    recommendation = data.get("recommendation", "")

    # Correct clickable link
    link_html = f'<a href="{link}" target="_blank">Read Original Article</a >' if link else ""

    html = f"""
    <div class="news-item">
        <h3>{title}</h3>

        <p><strong>Source:</strong> {source}</p>
        <p><strong>Published:</strong> {pub_date}</p>
        <p>{link_html}</p >

        <p><strong>Chinese Summary:</strong></p>
        <p>{cn_summary}</p >

        <p><strong>English Summary:</strong></p>
        <p>{en_summary}</p >

        <p><strong>Chinese Key Insights:</strong></p>
        <ul>
            {''.join(f'<li>{x}</li>' for x in cn_insights)}
        </ul>

        <p><strong>English Key Insights:</strong></p>
        <ul>
            {''.join(f'<li>{x}</li>' for x in en_insights)}
        </ul>

        <p><strong>Supply Chain Impact:</strong></p>
        <p>{supply_chain}</p>

        <p><strong>Impact on Nigeria Microgrid Projects:</strong></p>
        <p>{nigeria_impact}</p>

        <p><strong>Procurement Recommendation:</strong></p>
        <p>{recommendation}</p>
    </div>
    """

    return html