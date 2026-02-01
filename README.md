# Saba Energy Intelligence System  
A fully automated intelligence engine delivering daily insights on global solar supply chains, Nigeria market dynamics, and price movements — across **Email**, **PDF**, and **Web (GitHub Pages)**.

Website Address: https://yacobofwork.github.io/solar_briefing/index.html

---

## 🌍 Overview

The **Saba Energy Intelligence System** is a production-grade, fully automated intelligence pipeline designed for distributed solar projects in Nigeria.  
It collects, analyzes, summarizes, and publishes daily insights from multiple global and local data sources, ensuring the team always has a clear and up‑to‑date understanding of the solar supply chain landscape.

The system now supports **three synchronized output channels**:

### ✔ Email — Daily briefing delivered automatically  
### ✔ PDF — Professional, shareable report  
### ✔ Web (GitHub Pages) — Interactive browsing + historical archive  

All three channels share the same data, insights, and visual identity.

---

## ⚙️ Automated Daily Execution (New)

The entire intelligence pipeline runs automatically every day at 16:30, powered by a production‑grade execution script and a clean cron schedule.

1. Enhanced run_daily.sh

The system includes a robust execution script that provides:

* Auto‑detect project directory
* Auto‑activate Python 3.11 virtual environment
* Auto‑register symlink to /usr/local/bin/run_daily.sh
* Lock file to prevent duplicate runs
* Timeout protection
* Daily log rotation
* Cron schedule detection
* Cross‑machine compatibility (no hardcoded paths)


This ensures the pipeline runs reliably on any machine without manual setup.

2. Cron Schedule

To enable daily automation:

```shell
30 16 * * * run_daily.sh
```


Once the symlink is registered (automatically on first run), cron can trigger the entire workflow using a single clean command.

3. Daily Workflow

Every day at 16:30, the system automatically:

1. Fetches global + Nigeria solar news
2. Scrapes raw material prices (multi‑source fallback)
3. Generates AI insights
4. Builds PDF + Email + Web JSON snapshot
5. Updates GitHub Pages (daily + archive)
6. Writes logs and rotates them
7. Prints execution metadata (PID, cron schedule, timestamps)


No manual intervention is required.

---

## 🚀 Key Features

### **1. Multi‑Channel Publishing**
- 📧 **Email**: Responsive HTML email compatible with Outlook, Gmail, 163  
- 📄 **PDF**: Professional layout with charts, tables, and structured sections  
- 🌐 **Web**: Interactive GitHub Pages site with date navigation and archive

### **2. Automated Daily Intelligence**
- Global solar & storage news  
- China supply chain updates  
- Nigeria market intelligence  
- Daily price tables (modules, batteries, freight)  
- AI‑generated insights & summaries  
- Price trend charts (auto‑rendered)

### **3. Zero‑Maintenance Pipeline**
- Fully automated ingestion → processing → publishing  
- GitHub Actions / cron‑based execution  
- Automatic fallback & error‑tolerant design  
- Historical index auto‑generated

### **4. Unified Visual Identity**
All outputs (Email, PDF, Web) share the same **Teal brand color system**:
- Primary: `#005B5B`  
- Secondary: `#4CCBC0`  
- Accent: `#007A6F`  
- Background: `#f4f6f8`

---

## 🧠 System Architecture

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

## 🔄 Data Flow Overview

                ┌──────────────────────────────────────────┐
                │      Manual / Automated URL Sources       │
                │  (WeChat Articles, Web Pages, Price Feeds)│
                └──────────────────────────┬───────────────┘
                                           ▼
                               ingestion/url_queue.py
                               (pending URL storage)
                                           ▼
                    ┌──────────────────────────────────────────┐
                    │ fetcher.py / fetch_prices.py              │
                    │  - HTML fetch                             │
                    │  - Content extraction                     │
                    │  - Price scraping                         │
                    └──────────────────────────┬───────────────┘
                                               ▼
                                        insights.py
                        (AI summary, region classification,
                         key insights, price impact analysis)
                                               ▼
                    ┌──────────────────────────────────────────┐
                    │ Rendering Layer                           │
                    │  - chart_builder.py (PNG charts)          │
                    │  - pdf_builder.py   (Daily PDF)           │
                    │  - email_builder.py (HTML Email)          │
                    │  - json_builder.py  (Web JSON snapshot)   │
                    └──────────────────────────┬───────────────┘
                                               ▼
                                   output/
                    (PDF, Email HTML, JSON snapshots, Charts)
                                               ▼
                    ┌──────────────────────────────────────────┐
                    │ Publishing Layer                          │
                    │  - email_sender.py (Daily delivery)       │
                    │  - GitHub Pages update (Web UI + Archive) │
                    └──────────────────────────────────────────┘


---


## 📅 Daily Automation Flow

The system runs a fully automated end‑to‑end pipeline every day:

1. Fetch Data• Global solar & storage news
- China supply chain updates
- Nigeria market intelligence
- Daily price data (modules, batteries, freight)

2. AI Processing• Summaries for each region
- Price impact analysis
- Daily insight generation
- News classification (China / Nigeria / Global)

3. Rendering• HTML email (responsive)
- PDF report (professional layout)
- JSON snapshot for web UI
- Price trend chart (PNG)

4. Publishing• Send email briefing
- Save PDF to output directory
- Update GitHub Pages (daily report + archive)
- Refresh index.json for historical navigation



This pipeline ensures all three channels — **Email**, **PDF**, and **Web** — stay perfectly synchronized every day.


---

## 🌐 GitHub Pages (Web UI)

The system provides a fully interactive web interface:

### **Homepage**
- System overview  
- Architecture  
- Value proposition  
- Links to daily report & archive  

### **Daily Report Page**
- Date selector  
- Previous/Next navigation  
- Price tables  
- Price chart  
- AI insights  
- News sections  

### **Archive Page**
- Full historical list  
- One‑click access to any date  

---

## 🛠 Tech Stack

- **Python** — ingestion, processing, rendering  
- **Jinja2** — HTML templating  
- **WeasyPrint** — PDF generation  
- **Matplotlib** — chart rendering  
- **GitHub Pages** — web hosting  
- **GitHub Actions / cron** — automation  
- **HTML/CSS/JS** — web UI  
- **DeepSeek** — AI summarization  

---

## 📈 Why This System Matters

- Eliminates manual data collection  
- Ensures consistent daily intelligence  
- Supports procurement & operations decisions  
- Provides a unified view of global + Nigeria markets  
- Scales with the team and future data sources  
- Professional, reliable, and fully automated  

---

## 👤 Author

**Developed by:** Yacob  
**Role:** QA & Operations Support Engineer of Saba Energy  
**Email:** ywang@saba.energy  | yacobofwork@gmail.com

---

## 🔮 Roadmap

- [ ] Add monthly & yearly summary reports  
- [ ] Add search across historical news  
- [ ] Add Nigeria price forecasting module  
- [ ] Add API endpoint for internal tools  
- [ ] Add dark mode for web UI  
- [ ] Add multi‑language support (EN/中文)  

---

## 📄 License

Internal use only — Saba Energy.