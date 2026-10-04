from __future__ import annotations

import re
import sys
import urllib.request
from html import unescape
from pathlib import Path

import pandas as pd


OUTPUT_FILE = Path("Tata_Motors_One_Year_Data.xlsx")
OLD_FINANCIAL_FILE = Path("Financial-statistics-history-1 (1).xls")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )
}

STOCKS = [
    ("TMCV", "Tata Motors Limited / Commercial Vehicles"),
    ("TMPV", "Tata Motors Passenger Vehicles Limited"),
]


def clean_html_cell(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    return unescape(value).replace("\xa0", " ").strip()


def parse_number(value: str):
    value = value.replace(",", "").replace("%", "").strip()
    if value in {"", "-"}:
        return None
    try:
        return float(value)
    except ValueError:
        return value


def fetch_stockanalysis_history(symbol: str, company: str) -> pd.DataFrame:
    url = f"https://stockanalysis.com/quote/nse/{symbol}/history/"
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8", "ignore")

    rows = []
    for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.S | re.I):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, flags=re.S | re.I)
        cells = [clean_html_cell(cell) for cell in cells]
        if len(cells) != 8:
            continue
        if cells[0] == "Date" or not re.match(r"^[A-Z][a-z]{2} \d{1,2}, 20\d{2}$", cells[0]):
            continue
        rows.append(cells)

    if not rows:
        raise RuntimeError(f"No daily price rows were found for {symbol}.")

    df = pd.DataFrame(
        rows,
        columns=["Date", "Open", "High", "Low", "Close", "Adj. Close", "Change %", "Volume"],
    )
    df.insert(0, "Symbol", symbol)
    df.insert(1, "Company", company)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for column in ["Open", "High", "Low", "Close", "Adj. Close", "Change %", "Volume"]:
        df[column] = df[column].map(parse_number)
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    df["Previous Close"] = df["Close"].shift(1)
    df["Daily P/L per Share (INR)"] = df["Close"] - df["Previous Close"]
    df["Daily Return %"] = (df["Daily P/L per Share (INR)"] / df["Previous Close"]) * 100
    df["Turnover Approx (INR)"] = df["Close"] * df["Volume"]
    df["Source URL"] = url
    return df


def load_company_profit_data() -> pd.DataFrame:
    if not OLD_FINANCIAL_FILE.exists():
        return pd.DataFrame(
            [{"Sheet": "Missing", "Metric / Company": str(OLD_FINANCIAL_FILE), "Year": "", "Value": ""}]
        )

    sys.path.insert(0, ".codex_deps")
    import xlrd

    book = xlrd.open_workbook(str(OLD_FINANCIAL_FILE))
    records = []
    wanted_terms = ("profit", "pat", "turnover", "revenue", "sales")
    for sheet in book.sheets():
        years = [sheet.cell_value(1, column) for column in range(1, sheet.ncols)]
        for row in range(sheet.nrows):
            label = str(sheet.cell_value(row, 0)).strip()
            if not label or not any(term in label.lower() for term in wanted_terms):
                continue
            for year, value in zip(years, [sheet.cell_value(row, column) for column in range(1, sheet.ncols)]):
                if year != "" and value != "":
                    records.append(
                        {
                            "Sheet": sheet.name,
                            "Metric / Company": label,
                            "Year": year,
                            "Value": value,
                        }
                    )
    return pd.DataFrame(records)


def build_summary(prices: pd.DataFrame) -> pd.DataFrame:
    records = []
    for symbol, group in prices.groupby("Symbol"):
        valid = group.dropna(subset=["Close"])
        if valid.empty:
            continue
        first = valid.iloc[0]
        last = valid.iloc[-1]
        profit = last["Close"] - first["Close"]
        records.append(
            {
                "Symbol": symbol,
                "Company": last["Company"],
                "From Date": first["Date"],
                "To Date": last["Date"],
                "Rows Included": len(valid),
                "Start Close": first["Close"],
                "End Close": last["Close"],
                "Profit/Loss per Share (INR)": profit,
                "Return %": profit / first["Close"] * 100,
                "Highest Close": valid["Close"].max(),
                "Lowest Close": valid["Close"].min(),
                "Average Daily Volume": valid["Volume"].mean(),
            }
        )
    return pd.DataFrame(records)


def save_workbook() -> None:
    price_frames = [fetch_stockanalysis_history(symbol, company) for symbol, company in STOCKS]
    prices = pd.concat(price_frames, ignore_index=True)

    strategy = pd.DataFrame(
        [
            {
                "Area": "How share profit works",
                "Point": "Daily P/L per share = today's close minus previous close. Multiply by shares held.",
            },
            {
                "Area": "Why two symbols",
                "Point": "Tata Motors data now appears under separated listed symbols such as TMCV and TMPV after the demerger.",
            },
            {
                "Area": "Commercial Vehicles",
                "Point": "Focus on trucks, buses, passenger carriers, financing partnerships, margins, and growth.",
            },
            {
                "Area": "Passenger Vehicles",
                "Point": "Focus on cars, utility vehicles, EV growth, launches, and domestic/international expansion.",
            },
            {
                "Area": "Data note",
                "Point": "Public pages used here expose recent daily rows. Use an NSE/broker export for a licensed full one-year feed.",
            },
        ]
    )

    sources = pd.DataFrame(
        [
            {
                "Source": "StockAnalysis TMCV price history",
                "URL": "https://stockanalysis.com/quote/nse/TMCV/history/",
            },
            {
                "Source": "StockAnalysis TMPV price history",
                "URL": "https://stockanalysis.com/quote/nse/TMPV/history/",
            },
            {
                "Source": "Local financial history workbook",
                "URL": str(OLD_FINANCIAL_FILE),
            },
            {
                "Source": "Tata Motors investor relations",
                "URL": "https://cv.tatamotors.com/investors",
            },
            {
                "Source": "Tata Motors annual reports",
                "URL": "https://www.tatamotors.com/annual-reports/",
            },
        ]
    )

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl", datetime_format="yyyy-mm-dd") as writer:
        build_summary(prices).to_excel(writer, sheet_name="Summary", index=False)
        prices.to_excel(writer, sheet_name="Daily Price Volume", index=False)
        load_company_profit_data().to_excel(writer, sheet_name="Company Profit Data", index=False)
        strategy.to_excel(writer, sheet_name="Business Strategy", index=False)
        sources.to_excel(writer, sheet_name="Evidence Sources", index=False)

        workbook = writer.book
        for worksheet in workbook.worksheets:
            worksheet.freeze_panes = "A2"
            for cell in worksheet[1]:
                cell.style = "Headline 4"
            for column in worksheet.columns:
                letter = column[0].column_letter
                width = max(12, min(60, max(len(str(cell.value or "")) for cell in column) + 2))
                worksheet.column_dimensions[letter].width = width


if __name__ == "__main__":
    save_workbook()
    print(f"Saved: {OUTPUT_FILE.resolve()}")
