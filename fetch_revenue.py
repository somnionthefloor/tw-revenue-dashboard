#!/usr/bin/env python3
"""Fetch monthly revenue data for Taiwanese companies from FinMind API."""

import json
import os
import sys
import time
from datetime import datetime

import requests

COMPANIES = {
    "메모리": [
        {"code": "2408", "name": "Nanya Tech"},
        {"code": "2344", "name": "Winbond"},
        {"code": "2337", "name": "Macronix"},
    ],
    "비메모리": [
        {"code": "2454", "name": "MediaTek"},
        {"code": "3034", "name": "Novatek"},
        {"code": "2379", "name": "Realtek"},
    ],
    "파운드리": [
        {"code": "2330", "name": "TSMC"},
        {"code": "2303", "name": "UMC"},
        {"code": "5347", "name": "VIS"},
    ],
    "후공정(OSAT)": [
        {"code": "3711", "name": "ASE Tech"},
        {"code": "6147", "name": "Chipbond"},
        {"code": "6239", "name": "PTI"},
        {"code": "8150", "name": "ChipMOS"},
        {"code": "2449", "name": "KYEC"},
    ],
    "반도체 유통": [
        {"code": "3260", "name": "Adata"},
        {"code": "2451", "name": "Transcend"},
        {"code": "8299", "name": "Phison"},
    ],
    "Apple Vendor": [
        {"code": "2317", "name": "Hon Hai"},
        {"code": "4938", "name": "Pegatron"},
        {"code": "3008", "name": "Largan"},
        {"code": "3406", "name": "Genius"},
        {"code": "2474", "name": "Catcher"},
    ],
    "서버": [
        {"code": "5274", "name": "Aspeed"},
        {"code": "4919", "name": "Nuvoton"},
        {"code": "2382", "name": "Quanta"},
        {"code": "6669", "name": "Wiwynn"},
        {"code": "2356", "name": "Inventec"},
        {"code": "2315", "name": "Mitac"},
        {"code": "3515", "name": "ASRock"},
        {"code": "3231", "name": "Wistron"},
    ],
    "PC": [
        {"code": "2353", "name": "Acer"},
        {"code": "2357", "name": "Asustek"},
        {"code": "2376", "name": "Gigabyte"},
        {"code": "2324", "name": "Compal"},
    ],
    "PCB": [
        {"code": "3037", "name": "Unimicron"},
        {"code": "8046", "name": "Nanya PCB"},
        {"code": "3189", "name": "Kinsus"},
    ],
    "EV(패키징)": [
        {"code": "6121", "name": "Simplo"},
        {"code": "3211", "name": "Dynapack"},
    ],
    "LCD 패널": [
        {"code": "2409", "name": "AUO"},
        {"code": "3481", "name": "Innolux"},
        {"code": "6116", "name": "Hannstar"},
    ],
    "MLCC": [
        {"code": "2327", "name": "Yageo"},
        {"code": "2492", "name": "Walsin"},
    ],
    "전력/전원": [
        {"code": "2308", "name": "Delta"},
        {"code": "2301", "name": "Lite-On"},
    ],
    "레거시 팹리스": [
        {"code": "3006", "name": "ESMT"},
        {"code": "8271", "name": "AP Memory"},
        {"code": "5351", "name": "Etron"},
    ],
}

FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def fetch_company(code, start_date="2020-01-01"):
    """Fetch monthly revenue for a company from FinMind."""
    params = {
        "dataset": "TaiwanStockMonthRevenue",
        "data_id": code,
        "start_date": start_date,
        "end_date": datetime.now().strftime("%Y-%m-%d"),
    }
    try:
        r = requests.get(FINMIND_URL, params=params, timeout=30)
        data = r.json()
        if data.get("status") == 200 and data.get("data"):
            return data["data"]
    except Exception as e:
        print(f"  Error: {e}")
    return []


def transform_data(records):
    """Transform FinMind records into {year: {month: revenue}} format.
    Revenue is in NTD thousands (千元) to match MOPS convention."""
    result = {}
    for rec in records:
        year = rec["revenue_year"]
        month = rec["revenue_month"]
        revenue = rec["revenue"]  # in NTD (元)
        revenue_thousands = revenue // 1000  # convert to 千元
        year_str = str(year)
        if year_str not in result:
            result[year_str] = {}
        result[year_str][str(month)] = revenue_thousands
    return result


def fetch_all(start_year=2020):
    os.makedirs(DATA_DIR, exist_ok=True)
    start_date = f"{start_year}-01-01"

    all_companies = []
    for category, companies in COMPANIES.items():
        for company in companies:
            all_companies.append({**company, "category": category})

    result = {}
    years_set = set()
    total = len(all_companies)

    for i, company in enumerate(all_companies, 1):
        code = company["code"]
        name = company["name"]
        print(f"[{i}/{total}] Fetching {name} ({code})...", end=" ", flush=True)

        records = fetch_company(code, start_date)
        if records:
            revenue = transform_data(records)
            result[code] = {
                "name": name,
                "category": company["category"],
                "revenue": revenue,
            }
            years_set.update(int(y) for y in revenue.keys())
            month_count = sum(len(m) for m in revenue.values())
            print(f"OK ({month_count} data points)")
        else:
            result[code] = {
                "name": name,
                "category": company["category"],
                "revenue": {},
            }
            print("no data")

        time.sleep(0.3)

    years = sorted(years_set)
    output_path = os.path.join(DATA_DIR, "revenue_data.json")
    meta = {
        "last_updated": datetime.now().isoformat(),
        "years": years,
        "companies": result,
        "categories": {cat: [c["code"] for c in comps] for cat, comps in COMPANIES.items()},
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(result)} companies to {output_path}")
    print(f"Years: {years}")
    return meta


if __name__ == "__main__":
    start_year = int(sys.argv[1]) if len(sys.argv) > 1 else 2020
    fetch_all(start_year)
