import requests
from bs4 import BeautifulSoup
from datetime import date
from src.system.logger import setup_logger
from src.system.config_loader import load_config

logger = setup_logger("fetch_prices")
config = load_config()


# ============================================================
# Generic HTML price fetcher
# ============================================================
def fetch_html_price(url: str, selectors: dict) -> list[dict]:
    items = []
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for row in soup.select(selectors.get("item", "")):
            try:
                name = row.select_one(selectors.get("name")).get_text(strip=True)
                price = row.select_one(selectors.get("price")).get_text(strip=True)
                change = row.select_one(selectors.get("change")).get_text(strip=True) if selectors.get("change") else ""

                items.append({
                    "item": name,
                    "price": price,
                    "change": change,
                    "source": url
                })
            except Exception as e:
                logger.warning(f"Failed to parse one price entry from {url}: {e}")

    except Exception as e:
        logger.error(f"Failed to fetch HTML price from {url}: {e}")

    return items


# ============================================================
# TradingEconomics fetcher
# ============================================================
def fetch_te_price(url: str, item_name: str) -> list[dict]:
    items = []
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        price_cell = soup.select_one(".table .datatable-row .datatable-cell:nth-child(2)")
        if not price_cell:
            logger.warning(f"TradingEconomics price not found: {url}")
            return []

        price = price_cell.get_text(strip=True)
        items.append({
            "item": item_name.capitalize(),
            "price": price,
            "change": "",
            "source": "TradingEconomics"
        })

    except Exception as e:
        logger.error(f"Failed to fetch TradingEconomics price from {url}: {e}")

    return items


# ============================================================
# Google Finance fetcher
# ============================================================
def fetch_google_finance(url: str, ticker: str) -> list[dict]:
    items = []
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        price_el = soup.select_one(".YMlKec")
        if not price_el:
            logger.warning(f"Google Finance price not found: {url}")
            return []

        price = price_el.get_text(strip=True)
        items.append({
            "item": ticker,
            "price": price,
            "change": "",
            "source": "Google Finance"
        })

    except Exception as e:
        logger.error(f"Failed to fetch Google Finance price from {url}: {e}")

    return items


# ============================================================
# Main function: fetch all prices
# ============================================================
def fetch_all_prices() -> list[dict]:
    logger.info("Starting price data fetch...")

    price_list: list[dict] = []

    # Domestic prices
    domestic_cfg = config.get("prices", {}).get("domestic", {})
    for name, cfg in domestic_cfg.items():
        if not cfg.get("enabled", False):
            continue
        logger.info(f"Fetching domestic price source: {name}")
        price_list.extend(fetch_html_price(cfg.get("url", ""), cfg.get("selectors", {})))

    # International prices: TradingEconomics
    te_cfg = config.get("prices", {}).get("international", {}).get("tradingeconomics", {})
    if te_cfg.get("enabled", False):
        base = te_cfg.get("base_url", "")
        for item in te_cfg.get("commodities", []):
            url = base.format(item=item)
            logger.info(f"Fetching TradingEconomics price: {item}")
            price_list.extend(fetch_te_price(url, item))

    # International prices: Google Finance
    gf_cfg = config.get("prices", {}).get("international", {}).get("google_finance", {})
    if gf_cfg.get("enabled", False):
        base = gf_cfg.get("base_url", "")
        for ticker in gf_cfg.get("tickers", []):
            url = base.format(ticker=ticker)
            logger.info(f"Fetching Google Finance price: {ticker}")
            price_list.extend(fetch_google_finance(url, ticker))

    logger.info(f"Fetched {len(price_list)} price entries in total.")

    # Add date field
    today = date.today().isoformat()
    for item in price_list:
        item["date"] = today

    return price_list