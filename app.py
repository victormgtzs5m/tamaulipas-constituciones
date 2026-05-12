import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3


# =============================
# CONFIGURACIÓN DE PÁGINA
# =============================
st.set_page_config(
    page_title="Visualizador de Producción",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================
# BASE DE DATOS LOCAL
# =============================
ruta_db = r"C:\Users\VMGS\OneDrive - CONSORCIO PETROLERO 5M DEL GOLFO\Escritorio\Resplado C5M\Web\producion.db"

# =============================
# COLUMNAS
# =============================
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

COL_ACEITE = "ACEITE"
COL_AGUA = "AGUA"
COL_GAS = "GAS"

REQUIRED_COLS = [
    COL_POZO, COL_FECHA, COL_YAC,
    COL_DIAS, COL_ACEITE, COL_AGUA, COL_GAS
]

# =============================
# ESTILO
# =============================
st.markdown("""
<style>
    .main {
        background-color: #f7f9fb;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        max-width: 100%;
    }

    [data-testid="stSidebar"] {
        display: none;
    }

    [data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e6e9ef;
        padding: 4px 8px;
        border-radius: 8px;
        min-height: 58px;
        box-shadow: 0 2px 10px rgba(20, 31, 56, 0.05);
    }

    [data-testid="stMetricLabel"] {
        font-size: 12px;
        font-weight: bold;
    }

    [data-testid="stMetricValue"] {
        font-size: 17px;
        font-weight: bold;
    }

    .main-title {
        font-size: 20px;
        font-weight: 700;
        color: #17202A;
        margin-top: 50px;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #697386;
        font-size: 0.95rem;
        margin-bottom: 0.8rem;
    }

    .filter-box {
        background-color: white;
        border: 1px solid #e6e9ef;
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 12px;
        box-shadow: 0 2px 10px rgba(20, 31, 56, 0.04);
    }

    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #17202A;
        margin-top: 0.6rem;
        margin-bottom: 0.4rem;
    }

    .small-note {
        color: #697386;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================
# CARGA Y CÁLCULO DE DATOS
# =============================
@st.cache_data(show_spinner="Cargando base de datos...")
def load_data():

    with sqlite3.connect(ruta_db) as conn:
        df = pd.read_sql_query('SELECT * FROM "produccion"', conn)

    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas en la base: {missing}")

    df[COL_FECHA] = pd.to_datetime(df[COL_FECHA], errors="coerce", dayfirst=True)
    df = df.dropna(subset=[COL_POZO, COL_FECHA])

    for c in [COL_DIAS, COL_ACEITE, COL_AGUA, COL_GAS]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    df = df.sort_values([COL_POZO, COL_FECHA]).reset_index(drop=True)

    df[COL_DIAS] = df[COL_DIAS].replace(0, np.nan)

    # =============================
    # CONVERSIONES
    # =============================
    # ACEITE y AGUA vienen en m3
    df["ACEITE_BBL"] = df[COL_ACEITE] * 6.28981
    df["AGUA_BBL"] = df[COL_AGUA] * 6.28981

    # GAS viene en m3 y se convierte a pies cúbicos
    df["GAS_PC"] = df[COL_GAS] * 35.3147

    # =============================
    # GASTOS
    # =============================
    df[COL_QO] = df["ACEITE_BBL"] / df[COL_DIAS]
    df[COL_QW] = df["AGUA_BBL"] / df[COL_DIAS]

    # Qg en mpcd
    df[COL_QG] = (df["GAS_PC"] / df[COL_DIAS]) / 1000

    # Qg en pc/d para RGA
    df["Qg_pc_d"] = df["GAS_PC"] / df[COL_DIAS]

    # =============================
    # ACUMULADAS
    # =============================
    df[COL_NP] = df.groupby(COL_POZO)["ACEITE_BBL"].cumsum() / 1000
    df[COL_WP] = df.groupby(COL_POZO)["AGUA_BBL"].cumsum() / 1000
    df[COL_GP] = df.groupby(COL_POZO)["GAS_PC"].cumsum() / 1_000_000

    # =============================
    # RGA Y % AGUA
    # =============================
    df[COL_RGA] = np.where(
        df[COL_QO] > 0,
        df["Qg_pc_d"] / df[COL_QO],
        0
    )

    df[COL_WC] = np.where(
        (df[COL_QO] + df[COL_QW]) > 0,
        (df[COL_QW] / (df[COL_QO] + df[COL_QW])) * 100,
        0
    )

    df = df.replace([np.inf, -np.inf], 0).fillna(0)

    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"No fue posible cargar la base: {e}")
    st.stop()

# =============================
# COMPLETAR FECHAS MENSUALES
# =============================
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

    # REINDEX
    data = data.reindex(fechas_completas)

    data.index.name = COL_FECHA
    data = data.reset_index()

    # =========================
    # RELLENAR IDENTIFICADORES
    # =========================
    data[COL_POZO] = data[COL_POZO].fillna(pozo)

    if COL_YAC in data.columns:
        data[COL_YAC] = data[COL_YAC].fillna(yacimiento)

    # =========================
    # COLUMNAS ORIGINALES
    # =========================
    columnas_originales = [
        COL_DIAS,
        COL_ACEITE,
        COL_AGUA,
        COL_GAS
    ]

    for col in columnas_originales:
        if col in data.columns:
            data[col] = data[col].fillna(0)

    # =========================
    # GASTOS
    # =========================
    columnas_gastos = [
        COL_QO,
        COL_QW,
        COL_QG,
        COL_WC,
        COL_RGA
    ]

    for col in columnas_gastos:
        if col in data.columns:
            data[col] = data[col].fillna(0)

    # =========================
    # ACUMULADAS
    # =========================
    columnas_acumuladas = [
        COL_NP,
        COL_WP,
        COL_GP
    ]

    for col in columnas_acumuladas:
        if col in data.columns:
            data[col] = data[col].ffill().fillna(0)

    return data
# =============================
# ENCABEZADO
# =============================
st.markdown(
    "<div class='main-title'>Campo Tamaulipas-Constituciones Producción</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='subtitle'>Producción diaria promedio mensual por yacimiento</div>",
    unsafe_allow_html=True
)

# =============================
# FILTROS
# =============================
st.markdown("<div class='filter-box'>", unsafe_allow_html=True)

f1, f2, f3, f4 = st.columns([2.0, 2.0, 2.2, 2.2])

with f1:
    yacs = sorted(df[COL_YAC].dropna().astype(str).unique())
    yac_sel = st.multiselect(
        "Yacimiento",
        yacs,
        default=yacs
    )

df_yac = df[df[COL_YAC].astype(str).isin(yac_sel)] if yac_sel else df.copy()

with f2:
    pozos = sorted(df_yac[COL_POZO].dropna().astype(str).unique())
    pozo_sel = st.selectbox(
        "Pozo / Terminación",
        pozos
    )

with f3:
    min_date = df_yac[COL_FECHA].min().date()
    max_date = df_yac[COL_FECHA].max().date()

    date_range = st.date_input(
        "Rango de fechas",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

with f4:
    vista = st.radio(
        "Tipo de análisis",
        ["Pozo individual", "Comparativo multipozo"],
        horizontal=True
    )

st.markdown("</div>", unsafe_allow_html=True)

# =============================
# FILTRADO
# =============================
if isinstance(date_range, tuple) and len(date_range) == 2:
    f_ini = pd.to_datetime(date_range[0])
    f_fin = pd.to_datetime(date_range[1])
else:
    f_ini = df_yac[COL_FECHA].min()
    f_fin = df_yac[COL_FECHA].max()

mask = (
    (df_yac[COL_POZO].astype(str) == str(pozo_sel)) &
    (df_yac[COL_FECHA] >= f_ini) &
    (df_yac[COL_FECHA] <= f_fin)
)

dfp = df_yac.loc[mask].copy()

if dfp.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

dfp = completar_fechas_mensuales(dfp)

# =============================
# FECHAS REALES CON PRODUCCIÓN
# =============================
prod_total = dfp[[COL_QO, COL_QW, COL_QG]].fillna(0).sum(axis=1)
df_prod = dfp[prod_total > 0]

if df_prod.empty:
    df_prod = dfp.copy()

first_row = df_prod.iloc[0]
last_row = df_prod.iloc[-1]

# =============================
# KPIS
# =============================
if vista == "Pozo individual":

    st.markdown(
        f"<span class='small-note'>Pozo seleccionado: <b>{pozo_sel}</b> | "
        f"Yacimiento: <b>{first_row.get(COL_YAC, '')}</b></span>",
        unsafe_allow_html=True
    )

    k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)

    k1.metric("Inicio producción", first_row[COL_FECHA].strftime("%d/%m/%Y"))
    k2.metric("Última producción", last_row[COL_FECHA].strftime("%d/%m/%Y"))
    k3.metric("Qoi aceite", f"{first_row[COL_QO]:,.1f} bpd")
    k4.metric("Último Qo", f"{last_row[COL_QO]:,.1f} bpd")
    k5.metric("Último Qw", f"{last_row[COL_QW]:,.1f} bpd")
    k6.metric("Último Qg", f"{last_row[COL_QG]:,.1f} mpcd")
    k7.metric("Np total", f"{dfp[COL_NP].iloc[-1]:,.2f} mbl")
    k8.metric("Wp / Gp", f"{dfp[COL_WP].iloc[-1]:,.2f} / {dfp[COL_GP].iloc[-1]:,.2f}")

# =============================
# FUNCIÓN COMPARATIVA
# =============================
def comparative_plot(data, y_col, title, y_title, pozos_sel_comp, semilog=False):

    fig = go.Figure()

    for pozo in pozos_sel_comp:

        dfi = data[data[COL_POZO].astype(str) == str(pozo)].copy()

        if dfi.empty:
            continue

        y_values = dfi[y_col].copy()

        if semilog:
            y_values = y_values.replace(0, np.nan)

        fig.add_trace(
            go.Scatter(
                x=dfi[COL_FECHA],
                y=y_values,
                mode="lines",
                name=str(pozo),
                line=dict(width=2.5),
                connectgaps=False,
                hovertemplate=
                    "<b>Pozo: %{fullData.name}</b><br>" +
                    "Fecha: %{x|%d/%m/%Y}<br>" +
                    f"{y_title}: " + "%{y:,.2f}<extra></extra>"
            )
        )

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=18, family="Arial", color="#17202A")
        ),
        template="plotly_white",
        hovermode="x unified",
        height=520,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=35, r=35, t=60, b=35),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig.update_xaxes(
        title_text="Fecha",
        tickformat="%Y",
        showgrid=True,
        gridcolor="#EAECEE",
        zeroline=False
    )

    fig.update_yaxes(
        title_text=y_title,
        type="log" if semilog else "linear",
        showgrid=True,
        gridcolor="#EAECEE",
        zeroline=False,
        separatethousands=True
    )

    return fig

# =============================
# VISTA 1: POZO INDIVIDUAL
# =============================
if vista == "Pozo individual":

    # =====================================================
    # GRÁFICO 1: ACEITE + % AGUA + NP + GAS
    # =====================================================
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])

    fig1.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_QO],
            mode="lines",
            name="Qo (bpd)",
            line=dict(width=3, color="#27AE60"),
            fill="tozeroy",
            fillcolor="rgba(39,174,96,0.25)"
        ),
        secondary_y=False
    )

    fig1.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_WC],
            mode="lines",
            name="% Agua",
            line=dict(width=2, color="#0000FF")
        ),
        secondary_y=False
    )

    fig1.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_NP],
            mode="lines",
            name="Np (mbl)",
            line=dict(width=3, color="#1B4F72")
        ),
        secondary_y=True
    )

    fig1.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_QG],
            mode="lines",
            name="Qg (mpcd)",
            line=dict(width=3, color="#FF0000")
        ),
        secondary_y=True
    )

    fig1.update_layout(
        title="Gasto de aceite, % Agua, acumulada de aceite y gasto de gas",
        template="plotly_white",
        hovermode="x unified",
        height=520,
        legend=dict(orientation="h", y=1.02),
        margin=dict(l=35, r=35, t=60, b=35)
    )

    fig1.update_xaxes(title_text="Fecha", tickformat="%Y")
    fig1.update_yaxes(title_text="Qo (bpd) / % Agua", secondary_y=False)
    fig1.update_yaxes(title_text="Np (mbl) / Qg (mpcd)", secondary_y=True)

    st.plotly_chart(fig1, use_container_width=True)

    # =====================================================
    # GRÁFICO 2: AGUA + WP
    # =====================================================
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

    fig2.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_QW],
            mode="lines",
            name="Qw (bpd)",
            line=dict(width=3, color="#3498DB"),
            fill="tozeroy",
            fillcolor="rgba(52,152,219,0.20)"
        ),
        secondary_y=False
    )

    fig2.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_WP],
            mode="lines",
            name="Wp (mbl)",
            line=dict(width=3, color="#154360")
        ),
        secondary_y=True
    )

    fig2.update_layout(
        title="Agua y acumulada de agua",
        template="plotly_white",
        hovermode="x unified",
        height=520,
        legend=dict(orientation="h", y=1.02),
        margin=dict(l=35, r=35, t=60, b=35)
    )

    fig2.update_xaxes(title_text="Fecha", tickformat="%Y")
    fig2.update_yaxes(title_text="Qw (bpd)", secondary_y=False)
    fig2.update_yaxes(title_text="Wp (mbl)", secondary_y=True)

    st.plotly_chart(fig2, use_container_width=True)

    # =====================================================
    # GRÁFICO 3: RGA + GP
    # =====================================================
    fig3 = make_subplots(specs=[[{"secondary_y": True}]])

    fig3.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_RGA],
            mode="lines",
            name="RGA (pc/bl)",
            line=dict(width=2, color="#FF0000")
        ),
        secondary_y=False
    )

    fig3.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_GP],
            mode="lines",
            name="Gp (mmpc)",
            line=dict(width=3, color="#641E16")
        ),
        secondary_y=True
    )

    fig3.update_layout(
        title="RGA y acumulada de gas",
        template="plotly_white",
        hovermode="x unified",
        height=520,
        legend=dict(orientation="h", y=1.02),
        margin=dict(l=35, r=35, t=60, b=35)
    )

    fig3.update_xaxes(title_text="Fecha", tickformat="%Y")
    fig3.update_yaxes(title_text="RGA (pc/bl)", secondary_y=False)
    fig3.update_yaxes(title_text="Gp (mmpc)", secondary_y=True)

    st.plotly_chart(fig3, use_container_width=True)

    # =============================
    # TABLA
    # =============================
    st.markdown("<div class='section-title'>Datos filtrados del pozo</div>", unsafe_allow_html=True)

    show_cols = [
        c for c in [
            COL_POZO, COL_FECHA, COL_YAC, COL_DIAS,
            COL_ACEITE, COL_AGUA, COL_GAS,
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

# =============================
# VISTA 2: COMPARATIVO MULTIPOZO
# =============================
elif vista == "Comparativo multipozo":

    st.markdown(
        "<div class='section-title'>Comparativo de producción por pozos seleccionados</div>",
        unsafe_allow_html=True
    )

    pozos_comp = sorted(df_yac[COL_POZO].dropna().astype(str).unique())

    pozos_sel_comp = st.multiselect(
        "Selecciona pozos para comparar",
        pozos_comp,
        default=[pozo_sel] if pozo_sel in pozos_comp else []
    )

    if pozos_sel_comp:

        df_comp_raw = df_yac[
            (df_yac[COL_POZO].astype(str).isin(pozos_sel_comp)) &
            (df_yac[COL_FECHA] >= f_ini) &
            (df_yac[COL_FECHA] <= f_fin)
        ].copy()

        lista_pozos = []

        for pozo in pozos_sel_comp:
            dfi = df_comp_raw[df_comp_raw[COL_POZO].astype(str) == str(pozo)].copy()

            if dfi.empty:
                continue

            dfi = completar_fechas_mensuales(dfi)

            for col in [COL_QO, COL_RGA, COL_WC]:
                if col in dfi.columns:
                    dfi[col] = dfi[col].fillna(0)

            lista_pozos.append(dfi)

        if lista_pozos:
            df_comp = pd.concat(lista_pozos, ignore_index=True)
            df_comp = df_comp.sort_values([COL_POZO, COL_FECHA])

            st.plotly_chart(
                comparative_plot(
                    df_comp,
                    COL_QO,
                    "Comparativo de producción de aceite por pozo",
                    "Qo (bpd)",
                    pozos_sel_comp,
                    semilog=False
                ),
                use_container_width=True
            )

            st.plotly_chart(
                comparative_plot(
                    df_comp,
                    COL_RGA,
                    "Comparativo semilog de RGA por pozo",
                    "RGA (pc/bl)",
                    pozos_sel_comp,
                    semilog=True
                ),
                use_container_width=True
            )

            st.plotly_chart(
                comparative_plot(
                    df_comp,
                    COL_WC,
                    "Comparativo de corte de agua por pozo",
                    "% Agua",
                    pozos_sel_comp,
                    semilog=False
                ),
                use_container_width=True
            )

        else:
            st.warning("No hay datos disponibles para los pozos seleccionados.")

    else:
        st.info("Selecciona uno o más pozos para generar el comparativo.")

st.caption("Desarrollado en Python + Streamlit.")