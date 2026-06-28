import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go

#  page config
st.set_page_config(page_title="Flight Data EDA Dashboard", layout="wide", page_icon="✈️")

# data cleaning
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
    df["Departure_Hour"] = dep.dt.hour+dep.dt.minute / 60
    df["Arrival_Hour"] = arr.dt.hour + arr.dt.minute / 60
    
    return df.drop(columns=["Route", "Unnamed: 0", "Departure_Time", "Arrival_Time", "Layover_Time_Location"], errors="ignore")

def load_and_clean_bom(df_nmi_reference):
    df = pd.read_csv("csv_data/google_flight_bom.csv")
    df["Price"] = pd.to_numeric(df["Price"].astype(str).str.replace("₹", "", regex=False).str.replace(",", "", regex=False), errors="coerce")
    df[["Source", "Destination"]] = df["Route"].str.split("–", expand=True)
    
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

# app
st.title("Flight Data Analytics: NMI vs BOM Airport Comparison")
st.markdown("An analysis application to filter, visualize, and benchmark flight networks.")

tab1,tab2 = st.tabs([
    "Airport Comparison", 
   
    "Data"
])

with tab1:
    st.header("Comparison between NMI and BOM Airports")
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] {
            font-size: 18px !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Flights Analyzed", value=f"NMI: {len(df_nmi)} | BOM: {len(df_bom)}")
    with col2:
        st.metric(label="Average Ticket Price", value=f"NMI: ₹{df_nmi['Price'].mean():.2f} | BOM: ₹{df_bom['Price'].mean():.2f}")
    with col3:
        st.metric(label="Average CO₂ Emissions", value=f"NMI: {df_nmi['CO2_Emissions'].mean():.1f} kg | BOM: {df_bom['CO2_Emissions'].mean():.1f} kg")
        
    # Count by connected airports
    st.subheader("Aggregated Flight Volume by Connected Airports")
    
    from_nmi = df_nmi[df_nmi["Source"] == "NMI"].groupby("Destination").size().rename("Flights from NMI")
    to_nmi = df_nmi[df_nmi["Destination"] == "NMI"].groupby("Source").size().rename("Flights to NMI")
    flights_nmi = pd.concat([to_nmi, from_nmi], axis=1).fillna(0).astype(int).reset_index().rename(columns={"index": "Airport"})
    flights_nmi["Airport Source Group"] = "NMI"

    from_bom = df_bom[df_bom["Source"] == "BOM"].groupby("Destination").size().rename("Flights from BOM")
    to_bom = df_bom[df_bom["Destination"] == "BOM"].groupby("Source").size().rename("Flights to BOM")
    flights_bom = pd.concat([to_bom, from_bom], axis=1).fillna(0).astype(int).reset_index().rename(columns={"index": "Airport"})
    flights_bom["Airport Source Group"] = "BOM"

        # merged
    combined_destinations = pd.merge(flights_nmi, flights_bom, on="Airport", how="outer").fillna(0)
    
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(x=combined_destinations["Airport"], y=combined_destinations["Flights from NMI"], name="Departures from NMI", marker_color="#2ec4b6"))
    fig_comp.add_trace(go.Bar(x=combined_destinations["Airport"], y=combined_destinations["Flights from BOM"], name="Departures from BOM", marker_color="#ff9f1c"))
    fig_comp.update_layout(barmode='group', xaxis_title="Domestic Airports", yaxis_title="Number of flights")
    st.plotly_chart(fig_comp, use_container_width=True)

    # Ticket price
    st.subheader("Ticket Price Comparison")
    price_df = pd.concat([
    df_nmi.assign(Airport="NMI"),
    df_bom.assign(Airport="BOM")
    ])
         # remove outliers
    q1 = price_df["Price"].quantile(0.25)
    q3 = price_df["Price"].quantile(0.75)
    iqr = q3 - q1

    filtered_df = price_df[
        (price_df["Price"] >= q1 - 1.5 * iqr) &
        (price_df["Price"] <= q3 + 1.5 * iqr)
    ]
                 # Boxplot
    fig = px.box(
        filtered_df,
        x="Airport",
        y="Price",
        color="Airport",
        points="all"
    )
            # Layout customization
    fig.update_layout(
        xaxis_title="Airport",
        yaxis_title="Ticket Price (₹)",
        height=600
    )
    mean_values = price_df.groupby("Airport")["Price"].mean().reset_index()
    fig.add_scatter(
        x=mean_values["Airport"],
        y=mean_values["Price"],
        mode="markers",
        marker=dict(color="red", size=12, symbol="circle"),
        name="Mean Price"
    )
    fig.update_layout(
        height=600,
        yaxis_title="Price (₹)"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Airlines count
    st.subheader("Airlines: NMI vs BOM")
    airline_counts = (
    pd.concat([
            df_nmi["Airline"].value_counts().rename("NMI"),
            df_bom["Airline"].value_counts().rename("BOM")
        ], axis=1)
        .fillna(0)
        .astype(int)
    )
    airline_counts = airline_counts.reset_index()
    airline_counts.columns = ["Airline", "NMI", "BOM"]
    chart_data = airline_counts.melt(
    id_vars="Airline",
    value_vars=["NMI", "BOM"],
    var_name="Airport",
    value_name="Flights"
    )
    fig = px.bar(
        chart_data,
        x="Airline",
        y="Flights",
        color="Airport",
        barmode="group"
    )
    fig.update_yaxes(range=[0, 50])  
    st.plotly_chart(fig, use_container_width=True)


    # Cheap vs expensive
    st.subheader("Cheapest vs Most Expensive Flights")
    summary = pd.DataFrame({
    "Airport": ["NMI", "BOM"],
    "Min Price": [
        df_nmi["Price"].min(),
        df_bom["Price"].min()
    ],
    "Max Price": [
        df_nmi["Price"].max(),
        df_bom["Price"].max()
    ]
    })

    fig = px.bar(
        summary,
        x="Airport",
        y=["Min Price", "Max Price"],
        barmode="group"
    )

    st.plotly_chart(fig, use_container_width=True)

   # co2
    st.subheader("CO₂ Footprint Breakdown")
    fig_nmi_scatter = px.scatter(
    df_nmi,
    x="Duration",
    y="CO2_Emissions",
    color="Airline",
    size="Price",
    hover_data=["Source", "Destination"],
    title="Navi Mumbai (NMI) — Flight Duration vs CO₂ Emissions"
    )

    fig_nmi_scatter.update_layout(
        xaxis_title="Flight Duration",
        yaxis_title="CO₂ Emissions (kg)"
    )

    st.plotly_chart(fig_nmi_scatter, use_container_width=True)
    
    
    fig_bom_scatter = px.scatter(
    df_bom,
    x="Duration",
    y="CO2_Emissions",
    color="Airline",
    size="Price",
    hover_data=["Source", "Destination"],
    title="Mumbai (BOM) — Flight Duration vs CO₂ Emissions"
    )

    fig_bom_scatter.update_layout(
        xaxis_title="Flight Duration",
        yaxis_title="CO₂ Emissions (kg)"
    )

    st.plotly_chart(fig_bom_scatter, use_container_width=True)
        
        
with tab2:
    st.header("Datasets (web scraped from Google Flights)")
    
    st.subheader("Navi Mumbai NMI Airport")
    raw_nmi = pd.read_csv("csv_data/google_flight_nmi.csv")
    raw_nmi = raw_nmi.drop(
        columns=[
            "Unnamed: 0"
        ],
        errors="ignore"
    )
    st.dataframe(raw_nmi, use_container_width=True)
    
    st.subheader("Mumbai BOM Airport")
    raw_bom = pd.read_csv("csv_data/google_flight_bom.csv")
    raw_bom = raw_bom.drop(
        columns=[
            "Unnamed: 0"
        ],
        errors="ignore"
    )
    st.dataframe(raw_bom, use_container_width=True)


st.markdown(
    """
    <style>
    .footer {
       width: 100%;
       bottom:0;
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