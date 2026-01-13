import requests
from bs4 import BeautifulSoup
from solar_intel_v2.system.utils import setup_logger
from solar_intel_v2.system.config_loader import load_config
from datetime import date

logger = setup_logger("prices")
config = load_config()


# ============================================================
# HTML 通用抓取器
# ============================================================
def fetch_html_price(url, selectors):
    items = []

    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        for row in soup.select(selectors["item"]):
            try:
                name = row.select_one(selectors["name"]).get_text(strip=True)
                price = row.select_one(selectors["price"]).get_text(strip=True)

                if selectors.get("change"):
                    change = row.select_one(selectors["change"]).get_text(strip=True)
                else:
                    change = ""

                items.append({
                    "item": name,
                    "price": price,
                    "change": change,
                    "source": url
                })

            except Exception as e:
                logger.warning(f"单条价格解析失败：{e}")

    except Exception as e:
        logger.error(f"HTML 价格抓取失败：{url} | {e}")

    return items


# ============================================================
# TradingEconomics 抓取器
# ============================================================
def fetch_te_price(url, item_name):
    items = []

    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        price_cell = soup.select_one(".table .datatable-row .datatable-cell:nth-child(2)")
        if not price_cell:
            logger.warning(f"TE 未找到价格：{url}")
            return []

        price = price_cell.get_text(strip=True)

        items.append({
            "item": item_name.capitalize(),
            "price": price,
            "change": "",
            "source": "TradingEconomics"
        })

    except Exception as e:
        logger.error(f"TradingEconomics 抓取失败：{url} | {e}")

    return items


# ============================================================
# Google Finance 抓取器
# ============================================================
def fetch_google_finance(url, ticker):
    items = []

    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        price = soup.select_one(".YMlKec")
        if not price:
            logger.warning(f"Google Finance 未找到价格：{url}")
            return []

        price = price.get_text(strip=True)

        items.append({
            "item": ticker,
            "price": price,
            "change": "",
            "source": "Google Finance"
        })

    except Exception as e:
        logger.error(f"Google Finance 抓取失败：{url} | {e}")

    return items


# ============================================================
# 主函数：抓取所有价格
# ============================================================
def fetch_all_prices():
    logger.info("开始抓取价格数据…")

    price_list = []

    # -------------------------
    # 国内价格
    # -------------------------
    domestic_cfg = config["prices"]["domestic"]

    for name, cfg in domestic_cfg.items():
        if not cfg.get("enabled", False):
            continue

        logger.info(f"抓取国内价格源：{name}")

        items = fetch_html_price(cfg["url"], cfg["selectors"])
        price_list += items

    # -------------------------
    # 国际价格：TradingEconomics
    # -------------------------
    te_cfg = config["prices"]["international"]["tradingeconomics"]
    if te_cfg.get("enabled", False):
        base = te_cfg["base_url"]
        for item in te_cfg["commodities"]:
            url = base.format(item=item)
            logger.info(f"抓取 TE 价格：{item}")
            price_list += fetch_te_price(url, item)

    # -------------------------
    # 国际价格：Google Finance
    # -------------------------
    gf_cfg = config["prices"]["international"]["google_finance"]
    if gf_cfg.get("enabled", False):
        base = gf_cfg["base_url"]
        for ticker in gf_cfg["tickers"]:
            url = base.format(ticker=ticker)
            logger.info(f"抓取 Google Finance：{ticker}")
            price_list += fetch_google_finance(url, ticker)

    logger.info(f"成功抓取 {len(price_list)} 条价格数据")

    # ============================================================
    # 关键修复：为每条价格补上日期字段（适配 dict）
    # ============================================================
    today = date.today().isoformat()

    price_list_with_date = []
    for item in price_list:
        item["date"] = today
        price_list_with_date.append(item)

    return price_list_with_date