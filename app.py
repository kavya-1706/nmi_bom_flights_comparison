# import streamlit as st
# import pandas as pd

# # csv files
# df1 = pd.read_csv("csv_data/google_flight_bom.csv")
# df2 = pd.read_csv("csv_data/google_flight_nmi.csv")


# # data cleaning:

# def clean(df):

#     # copy
#     df = df.copy()

#     # Price
#     df["Price"] = (
#         df["Price"]
#         .str.replace("₹", "", regex=False)
#         .str.replace(",", "", regex=False)
#     )

#     df["Price"] = pd.to_numeric(
#         df["Price"],
#         errors="coerce"
#     )

#     # Route
#     df[["Source", "Destination"]] = (
#         df["Route"]
#         .str.split("–", expand=True)
#     )

#     # Duration → decimal hours
#     duration = (
#         df["Duration"]
#         .str.replace("hr", "hours")
#         .str.replace("min", "minutes")
#     )

#     df["Duration"] = (
#         pd.to_timedelta(
#             duration,
#             errors="coerce"
#         )
#         .dt.total_seconds()
#         / 3600
#     )

#     df["Duration"] = (
#         df["Duration"]
#         .round(2)
#     )

#     # CO2
#     df["CO2_Emissions"] = (
#         df["CO2_Emissions"]
#         .str.extract(r"(\d+)")
#         .iloc[:, 0]
#     )

#     df["CO2_Emissions"] = (
#         pd.to_numeric(
#             df["CO2_Emissions"],
#             errors="coerce"
#         )
#     )

#     # Emissions change
#     df["Emissions_Change"] = (
#         df["Emissions_Change"]
#         .str.extract(r"([+-]?\d+)")
#         .iloc[:, 0]
#     )

#     df["Emissions_Change"] = (
#         pd.to_numeric(
#             df["Emissions_Change"],
#             errors="coerce"
#         )
#     )

#     # Drop unwanted
#     df = df.drop(
#         columns=[
#             "Route",
#             "Unnamed: 0"
#         ],
#         errors="ignore"
#     )

#     return df
# df1_new = clean(df1)
# df2_new = clean(df2)


# st.title("Flight data comparison: BOM and NMI")
# tab1,tab2= st.tabs([
#     "Data", "Exploratory Data Analysis"
# ])
# with tab1:
    
#     st.subheader("BOM flights")
#     st.dataframe(
#         df1,
#         use_container_width=True
#     )
#     st.subheader("NMI flights")
#     st.dataframe(
#         df2,
#         use_container_width=True
#     )
# with tab2:
#     st.subheader("Exploratory Data Analysis")
#     st.subheader("Cleaned data:")
#     st.dataframe(
#         df1_new,
#         use_container_width=True
#     )



####### start
import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go

#  Set page configuration
st.set_page_config(page_title="Flight Data EDA Dashboard", layout="wide", page_icon="✈️")

# # --- DATA CLEANING FUNCTIONS (From your Jupyter Notebook) ---
# @st.cache_data
def load_and_clean_nmi():
    df = pd.read_csv("csv_data/google_flight_nmi.csv")
    df["Price"] = pd.to_numeric(df["Price"].astype(str).str.replace("₹", "", regex=False).str.replace(",", "", regex=False), errors="coerce")
    df[["Source", "Destination"]] = df["Route"].str.split("–", expand=True)
    
    duration = df["Duration"].astype(str).str.replace("hr", "hours").str.replace("min", "minutes")
    df["Duration"] = (pd.to_timedelta(duration, errors="coerce").dt.total_seconds() / 3600).round(2)
    
    df["CO2_Emissions"] = pd.to_numeric(df["CO2_Emissions"].astype(str).str.extract(r"(\d+)").iloc[:, 0], errors="coerce")
    df["Emissions_Change"] = pd.to_numeric(df["Emissions_Change"].astype(str).str.extract(r"([+-]?\d+)").iloc[:, 0], errors="coerce")
    df["Stops"] = df["Stops"].map({"Nonstop": 0, "1 stop": 1, "2 stops": 2})
    
    def split_layover(x):
        if pd.isna(x) or "0 minute" in str(x).lower():
            return pd.Series([0.0, "NO_LOC"])
        hr = re.search(r"(\d+)\s*hr", str(x))
        mins = re.search(r"(\d+)\s*min", str(x))
        h = int(hr.group(1)) if hr else 0
        m = int(mins.group(1)) if mins else 0
        decimal = round(h + m/60, 2)
        loc = re.search(r"\b([A-Z]{3})\b$", str(x))
        location = loc.group(1) if loc else "NO_LOC"
        return pd.Series([decimal, location])

    df[["Layover_Time", "Layover_Location"]] = df["Layover_Time_Location"].apply(split_layover)
    
    dep = pd.to_datetime(df["Departure_Time"].astype(str).str.strip(), format="%I:%M %p", errors="coerce")
    arr = pd.to_datetime(df["Arrival_Time"].astype(str).str.strip(), format="%I:%M %p", errors="coerce")
    df["Departure_Hour"] = dep.dt.hour + dep.dt.minute / 60
    df["Arrival_Hour"] = arr.dt.hour + arr.dt.minute / 60
    
    return df.drop(columns=["Route", "Unnamed: 0", "Departure_Time", "Arrival_Time", "Layover_Time_Location"], errors="ignore")

# @st.cache_data
def load_and_clean_bom(df_nmi_reference):
    df = pd.read_csv("csv_data/google_flight_bom.csv")
    df["Price"] = pd.to_numeric(df["Price"].astype(str).str.replace("₹", "", regex=False).str.replace(",", "", regex=False), errors="coerce")
    df[["Source", "Destination"]] = df["Route"].str.split("–", expand=True)
    
    # Matching duration behavior directly using df_nmi's lengths/indices as per your notebook setup safely
    df["Duration"] = df_nmi_reference["Duration"].round(2)
    
    df["CO2_Emissions"] = pd.to_numeric(df["CO2_Emissions"].astype(str).str.extract(r"(\d+)").iloc[:, 0], errors="coerce")
    df["Emissions_Change"] = pd.to_numeric(df["Emissions_Change"].astype(str).str.extract(r"([+-]?\d+)").iloc[:, 0], errors="coerce")
    df["Stops"] = df["Stops"].map({"Nonstop": 0, "1 stop": 1, "2 stops": 2})
    
    def split_layover(x):
        if pd.isna(x) or "0 minute" in str(x).lower():
            return pd.Series([0.0, "NO_LOC"])
        hr = re.search(r"(\d+)\s*hr", str(x))
        mins = re.search(r"(\d+)\s*min", str(x))
        h = int(hr.group(1)) if hr else 0
        m = int(mins.group(1)) if mins else 0
        decimal = round(h + m/60, 2)
        loc = re.search(r"\b([A-Z]{3})\b$", str(x))
        location = loc.group(1) if loc else "NO_LOC"
        return pd.Series([decimal, location])

    df[["Layover_Time", "Layover_Location"]] = df["Layover_Time_Location"].apply(split_layover)
    
    dep = pd.to_datetime(df["Departure_Time"].astype(str).str.strip(), format="%I:%M %p", errors="coerce")
    arr = pd.to_datetime(df["Arrival_Time"].astype(str).str.strip(), format="%I:%M %p", errors="coerce")
    df["Departure_Hour"] = dep.dt.hour + dep.dt.minute / 60
    df["Arrival_Hour"] = arr.dt.hour + arr.dt.minute / 60
    
    return df.drop(columns=["Route", "Unnamed: 0", "Departure_Time", "Arrival_Time", "Layover_Time_Location"], errors="ignore")

df_nmi = load_and_clean_nmi()
df_bom = load_and_clean_bom(df_nmi)


st.title("Flight Data Analytics: NMI vs BOM Airport Comparison")
st.markdown("An analysis application to filter, visualize, and benchmark flight networks.")

tab1, tab2, tab3, tab4 = st.tabs([
    "Airport Comparison", 
    "NMI Flights EDA", 
    "BOM Flights EDA", 
    "Data"
])

with tab1:
    st.header("Comparative Metrics Benchmark")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Flights Analyzed", value=f"NMI: {len(df_nmi)} | BOM: {len(df_bom)}")
    with col2:
        st.metric(label="Average Ticket Price", value=f"₹{df_nmi['Price'].mean():.2f}", delta=f"BOM: ₹{df_bom['Price'].mean():.2f}", delta_color="inverse")
    with col3:
        st.metric(label="Avg CO₂ Emissions", value=f"{df_nmi['CO2_Emissions'].mean():.1f} kg", delta=f"BOM: {df_bom['CO2_Emissions'].mean():.1f} kg", delta_color="inverse")
        
    st.markdown("---")
    st.subheader("Aggregated Flight Volume by Connected Airports")
    
    from_nmi = df_nmi[df_nmi["Source"] == "NMI"].groupby("Destination").size().rename("Flights from NMI")
    to_nmi = df_nmi[df_nmi["Destination"] == "NMI"].groupby("Source").size().rename("Flights to NMI")
    flights_nmi = pd.concat([to_nmi, from_nmi], axis=1).fillna(0).astype(int).reset_index().rename(columns={"index": "Airport"})
    flights_nmi["Airport Source Group"] = "NMI Hub Network"

    from_bom = df_bom[df_bom["Source"] == "BOM"].groupby("Destination").size().rename("Flights from BOM")
    to_bom = df_bom[df_bom["Destination"] == "BOM"].groupby("Source").size().rename("Flights to BOM")
    flights_bom = pd.concat([to_bom, from_bom], axis=1).fillna(0).astype(int).reset_index().rename(columns={"index": "Airport"})
    flights_bom["Airport Source Group"] = "BOM Hub Network"

    # Merge for a shared Plotly representation
    combined_destinations = pd.merge(flights_nmi, flights_bom, on="Airport", how="outer").fillna(0)
    
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(x=combined_destinations["Airport"], y=combined_destinations["Flights from NMI"], name="Departures from NMI", marker_color="#2ec4b6"))
    fig_comp.add_trace(go.Bar(x=combined_destinations["Airport"], y=combined_destinations["Flights from BOM"], name="Departures from BOM", marker_color="#ff9f1c"))
    fig_comp.update_layout(barmode='group', xaxis_title="Connected Domestic Airports", yaxis_title="Flight Route Frequencies")
    st.plotly_chart(fig_comp, use_container_width=True)

# --- TAB 2: NMI EDA ---
with tab2:
    st.header("Exploratory Insights — Navi Mumbai International (NMI)")
    
    col_nmi_1, col_nmi_2 = st.columns(2)
    with col_nmi_1:
        st.subheader("Price Metrics Matrix by Active Airlines")
        fig_nmi_box = px.box(df_nmi, x="Airline", y="Price", color="Airline", points="all", color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_nmi_box, use_container_width=True)
        
    with col_nmi_2:
        st.subheader("CO₂ Footprint Breakdown")
        fig_nmi_scatter = px.scatter(df_nmi, x="Duration", y="CO2_Emissions", color="Airline", size="Price", hover_data=["Source", "Destination"])
        st.plotly_chart(fig_nmi_scatter, use_container_width=True)

# --- TAB 3: BOM EDA ---
with tab3:
    st.header("Exploratory Insights — Chhatrapati Shivaji Maharaj International (BOM)")
    
    col_bom_1, col_bom_2 = st.columns(2)
    with col_bom_1:
        st.subheader("Price Metrics Matrix by Active Airlines")
        fig_bom_box = px.box(df_bom, x="Airline", y="Price", color="Airline", color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_bom_box, use_container_width=True)
        
    with col_bom_2:
        st.subheader("CO₂ Footprint Breakdown")
        fig_bom_scatter = px.scatter(df_bom, x="Duration", y="CO2_Emissions", color="Airline", size="Price", hover_data=["Source", "Destination"])
        st.plotly_chart(fig_bom_scatter, use_container_width=True)

# --- TAB 4: RAW DATASETS ---
with tab4:
    st.header("Datasets (web scraped from Google Flights)")
    
    st.subheader("Navi Mumbai NMI Airport")
    st.dataframe(df_nmi, use_container_width=True)
    
    st.subheader("Mumbai BOM Airport")
    st.dataframe(df_bom, use_container_width=True)

st.markdown("---")
st.markdown(
    """
    <style>
    .footer {
       width: 100%;
        background-color: #0e1117;
        color: #ff9f1c;
        text-align: center;
        padding: 10px;
        font-weight: bold;
        border-top: 1px solid #31333F;
        margin-top: 50px;
    }
    </style>
    <div class="footer">
        <p>Made by: Kavya Anil (Email: anilkavya266@gmail.com , GitHub: https://github.com/kavya-1706)</p> 
        <p>GitHub repository: https://github.com/kavya-1706/nmi_bom_flights_comparison</p>
        <p> Data from Google Flights </p>
    </div>
    """,
    unsafe_allow_html=True
)