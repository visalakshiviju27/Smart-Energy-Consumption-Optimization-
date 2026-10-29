import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from io import BytesIO

PAGE CONFIGURATION

st.set_page_config(
page_title="Smart Energy Dashboard",
page_icon="⚡",
layout="wide"
)

st.title("⚡ Smart Energy Consumption & Optimization")
st.caption("Analyze energy consumption and explore energy-saving opportunities.")

LOAD EXCEL DATASET

PROJECT_DIR = Path(file).resolve().parent.parent

possible_files = [
PROJECT_DIR / "dataset" / "Smart_Energy_Cleaned.xlsx",
PROJECT_DIR / "dataset" / "energydata_complete.xlsx",
PROJECT_DIR / "Smart_Energy_Cleaned.xlsx",
PROJECT_DIR / "energydata_complete.xlsx",
]

data_file = next((f for f in possible_files if f.exists()), None)

if data_file is not None:
try:
df = pd.read_excel(data_file, engine="openpyxl")
st.success("Excel dataset loaded successfully!")
except Exception as error:
st.error(f"Error reading Excel file: {error}")
st.stop()
else:
uploaded_file = st.file_uploader(
"Upload your Excel dataset (.xlsx)",
type=["xlsx"]
)

if uploaded_file is None:
    st.info("Please upload your cleaned Excel dataset to continue.")
    st.stop()

try:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
except Exception as error:
    st.error(f"Error reading uploaded Excel file: {error}")
    st.stop()

CHECK COLUMNS

df.columns = df.columns.astype(str).str.strip()

if "Appliances" not in df.columns:
st.error("Column 'Appliances' not found. Check your Excel column names.")
st.write("Available columns:", df.columns.tolist())
st.stop()

date_col = next(
(c for c in df.columns if c.lower() == "date"),
None
)

if date_col is None:
st.error("Column 'date' not found in your Excel dataset.")
st.write("Available columns:", df.columns.tolist())
st.stop()

if date_col != "date":
df = df.rename(columns={date_col: "date"})

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["Appliances"] = pd.to_numeric(df["Appliances"], errors="coerce")
df = df.dropna(subset=["date", "Appliances"]).copy()

if df.empty:
st.error("No valid data found in the Excel file.")
st.stop()

df["hour"] = df["date"].dt.hour
df["day"] = df["date"].dt.day_name()
df["date_only"] = df["date"].dt.date

SIDEBAR FILTERS

st.sidebar.header("Dashboard Filters")

min_date = df["date"].min().date()
max_date = df["date"].max().date()

date_range = st.sidebar.date_input(
"Select date range",
value=(min_date, max_date),
min_value=min_date,
max_value=max_date
)

if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
st.info("Please select both start and end dates.")
st.stop()

start_date, end_date = date_range

if start_date > end_date:
st.error("Start date must be before end date.")
st.stop()

filtered = df[
(df["date"].dt.date >= start_date)
& (df["date"].dt.date <= end_date)
].copy()

if filtered.empty:
st.warning("No data available for this date range.")
st.stop()

KEY METRICS

st.subheader("📊 Energy Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Average Reading", f"{filtered['Appliances'].mean():.2f}")
c2.metric("Maximum Reading", f"{filtered['Appliances'].max():.2f}")
c3.metric("Minimum Reading", f"{filtered['Appliances'].min():.2f}")
c4.metric("Records Analyzed", f"{len(filtered):,}")

st.caption("Readings use the units and measurement interval defined by the dataset.")

HOURLY CONSUMPTION

st.divider()
st.subheader("🕒 Average Consumption by Hour")

hourly = (
filtered.groupby("hour", as_index=False)["Appliances"]
.mean()
)
hourly.columns = ["Hour", "Average Consumption"]

fig_hour = px.bar(
hourly,
x="Hour",
y="Average Consumption",
title="Average Appliance Consumption by Hour",
color="Average Consumption",
color_continuous_scale="Blues"
)
fig_hour.update_layout(coloraxis_showscale=False, xaxis=dict(dtick=1))
st.plotly_chart(fig_hour, use_container_width=True)

peak = hourly.loc[hourly["Average Consumption"].idxmax()]
st.info(
f"Peak average consumption: {int(peak['Hour']):02d}:00 "
f"({peak['Average Consumption']:.2f})."
)

DAILY TREND

st.subheader("📈 Daily Consumption Trend")

daily = (
filtered.groupby("date_only", as_index=False)["Appliances"]
.mean()
)
daily.columns = ["Date", "Average Consumption"]

fig_daily = px.line(
daily,
x="Date",
y="Average Consumption",
markers=True,
title="Daily Average Consumption"
)
st.plotly_chart(fig_daily, use_container_width=True)

WEEKLY ANALYSIS

st.subheader("📅 Consumption by Day of the Week")

day_order = [
"Monday", "Tuesday", "Wednesday", "Thursday",
"Friday", "Saturday", "Sunday"
]

day_usage = (
filtered.groupby("day")["Appliances"]
.mean()
.reindex(day_order)
.dropna()
.rename("Average Consumption")
.reset_index()
)
day_usage.columns = ["Day", "Average Consumption"]

fig_day = px.bar(
day_usage,
x="Day",
y="Average Consumption",
title="Average Consumption by Day",
color="Average Consumption"
)
st.plotly_chart(fig_day, use_container_width=True)

DISTRIBUTION

st.subheader("📊 Consumption Distribution")

fig_hist = px.histogram(
filtered,
x="Appliances",
nbins=30,
title="Distribution of Appliance Readings",
marginal="box"
)
st.plotly_chart(fig_hist, use_container_width=True)

TEMPERATURE ANALYSIS

if "T_out" in filtered.columns:
st.subheader("🌡️ Outside Temperature vs Consumption")

temp_df = filtered[["T_out", "Appliances"]].copy()
temp_df["T_out"] = pd.to_numeric(temp_df["T_out"], errors="coerce")
temp_df = temp_df.dropna()

if not temp_df.empty:
    fig_temp = px.scatter(
        temp_df,
        x="T_out",
        y="Appliances",
        opacity=0.5,
        title="Temperature vs Appliance Consumption"
    )
    st.plotly_chart(fig_temp, use_container_width=True)

    corr = temp_df["T_out"].corr(temp_df["Appliances"])
    st.write(f"Temperature correlation: **{corr:.3f}**")

CORRELATION HEATMAP

st.subheader("🔗 Correlation Analysis")

numeric_df = filtered.select_dtypes(include="number")
numeric_df = numeric_df.loc[:, numeric_df.nunique() > 1]

if numeric_df.shape[1] >= 2:
corr_matrix = numeric_df.corr()

fig_corr = px.imshow(
    corr_matrix,
    text_auto=".2f",
    aspect="auto",
    color_continuous_scale="RdBu_r",
    zmin=-1,
    zmax=1,
    title="Correlation Heatmap"
)
st.plotly_chart(fig_corr, use_container_width=True)

OPTIMIZATION RECOMMENDATIONS

st.divider()
st.subheader("💡 Energy Optimization")

st.markdown("""

- Peak-hour analysis: Investigate why consumption is higher during peak periods.
- Standby power: Switch off unused appliances when practical.
- Temperature: Review heating and cooling settings where relevant.
- Unusual readings: Investigate unexpected spikes before taking action.

These are suggestions to investigate, not guaranteed energy savings.
""")

SAVING SCENARIO

st.subheader("⚙️ Energy-Saving Simulator")

reduction = st.slider(
"Assumed reduction in readings (%)",
min_value=0,
max_value=50,
value=10,
step=5
)

baseline = filtered["Appliances"].mean()
simulated = baseline * (1 - reduction / 100)

c1, c2, c3 = st.columns(3)
c1.metric("Baseline Average", f"{baseline:.2f}")
c2.metric("Simulated Average", f"{simulated:.2f}")
c3.metric("Hypothetical Reduction", f"{baseline - simulated:.2f}")

st.caption("This is a simulation, not a measurement of actual savings.")

DOWNLOAD FILTERED DATA AS EXCEL

st.subheader("⬇️ Download Filtered Excel Data")

excel_buffer = BytesIO()

with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
filtered.to_excel(writer, index=False, sheet_name="Energy Data")

st.download_button(
label="Download Excel File (.xlsx)",
data=excel_buffer.getvalue(),
file_name="filtered_energy_data.xlsx",
mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.caption("Smart Energy Consumption & Optimization Project")
