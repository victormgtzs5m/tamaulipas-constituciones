import pandas as pd
import plotly.express as px
import streamlit as st

pozos = [
    "C1110", "C1123", "C216", "C222", "C502", "C523", "C539",
    "C541", "C544", "C553", "C564", "C628", "T725", "T748",
    "T798", "T80", "T834", "T89", "T949", "C1179", "C549",
    "T101D", "T1062", "T799", "T822", "T902", "T903", "T94D"
]

qi = [
    47, 34, 30, 60, 210, 60, 55, 80, 60, 55, 50, 69,
    60, 256, 100, 120, 56, 60, 98, 60, 60, 60, 60,
    50, 59, 90, 120, 55
]

eur = [
    47.77, 47.90, 0.26, 6.85, 33.50, 7.23, 3.34, 26.55,
    7.67, 45.08, 7.17, 27.00, 39.00, 28.27, 26.60,
    21.83, 25.80, 32.44, 47.83, 31.60, 8.63, 7.85,
    18.83, 34.57, 19.63, 23.85, 58.40, 60.00
]

tipo = ["Reparación Mayor"] * len(pozos)

df = pd.DataFrame({
    "Pozo": pozos,
    "Qi": qi,
    "EUR": eur,
    "Tipo": tipo
})

fig = px.scatter(
    df,
    x="Qi",
    y="EUR",
    color="Tipo",
    text="Pozo",
    size="EUR",
    size_max=35,
    title="Qi vs EUR - Reparaciones Mayores Históricas"
)

fig.update_traces(
    textposition="top center"
)

fig.update_layout(
    template="plotly_white",
    xaxis_title="Gasto inicial, Qi (bpd)",
    yaxis_title="EUR (Mbbl)",
    font=dict(size=15),
    height=650
)


st.plotly_chart(fig, use_container_width=True)