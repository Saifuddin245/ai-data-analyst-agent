# My AI Data Analyst — Free Starter

## What it does
- Upload CSV and Excel files
- Standardizes column names
- Removes fully empty rows/columns and exact duplicate rows
- Reports missing values (does not silently fill or delete them)
- Shows numeric summaries and charts
- Answers a small set of transparent questions using Python rules
- Runs a single read-only SELECT/WITH query in DuckDB
- Exports cleaned CSV, Excel workbook and text report

This is a local analytics starter, not yet a general-purpose LLM agent. It does not send your dataset to an online AI service.

## Laptop requirements
- Windows 10/11, 64-bit
- Python 3.11 or 3.12 recommended
- 8 GB RAM minimum; 16 GB recommended
- Internet is needed only to install packages initially

## Installation (Windows 11)
1. Install Python 3.11 from https://www.python.org/downloads/
2. During installation, tick **Add python.exe to PATH**.
3. Open the project folder in File Explorer.
4. Click the address bar, type `cmd`, and press Enter.
5. Run these commands:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If `py -3.11` is not recognized, try:
```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Streamlit opens the app in your browser, usually at http://localhost:8501.
Keep the terminal window open while using the app. To stop it, press Ctrl+C in the terminal.

## First test
1. Upload `sample_retail_sales.csv`.
2. Check the Data Preview and Data Quality tabs.
3. In Analysis & Charts, choose Bar chart, `region`, and `sales`.
4. In Ask Your Data, ask `What is total sales?`
5. In SQL & Reports, run `SELECT region, SUM(sales) AS total_sales FROM data GROUP BY region ORDER BY total_sales DESC`
6. Download the cleaned CSV, Excel workbook and text report.

Expected sample checks:
- 10 source rows
- 1 exact duplicate row removed
- 9 cleaned rows
- Total sales after duplicate removal = 9,350

## Troubleshooting
- `pip is not recognized`: use `python -m pip ...`
- `streamlit is not recognized`: activate `.venv` and run `python -m streamlit run app.py`
- Browser did not open: manually visit http://localhost:8501
- Excel import error: make sure the file is `.xlsx` and close it in Excel before retrying.
- Port is busy: run `streamlit run app.py --server.port 8502`

## Safe-use notes
- Work on a copy of important data.
- Inspect missing values before deciding how to handle them.
- Validate totals against the original workbook.
- Do not upload confidential company/customer data to public services.
- SQL is intended for read-only analysis. Review every query and result.
