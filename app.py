import streamlit as st
import pandas as pd

# csv files
df1 = pd.read_csv("csv_data/google_flight_bom.csv")
df2 = pd.read_csv("csv_data/google_flight_nmi.csv")


# data cleaning:

def clean(df):

    # copy
    df = df.copy()

    # Price
    df["Price"] = (
        df["Price"]
        .str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
    )

    df["Price"] = pd.to_numeric(
        df["Price"],
        errors="coerce"
    )

    # Route
    df[["Source", "Destination"]] = (
        df["Route"]
        .str.split("–", expand=True)
    )

    # Duration → decimal hours
    duration = (
        df["Duration"]
        .str.replace("hr", "hours")
        .str.replace("min", "minutes")
    )

    df["Duration"] = (
        pd.to_timedelta(
            duration,
            errors="coerce"
        )
        .dt.total_seconds()
        / 3600
    )

    df["Duration"] = (
        df["Duration"]
        .round(2)
    )

    # CO2
    df["CO2_Emissions"] = (
        df["CO2_Emissions"]
        .str.extract(r"(\d+)")
        .iloc[:, 0]
    )

    df["CO2_Emissions"] = (
        pd.to_numeric(
            df["CO2_Emissions"],
            errors="coerce"
        )
    )

    # Emissions change
    df["Emissions_Change"] = (
        df["Emissions_Change"]
        .str.extract(r"([+-]?\d+)")
        .iloc[:, 0]
    )

    df["Emissions_Change"] = (
        pd.to_numeric(
            df["Emissions_Change"],
            errors="coerce"
        )
    )

    # Drop unwanted
    df = df.drop(
        columns=[
            "Route",
            "Unnamed: 0"
        ],
        errors="ignore"
    )

    return df
df1_new = clean(df1)
df2_new = clean(df2)


st.title("Flight data comparison: BOM and NMI")
tab1,tab2= st.tabs([
    "Data", "Exploratory Data Analysis"
])
with tab1:
    
    st.subheader("BOM flights")
    st.dataframe(
        df1,
        use_container_width=True
    )
    st.subheader("NMI flights")
    st.dataframe(
        df2,
        use_container_width=True
    )
with tab2:
    st.subheader("Exploratory Data Analysis")
    st.subheader("Cleaned data:")
    st.dataframe(
        df1_new,
        use_container_width=True
    )