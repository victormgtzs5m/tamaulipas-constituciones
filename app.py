import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from plotly.subplots import make_subplots
import pandas as pd
import sqlite3
import requests
import os

sharepoint_url = "https://c5mdelgolfo.sharepoint.com/:u:/s/TamaulipasConstituciones/IQBUYd6tezWuSYlWmqcveGcZAbrlV3uCJRbSdCrMn7uz2lM?download=1"

if not os.path.exists("produccion.db"):

    response = requests.get(sharepoint_url)

    with open("produccion.db", "wb") as f:
        f.write(response.content)

conn = sqlite3.connect("produccion.db")

df = pd.read_sql_query(
    'SELECT * FROM "produccion"',
    conn
)

st.set_page_config(
    page_title="Visualizador de Producción",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    "<h1 style='font-size:30px; font-weight:700;'>Campo Tamaulipas-Constituciones Producción</h1>",
    unsafe_allow_html=True
)

# -----------------------------
# Configuración de columnas
# -----------------------------
COL_POZO = "TERMINACION"
COL_FECHA = "FECHA"
COL_YAC = "Yacimiento"
COL_DIAS = "DIAS"
COL_QO = "Qo (bpd)"
COL_QW = "Qw (bpd)"
COL_QG = "Qg (mpcd)"
COL_NP = "Npx (mbl)"
COL_WP = "Wpx (mbl)"
COL_GP = "Gpx (mmpc)"
COL_WC = "%Agua"
COL_RGA = "RGA (pc/bl)"
COL_NPT = "ACEITE"
COL_WPT = "AGUA"
COL_GPT = "GAS"

REQUIRED_COLS = [
    COL_POZO, COL_FECHA, COL_YAC,
    COL_QO, COL_QW, COL_QG,
    COL_NP, COL_WP, COL_GP
]

# -----------------------------
# Estilo visual
# -----------------------------
st.markdown("""
<style>
    .main {background-color: #f7f9fb;}

    [data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e6e9ef;
        padding: 2px 6px;
        border-radius: 6px;
        min-height: 55px;
        box-shadow: 0 2px 10px rgba(20, 31, 56, 0.05);
    }

    [data-testid="stMetricLabel"] {
        font-size: 12px;
        font-weight: bold;
    }

    [data-testid="stMetricValue"] {
        font-size: 16px;
        font-weight: bold;
    }

    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #17202A;
        margin-top: 0.4rem;
        margin-bottom: 0.4rem;
    }

    .small-note {
        color: #697386;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Lectura de datos
# -----------------------------
@st.cache_data(show_spinner="Cargando base de datos...")
def load_data(uploaded_file=None):
    source = uploaded_file if uploaded_file is not None else Path("Base.xlsx")
    df = pd.read_excel(source, sheet_name="TMPL-CONST")

    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas en la base: {missing}")

    df[COL_FECHA] = pd.to_datetime(df[COL_FECHA], errors="coerce")
    df = df.dropna(subset=[COL_POZO, COL_FECHA])

    numeric_cols = [
        COL_QO, COL_QW, COL_QG,
        COL_NP, COL_WP, COL_GP,
        COL_DIAS, COL_WC, COL_RGA
    ]

    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.sort_values([COL_POZO, COL_FECHA]).reset_index(drop=True)

    return df

# -----------------------------
# Completar fechas mensuales
# -----------------------------
def completar_fechas_mensuales(data):
    data = data.copy()
    data[COL_FECHA] = pd.to_datetime(data[COL_FECHA])

    if data.empty:
        return data

    pozo = data[COL_POZO].iloc[0]
    yacimiento = data[COL_YAC].iloc[0] if COL_YAC in data.columns else ""

    fecha_min = data[COL_FECHA].min()
    fecha_max = data[COL_FECHA].max()

    fechas_completas = pd.date_range(
        start=fecha_min,
        end=fecha_max,
        freq="MS"
    )

    data = data.set_index(COL_FECHA)
    data = data.reindex(fechas_completas)

    data.index.name = COL_FECHA
    data = data.reset_index()

    data[COL_POZO] = data[COL_POZO].fillna(pozo)

    if COL_YAC in data.columns:
        data[COL_YAC] = data[COL_YAC].fillna(yacimiento)

    columnas_gastos = [COL_QO, COL_QW, COL_QG, COL_DIAS, COL_WC, COL_RGA]
    columnas_acumuladas = [COL_NP, COL_WP, COL_GP]

    for col in columnas_gastos:
        if col in data.columns:
            data[col] = data[col].fillna(0)

    for col in columnas_acumuladas:
        if col in data.columns:
            data[col] = data[col].ffill().fillna(0)

    return data

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.title("🛢️ Producción")
    st.caption("Visualizador mensual por pozo y yacimiento")
    uploaded = st.file_uploader("Cargar otra base Excel", type=["xlsx"])

try:
    df = load_data(uploaded)
except Exception as e:
    st.error(f"No fue posible cargar la base: {e}")
    st.stop()

# -----------------------------
# Filtros
# -----------------------------
with st.sidebar:
    yacs = sorted(df[COL_YAC].dropna().astype(str).unique())
    yac_sel = st.multiselect("Yacimiento", yacs, default=yacs)

    df_yac = df[df[COL_YAC].astype(str).isin(yac_sel)] if yac_sel else df.copy()
    pozos = sorted(df_yac[COL_POZO].dropna().astype(str).unique())

    pozo_sel = st.selectbox("Pozo / Terminación", pozos)

    min_date = df_yac[COL_FECHA].min().date()
    max_date = df_yac[COL_FECHA].max().date()

    date_range = st.date_input(
        "Rango de fechas",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    suavizado = st.slider(
        "Suavizado móvil mensual",
        min_value=1,
        max_value=12,
        value=1,
        help="Promedio móvil para suavizar curvas de gasto."
    )

if isinstance(date_range, tuple) and len(date_range) == 2:
    f_ini, f_fin = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
else:
    f_ini, f_fin = df_yac[COL_FECHA].min(), df_yac[COL_FECHA].max()

mask = (
    (df_yac[COL_POZO].astype(str) == str(pozo_sel)) &
    (df_yac[COL_FECHA] >= f_ini) &
    (df_yac[COL_FECHA] <= f_fin)
)

dfp = df_yac.loc[mask].copy()

if dfp.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# Completar fechas faltantes
dfp = completar_fechas_mensuales(dfp)

# =========================
# ACUMULADAS REALES DEL POZO
# =========================

dfp[COL_NPT] = dfp[COL_NPT].fillna(0).cumsum() * 6.2898 /1000
dfp[COL_WPT] = dfp[COL_WPT].fillna(0).cumsum() * 6.2898 / 1000
dfp[COL_GPT] = dfp[COL_GPT].fillna(0).cumsum() * 6.2898 / 1000


# Fechas reales con producción
prod_total = dfp[[COL_QO, COL_QW, COL_QG]].fillna(0).sum(axis=1)
df_prod = dfp[prod_total > 0]

if df_prod.empty:
    df_prod = dfp.copy()

first_row = df_prod.iloc[0]
last_row = df_prod.iloc[-1]

# Suavizado
for c in [COL_QO, COL_QW, COL_QG]:
    dfp[f"{c}_suav"] = dfp[c].rolling(suavizado, min_periods=1).mean()

# -----------------------------
# Encabezado
# -----------------------------
st.markdown(
    f"<span class='small-note'>Pozo seleccionado: <b>{pozo_sel}</b> | "
    f"Yacimiento: <b>{first_row.get(COL_YAC, '')}</b></span>",
    unsafe_allow_html=True
)

# -----------------------------
# KPIs principales
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Fecha inicio producción", first_row[COL_FECHA].strftime("%d/%m/%Y"))
col2.metric("Última fecha con producción", last_row[COL_FECHA].strftime("%d/%m/%Y"))
col3.metric("Primer Qo", f"{first_row[COL_QO]:,.1f} bpd")
col4.metric("Último Qo", f"{last_row[COL_QO]:,.1f} bpd")

col5, col6, col7, col8 = st.columns(4)

col5.metric("Último Qw", f"{last_row[COL_QW]:,.1f} bpd")
col6.metric("Último Qg", f"{last_row[COL_QG]:,.1f} mpcd")
col7.metric(
    "Np total del pozo",
    f"{dfp[COL_NPT].iloc[-1]:,.2f} mbl"
)
col8.metric("Wp / Gp", f"{dfp[COL_WPT].iloc[-1]:,.2f} mbl / {dfp[COL_GPT].iloc[-1]:,.2f} mmpc")

# -----------------------------
# Funciones de gráficos
# -----------------------------

def time_series_chart(data, cols, title, ytitle):

    fig = make_subplots(
        specs=[[{"secondary_y": True}]]
    )

    for col in cols:

        visible_col = f"{col}_suav" if f"{col}_suav" in data.columns else col

        # =========================
        # ACEITE -> AREA
        # =========================
        if col == COL_QO:

            trace = go.Scatter(
                x=data[COL_FECHA],
                y=data[visible_col],
                mode="lines",
                name="Qo (bpd)",
                line=dict(
                    width=3,
                    color="#27AE60"
                ),
                fill="tozeroy",
                fillcolor="rgba(39,174,96,0.25)",
                hovertemplate=
                    "<b>%{x|%d/%m/%Y}</b><br>" +
                    "Qo: %{y:,.2f} bpd<extra></extra>"
            )

            fig.add_trace(trace, secondary_y=False)

        # =========================
        # AGUA
        # =========================
        elif col == COL_QW:

            trace = go.Scatter(
                x=data[COL_FECHA],
                y=data[visible_col],
                mode="lines+markers",
                name="Qw (bpd)",
                line=dict(
                    width=2,
                    color="#0000FF"
                ),
                marker=dict(size=5),
                hovertemplate=
                    "<b>%{x|%d/%m/%Y}</b><br>" +
                    "Qw: %{y:,.2f} bpd<extra></extra>"
            )

            fig.add_trace(trace, secondary_y=False)

        # =========================
        # GAS -> EJE SECUNDARIO
        # =========================
        elif col == COL_QG:

            trace = go.Scatter(
                x=data[COL_FECHA],
                y=data[visible_col],
                mode="lines+markers",
                name="Qg (mpcd)",
                line=dict(
                    width=2,
                    color="#FF0000"
                ),
                marker=dict(size=5),
                hovertemplate=
                    "<b>%{x|%d/%m/%Y}</b><br>" +
                    "Qg: %{y:,.2f} mpcd<extra></extra>"
            )

            fig.add_trace(trace, secondary_y=True)

        # =========================
        # OTROS
        # =========================
        else:

            trace = go.Scatter(
                x=data[COL_FECHA],
                y=data[visible_col],
                mode="lines+markers",
                name=col,
                line=dict(width=2),
                marker=dict(size=5)
            )

            fig.add_trace(trace, secondary_y=False)

    # =========================
    # LAYOUT
    # =========================
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(
                size=18,
                family="Arial",
                color="#17202A"
            )
        ),

        template="plotly_white",

        hovermode="x unified",

        height=430,

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),

        margin=dict(
            l=30,
            r=30,
            t=60,
            b=35
        ),

        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    # =========================
    # EJE X
    # =========================
    fig.update_xaxes(
        title_text="Fecha",
        showgrid=True,
        gridcolor="#EAECEE",
        zeroline=False,
        tickformat="%Y"
    )

    # =========================
    # EJE IZQUIERDO
    # =========================
    fig.update_yaxes(
        title_text="Aceite / Agua (bpd)",
        secondary_y=False,
        showgrid=True,
        gridcolor="#EAECEE",
        zeroline=False,
        separatethousands=True
    )

    # =========================
    # EJE DERECHO
    # =========================
    fig.update_yaxes(
        title_text="Gas (mpcd)",
        secondary_y=True,
        showgrid=False,
        zeroline=False,
        separatethousands=True
    )

    fig.update_traces(
        connectgaps=True
    )

    return fig

def cumulative_chart(data):

    fig = make_subplots(
        specs=[[{"secondary_y": True}]]
    )

    colores = {
        COL_NPT: "#008000",
        COL_WPT: "#0000FF",
        COL_GPT: "#FF0000"
    }

    nombres = {
        COL_NPT: "Np (mbl)",
        COL_WPT: "Wp (mbl)",
        COL_GPT: "Gp (mmpc)"
    }

    for col in [COL_NPT, COL_WPT, COL_GPT]:

        trace = go.Scatter(
            x=data[COL_FECHA],
            y=data[col],
            mode="lines",
            name=nombres.get(col, col),
            line=dict(
                width=3,
                color=colores.get(col, None)
            ),
            hovertemplate=
                "<b>%{x|%d/%m/%Y}</b><br>" +
                "%{y:,.2f}<extra></extra>"
        )

        # =========================
        # GAS EN EJE SECUNDARIO
        # =========================
        if col == COL_GPT:
            fig.add_trace(trace, secondary_y=True)

        else:
            fig.add_trace(trace, secondary_y=False)

    # =========================
    # LAYOUT
    # =========================
    fig.update_layout(
        title=dict(
            text="Producción acumulada de aceite, agua y gas",
            font=dict(
                size=18,
                family="Arial",
                color="#17202A"
            )
        ),

        hovermode="x unified",

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),

        margin=dict(
            l=30,
            r=25,
            t=60,
            b=35
        ),

        height=430,

        template="plotly_white",

        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    # =========================
    # EJE X
    # =========================
    fig.update_xaxes(
        title_text="Fecha",
        showgrid=True,
        gridcolor="#EAECEE",
        zeroline=False,
        tickformat="%Y"
    )

    # =========================
    # EJE IZQUIERDO
    # =========================
    fig.update_yaxes(
        title_text="Np / Wp (mbl)",
        secondary_y=False,
        showgrid=True,
        gridcolor="#EAECEE",
        zeroline=False,
        separatethousands=True
    )

    # =========================
    # EJE DERECHO
    # =========================
    fig.update_yaxes(
        title_text="Gp (mmpc)",
        secondary_y=True,
        showgrid=False,
        zeroline=False,
        separatethousands=True
    )

    return fig

# -----------------------------
# Gráficos por pozo
# -----------------------------
st.markdown("<div class='section-title'>Comportamiento mensual del pozo</div>", unsafe_allow_html=True)

#left, right = st.columns(2)

#with left:
 #   st.plotly_chart(
 #       time_series_chart(
 #           dfp,
 #           [COL_QO, COL_QW, COL_QG],
 #           "Gastos de producción",
 #           "Gasto"
 #       ),
 #       use_container_width=True
 #   )

#with right:
#    st.plotly_chart(
#        cumulative_chart(dfp),
#        use_container_width=True
#    )

#left2, right2 = st.columns(2)

#with left2:
#    if COL_WC in dfp.columns:
#        fig_wc = time_series_chart(dfp, [COL_WC], "Corte de agua", "% agua")
#        st.plotly_chart(fig_wc, use_container_width=True)
#
#with right2:
#    if COL_RGA in dfp.columns:
#        fig_rga = time_series_chart(dfp, [COL_RGA], "Relación gas-aceite", "pc/bl")
#        st.plotly_chart(fig_rga, use_container_width=True)

st.plotly_chart(
    time_series_chart(
        dfp,
        [COL_QO, COL_QW, COL_QG],
        "Gastos de producción",
        "Gasto"
    ),
    use_container_width=True
)

st.plotly_chart(
    cumulative_chart(dfp),
    use_container_width=True
)

# -----------------------------
# Comparativo por yacimiento / pozos
# -----------------------------


# -----------------------------
# Tabla descargable
# -----------------------------
st.markdown("<div class='section-title'>Datos filtrados del pozo</div>", unsafe_allow_html=True)

show_cols = [
    c for c in [
        COL_POZO, COL_FECHA, COL_YAC, COL_DIAS,
        COL_QO, COL_QW, COL_QG,
        COL_NP, COL_WP, COL_GP,
        COL_WC, COL_RGA
    ]
    if c in dfp.columns
]

st.dataframe(
    dfp[show_cols],
    use_container_width=True,
    hide_index=True
)

csv = dfp[show_cols].to_csv(index=False).encode("utf-8-sig")

st.download_button(
    "Descargar datos filtrados en CSV",
    data=csv,
    file_name=f"produccion_{pozo_sel}.csv",
    mime="text/csv"
)

st.caption(
    "Desarrollado en Python + Streamlit. "
    "Puedes modificar app.py para agregar mapas, pronósticos, curvas de declinación o conexión directa a Access."
)