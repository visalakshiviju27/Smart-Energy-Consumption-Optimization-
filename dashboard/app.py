import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

#---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
page_title="Smart Energy Dashboard",
page_icon="⚡",
layout="wide"
)

st.title("⚡ Smart Energy Consumption & Optimization")
st.caption(
"Analyze energy consumption patterns, identify peak periods, "
"and explore potential energy-saving opportunities."
)

#---------------- LOAD EXCEL DATASET ----------------

PROJECT_DIR = Path(file).resolve().parent.parent

possible_files = [
PROJECT_DIR / "dataset" / "Smart_Energy_Cleaned.xlsx",
PROJECT_DIR / "dataset" / "energydata_complete.xlsx",
PROJECT_DIR / "Smart_Energy_Cleaned.xlsx",
PROJECT_DIR / "energydata_complete.xlsx",
]

data_file = next((file for file in possible_files if file.exists()), None)

#Allow Excel upload if the file is not found in the repository

if data_file is not None:
try:
df = pd.read_excel(data_file, engine="openpyxl")
st.success(f"Excel dataset loaded: {data_file.name}")
except Exception as error:
st.error(f"Unable to read the Excel file: {error}")
st.stop()
except Exception as error:
st.error(f"Unable to read the Excel file: {error}")
st.stop()
else:
st.warning("Excel file not found in the dataset folder.")
uploaded_file = st.file_uploader(
"Upload your cleaned Excel dataset (.xlsx)",
type=["xlsx"]
)

if uploaded_file is None:
    st.info(
        "Upload your Excel file here, or add it to your repository's "
        "dataset folder."
    )
    st.stop()

try:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
except Exception as error:
    st.error(f"Unable to read the uploaded Excel file: {error}")
    st.stop()

---------------- VALIDATE DATA ----------------

Remove accidental spaces from column names

df.columns = df.columns.astype(str).str.strip()

if "Appliances" not in df.columns:
st.error(
"The Excel file must contain an 'Appliances' column. "
f"Available columns: {df.columns.tolist()}"
)
st.stop()

Find the date column, ignoring capitalization

date_column = next(
(col for col in df.columns if col.lower() == "date"),
None
)

if date_column is None:
st.error(
"The Excel file must contain a 'date' column. "
f"Available columns: {df.columns.tolist()}"
)
st.stop()

if date_column != "date":
df = df.rename(columns={date_column: "date"})

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["Appliances"] = pd.to_numeric(df["Appliances"], errors="coerce")

df = df.dropna(subset=["date", "Appliances"]).copy()

if df.empty:
st.error("No valid date and appliance readings were found.")
st.stop()

Create date-related columns

df["day"] = df["date"].dt.day_name()
df["hour"] = df["date"].dt.hour
df["date_only"] = df["date"].dt.date

---------------- SIDEBAR FILTERS ----------------

st.sidebar.header("🔎 Dashboard Filters")

min_date = df["date"].min().date()
max_date = df["date"].max().date()

date_range = st.sidebar.date_input(
"Select date range",
value=(min_date, max_date),
min_value=min_date,
max_value=max_date
)

if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
st.info("Please select both a start date and an end date.")
st.stop()

start_date, end_date = date_range

if start_date > end_date:
st.error("Start date must be before or equal to end date.")
st.stop()

filtered = df[
(df["date"].dt.date >= start_date)
& (df["date"].dt.date <= end_date)
].copy()

if filtered.empty:
st.warning("No records are available for the selected dates.")
st.stop()

---------------- KEY METRICS ----------------

st.subheader("📊 Energy Overview")

average_usage = filtered["Appliances"].mean()
maximum_usage = filtered["Appliances"].max()
minimum_usage = filtered["Appliances"].min()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Average Reading", f"{average_usage:.2f} Wh")
col2.metric("Maximum Reading", f"{maximum_usage:.2f} Wh")
col3.metric("Minimum Reading", f"{minimum_usage:.2f} Wh")
col4.metric("Records Analyzed", f"{len(filtered):,}")

st.caption(
"These figures summarize the Appliances readings in the dataset. "
"They should not be interpreted as total household energy consumption "
"without confirming the measurement interval and units."
)

---------------- HOURLY CONSUMPTION ----------------

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
color="Average Consumption",
color_continuous_scale="Blues",
title="Average Appliance Readings Across the Day"
)

fig_hour.update_layout(
xaxis=dict(dtick=1, title="Hour of Day"),
coloraxis_showscale=False
)

st.plotly_chart(fig_hour, use_container_width=True)

peak_row = hourly.loc[hourly["Average Consumption"].idxmax()]

st.info(
f"Peak average reading: {int(peak_row['Hour']):02d}:00 "
f"({peak_row['Average Consumption']:.2f} Wh). "
"Investigate this period to understand which activities contribute "
"to higher consumption."
)

---------------- DAILY TREND ----------------

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
title="Daily Average Appliance Readings"
)

st.plotly_chart(fig_daily, use_container_width=True)

---------------- DAY OF WEEK ----------------

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

day_usage = day_usage.rename(columns={"day": "Day"})

fig_day = px.bar(
day_usage,
x="Day",
y="Average Consumption",
color="Average Consumption",
color_continuous_scale="Teal",
title="Average Consumption by Day"
)

fig_day.update_layout(coloraxis_showscale=False)

st.plotly_chart(fig_day, use_container_width=True)

---------------- DISTRIBUTION ----------------

st.subheader("📊 Consumption Distribution")

fig_hist = px.histogram(
filtered,
x="Appliances",
nbins=30,
marginal="box",
title="Distribution of Appliance Readings"
)

st.plotly_chart(fig_hist, use_container_width=True)

---------------- TEMPERATURE ANALYSIS ----------------

if "T_out" in filtered.columns:
st.subheader("🌡️ Outside Temperature vs Consumption")

temp_df = filtered[["T_out", "Appliances"]].copy()
temp_df["T_out"] = pd.to_numeric(
    temp_df["T_out"], errors="coerce"
)
temp_df = temp_df.dropna()

if not temp_df.empty:
    fig_temp = px.scatter(
        temp_df,
        x="T_out",
        y="Appliances",
        opacity=0.5,
        title="Outside Temperature and Appliance Readings",
        labels={
            "T_out": "Outside Temperature",
            "Appliances": "Appliance Reading"
        }
    )

    st.plotly_chart(fig_temp, use_container_width=True)

    correlation = temp_df["T_out"].corr(temp_df["Appliances"])

    st.write(
        f"Correlation between outside temperature and appliance "
        f"readings: **{correlation:.3f}**"
    )

    st.caption(
        "Correlation indicates association, not necessarily causation."
    )

---------------- CORRELATION HEATMAP ----------------

st.subheader("🔗 Correlation Analysis")

numeric_df = filtered.select_dtypes(include="number")
numeric_df = numeric_df.loc[:, numeric_df.nunique() > 1]

if numeric_df.shape[1] >= 2:
corr_matrix = numeric_df.corr()

if "Appliances" in corr_matrix.columns:
    appliance_corr = (
        corr_matrix["Appliances"]
        .drop("Appliances")
        .dropna()
    )

    if not appliance_corr.empty:
        st.write("Variables most positively associated with Appliances:")

        st.dataframe(
            appliance_corr.sort_values(ascending=False)
            .head(5)
            .rename("Correlation")
            .to_frame(),
            use_container_width=True
        )

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

else:
st.info("Not enough varying numerical columns for correlation analysis.")

---------------- OPTIMIZATION RECOMMENDATIONS ----------------

st.divider()
st.subheader("💡 Energy Optimization Recommendations")

st.markdown(
"""
- Peak-hour analysis: Investigate the activities and appliances
associated with the highest average readings.
- Standby power: Check whether unused equipment can be switched off.
- Temperature-related usage: Review heating and cooling settings
where appropriate.
- Unusual readings: Investigate spikes before deciding whether they
indicate faults or normal activity.

These are potential actions to investigate, not verified energy savings.
"""

)

---------------- SIMULATED SAVING SCENARIO ----------------

st.subheader("⚙️ Energy-Saving Scenario Simulator")

reduction = st.slider(
"Assumed reduction in appliance readings (%)",
min_value=0,
max_value=50,
value=10,
step=5
)

baseline = filtered["Appliances"].mean()
simulated = baseline * (1 - reduction / 100)

col1, col2, col3 = st.columns(3)

col1.metric("Baseline Average", f"{baseline:.2f} Wh")
col2.metric("Simulated Average", f"{simulated:.2f} Wh")
col3.metric(
"Hypothetical Reduction",
f"{baseline - simulated:.2f} Wh",
delta=f"-{reduction}%"
)

st.caption(
"This is a hypothetical scenario, not a measured or guaranteed saving."
)

---------------- DOWNLOAD FILTERED EXCEL ----------------

st.subheader("⬇️ Export Filtered Data as Excel")

from io import BytesIO

excel_buffer = BytesIO()

with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
filtered.to_excel(writer, index=False, sheet_name="Filtered Energy Data")

st.download_button(
label="Download Filtered Dataset (.xlsx)",
data=excel_buffer.getvalue(),
file_name="filtered_energy_data.xlsx",
mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.caption(
"Smart Energy Consumption & Optimization | "
"Interactive Analysis Dashboard"
)
