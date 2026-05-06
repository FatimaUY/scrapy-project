# 🕷️ Scrapy Project — Centrale-Brico Scraper

A **web scraping pipeline built with Scrapy** to extract structured data (categories + products) from [centrale-brico.com](https://www.centrale-brico.com), store it in **CSV, JSON, and SQLite database**, and maintain a clean ETL-style architecture.

---

## 🚀 Features

- 🗂️ Scrapes hierarchical product categories
- 📦 Extracts products linked to categories
- 💾 Stores data in SQLite database
- 📤 Exports to CSV & JSON
- 🧹 Data cleaning & validation pipeline
- ⚙️ Runner script to automate full workflow

---

## 📁 Project Architecture

```
scrapy-project/
│
├── webscraper/
│   ├── webscraper/
│   │   ├── spiders/
│   │   │   ├── categoryspider.py      # 🗂️ Category scraper
│   │   │   └── productspider.py       # 📦 Product scraper
│   │   ├── items.py                   # 🧩 Data schemas
│   │   ├── pipelines.py               # 🧹 ETL pipelines
│   │   └── settings.py                # ⚙️ Scrapy configuration
│   └── scrapy.cfg
│
├── output/                            # 📤 Exported files (CSV / JSON)
├── logs/                              # 📋 Spider logs
├── scraping_data.db                   # 🗄️ SQLite database
├── runner.py                          # 🤖 Pipeline automation script
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the project

```bash
git clone https://github.com/FatimaUY/scrapy-project.git
cd scrapy-project
```

### 2. Create virtual environment

```bash
python -m venv .venv
```

### 3. Activate environment

**Linux / macOS**

```bash
source .venv/bin/activate
```

**Windows**

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install scrapy
```

---

## 🕸️ Spiders Overview

### 🗂️ Category Spider (`brico_spider.py`)

Scrapes all categories from the website and builds a hierarchical structure.

**Extracted fields:**

- id_cat
- name_cat
- url_cat
- parent_cat
- is_page

**Outputs:**

- CSV & JSON files
- SQLite table: `categories`

---

### 📦 Product Spider (`product_spider.py`)

Reads categories from the database and scrapes all products per category.

**Extracted fields:**

- id_product
- name_product
- price
- url_product
- category_name
- id_cat

**Outputs:**

- CSV & JSON files
- SQLite table: `products`

> ⚠️ Must run category spider first

---

## 🗄️ Database Schema

### 📂 categories

- id_cat (PK)
- name_cat
- url_cat
- parent_cat
- is_page
- created_at
- updated_at

### 📦 products

- id_product (PK)
- name_product
- price
- url_product
- id_cat (FK)
- category_name
- created_at
- updated_at

---

## 🔧 Pipeline System

- 🧹 DataCleaningPipeline → clean raw data
- ✅ DataValidationPipeline → validate & generate IDs
- 🚫 DuplicateRemovalPipeline → remove duplicates
- 💾 DatabasePipeline → store into SQLite

---

## ▶️ Usage

### 🚀 Run full pipeline

```bash
python runner.py
```

### 🗂️ Run categories only

```bash
python runner.py categories
```

### 📦 Run products only

```bash
python runner.py products
```

---

## 🛠️ Manual execution

```bash
scrapy crawl brico_spider
scrapy crawl product_spider
```

> ⚠️ Always run categories before products

---

