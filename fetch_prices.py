import requests
from bs4 import BeautifulSoup

def fetch_price_table(url, selector, source):
    """通用价格抓取函数"""
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.encoding = resp.apparent_encoding
    soup = BeautifulSoup(resp.text, "html.parser")

    rows = soup.select(selector)
    results = []

    for row in rows:
        cols = [c.get_text(strip=True) for c in row.select("td")]
        if len(cols) >= 3:
            results.append({
                "item": cols[0],
                "price": cols[1],
                "change": cols[2],
                "source": source
            })

    return results


def fetch_pv_prices():
    """光伏价格：硅料 / 硅片 / 电池片 / 组件"""
    return fetch_price_table(
        url="https://www.solarzoom.com/price/",
        selector="table tr",
        source="PV"
    )


def fetch_bess_prices():
    """储能价格：电芯 / PACK / 系统"""
    return fetch_price_table(
        url="https://www.escn.com.cn/price/",
        selector="table tr",
        source="BESS"
    )


def fetch_all_prices():
    prices = []
    prices.extend(fetch_pv_prices())
    prices.extend(fetch_bess_prices())
    return prices