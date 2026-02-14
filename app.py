import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    return pd.read_parquet("data/races5.parquet")

df_all_parquet = load_data()
st.write(df_all_parquet.head())

