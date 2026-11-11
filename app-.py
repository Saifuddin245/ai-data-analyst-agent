import io
import re
from datetime import datetime

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="AI Data Analyst Agent", page_icon="📊", layout="wide")

# Branded welcome header. The founder photo can be added here later.
st.markdown("""
<style>
.hero-card {
    background: linear-gradient(120deg, #10243a 0%, #1d4261 100%);
    padding: 28px 30px;
    border-radius: 18px;
    color: #ffffff;
    margin: 4px 0 18px 0;
}
.hero-kicker {
    color: #a9d8ff;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
.hero-card h1 {
    color: #ffffff;
    margin: 8px 0 4px 0;
    font-size: 2.25rem;
}
.hero-tagline {
    color: #d8edff;
    font-size: 1.12rem;
    font-weight: 600;
    margin-bottom: 8px;
}
.hero-description {
    color: #e7f0f8;
    font-size: 0.98rem;
    max-width: 850px;
    margin-bottom: 18px;
}
.founder-row {
    display: flex;
    align-items: center;
    gap: 14px;
    border-top: 1px solid rgba(255,255,255,0.25);
    padding-top: 16px;
}
.founder-avatar {
    width: 58px;
    height: 58px;
    min-width: 58px;
    border-radius: 50%;
    background: #e7f2fb;
    color: #163752;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.15rem;
    font-weight: 800;
}
.founder-name {
    color: #ffffff;
    font-size: 1.12rem;
    font-weight: 750;
}
.founder-role {
    color: #c7e3f8;
    font-size: 0.9rem;
    margin-top: 2px;
}
.feature-note {
    color: #64748b;
    font-size: 0.82rem;
}
</style>
<div class="hero-card">
    <div class="hero-kicker">Welcome to</div>
    <h1>📊 AI Data Analyst Agent</h1>
    <div class="hero-tagline">Your Data. Smarter Decisions.</div>
    <div class="hero-description">
        Explore, clean and understand your data with practical analytics,
        interactive charts and downloadable reports.
    </div>
    <div class="founder-row">
        <div class="founder-avatar">SS</div>
        <div>
            <div class="founder-name">Sk Saifuddin</div>
            <div class="founder-role">Founder &amp; Developer</div>
            <div class="founder-role">BBA Student | Aspiring Data Analyst</div>
        </div>
    </div>
</div>
<p><strong>About the founder:</strong> I am a BBA student and aspiring Data Analyst, passionate about transforming raw data into meaningful business insights.</p>
""", unsafe_allow_html=True)

st.caption("Upload a CSV or Excel dataset to get started. Your existing analysis tools are available below.")

@st.cache_data
def load_file(file_bytes: bytes, filename: str):
    name = filename.lower()
    if name.endswith(".csv"):
        try:
            return pd.read_csv(io.BytesIO(file_bytes))
        except UnicodeDecodeError:
            return pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(file_bytes))
    raise ValueError("Please upload a CSV or Excel file.")

def clean_data(df: pd.DataFrame):
    cleaned = df.copy()
    cleaned.columns = [
        re.sub(r"\s+", "_", str(c).strip()).lower() or f"column_{i+1}"
        for i, c in enumerate(cleaned.columns)
    ]
    # Remove fully empty rows and columns, then exact duplicate rows.
    cleaned = cleaned.dropna(axis=0, how="all").dropna(axis=1, how="all")
    before = len(cleaned)
    cleaned = cleaned.drop_duplicates()
    duplicates_removed = before - len(cleaned)
    # Convert text columns to numeric only when almost all non-empty values parse.
    for col in cleaned.select_dtypes(include="object").columns:
        original = cleaned[col]
        stripped = original.astype("string").str.replace(",", "", regex=False).str.strip()
        numeric = pd.to_numeric(stripped, errors="coerce")
        nonempty = stripped.notna() & (stripped != "")
        if nonempty.sum() and numeric[nonempty].notna().mean() >= 0.90:
            cleaned[col] = numeric
    return cleaned, duplicates_removed

def make_insights(df: pd.DataFrame):
    insights = []
    rows, cols = df.shape
    insights.append(f"The dataset contains {rows:,} rows and {cols:,} columns.")
    missing = df.isna().sum()
    missing_cols = missing[missing > 0].sort_values(ascending=False)
    if len(missing_cols):
        top = ", ".join(f"{c} ({int(n):,})" for c, n in missing_cols.head(5).items())
        insights.append(f"Missing values were found. Highest counts: {top}.")
    else:
        insights.append("No missing values were detected in the cleaned dataset.")
    numeric = df.select_dtypes(include="number")
    if not numeric.empty:
        for col in numeric.columns[:8]:
            s = numeric[col].dropna()
            if len(s):
                insights.append(
                    f"{col}: total = {s.sum():,.2f}; average = {s.mean():,.2f}; "
                    f"minimum = {s.min():,.2f}; maximum = {s.max():,.2f}."
                )
    date_cols = []
    for col in df.columns:
        if any(word in col.lower() for word in ["date", "day", "month", "year"]):
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().mean() > 0.5:
                date_cols.append((col, parsed))
    for col, parsed in date_cols[:2]:
        insights.append(
            f"{col} appears to contain dates from {parsed.min().date()} to {parsed.max().date()}."
        )
    return insights

def answer_question(question: str, df: pd.DataFrame):
    q = question.lower()
    numeric_cols = list(df.select_dtypes(include="number").columns)
    if not numeric_cols:
        return "I couldn't find numeric columns. Check whether numeric values were imported as text."
    if any(k in q for k in ["total", "sum", "revenue", "sales", "profit"]):
        candidates = [c for c in numeric_cols if any(k in c.lower() for k in ["sales", "revenue", "profit", "amount", "total"])]
        col = candidates[0] if candidates else numeric_cols[0]
        return f"Total for **{col}** is **{df[col].sum():,.2f}**."
    if any(k in q for k in ["average", "mean", "avg"]):
        col = numeric_cols[0]
        for c in numeric_cols:
            if c.lower() in q:
                col = c
                break
        return f"Average **{col}** is **{df[col].mean():,.2f}**."
    if any(k in q for k in ["highest", "maximum", "max", "largest"]):
        col = numeric_cols[0]
        for c in numeric_cols:
            if c.lower() in q:
                col = c
                break
        idx = df[col].idxmax()
        return f"Highest **{col}** is **{df.loc[idx, col]:,.2f}** (row index {idx})."
    if any(k in q for k in ["lowest", "minimum", "min", "smallest"]):
        col = numeric_cols[0]
        for c in numeric_cols:
            if c.lower() in q:
                col = c
                break
        idx = df[col].idxmin()
        return f"Lowest **{col}** is **{df.loc[idx, col]:,.2f}** (row index {idx})."
    if "missing" in q or "null" in q or "empty" in q:
        miss = df.isna().sum()
        miss = miss[miss > 0]
        return "Missing values by column:\n\n" + (miss.to_string() if len(miss) else "No missing values found.")
    if "duplicate" in q:
        return f"There are **{int(df.duplicated().sum())}** duplicate rows in the current dataset."
    return ("I can currently answer basic questions about totals, averages, highest/lowest values, "
            "missing values and duplicates. Try: 'What is total sales?' or 'Which value is highest?'")

st.subheader("Upload your dataset")
st.write("Supported formats: CSV, XLSX and XLS")
uploaded = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx", "xls"])
if uploaded is None:
    st.info("Start by uploading the included sample_retail_sales.csv file, or choose your own dataset.")
    st.subheader("What you can do with this platform")
    feature_cols = st.columns(3)
    with feature_cols[0]:
        st.markdown("### 🧹 Data cleaning")
        st.write("Standardize column names, remove fully empty rows and columns, remove exact duplicate rows, and detect numeric-looking columns.")
    with feature_cols[1]:
        st.markdown("### 🔎 Data quality")
        st.write("Review missing values, data types, missing-value percentages and unique-value counts for each column.")
    with feature_cols[2]:
        st.markdown("### 📊 Data analysis")
        st.write("Explore numeric summaries and create bar, line, histogram and scatter charts.")
    feature_cols = st.columns(3)
    with feature_cols[0]:
        st.markdown("### 💬 Ask your data")
        st.write("Ask basic questions about totals, averages, highest and lowest values, missing values and duplicates.")
    with feature_cols[1]:
        st.markdown("### 🗃️ SQL playground")
        st.write("Run a single read-only SELECT or WITH query against your uploaded dataset using DuckDB.")
    with feature_cols[2]:
        st.markdown("### 📥 Export reports")
        st.write("Download cleaned data as CSV, an analysis report as text, or a multi-sheet Excel workbook.")
    st.caption("Note: Ask Your Data currently uses transparent Python rules, not a connected large language model. Missing values are reported, not automatically filled. PDF export and automatic AI-generated answers are not included in this version yet.")
    st.stop()

try:
    raw = load_file(uploaded.getvalue(), uploaded.name)
except Exception as exc:
    st.error(f"Could not read this file: {exc}")
    st.stop()

if raw.empty:
    st.warning("The uploaded file has no data rows.")
    st.stop()

df, duplicates_removed = clean_data(raw)
if df.empty or len(df.columns) == 0:
    st.error("No usable data remains after removing completely empty rows/columns.")
    st.stop()

st.success(f"Loaded {uploaded.name} successfully.")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Rows", f"{len(df):,}")
k2.metric("Columns", f"{len(df.columns):,}")
k3.metric("Duplicates removed", f"{duplicates_removed:,}")
k4.metric("Missing cells", f"{int(df.isna().sum().sum()):,}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📋 Data Preview", "🧹 Data Quality", "📈 Analysis & Charts", "💬 Ask Your Data", "🧾 SQL & Reports"]
)

with tab1:
    st.subheader("Cleaned data preview")
    st.dataframe(df.head(500), use_container_width=True)
    st.caption("Showing up to the first 500 rows in the preview.")

with tab2:
    st.subheader("Data quality report")
    quality = pd.DataFrame({
        "Data type": df.dtypes.astype(str),
        "Missing values": df.isna().sum(),
        "Missing %": (df.isna().mean() * 100).round(2),
        "Unique values": df.nunique(dropna=True)
    })
    st.dataframe(quality, use_container_width=True)
    st.write(f"Exact duplicate rows removed during cleaning: **{duplicates_removed:,}**")
    st.warning("Cleaning is conservative: missing values are reported, not automatically filled or deleted. Review before using results for business decisions.")

with tab3:
    st.subheader("Automatic numeric summary")
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        st.info("No numeric columns were detected.")
    else:
        st.dataframe(numeric.describe().T, use_container_width=True)
        chart_type = st.selectbox("Chart type", ["Bar chart", "Line chart", "Histogram", "Scatter plot"])
        if chart_type == "Histogram":
            xcol = st.selectbox("Numeric column", numeric.columns)
            fig = px.histogram(df, x=xcol, title=f"Distribution of {xcol}")
        elif chart_type == "Scatter plot":
            if len(numeric.columns) < 2:
                st.info("Scatter plot needs at least two numeric columns.")
                fig = None
            else:
                xcol = st.selectbox("X axis", numeric.columns, key="scatter_x")
                y_options = [c for c in numeric.columns if c != xcol]
                ycol = st.selectbox("Y axis", y_options, key="scatter_y")
                fig = px.scatter(df, x=xcol, y=ycol, title=f"{ycol} vs {xcol}")
        else:
            category_cols = list(df.select_dtypes(exclude="number").columns)
            if category_cols:
                xcol = st.selectbox("Category / X axis", category_cols)
                ycol = st.selectbox("Value / Y axis", numeric.columns)
                grouped = df.groupby(xcol, dropna=False)[ycol].sum().reset_index().head(30)
                fig = px.bar(grouped, x=xcol, y=ycol, title=f"{ycol} by {xcol}") if chart_type == "Bar chart" else px.line(grouped, x=xcol, y=ycol, title=f"{ycol} by {xcol}")
            else:
                st.info("A category/text column is needed for this chart type.")
                fig = None
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Ask questions about your dataset")
    st.caption("This free starter uses transparent Python rules, not a large language model. It will not invent answers.")
    question = st.text_input("Your question", placeholder="Example: What is total sales?")
    if st.button("Analyze question"):
        if question.strip():
            st.markdown(answer_question(question, df))
        else:
            st.warning("Type a question first.")
    st.markdown("**Try these questions:**")
    st.write("- What is total sales?")
    st.write("- What is the average profit?")
    st.write("- Which value is highest?")
    st.write("- Show missing values")
    st.write("- How many duplicates are there?")

with tab5:
    st.subheader("Read-only SQL playground")
    st.caption("Table name: data. Only a single SELECT or WITH query is allowed. Do not include destructive commands.")
    sql = st.text_area("SQL query", value="SELECT * FROM data LIMIT 10", height=120)
    if st.button("Run SQL"):
        cleaned_sql = sql.strip()
        first = cleaned_sql.split(None, 1)[0].lower() if cleaned_sql else ""
        forbidden = ["insert", "update", "delete", "drop", "alter", "create", "attach", "copy", "export", "install", "load", "pragma", "call", "execute"]
        if first not in ("select", "with") or ";" in cleaned_sql or any(re.search(rf"\b{k}\b", cleaned_sql.lower()) for k in forbidden):
            st.error("Only one read-only SELECT/WITH query is permitted.")
        else:
            try:
                con = duckdb.connect(database=":memory:")
                con.register("data", df)
                result = con.execute(cleaned_sql).df()
                st.dataframe(result, use_container_width=True)
                st.download_button("Download SQL result as CSV", result.to_csv(index=False).encode("utf-8"), "sql_result.csv", "text/csv")
                con.close()
            except Exception as exc:
                st.error(f"SQL error: {exc}")

st.divider()
st.subheader("Download your outputs")
csv_bytes = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download cleaned CSV", csv_bytes, "cleaned_data.csv", "text/csv")

insights = make_insights(df)
report = [
    "MY AI DATA ANALYST — DATA REPORT",
    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    f"Source file: {uploaded.name}",
    f"Rows: {len(df)} | Columns: {len(df.columns)}",
    f"Exact duplicates removed: {duplicates_removed}",
    "",
    "AUTOMATIC INSIGHTS",
    *[f"- {item}" for item in insights],
    "",
    "DATA QUALITY BY COLUMN",
    quality.to_string() if 'quality' in locals() else pd.DataFrame({
        "Missing values": df.isna().sum(),
        "Data type": df.dtypes.astype(str)
    }).to_string()
]
st.download_button("⬇️ Download text analysis report", "\n".join(report).encode("utf-8"), "analysis_report.txt", "text/plain")

try:
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Cleaned Data", index=False)
        pd.DataFrame(insights, columns=["Insight"]).to_excel(writer, sheet_name="Insights", index=False)
        pd.DataFrame({"Column": df.columns, "Missing Values": df.isna().sum().values}).to_excel(writer, sheet_name="Data Quality", index=False)
    st.download_button("⬇️ Download Excel workbook", excel_buffer.getvalue(), "data_analysis_output.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
except Exception as exc:
    st.info(f"Excel export is unavailable: {exc}")

st.caption("Always review cleaning decisions, formulas, SQL results and business recommendations before sharing a report.")
