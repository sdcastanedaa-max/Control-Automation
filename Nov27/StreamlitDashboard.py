import streamlit as st
import pandas as pd

st.set_page_config(page_title="Smart Hairdryer", layout="wide")

csv_path = r"C:\Users\luas1\OneDrive\Documentos\SENSE\A_CEE\Repository_ACEE\Nov27\Datasets\export_MarginalPriceDayAheadMarket_2025-11-27_16_23.csv"

# 1) Read with semicolon separator
df_price = pd.read_csv(csv_path, sep=";")

# 2) Parse datetime column
df_price["datetime"] = pd.to_datetime(
    df_price["datetime"],
    format="%Y-%m-%dT%H:%M:%S%z",
    utc=True
)

# 3) Use datetime as index (nice for plotting)
df_price = df_price.set_index("datetime")

# --- Streamlit UI ---
st.title("Smart Hairdryer")
st.write("Input your hair type, preferred drying time, and operating mode (Performance / Energy Saving).")

st.subheader("Electricity price data (first 5 rows)")
st.dataframe(df_price.head())

st.subheader("Value over time")
st.line_chart(df_price["value"])
