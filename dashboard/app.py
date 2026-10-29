import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Smart Energy Dashboard",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Smart Energy Consumption Optimization")
st.caption(
    "Explore energy usage, building performance, "
    "appliance consumption and renewable generation."
)

# Load the Excel dataset
file_path = (
    Path(__file__).resolve().parent.parent
    / "dataset"
    / "cleaned_dataset.xlsx"
)

if file_path.exists():
    df = pd.read_excel(file_path)
else:
    uploaded_file = st.file_uploader(
        "Upload cleaned_dataset.xlsx",
        type=["xlsx"]
    )
    if uploaded_file is None:
        st.info("Upload your energy consumption dataset to continue.")
        st.stop()
    df = pd.read_excel(uploaded_file)

# Validate required columns
required_columns = [
    "Timestamp",
    "Building_Type",
    "Appliance",
    "Energy_Consumption_kWh",
    "Temperature_C",
    "Occupancy_Percent",
    "Tariff_Period",
    "Renewable_Generation_kWh"
]

missing = [c for c in required_columns if c not in df.columns]

if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

# Clean and prepare data
df = df.drop_duplicates().copy()
df["Timestamp"] = pd.to_datetime(
    df["Timestamp"], errors="coerce"
)

numeric_columns = [
    "Energy_Consumption_kWh",
    "Temperature_C",
    "Occupancy_Percent",
    "Renewable_Generation_kWh"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(
    subset=[
        "Timestamp",
        "Energy_Consumption_kWh",
        "Renewable_Generation_kWh"
    ]
)

df = df[
    (df["Energy_Consumption_kWh"] >= 0)
    & (df["Renewable_Generation_kWh"] >= 0)
]

if df.empty:
    st.error("No valid energy records are available.")
    st.stop()

# Sidebar filters
st.sidebar.header("Dashboard Filters")

buildings = sorted(df["Building_Type"].dropna().unique())
selected_buildings = st.sidebar.multiselect(
    "Building Type",
    buildings,
    default=buildings
)

appliances = sorted(df["Appliance"].dropna().unique())
selected_appliances = st.sidebar.multiselect(
    "Appliance",
    appliances,
    default=appliances
)

tariffs = sorted(df["Tariff_Period"].dropna().unique())
selected_tariffs = st.sidebar.multiselect(
    "Tariff Period",
    tariffs,
    default=tariffs
)

filtered = df[
    df["Building_Type"].isin(selected_buildings)
    & df["Appliance"].isin(selected_appliances)
    & df["Tariff_Period"].isin(selected_tariffs)
].copy()

if filtered.empty:
    st.warning("No records match your selected filters.")
    st.stop()

# KPI cards
total_energy = filtered["Energy_Consumption_kWh"].sum()
total_renewable = filtered["Renewable_Generation_kWh"].sum()
average_energy = filtered["Energy_Consumption_kWh"].mean()

renewable_coverage = (
    total_renewable / total_energy * 100
    if total_energy > 0 else 0
)

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Energy (kWh)", f"{total_energy:,.2f}")
k2.metric("Renewable Generation (kWh)", f"{total_renewable:,.2f}")
k3.metric("Average Reading (kWh)", f"{average_energy:,.3f}")
k4.metric("Renewable / Consumption", f"{renewable_coverage:.1f}%")

st.divider()

# Chart 1: Energy by building
st.subheader("1. Energy Consumption by Building")

building_energy = (
    filtered.groupby("Building_Type", as_index=False)
    ["Energy_Consumption_kWh"].sum()
    .sort_values("Energy_Consumption_kWh", ascending=False)
)

fig = px.bar(
    building_energy,
    x="Building_Type",
    y="Energy_Consumption_kWh",
    color="Building_Type",
    title="Total Energy Consumption by Building",
    labels={
        "Building_Type": "Building Type",
        "Energy_Consumption_kWh": "Energy (kWh)"
    }
)
st.plotly_chart(fig, use_container_width=True)

# Chart 2: Energy by appliance
st.subheader("2. Energy Consumption by Appliance")

appliance_energy = (
    filtered.groupby("Appliance", as_index=False)
    ["Energy_Consumption_kWh"].sum()
    .sort_values("Energy_Consumption_kWh", ascending=False)
)

fig = px.bar(
    appliance_energy,
    x="Energy_Consumption_kWh",
    y="Appliance",
    orientation="h",
    title="Which Appliances Consume the Most Energy?",
    labels={
        "Energy_Consumption_kWh": "Energy (kWh)",
        "Appliance": "Appliance"
    }
)
st.plotly_chart(fig, use_container_width=True)

# Chart 3: Tariff comparison
st.subheader("3. Energy Consumption by Tariff Period")

tariff_energy = (
    filtered.groupby("Tariff_Period", as_index=False)
    ["Energy_Consumption_kWh"].sum()
)

fig = px.pie(
    tariff_energy,
    names="Tariff_Period",
    values="Energy_Consumption_kWh",
    title="Consumption Share by Tariff Period",
    hole=0.4
)
st.plotly_chart(fig, use_container_width=True)

# Chart 4: Energy over time
st.subheader("4. Energy Consumption Over Time")

daily = (
    filtered.set_index("Timestamp")
    .resample("D")["Energy_Consumption_kWh"]
    .sum()
    .reset_index()
)

fig = px.line(
    daily,
    x="Timestamp",
    y="Energy_Consumption_kWh",
    markers=True,
    title="Daily Energy Consumption Trend",
    labels={
        "Timestamp": "Date",
        "Energy_Consumption_kWh": "Energy (kWh)"
    }
)
st.plotly_chart(fig, use_container_width=True)

# Chart 5: Renewable generation versus consumption
st.subheader("5. Renewable Generation vs Energy Consumption")

energy_comparison = (
    filtered.groupby("Building_Type", as_index=False)[
        ["Energy_Consumption_kWh", "Renewable_Generation_kWh"]
    ].sum()
)

comparison_long = energy_comparison.melt(
    id_vars="Building_Type",
    var_name="Energy Type",
    value_name="Energy (kWh)"
)

fig = px.bar(
    comparison_long,
    x="Building_Type",
    y="Energy (kWh)",
    color="Energy Type",
    barmode="group",
    title="Consumption and Renewable Generation by Building"
)
st.plotly_chart(fig, use_container_width=True)

# Chart 6: Occupancy and consumption
st.subheader("6. Occupancy vs Energy Consumption")

fig = px.scatter(
    filtered.dropna(
        subset=["Occupancy_Percent", "Energy_Consumption_kWh"]
    ),
    x="Occupancy_Percent",
    y="Energy_Consumption_kWh",
    color="Building_Type",
    hover_data=["Appliance", "Timestamp"],
    title="Does Occupancy Relate to Energy Use?",
    labels={
        "Occupancy_Percent": "Occupancy (%)",
        "Energy_Consumption_kWh": "Energy (kWh)"
    }
)
st.plotly_chart(fig, use_container_width=True)

# Data table and download
with st.expander("View Filtered Dataset"):
    st.dataframe(filtered, use_container_width=True)

st.download_button(
    "Download Filtered Data as CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_energy_data.csv",
    mime="text/csv"
)

st.caption("Smart Energy Consumption Optimization | Python + Streamlit")
