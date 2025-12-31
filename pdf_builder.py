

from weasyprint import HTML

def html_to_pdf(html_content, output_path):
    """将 HTML 转成 PDF"""
    HTML(string=html_content).write_pdf(output_path)




def build_pdf_html(date, price_insight, price_list, news_grouped):
    """生成 PDF 用的 HTML 模板"""

    # 1) 生成价格表 rows
    price_rows = ""
    for p in price_list:
        price_rows += f"""
        <tr>
            <td>{p['item']}</td>
            <td>{p['price']}</td>
            <td>{p['change']}</td>
            <td>{p['source']}</td>
        </tr>
        """

    # 2) 生成新闻 sections
    news_sections = ""
    for category, items in news_grouped.items():
        news_sections += f"<h3>{category}</h3>"
        for item in items:
            news_sections += f"""
            <div class="news-card">
                <div class="news-title">{item['title']}</div>
                <a class="news-link" href=" 'link']">Original Link</a >
                <div>{item['insight']}</div>
            </div>
            """

    # 3) 插入到模板
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <title>China PV & BESS Daily Intelligence Report</title>

    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            color: #333;
            line-height: 1.6;
        }}

        h1 {{
            text-align: center;
            color: #2A4E8A;
            margin-bottom: 10px;
        }}

        h2 {{
            color: #1A73E8;
            border-bottom: 2px solid #1A73E8;
            padding-bottom: 4px;
            margin-top: 40px;
        }}

        h3 {{
            color: #2A4E8A;
            margin-top: 25px;
        }}

        .date-line {{
            text-align: center;
            font-size: 14px;
            color: #666;
            margin-bottom: 30px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            font-size: 14px;
        }}

        th {{
            background-color: #f2f2f2;
            border: 1px solid #ccc;
            padding: 8px;
            text-align: left;
        }}

        td {{
            border: 1px solid #ccc;
            padding: 8px;
        }}

        .news-card {{
            border: 1px solid #ddd;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 16px;
            background-color: #fafafa;
        }}

        .news-title {{
            font-size: 16px;
            font-weight: bold;
            color: #2A4E8A;
        }}

        .news-link {{
            font-size: 13px;
            color: #1A73E8;
        }}

        .footer {{
            margin-top: 50px;
            text-align: center;
            font-size: 12px;
            color: #777;
        }}
    </style>
    </head>

    <body>

    <h1>China PV & BESS Daily Intelligence Report</h1>
    <div class="date-line">Date: {date}</div>

    <h2>📌 Price Impact Analysis</h2>
    <div>{price_insight}</div>

    <h2>📊 Supply Chain Price Trends</h2>
    <table>
        <thead>
            <tr>
                <th>Item</th>
                <th>Price</th>
                <th>Change</th>
                <th>Source</th>
            </tr>
        </thead>
        <tbody>
            {price_rows}
        </tbody>
    </table>

    <h2>📰 Industry News</h2>
    {news_sections}

    <div class="footer">
        Generated automatically by the China PV & BESS Intelligence System
    </div>

    </body>
    </html>
    """

    return html