import requests
from bs4 import BeautifulSoup


def fetch_price_table(url, source):
    headers = {"User-Agent": "Mozilla/5.0"}

    """智能价格抓取器：自动识别 table / ul / div 列表结构"""
    results = []

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")

        # ============================
        # 1) 优先识别 <table>
        # ============================
        tables = soup.find_all("table")
        for table in tables:
            for tr in table.find_all("tr"):
                tds = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if len(tds) < 2:
                    continue

                item = tds[0]
                price = tds[1]
                change = tds[2] if len(tds) > 2 else ""

                if not item or not price:
                    continue

                results.append({
                    "item": item,
                    "price": price,
                    "change": change,
                    "source": source,
                    "type": detect_price_type(item)
                })

        # ============================
        # 2) 识别 <ul><li> 列表结构
        # ============================
        for ul in soup.find_all("ul"):
            for li in ul.find_all("li"):
                text = li.get_text(strip=True)
                if not text or len(text) < 6:
                    continue

                # 简单分割：硅料 56 元/kg +0.5%
                parts = text.split()
                if len(parts) < 2:
                    continue

                item = parts[0]
                price = parts[1]
                change = parts[2] if len(parts) > 2 else ""

                results.append({
                    "item": item,
                    "price": price,
                    "change": change,
                    "source": source
                })

        # ============================
        # 3) 识别 <div class="xxx"> 列表结构
        # ============================
        for div in soup.find_all("div"):
            text = div.get_text(strip=True)
            if not text or len(text) < 6:
                continue

            # 过滤非价格类文本
            if "元" not in text and "￥" not in text:
                continue

            parts = text.split()
            if len(parts) < 2:
                continue

            item = parts[0]
            price = parts[1]
            change = parts[2] if len(parts) > 2 else ""

            results.append({
                "item": item,
                "price": price,
                "change": change,
                "source": source
            })

    except Exception as e:
        print(f"[WARN] 价格抓取失败：{url} - {e}")

    # 去重
    unique = []
    seen = set()
    for r in results:
        key = (r["item"], r["price"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique


def fetch_pv_prices():
    """光伏价格：硅料 / 硅片 / 电池片 / 组件（主源 + 备用源）"""

    # 主源：Solarzoom
    primary = fetch_price_table(
        url="https://www.solarzoom.com/price/",
        source="PV"
    )

    if primary:
        return primary

    print("[WARN] Solarzoom 无数据，切换到北极星光伏价格…")

    # 备用源：北极星光伏
    fallback = fetch_price_table(
        url="https://guangfu.bjx.com.cn/price/",
        source="PV"
    )

    return fallback


def fetch_bess_prices():
    """储能价格：电芯 / PACK / 系统（主源 + 备用源）"""

    # 主源：ESCN
    primary = fetch_price_table(
        url="https://www.escn.com.cn/price/",
        source="BESS"
    )

    if primary:
        return primary

    print("[WARN] ESCN 无数据，切换到北极星储能价格…")

    # 备用源：北极星储能
    fallback = fetch_price_table(
        url="https://chuneng.bjx.com.cn/price/",
        source="BESS"
    )
    return fallback


def fetch_all_prices():
    prices = []

    for func in [fetch_pv_prices, fetch_bess_prices]:
        try:
            prices.extend(func())
        except Exception as e:
            print(f"[WARN] 价格模块失败：{func.__name__} - {e}")

    return prices

# 自动识别价格类型
def detect_price_type(item_text):
    """根据 item 文本自动识别价格类型"""

    text = item_text.lower()

    # PV
    if any(k in text for k in ["硅料", "致密料", "单晶料", "多晶料"]):
        return "Silicon Material"

    if any(k in text for k in ["硅片", "182", "210", "m10", "g12"]):
        return "Wafer"

    if any(k in text for k in ["电池片", "perc", "topcon", "hjt"]):
        return "Cell"

    if any(k in text for k in ["组件", "模组", "550w", "600w"]):
        return "Module"

    # BESS
    if any(k in text for k in ["电芯", "lfp", "ncm", "磷酸铁锂"]):
        return "Battery Cell"

    if "pack" in text:
        return "Pack"

    if any(k in text for k in ["储能系统", "1c", "2c", "集装箱"]):
        return "System"

    return "Unknown"