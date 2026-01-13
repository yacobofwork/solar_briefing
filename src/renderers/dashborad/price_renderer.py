
def render_price_insight(data):
    sections = data.get("sections", [])
    html = ""

    for sec in sections:
        subtitle = sec.get("subtitle", "").strip()
        content = sec.get("content", "").strip()

        if not subtitle and not content:
            continue

        html += f"""
        <h3>{subtitle}</h3>
        <p>{content}</p>
        """

    return html