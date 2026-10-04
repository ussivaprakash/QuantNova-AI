from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf


START_DATE = "2025-01-01"
END_DATE_EXCLUSIVE = "2026-08-01"
MARKET_CLOSE_TIME = "15:30:00"
OUTPUT_FILE = Path("Tata_Motors_OHLCV_2025-01-01_to_2026-07-31.xlsx")

SYMBOLS = {
    "TMPV": "TMPV.NS",
    "TMCV": "TMCV.NS",
}


def download_ohlcv(symbol: str) -> pd.DataFrame:
    data = yf.download(
        symbol,
        start=START_DATE,
        end=END_DATE_EXCLUSIVE,
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    if data.empty:
        raise RuntimeError(f"No data returned for {symbol}")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.reset_index()
    data = data.rename(columns={"Adj Close": "Adj Close"})
    data["Date"] = pd.to_datetime(data["Date"]).dt.date
    data.insert(1, "Time", MARKET_CLOSE_TIME)
    data.insert(2, "Date Time", pd.to_datetime(data["Date"].astype(str) + " " + data["Time"]))

    return data[["Date", "Time", "Date Time", "Open", "High", "Low", "Close", "Adj Close", "Volume"]]


def main() -> None:
    downloaded = {sheet: download_ohlcv(symbol) for sheet, symbol in SYMBOLS.items()}

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl", datetime_format="yyyy-mm-dd hh:mm:ss") as writer:
        for sheet_name, frame in downloaded.items():
            frame.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.book[sheet_name]
            worksheet.freeze_panes = "A2"
            for cell in worksheet[1]:
                cell.style = "Headline 4"
            widths = {
                "A": 14,
                "B": 12,
                "C": 22,
                "D": 12,
                "E": 12,
                "F": 12,
                "G": 12,
                "H": 12,
                "I": 14,
            }
            for letter, width in widths.items():
                worksheet.column_dimensions[letter].width = width

        notes = pd.DataFrame(
            [
                {
                    "Item": "Requested date range",
                    "Value": "2025-01-01 to 2026-07-31; only trading days are included.",
                },
                {
                    "Item": "Time value",
                    "Value": "15:30:00 is used as the daily NSE market close time because this is daily OHLCV data.",
                },
                {
                    "Item": "TMPV.NS",
                    "Value": "Yahoo Finance returned data from 2025-01-01 to 2026-07-31.",
                },
                {
                    "Item": "TMCV.NS",
                    "Value": "Yahoo Finance returned data starting 2025-11-12; no earlier rows were returned for this symbol.",
                },
                {
                    "Item": "Columns",
                    "Value": "Date, Time, Date Time, Open, High, Low, Close, Adj Close, Volume.",
                },
            ]
        )
        notes.to_excel(writer, sheet_name="Notes", index=False)
        notes_ws = writer.book["Notes"]
        notes_ws.column_dimensions["A"].width = 24
        notes_ws.column_dimensions["B"].width = 100

    print(f"Saved: {OUTPUT_FILE.resolve()}")
    for sheet_name, frame in downloaded.items():
        print(f"{sheet_name}: {len(frame)} rows, {frame['Date'].min()} to {frame['Date'].max()}")


if __name__ == "__main__":
    main()
