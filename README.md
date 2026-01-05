

## 🌞 SABA Energy Intelligence System
Our company overview:

* [Saba Energy](https://www.saba.energy/)

SABA Energy Intelligence System overview:
* https://yacobofwork.github.io/solar_briefing/
![img_2.png](img_2.png)

Internal Technical Documentation — Version 1.0

---

### 📌 1. Introduction

SABA Solar Intelligence System is an internal intelligence automation platform designed to support SABA Energy’s global solar and energy‑storage operations.
The system consolidates multi‑source industry information, applies AI‑driven analysis, and generates professional‑grade daily reports for internal decision‑making.

The platform is built with:

* Modular and maintainable architecture
* Automated data ingestion (web, WeChat, price feeds)
* AI‑powered summarization and insights
* Professional PDF and HTML email rendering
* Automated delivery with fallback mechanisms
* Extensible pipeline for future intelligence modules


This system is actively used by the [SABA Energy](https://www.saba.energy) team to improve situational awareness, procurement planning, and market intelligence.

---

### 🏗️ 2. System Architecture

```markdown
solar_briefing/
│
├── main.py                     # Main workflow orchestrator
├── config.yaml                 # Global configuration
├── requirements.txt            # Python dependencies
│
├── ingestion/                  # Data ingestion layer
│     ├── url_queue.py          # URL queue manager (pending/fetched/failed)
│     ├── wechat_link_reader.py # Reads WeChat links → queue
│     ├── ...                   # Future ingestion modules
│
├── fetcher.py                 # Web/WeChat article fetcher
├── fetch_prices.py            # Price data ingestion
├── save_price_history.py      # Historical price storage
│
├── insights.py                # AI summarization & insights generation
│
├── chart_builder.py           # Price trend chart generator
├── pdf_builder.py             # PDF report generator
├── email_builder.py           # HTML email generator
├── email_sender.py            # Email delivery (primary/backup SMTP)
│
├── templates/                 # HTML/PDF templates
├── prompts/                   # AI prompt templates
├── renderers/                 # Rendering utilities
│
├── data/                      # Raw data & URL queue
│     └── incoming_urls.jsonl
│
├── output/                    # Generated reports & charts
│
└── logs/                      # Runtime logs
```

---

### 🔄 3. Data Flow Overview

                ┌────────────────────────────┐
                │   Manual / Automated URLs   │
                │ (WeChat, Web, Price Feeds)  │
                └──────────────┬─────────────┘
                               ▼
                    ingestion/url_queue.py
                     (pending URL storage)
                               ▼
                     fetcher.py / fetch_prices.py
                     (HTML fetch + data extraction)
                               ▼
                         insights.py
                (AI summary, key insights, impact)
                               ▼
                chart_builder / pdf_builder / email_builder
                               ▼
                      output/ (PDF + Email)
                               ▼
                        email_sender.py
                     (Daily automated delivery)


---

### 📥 4. Ingestion Layer

#### 4.1 URL Queue System

All external URLs enter the system through:
```json
data/incoming_urls.jsonl
```

Each record contains:

```json
{
  "url": "...",
  "source": "wechat | web",
  "added_at": "2026-01-05T10:00:00Z",
  "status": "pending | fetched | failed"
}
```

The queue ensures:

* Deduplication
* Status tracking
* Unified ingestion pipeline
* Easy debugging and auditing


---

#### 4.2 WeChat Link Reader (Manual Input)

Team members can manually paste WeChat article links into:

```
wechat_links.txt
```

Then run:
```python
 python -m ingestion.wechat_link_reader
```

The system will:

* Read all links
* Validate them
* Add them to the URL queue
* Avoid duplicates

This is the recommended method for internal WeChat article ingestion.

---

### 🧠 5. AI Insights Layer

The system uses structured prompt templates to generate:

* English & Chinese summaries
* Key insights
* Supply chain impact analysis
* Nigeria market relevance
* Procurement recommendations


All prompts are stored in:
```markdown
prompts/
```

This layer ensures consistent, high‑quality intelligence output.

---

### 🖼️ 6. Rendering Layer

#### 6.1 PDF Report

Features:

* Gradient cover with SABA branding
* Auto‑generated table of contents
* Card‑style news layout
* Price trend charts
* Clean, professional typography


#### 6.2 HTML Email

Features:

* Responsive layout
* Outlook/Gmail compatible
* Embedded charts (CID)
* Clear visual hierarchy


---

### 🛠️ 7. Command Line Interface (CLI)

Ingest WeChat links
```python
 python -m ingestion.wechat_link_reader
```
Run full daily pipeline

```python
python main.py
```


---

### 🚀 8. Key Features

✔ Automated Data Ingestion

* Web news
* WeChat articles
* Price data
* Manual link ingestion
* URL queue with deduplication


✔ AI‑Powered Analysis

* Summaries
* Insights
* Impact assessment
* Recommendations


✔ Professional Output

* PDF daily report
* HTML email
* Charts & visualizations


✔ Reliable Delivery

* SMTP primary/backup
* Logging
* Error handling


✔ Modular & Extensible

* Add new ingestion modules
* Add new AI prompts
* Add new output formats
* Add new delivery channels


---

### 🧩 9. Future Roadmap

Data Sources

* WeChat Official Account homepage crawler
* Policy announcement feeds
* Corporate disclosures
* RSS/Atom feeds


Intelligence

* Weekly/monthly automated reports
* Price forecasting
* Supply chain risk alerts
* Competitor analysis


Delivery

* Microsoft Teams
* WhatsApp

Engineering

* PostgreSQL database
* Redis caching
* Airflow scheduling
* Sentry monitoring


---

### 📄 10. License

Internal use only.

This system is proprietary to SABA Energy and must not be distributed externally.

---

### 👤 11. Maintainer

* Yacob： QA & Operations Support Engineer of Saba Energy



