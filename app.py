import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import plotly.express as px


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
st.set_page_config(
    page_title="Visualizador de Producción",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="collapsed"
)
#st.cache_data.clear()
# =========================================================
# RUTA DE LA BASE DE DATOS
# Cambia esta ruta si tu archivo .db está en otra carpeta.
# =========================================================

# Ruta de la base
ruta_db = "prodcoord.db"

# Tablas
TABLA_PROD = "Produccion"
TABLA_COORD = "Coord"
TABLA_CONTORNO = "Contorno"
TABLA_ASIGNACION = "Asignacion"
TABLA_TERM = "TERM"

@st.cache_data(show_spinner=False)
def load_table(tabla):

    conn = sqlite3.connect(ruta_db)

    df = pd.read_sql(
        f"SELECT * FROM {tabla}",
        conn
    )

    conn.close()

    return df
# Conexión
#conn = sqlite3.connect(ruta_db)

# Leer producción
#df_prod = pd.read_sql(f"SELECT * FROM {TABLA_PROD}", conn)

# Leer coordenadas
#df_coord = pd.read_sql(f"SELECT * FROM {TABLA_COORD}", conn)

#conn.close()
#ruta_db = r"C:\Users\VMGS\OneDrive - CONSORCIO PETROLERO 5M DEL GOLFO\Escritorio\Resplado C5M\Web\prod.db"

# Nombre de la tabla en SQLite
#TABLA_PROD = "PROD"

# =========================================================
# COLUMNAS DE LA BASE NUEVA
# La base solo debe traer estas columnas:
# Terminacion, Fecha, Yacimiento, Conta, Dias, Aceite, Gas, Agua
# =========================================================
COL_POZO = "TERMINACION"
COL_FECHA = "FECHA"
COL_YAC = "YACIMIENTO"
COL_CONTA = "CONTA"
COL_DIAS = "DIAS"
COL_ACEITE = "ACEITE"
COL_GAS = "GAS"
COL_AGUA = "AGUA"

# Columnas calculadas para el visualizador
COL_ACEITE_BBL = "Aceite (bl)"
COL_AGUA_BBL = "Agua (bl)"
COL_GAS_PC = "Gas (pc)"

COL_QO = "Qo (bpd)"
COL_QW = "Qw (bpd)"
COL_QG = "Qg (mpcd)"
COL_QG_PCD = "Qg (pcd)"

COL_NP = "Np (mbl)"
COL_WP = "Wp (mbl)"
COL_GP = "Gp (mmpc)"

COL_WC = "%Agua"
COL_RGA = "RGA (pc/bl)"
COL_FECHA_FILTRO = "FECHA_FILTRO"

COL_TIEMPO_NORM = "Tiempo normalizado"


REQUIRED_COLS = [
    COL_POZO, COL_FECHA, COL_YAC, COL_CONTA,
    COL_DIAS, COL_ACEITE, COL_GAS, COL_AGUA
]

# Factores de conversión
M3_A_BBL = 6.28981
M3_A_PC = 35.3147

# =========================================================
# ESTILO
# =========================================================
st.markdown("""
<style>
    .main { background-color: #f7f9fb; }

    .block-container {
        padding-top: 1.2rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        max-width: 100%;
    }

    [data-testid="stSidebar"] { display: none; }

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

# =========================================================
# FUNCIONES AUXILIARES
# =========================================================
def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte encabezados a mayúsculas para evitar errores por Fecha/FECHA, Aceite/ACEITE, etc."""
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df


def convertir_fechas(serie: pd.Series) -> pd.Series:
    """Convierte fechas robustamente: dd/mm/yyyy, yyyy-mm-dd y serial Excel."""
    s = serie.copy()

    fecha = pd.to_datetime(s, errors="coerce", dayfirst=False)

    faltan = fecha.isna()
    if faltan.any():
        fecha.loc[faltan] = pd.to_datetime(s.loc[faltan], errors="coerce", dayfirst=False)

    faltan = fecha.isna()
    if faltan.any():
        nums = pd.to_numeric(s.loc[faltan], errors="coerce")
        fecha.loc[faltan] = pd.to_datetime(
            nums,
            unit="D",
            origin="1899-12-30",
            errors="coerce"
        )

    return fecha

def completar_fechas_pozo(df_pozo: pd.DataFrame) -> pd.DataFrame:
    df_pozo = df_pozo.copy()
    df_pozo = df_pozo.sort_values(COL_FECHA)

    pozo = df_pozo[COL_POZO].iloc[0]
    yac = df_pozo[COL_YAC].iloc[0]
    conta = df_pozo[COL_CONTA].iloc[0]

    fecha_ini = df_pozo[COL_FECHA].min()
    fecha_fin = df_pozo[COL_FECHA].max()

    fechas_completas = pd.date_range(
        start=fecha_ini,
        end=fecha_fin,
        freq="MS"
    )

    base = pd.DataFrame({COL_FECHA: fechas_completas})
    df_out = base.merge(df_pozo, on=COL_FECHA, how="left")

    df_out[COL_POZO] = df_out[COL_POZO].fillna(pozo)
    df_out[COL_YAC] = df_out[COL_YAC].fillna(yac)
    df_out[COL_CONTA] = df_out[COL_CONTA].fillna(conta)

    # IMPORTANTE:
    # Respeta los DIAS reales de la base.
    # Solo pone 0 días en meses inventados sin producción.
    df_out[COL_DIAS] = df_out[COL_DIAS].fillna(0)

    for col in [COL_ACEITE, COL_GAS, COL_AGUA]:
        df_out[col] = df_out[col].fillna(0)

    df_out[COL_FECHA_FILTRO] = df_out[COL_FECHA]

    return df_out

# =========================================================
# CARGA BASE Y CÁLCULOS DINÁMICOS
# =========================================================
def calcular_columnas_produccion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula conversiones, gastos, acumuladas, RGA y %Agua.
    NO completa fechas. Grafica solamente los registros reales existentes en la base.
    """
    df = df.copy()
    df = df.sort_values([COL_POZO, COL_FECHA]).reset_index(drop=True)
    df[COL_FECHA_FILTRO] = df[COL_FECHA]

    # Volúmenes mensuales convertidos
    df[COL_ACEITE_BBL] = df[COL_ACEITE] * M3_A_BBL
    df[COL_AGUA_BBL] = df[COL_AGUA] * M3_A_BBL
    df[COL_GAS_PC] = df[COL_GAS] * M3_A_PC

    # Gastos promedio diarios
    dias_validos = df[COL_DIAS].replace(0, np.nan)
    df[COL_QO] = df[COL_ACEITE_BBL] / dias_validos
    df[COL_QW] = df[COL_AGUA_BBL] / dias_validos
    df[COL_QG_PCD] = df[COL_GAS_PC] / dias_validos
    df[COL_QG] = df[COL_QG_PCD] / 1000.0

    for col in [COL_QO, COL_QW, COL_QG_PCD, COL_QG]:
        df[col] = df[col].replace([np.inf, -np.inf], np.nan).fillna(0)

    # Acumuladas por pozo usando únicamente registros reales de la base
    df[COL_NP] = df.groupby(COL_POZO)[COL_ACEITE_BBL].cumsum() / 1000.0
    df[COL_WP] = df.groupby(COL_POZO)[COL_AGUA_BBL].cumsum() / 1000.0
    df[COL_GP] = df.groupby(COL_POZO)[COL_GAS_PC].cumsum() / 1_000_000.0

    # RGA y corte de agua
    df[COL_RGA] = np.where(df[COL_QO] > 0, df[COL_QG_PCD] / df[COL_QO], 0)
    df[COL_WC] = np.where(
        (df[COL_QO] + df[COL_QW]) > 0,
        (df[COL_QW] / (df[COL_QO] + df[COL_QW])) * 100,
        0
    )

    return df.replace([np.inf, -np.inf], 0).fillna(0)


@st.cache_data(show_spinner="Cargando base de datos...")
def load_data() -> pd.DataFrame:
    """
    Carga la base original sin completar fechas.
    El visualizador trabaja solamente con los registros reales de SQLite.
    """
    with sqlite3.connect(ruta_db) as conn:
        df = pd.read_sql_query(f'SELECT * FROM "{TABLA_PROD}"', conn)

    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
    df = normalizar_columnas(df)

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(
            "Faltan columnas requeridas en la base: "
            f"{missing}. La tabla debe tener: Terminacion, Fecha, Yacimiento, Conta, Dias, Aceite, Gas, Agua."
        )

    df = df[REQUIRED_COLS].copy()

    # Limpieza básica
    df[COL_POZO] = df[COL_POZO].astype(str).str.strip()
    df[COL_YAC] = df[COL_YAC].astype(str).str.strip()
    df[COL_CONTA] = df[COL_CONTA].astype(str).str.strip()

    df[COL_FECHA] = convertir_fechas(df[COL_FECHA])
    df = df.dropna(subset=[COL_POZO, COL_FECHA])
    df = df[df[COL_POZO].str.upper().ne("NAN")]
    df[COL_FECHA] = df[COL_FECHA].dt.normalize()
    df[COL_FECHA_FILTRO] = df[COL_FECHA]

    for col in [COL_DIAS, COL_ACEITE, COL_GAS, COL_AGUA]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # No se completa ni se inventa ninguna fecha.
    df = df.sort_values([COL_POZO, COL_FECHA]).reset_index(drop=True)

    return df


@st.cache_data(show_spinner="Cargando coordenadas...")
def load_coord() -> pd.DataFrame:
    """Carga la tabla Coord para el mapa de burbujas."""
    with sqlite3.connect(ruta_db) as conn:
        coord = pd.read_sql_query(f'SELECT * FROM "{TABLA_COORD}"', conn)

    coord = coord.loc[:, ~coord.columns.astype(str).str.startswith("Unnamed")]
    coord = normalizar_columnas(coord)

    for c in ["CIMA X UTM", "CIMA Y UTM", "RADIO DRENE"]:
        if c in coord.columns:
            coord[c] = pd.to_numeric(coord[c], errors="coerce")

    if COL_POZO in coord.columns:
        coord[COL_POZO] = coord[COL_POZO].astype(str).str.strip()
    if COL_YAC in coord.columns:
        coord[COL_YAC] = coord[COL_YAC].astype(str).str.strip()
    if "POZO" in coord.columns:
        coord["POZO"] = coord["POZO"].astype(str).str.strip()

    return coord

#Aqui van los pozos historicos del campo del 2011 al 2020
@st.cache_data(show_spinner="Cargando pozos perforados históricos...")
def load_term_perforados() -> pd.DataFrame:
    term = load_table(TABLA_TERM)
    term = term.loc[:, ~term.columns.astype(str).str.startswith("Unnamed")]
    term = normalizar_columnas(term)

    # Si TERMINACION no viene como encabezado, usa la segunda columna
    if COL_POZO not in term.columns:
        segunda_col = term.columns[1]
        term = term.rename(columns={segunda_col: COL_POZO})

    term[COL_POZO] = term[COL_POZO].astype(str).str.strip()

    # Detectar año si existe
    col_anio = None
    for c in ["AÑO", "ANO", "YEAR"]:
        if c in term.columns:
            col_anio = c
            break

    if col_anio:
        term[col_anio] = pd.to_numeric(term[col_anio], errors="coerce")
        term = term[(term[col_anio] >= 2011) & (term[col_anio] <= 2020)]

    elif COL_FECHA in term.columns:
        term[COL_FECHA] = convertir_fechas(term[COL_FECHA])
        term = term[
            (term[COL_FECHA].dt.year >= 2011) &
            (term[COL_FECHA].dt.year <= 2020)
        ]

    term = term[[COL_POZO]].dropna().drop_duplicates()
    term["PERFORADO_TERM"] = "Sí"

    return term

# Ultimo Porcetaje de Agua por pozo
@st.cache_data(show_spinner=False)
def calcular_ultimo_wc_mapa(df_base):

    prod = calcular_columnas_produccion(df_base.copy())

    prod = prod.sort_values([COL_POZO, COL_FECHA])

    ultimo_wc = (
        prod.dropna(subset=[COL_WC])
        .groupby(COL_POZO, as_index=False)
        .tail(1)[[COL_POZO, COL_WC]]
        .rename(columns={COL_WC: "ULTIMO_WC"})
    )

    return ultimo_wc

#######Mapa con tiempo


def mapa_burbujas(df_base: pd.DataFrame, df_coord: pd.DataFrame):
    """Mapa de burbujas con radios de drene y leyenda interactiva por grupos."""

    st.markdown("<div class='section-title'>Mapa de burbujas y radios de drene</div>", unsafe_allow_html=True)

    coord = df_coord.copy()
    prod = calcular_columnas_produccion(df_base.copy())

    contorno = load_table(TABLA_CONTORNO)
    asignacion = load_table(TABLA_ASIGNACION)

    acum = (
        prod.groupby(COL_POZO, as_index=False)
        .agg({
            COL_ACEITE_BBL: "sum",
            COL_AGUA_BBL: "sum",
            COL_GAS_PC: "sum"
        })
        .rename(columns={
            COL_ACEITE_BBL: "NP_BLS",
            COL_AGUA_BBL: "WP_BLS",
            COL_GAS_PC: "GP_PC"
        })
    )

    mapa = coord.merge(acum, on=COL_POZO, how="left")
    ultimo_wc = calcular_ultimo_wc_mapa(df_base)

    mapa = mapa.merge(
        ultimo_wc,
        on=COL_POZO,
        how="left"
    )

    term = load_term_perforados()

    mapa = mapa.merge(
        term,
        on=COL_POZO,
        how="left"
    )

    mapa["PERFORADO_TERM"] = mapa["PERFORADO_TERM"].fillna("No")

    mapa["ULTIMO_WC"] = mapa["ULTIMO_WC"].fillna(0)

    mapa[["NP_BLS", "WP_BLS", "GP_PC"]] = mapa[["NP_BLS", "WP_BLS", "GP_PC"]].fillna(0)

    if "RADIO DRENE" in mapa.columns:
        mapa["RADIO DRENE"] = pd.to_numeric(mapa["RADIO DRENE"], errors="coerce")
    else:
        mapa["RADIO DRENE"] = np.nan

    # Filtros propios del mapa
    c1, c2, c3, c4 = st.columns([1.3, 1.3, 1.3, 1.3])
    #c1, c2, c3 = st.columns([1.4, 1.4, 1.4])

    with c1:
        yacs_mapa = sorted(mapa[COL_YAC].dropna().astype(str).unique())
        yac_mapa = st.selectbox(
            "Yacimiento del mapa",
            options=[None] + yacs_mapa,
            format_func=lambda x: "Seleccionar yacimiento" if x is None else x,
            key="yac_mapa_burbujas"
        )

    if yac_mapa is None:
        st.info("Selecciona un yacimiento para visualizar el mapa.")
        return

    mapa = mapa[mapa[COL_YAC].astype(str) == str(yac_mapa)].copy()

    with c2:
        variable = st.selectbox(
            "Variable de burbuja",
            ["NP_BLS", "WP_BLS", "GP_PC","ULTIMO_WC"],
            format_func=lambda x: {
                "NP_BLS": "Aceite acumulado, Np [bls]",
                "WP_BLS": "Agua acumulada, Wp [bls]",
                "GP_PC": "Gas acumulado, Gp [pc]",
                "ULTIMO_WC": "Último % Agua [%]"
            }[x],
            key="variable_mapa_burbujas"
        )        


    with c3:
        pozos_mapa = sorted(mapa["POZO"].dropna().astype(str).unique()) if "POZO" in mapa.columns else []
        pozo_zoom = st.selectbox(
            "Zoom a pozo",
            options=["Todos"] + pozos_mapa,
            key="pozo_zoom_mapa"
        )

    with c4:
        filtro_term = st.selectbox(
            "Pozos perforados históricos TERM",
            ["Todos", "Solo perforados 2011-2020", "Solo no perforados"],
            key="filtro_term_mapa"
        )

        if filtro_term == "Solo perforados 2011-2020":
            mapa = mapa[mapa["PERFORADO_TERM"] == "Sí"].copy()

        elif filtro_term == "Solo no perforados":
            mapa = mapa[mapa["PERFORADO_TERM"] == "No"].copy()

    color_variable = {
        "NP_BLS": "green",
        "WP_BLS": "blue",
        "GP_PC": "red",
        "ULTIMO_WC": "deepskyblue"
    }

    max_val = mapa[variable].max()
    if max_val > 0:
        mapa["SIZE"] = 18 + (mapa[variable] / max_val) * 50
    else:
        mapa["SIZE"] = 18

    # Etiqueta: nombre del pozo + acumulada
    if "POZO" not in mapa.columns:
        mapa["POZO"] = mapa[COL_POZO]

    if variable == "ULTIMO_WC":
        mapa["ETIQUETA_MAPA"] = mapa[variable].fillna(0).map(lambda x: f"{x:.1f}%")
    else:
        mapa["ETIQUETA_MAPA"] = mapa[variable].fillna(0).map(lambda x: f"{x/1000:,.1f}")
    

    fig = go.Figure()

    # =========================
    # CONTORNO Y ASIGNACION
    # =========================

    contorno = contorno.sort_values("Orden")
    asignacion = asignacion.sort_values("Orden")

    # Cerrar poligonos
    contorno_plot = pd.concat(
        [contorno, contorno.iloc[[0]]],
        ignore_index=True
    )

    asignacion_plot = pd.concat(
        [asignacion, asignacion.iloc[[0]]],
        ignore_index=True
    )

    # Contorno campo
    fig.add_trace(go.Scatter(
        x=contorno_plot["X"],
        y=contorno_plot["Y"],
        mode="lines",
        name="Campo",
        line=dict(
            color="black",
            width=3
        ),
        hoverinfo="skip"
    ))

    # Asignacion
    fig.add_trace(go.Scatter(
        x=asignacion_plot["X"],
        y=asignacion_plot["Y"],
        mode="lines",
        name="Asignacion",
        line=dict(
            color="red",
            width=3,
            dash="dash"
        ),
        hoverinfo="skip"
    ))
    # =====================================================
    # RADIOS DE DRENE
    # legendgroup='radios' permite que la leyenda los oculte/muestre juntos.
    # =====================================================
    theta = np.linspace(0, 2*np.pi, 180)

    for _, row in mapa.iterrows():
        radio = row.get("RADIO DRENE")

        if (
            pd.notna(radio) and radio > 0 and
            pd.notna(row.get("CIMA X UTM")) and
            pd.notna(row.get("CIMA Y UTM"))
        ):
            x0 = row["CIMA X UTM"]
            y0 = row["CIMA Y UTM"]

            fig.add_trace(go.Scatter(
                x=x0 + radio * np.cos(theta),
                y=y0 + radio * np.sin(theta),
                mode="lines",
                line=dict(width=2, color="black"),
                name="Radio de drene (m)",
                legendgroup="radios",
                #mode="text",
                text=[f"{radio:,.0f} m"],
                textfont=dict(
                    size=9,
                    color="black"
                ),
                showlegend=False,
                hovertemplate=
                "<b>Pozo:</b> " + str(row.get("POZO", "")) + "<br>" +
                "<b>Radio drene:</b> " + f"{radio:,.0f} m" +
                "<extra></extra>",
            ))

    mapa_burb = mapa[mapa[variable] > 0].copy()
    # =====================================================
    # BURBUJAS
    # legendgroup='burbujas' permite que burbuja, brillo y punto se apaguen juntos.
    # =====================================================
    fig.add_trace(go.Scatter(
        x=mapa_burb["CIMA X UTM"],
        y=mapa_burb["CIMA Y UTM"],
        mode="markers+text",
        text=mapa_burb["ETIQUETA_MAPA"],
        textposition="top center",
        textfont=dict(size=13, color="blue"),
        marker=dict(
            size=mapa_burb["SIZE"],
            sizemode="diameter",
            opacity=0.65,
            color=color_variable[variable],
            line=dict(width=2, color="rgba(0,0,0,0.55)")
        ),
        customdata=mapa_burb[["POZO", COL_YAC, "NP_BLS", "WP_BLS", "GP_PC", "RADIO DRENE"]],
        hovertemplate=
            "<b>Pozo:</b> %{customdata[0]}<br>" +
            "<b>Yacimiento:</b> %{customdata[1]}<br>" +
            "<b>Np:</b> %{customdata[2]:,.0f} bls<br>" +
            "<b>Wp:</b> %{customdata[3]:,.0f} bls<br>" +
            "<b>Gp:</b> %{customdata[4]:,.0f} pc<br>" +
            "<b>Radio drene:</b> %{customdata[5]:,.0f} m<br>" +
            "<extra></extra>",
        name="Burbuja acumulada (mb)",
        legendgroup="burbujas",
        showlegend=True
    ))
   
   # Punto exacto de cima + nombre pozo
    fig.add_trace(go.Scatter(
    x=mapa["CIMA X UTM"],
    y=mapa["CIMA Y UTM"],

    mode="markers+text",

    text=mapa["POZO"],
    textposition="top center",

    textfont=dict(
        size=13,
        color="black"
    ),

    marker=dict(
        size=5,
        color="black"
    ),

    hoverinfo="skip",

    showlegend=False
    ))

    mapa_term = mapa[mapa["PERFORADO_TERM"] == "Sí"].copy()

    fig.add_trace(go.Scatter(
        x=mapa_term["CIMA X UTM"],
        y=mapa_term["CIMA Y UTM"],
        mode="markers",
        marker=dict(
            size=5,
            symbol="circle",
            color="red",
            #line=dict(width=3, color="orange")
        ),
        name="Perforados TERM 2011-2020",
        hovertemplate=
            "<b>Pozo perforado:</b> %{customdata[0]}<br>" +
            "<b>Yacimiento:</b> %{customdata[1]}<br>" +
            "<extra></extra>",
        customdata=mapa_term[["POZO", COL_YAC]],
        showlegend=True
    ))


    # Traza ficticia para que Radio de drene aparezca en la leyenda una sola vez
    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode="lines",
        line=dict(width=2, color="black"),
        name="Radio de drene (m)",
        legendgroup="radios",
        showlegend=True
    ))

    fig.update_layout(
        title=f"Mapa de burbujas - {yac_mapa}",
        template="plotly_white",
        height=1500,
        margin=dict(l=20, r=20, t=70, b=20),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            groupclick="togglegroup"
        )
    )

    fig.update_xaxes(title_text="UTM X")
    fig.update_yaxes(
        title_text="UTM Y",
        scaleanchor="x",
        scaleratio=1
    )

    # Zoom automático al pozo seleccionado
    if pozo_zoom != "Todos" and "POZO" in mapa.columns:
        row_zoom = mapa[mapa["POZO"].astype(str) == str(pozo_zoom)]
        if not row_zoom.empty:
            x0 = row_zoom["CIMA X UTM"].iloc[0]
            y0 = row_zoom["CIMA Y UTM"].iloc[0]
            radio_zoom = 2000
            fig.update_xaxes(range=[x0 - radio_zoom, x0 + radio_zoom])
            fig.update_yaxes(range=[y0 - radio_zoom, y0 + radio_zoom])

    st.plotly_chart(fig, use_container_width=True)


try:
    df = load_data()
    df_coord = load_coord()
except Exception as e:
    st.error(f"No fue posible cargar la base: {e}")
    st.stop()

#Analisis de las terminaciones
def analisis_term():
    st.markdown("<div class='section-title'>Análisis estadístico de terminaciones históricas</div>", unsafe_allow_html=True)

    term = load_table(TABLA_TERM)
    term = normalizar_columnas(term)
    term = term.loc[:, ~term.columns.astype(str).str.startswith("UNNAMED")]

    if COL_POZO not in term.columns:
        segunda_col = term.columns[1]
        term = term.rename(columns={segunda_col: COL_POZO})

    term[COL_POZO] = term[COL_POZO].astype(str).str.strip()

    # =========================
    # COLUMNAS TERM
    # =========================
    col_anio = "AÑO"
    col_qoi_prog = "QO PROG"
    col_qoi = "QOI"
    col_yac_term = COL_YAC

    cols_necesarias = [col_anio, col_qoi_prog, col_qoi, COL_POZO]

    for c in cols_necesarias:
        if c not in term.columns:
            st.error(f"No existe la columna '{c}' en TERM. Revisa el nombre exacto del encabezado.")
            st.write(term.columns.tolist())
            return

    # Si TERM no trae yacimiento, lo toma de Coord
    if col_yac_term not in term.columns:
        coord_yac = df_coord[[COL_POZO, COL_YAC]].drop_duplicates()
        term = term.merge(coord_yac, on=COL_POZO, how="left")

    term[col_anio] = pd.to_numeric(term[col_anio], errors="coerce")
    term[col_qoi_prog] = pd.to_numeric(term[col_qoi_prog], errors="coerce")
    term[col_qoi] = pd.to_numeric(term[col_qoi], errors="coerce")

    term = term[(term[col_anio] >= 2011) & (term[col_anio] <= 2020)].copy()

    term["DIF_QOI"] = term[col_qoi] - term[col_qoi_prog]
    term["CUMPLIMIENTO_QOI_%"] = np.where(
        term[col_qoi_prog] > 0,
        term[col_qoi] / term[col_qoi_prog] * 100,
        np.nan
    )

    # =========================
    # FILTROS PRINCIPALES
    # =========================
    c1, c2, c3 = st.columns(3)

    with c1:
        anios = sorted(term[col_anio].dropna().astype(int).unique())
        anio_sel = st.multiselect(
            "Campaña / año de perforación",
            anios,
            default=anios
        )

    term_f = term[term[col_anio].astype("Int64").isin(anio_sel)].copy()

    with c2:
        yacs = sorted(term_f[COL_YAC].dropna().astype(str).unique())
        yac_sel = st.multiselect(
            "Yacimiento",
            yacs,
            default=yacs
        )

    if yac_sel:
        term_f = term_f[term_f[COL_YAC].astype(str).isin(yac_sel)].copy()

    with c3:
        pozos = sorted(term_f[COL_POZO].dropna().astype(str).unique())
        pozo_sel = st.selectbox(
            "Pozo / Terminación",
            ["Todos"] + pozos
        )

    if pozo_sel != "Todos":
        term_f = term_f[term_f[COL_POZO].astype(str) == str(pozo_sel)].copy()

    if term_f.empty:
        st.warning("No hay datos con los filtros seleccionados.")
        return

    # =========================
    # MÉTRICAS
    # =========================
    #m1, m2, m3, m4 = st.columns(4)
    m1, m2 = st.columns(2)

    m1.metric("Pozos terminados", f"{term_f[COL_POZO].nunique():,.0f}")
    #m2.metric("Qoi Prog prom.", f"{term_f[col_qoi_prog].mean():,.1f}")
    m2.metric("Qoi promedio.", f"{term_f[col_qoi].mean():,.1f}")
    #m4.metric("Cumplimiento prom.", f"{term_f['CUMPLIMIENTO_QOI_%'].mean():,.1f} %")

    term_f = term_f.sort_values([col_anio, COL_POZO])

    term_f["POZO_CAMP"] = (
        term_f[col_anio].astype(int).astype(str)
        + " | "
        + term_f[COL_POZO].astype(str)
    )

    # =========================
    # 1. QOI PROGRAMADO VS QOI REAL
    # =========================
    fig1 = go.Figure()

    fig1.add_trace(go.Bar(
        x=term_f["POZO_CAMP"],
        #x=term_f[COL_POZO],
        y=term_f[col_qoi_prog],
        name="Qo programa (bpd)",
        marker=dict(
            color="#1F4E79",
            line=dict(color="#0B1F33", width=1.5)
        ),
        opacity=0.88,
        text=term_f[col_qoi_prog].round(1),
        textposition="outside"
    ))

    fig1.add_trace(go.Bar(
        x=term_f["POZO_CAMP"],
        #x=term_f[COL_POZO],
        y=term_f[col_qoi],
        name="Qoi real (bpd)",
        marker=dict(
            color="#00A65A",
            line=dict(color="#006B3A", width=1.5)
        ),
        opacity=0.95,
        text=term_f[col_qoi].round(1),
        textposition="outside"
    ))

    fig1.update_layout(
        title="<b>Comparación Qoi programado vs Qoi real por pozo</b>",
        xaxis=dict(
        tickangle=-75,
        categoryorder="array",
        categoryarray=term_f["POZO_CAMP"]
        ),
        xaxis_title="Terminación",
        yaxis_title="Qoi (bpd)",
        barmode="group",
        height=560,
        template="plotly_white",
        bargap=0.22,
        bargroupgap=0.08,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="right",
            x=1
        ),
        font=dict(
            size=14,
            color="black",
            family="Arial Black"
            ),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig1.update_xaxes(
        tickangle=-45,
        showline=True,
        linewidth=1,
        tickfont=dict(
        size=11,
        color="black",
        family="Tahoma"
        ),
        linecolor="black"
    )

    fig1.update_yaxes(
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        tickfont=dict(
        size=12,
        color="black",
        family="Arial Black"
        ),
        linecolor="black"
    )

    st.plotly_chart(fig1, use_container_width=True)

    # =========================
    # 2. QOI PROMEDIO Y NÚMERO DE POZOS POR CAMPAÑA (Grafico 2)
    # =========================
    resumen_anio = term_f.groupby(col_anio, as_index=False).agg(
        QOI_PROM=(col_qoi, "mean"),
        POZOS=(COL_POZO, "nunique")
    )

    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

    fig2.add_trace(
    go.Bar(
        x=resumen_anio[col_anio],
        y=resumen_anio["QOI_PROM"],
        name="Qoi real promedio",

        marker=dict(
            color="#14A1FF",
            line=dict(color="#000000", width=1.5)
        ),

        text=resumen_anio["QOI_PROM"].round(1),

        textposition="outside",

        textfont=dict(
            size=13,
            color="#000000",
            family="Tahoma"
        ),

        opacity=0.65
    ),
    secondary_y=False
    )

    #fig2.add_trace(
    #    go.Scatter(
    #        x=resumen_anio[col_anio],
    #        y=resumen_anio["POZOS"],
    #        mode="lines+markers+text",
    #        name="Número de pozos",
    #        line=dict(color="#d62728", width=2),
    #        marker=dict(
    #            size=10,
    #            color="#d62728",
    #            line=dict(color="white", width=1)
    #        ),
    #        text=resumen_anio["POZOS"],
    #        textposition="bottom center"
    #    ),
    #    secondary_y=True
    #)

    fig2.update_layout(
        title="<b>Qoi promedio y pozos por campaña</b>",
        height=520,
        font=dict(
            size=14,
            color="black",
            family="Arial Black"
            ),
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.15,
            xanchor="center",
            x=0.5
        ),
        #font=dict(size=13),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    for x, y, p in zip(
        resumen_anio[col_anio],
        resumen_anio["QOI_PROM"],
        resumen_anio["POZOS"]
    ):

        fig2.add_annotation(
            x=x,
            y=y * 0.05,   # posición abajo dentro barra

            text=f"<b>{p} pozos</b>",

            showarrow=False,

            font=dict(
                size=12,
                color="black",
                family="Arial Black"
            )
        )

    fig2.update_xaxes(
        title_text="Campaña",
        dtick=1,
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(
        size=12,
        color="black",
        family="Arial Black"
        ),

    )

    fig2.update_yaxes(
        title_text="Qoi promedio (bpd)",
        secondary_y=False,
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(
        size=12,
        color="black",
        family="Arial Black"
        ),
    )

    fig2.update_yaxes(
        title_text="Número de pozos",
        secondary_y=True,
        showgrid=False,
        tickfont=dict(
        size=12,
        color="black",
        family="Arial Black"
        ),
    )

    #st.plotly_chart(fig2, use_container_width=True)

    colg1, colg2 = st.columns(2)

    with colg1:
        st.plotly_chart(fig2, use_container_width=True)

    with colg2:

        # =========================
        # 3. BOXPLOT QOI POR CAMPAÑA
        # =========================
        fig3 = px.box(
            term_f,
            x=col_anio,
            y=col_qoi,
            points="all",
            hover_name=COL_POZO,
            title="<b>Modelo estadístico</b>",
            template="plotly_white"
        )
        
        #Color Cajas
        fig3.update_traces(
            marker=dict(
                color="#30E460",
                size=7,
                opacity=0.65,
                line=dict(color="black", width=1)
            ),
            line=dict(color="#006B3A", width=1),
            fillcolor="rgba(0,166,90,0.25)"
        )

        medianas = term_f.groupby(col_anio, as_index=False)[col_qoi].median()

        fig3.add_trace(go.Scatter(
            x=medianas[col_anio],
            y=medianas[col_qoi],
            mode="text",
            text=medianas[col_qoi].round(1),
            textposition="top center",
            textfont=dict(
                size=10,
                color="black"
            ),
            name="Mediana",
            showlegend=False
        ))

        fig3.update_layout(
            height=520,
            xaxis_title="Campaña",
            yaxis_title="Qoi por campaña (bpd)",
            font=dict(
            size=14,
            color="black",
            family="Arial Black"
            ),
            plot_bgcolor="white",
            paper_bgcolor="white"
        )

        fig3.update_xaxes(
            dtick=1,
            showline=True,
            linewidth=1,
            linecolor="black",
            tickfont=dict(
            size=12,
            color="black",
            family="Arial Black"
            ),
        )

        fig3.update_yaxes(
            showgrid=True,
            gridcolor="#EAECEE",
            showline=True,
            linewidth=1,
            linecolor="black",
            tickfont=dict(
            size=12,
            color="black",
            family="Arial Black"
            ),
        )

        #st.plotly_chart(fig3, use_container_width=True)

        st.plotly_chart(fig3, use_container_width=True)

        # =========================
    # 4. GASTO INICIAL VS NP POR POZO
    # =========================

    st.markdown("<div class='section-title'>Análisis de producción acumulada por campaña</div>", unsafe_allow_html=True)

    # Base de producción con acumuladas calculadas
    df_prod_term = calcular_columnas_produccion(df.copy())

    # =========================
    # FILTRO DE TIEMPO PARA NP
    # =========================
    c_np1, c_np2 = st.columns([1, 3])

    with c_np1:
        meses_np = st.selectbox(
            "Np acumulada a:",
            ["Total", "12 meses", "36 meses", "60 meses"],
            index=0,
            key="filtro_np_meses_term"
        )

    df_prod_term = df_prod_term.sort_values([COL_POZO, COL_FECHA]).copy()

    # Mes normalizado por pozo: 1, 2, 3, ...
    df_prod_term["MES_PROD_TERM"] = (
        df_prod_term
        .groupby(COL_POZO)
        .cumcount() + 1
    )

    if meses_np == "12 meses":
        df_prod_np = df_prod_term[df_prod_term["MES_PROD_TERM"] <= 12].copy()
        nombre_np = "Np a 12 meses"

    elif meses_np == "36 meses":
        df_prod_np = df_prod_term[df_prod_term["MES_PROD_TERM"] <= 36].copy()
        nombre_np = "Np a 36 meses"

    elif meses_np == "60 meses":
        df_prod_np = df_prod_term[df_prod_term["MES_PROD_TERM"] <= 60].copy()
        nombre_np = "Np a 60 meses"

    else:
        df_prod_np = df_prod_term.copy()
        nombre_np = "Np (mb)"

    # Np acumulada al periodo seleccionado
    np_pozo = (
        df_prod_np
        .sort_values([COL_POZO, COL_FECHA])
        .groupby(COL_POZO, as_index=False)
        .agg(
            NP_FINAL=(COL_NP, "last")
        )
    )
    # Base de producción con acumuladas calculadas
    #df_prod_term = calcular_columnas_produccion(df.copy())

    # Última Np de cada pozo
    #np_pozo = (
    #    df_prod_term
    #    .sort_values([COL_POZO, COL_FECHA])
    #    .groupby(COL_POZO, as_index=False)
    #    .agg(
    #        NP_FINAL=(COL_NP, "last")
    #    )
    #)

    # Unir Np con los pozos filtrados de TERM
    term_np = term_f.merge(
        np_pozo,
        on=COL_POZO,
        how="left"
    )

    term_np["NP_FINAL"] = pd.to_numeric(term_np["NP_FINAL"], errors="coerce").fillna(0)

    term_np = term_np.sort_values([col_anio, COL_POZO])

    term_np["POZO_CAMP"] = (
        term_np[col_anio].astype(int).astype(str)
        + " | "
        + term_np[COL_POZO].astype(str)
    )

    # =========================
    # 4.1 GASTO INICIAL Y NP FINAL POR POZO
    # =========================

    # =========================
# 4.1 GASTO INICIAL Y NP POR POZO / TIEMPO
# =========================

    modo_fig4 = st.radio(
        "Vista gráfico Qoi / Np",
        [
            "Qoi y Np en barras",
            "Solo Np en scatter"
        ],
        horizontal=True,
        key="modo_fig4_np"
    )

    if modo_fig4 == "Qoi y Np en barras":

        fig4 = make_subplots(specs=[[{"secondary_y": True}]])

        fig4.add_trace(
            go.Bar(
                x=term_np["POZO_CAMP"],
                y=term_np[col_qoi],
                name="Qoi (bpd)",
                marker=dict(
                    color="#00A65A",
                    line=dict(color="#000000", width=1.5)
                ),
                text=term_np[col_qoi].round(1),
                textposition="outside",
                textfont=dict(
                    size=12,
                    color="black",
                    family="Tahoma"
                ),
                opacity=0.80
            ),
            secondary_y=False
        )

        fig4.add_trace(
        go.Scatter(
            x=term_np["POZO_CAMP"],
            y=term_np["NP_FINAL"],

            name=nombre_np,

            mode="lines+markers+text",

            line=dict(
                color="#1F4E79",
                width=3
            ),

            marker=dict(
                size=9,
                color="#1F4E79",
                line=dict(
                    color="white",
                    width=1
                )
            ),

            text=term_np["NP_FINAL"].round(1),

            textposition="top center",

            textfont=dict(
                size=11,
                color="black",
                family="Tahoma"
            )
            ),
            secondary_y=True
        )

        fig4.update_layout(
            title=f"<b>Gasto inicial y {nombre_np} por pozo</b>",
            xaxis=dict(
                tickangle=-75,
                categoryorder="array",
                categoryarray=term_np["POZO_CAMP"]
            ),
            height=650,
            template="plotly_white",
            barmode="group",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.12,
                xanchor="center",
                x=0.5
            ),
            font=dict(
                size=14,
                color="black",
                family="Arial Black"
            ),
            plot_bgcolor="white",
            paper_bgcolor="white"
        )

        fig4.update_xaxes(
            title_text="Campaña | Terminación",
            showline=True,
            linewidth=1,
            linecolor="black",
            tickfont=dict(
                size=11,
                color="black",
                family="Tahoma"
            )
        )

        fig4.update_yaxes(
            title_text="Qoi (bpd)",
            secondary_y=False,
            showgrid=True,
            gridcolor="#EAECEE",
            showline=True,
            linewidth=1,
            linecolor="black",
            tickfont=dict(
                size=12,
                color="black",
                family="Arial Black"
            )
        )

        fig4.update_yaxes(
            title_text=f"{nombre_np}",
            secondary_y=True,
            showgrid=False,
            tickfont=dict(
                size=12,
                color="black",
                family="Arial Black"
            )
        )

        st.plotly_chart(fig4, use_container_width=True)

    else:

        # Datos de Np por tiempo para los pozos filtrados en TERM
        pozos_term_np = term_np[COL_POZO].dropna().astype(str).unique().tolist()

        df_scatter_np = df_prod_np[
            df_prod_np[COL_POZO].astype(str).isin(pozos_term_np)
        ].copy()

        df_scatter_np = df_scatter_np.merge(
            term_np[[COL_POZO, col_anio]].drop_duplicates(),
            on=COL_POZO,
            how="left"
        )

        fig4 = px.scatter(
            df_scatter_np,
            x="MES_PROD_TERM",
            y=COL_NP,
            color=COL_POZO,
            symbol=col_anio,
            hover_name=COL_POZO,
            hover_data={
                col_anio: True,
                "MES_PROD_TERM": True,
                COL_NP: ":,.1f"
            },
            title=f"<b>Comportamiento de {nombre_np} por tiempo de producción</b>",
            template="plotly_white"
        )

        fig4.update_traces(
            mode="lines+markers",
            marker=dict(
                size=5,
                line=dict(color="black", width=0.5)
            ),
            line=dict(width=2)
        )

        fig4.update_layout(
            height=560,
            legend_title_text="Pozo",
            font=dict(
                size=14,
                color="black",
                family="Arial Black"
            ),
            plot_bgcolor="white",
            paper_bgcolor="white"
        )

        fig4.update_xaxes(
            title_text="Tiempo de producción, meses",
            dtick=6,
            showline=True,
            linewidth=1,
            linecolor="black",
            tickfont=dict(
                size=12,
                color="black",
                family="Arial Black"
            )
        )

        fig4.update_yaxes(
            title_text=f"{nombre_np}",
            showgrid=True,
            gridcolor="#EAECEE",
            showline=True,
            linewidth=1,
            linecolor="black",
            tickfont=dict(
                size=12,
                color="black",
                family="Arial Black"
            )
        )

        st.plotly_chart(fig4, use_container_width=True)

    # =========================
    # 4.2 NP PROMEDIO Y NÚMERO DE POZOS POR CAMPAÑA
    # =========================

    resumen_np = term_np.groupby(col_anio, as_index=False).agg(
        NP_PROM=("NP_FINAL", "mean"),
        POZOS=(COL_POZO, "nunique")
    )

    fig5 = go.Figure()

    fig5.add_trace(
        go.Bar(
            x=resumen_np[col_anio],
            y=resumen_np["NP_PROM"],
            name="Np promedio",
            marker=dict(
                color="#FFA500",
                line=dict(color="#000000", width=1.5)
            ),
            text=resumen_np["NP_PROM"].round(1),
            textposition="outside",
            textfont=dict(
                size=13,
                color="black",
                family="Tahoma"
            ),
            opacity=0.80
        )
    )

    for x, y, p in zip(
        resumen_np[col_anio],
        resumen_np["NP_PROM"],
        resumen_np["POZOS"]
    ):
        fig5.add_annotation(
            x=x,
            y=y * 0.05,
            text=f"<b>{p} pozos</b>",
            showarrow=False,
            font=dict(
                size=12,
                color="black",
                family="Arial Black"
            )
        )

    fig5.update_layout(
        title=f"<b>{nombre_np} promedio y pozos por campaña</b>",
        #title="<b>Np promedio y pozos por campaña</b>",
        height=520,
        template="plotly_white",
        font=dict(
            size=14,
            color="black",
            family="Arial Black"
        ),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig5.update_xaxes(
        title_text="Campaña",
        dtick=1,
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(
            size=12,
            color="black",
            family="Arial Black"
        )
    )

    fig5.update_yaxes(
        title_text=f"{nombre_np}",
        #title_text="Np promedio (mbl)",
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(
            size=12,
            color="black",
            family="Arial Black"
        )
    )

    # =========================
    # 4.3 BOXPLOT NP POR CAMPAÑA
    # =========================

    fig6 = px.box(
        term_np,
        x=col_anio,
        y="NP_FINAL",
        points="all",
        hover_name=COL_POZO,
        title="<b>Modelo estadístico Np por campaña</b>",
        #title="<b>Modelo estadístico Np por campaña</b>",
        template="plotly_white"
    )

    fig6.update_traces(
        marker=dict(
            color="#F4B183",
            size=7,
            opacity=0.65,
            line=dict(color="black", width=1)
        ),
        line=dict(color="#C55A11", width=1),
        fillcolor="rgba(244,177,131,0.35)"
    )

    medianas_np = term_np.groupby(col_anio, as_index=False)["NP_FINAL"].median()

    fig6.add_trace(go.Scatter(
        x=medianas_np[col_anio],
        y=medianas_np["NP_FINAL"],
        mode="text",
        text=medianas_np["NP_FINAL"].round(1),
        textposition="top center",
        textfont=dict(
            size=10,
            color="black"
        ),
        name="Mediana",
        showlegend=False
    ))

    fig6.update_layout(
        height=520,
        xaxis_title="Campaña",
        yaxis_title=f"{nombre_np}",
        #yaxis_title="Producción Acumulada (mbl)",
        font=dict(
            size=14,
            color="black",
            family="Arial Black"
        ),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig6.update_xaxes(
        dtick=1,
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(
            size=12,
            color="black",
            family="Arial Black"
        )
    )

    fig6.update_yaxes(
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(
            size=12,
            color="black",
            family="Arial Black"
        )
    )

    colnp1, colnp2 = st.columns(2)

    with colnp1:
        st.plotly_chart(fig5, use_container_width=True)

    with colnp2:
        st.plotly_chart(fig6, use_container_width=True)
        
    # =========================
    # MAPA DE BURBUJAS FILTRADO CON TERM
    # =========================
    #st.markdown("<div class='section-title'>Mapa de pozos seleccionados en TERM</div>", unsafe_allow_html=True)

    pozos_term = term_f[COL_POZO].dropna().astype(str).unique().tolist()

    df_mapa_term = df.copy()
    df_coord_term = df_coord.copy()
    #df_mapa_term = df[df[COL_POZO].astype(str).isin(pozos_term)].copy()
    #df_coord_term = df_coord[df_coord[COL_POZO].astype(str).isin(pozos_term)].copy()

    if df_coord_term.empty:
        st.warning("Los pozos seleccionados en TERM no tienen coordenadas en Coord.")
    else:
        mapa_burbujas(df_mapa_term, df_coord_term)

# =========================================================
# FILTROS
# =========================================================
st.markdown("<div class='filter-box'>", unsafe_allow_html=True)

# No se usa filtro de CONTA.
# No se completan fechas.
# Se grafica solamente lo que existe en la base.
f1, f2, f3, f4 = st.columns([1.7, 2.3, 2.3, 2.2])

with f1:
    yacs = sorted(df[COL_YAC].dropna().astype(str).unique())
    yac_sel = st.multiselect("Filtro por Yacimiento", yacs, default=yacs)

# El filtro de Yacimiento solo se usa para listar/seleccionar pozos.
df_base_filtro = df[df[COL_YAC].astype(str).isin(yac_sel)].copy() if yac_sel else df.copy()

with f2:
    pozos = sorted(df_base_filtro[COL_POZO].dropna().astype(str).unique())

    if not pozos:
        st.warning("No hay pozos para el yacimiento seleccionado.")
        st.stop()

    pozo_sel = st.selectbox("Pozo / Terminación", pozos)

# Base real del pozo seleccionado.
# Se toma desde df completo para no truncar la historia real del pozo.
df_pozo_raw = df[df[COL_POZO].astype(str) == str(pozo_sel)].copy()

with f3:
    min_date = df_pozo_raw[COL_FECHA_FILTRO].min().date()
    max_date = df_pozo_raw[COL_FECHA_FILTRO].max().date()

    date_range = st.date_input(
        "Rango de fechas",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

with f4:
    vista = st.radio(
        "Tipo de análisis",
        ["Producción por pozo", "Comparativa por pozo", "Mapa de burbujas", "Campañas 2011-2020"],
        horizontal=True
    )
    #vista = st.radio(
     #   "Tipo de análisis",
      #  ["Producción por pozo", "Comparativa por pozo", "Mapa de burbujas"],
       # horizontal=True
    #)

st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# FILTRO DE FECHAS SIN ACOMPLETAR CALENDARIO
# =========================================================
if isinstance(date_range, tuple) and len(date_range) == 2:
    f_ini = pd.to_datetime(date_range[0]).normalize()
    f_fin = pd.to_datetime(date_range[1]).normalize()
else:
    f_ini = df_pozo_raw[COL_FECHA_FILTRO].min()
    f_fin = df_pozo_raw[COL_FECHA_FILTRO].max()

# Cambio clave:
# Se calculan columnas directamente sobre la base real del pozo.
# Ya no se llama completar_fechas_por_pozo().
#dfp_full = calcular_columnas_produccion(df_pozo_raw)

df_pozo_completo = completar_fechas_pozo(df_pozo_raw)
dfp_full = calcular_columnas_produccion(df_pozo_completo)

dfp = dfp_full[
    (dfp_full[COL_FECHA_FILTRO] >= f_ini) &
    (dfp_full[COL_FECHA_FILTRO] <= f_fin)
].copy()

dfp = dfp.sort_values(COL_FECHA).reset_index(drop=True)

if dfp.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# Primer y último registro con producción real para KPIs
prod_total = dfp[[COL_ACEITE_BBL, COL_AGUA_BBL, COL_GAS_PC]].fillna(0).sum(axis=1)
df_prod = dfp[prod_total > 0].copy()
if df_prod.empty:
    df_prod = dfp.copy()

first_row = df_prod.iloc[0]
last_row = df_prod.iloc[-1]

# =========================================================
# KPIs
# =========================================================
if vista == "Producción por pozo":

    st.markdown(
        f"<span class='small-note'>Pozo seleccionado: <b>{pozo_sel}</b> | "
        f"Yacimiento: <b>{first_row.get(COL_YAC, '')}</b> | ",
        #f"Conta: <b>{first_row.get(COL_CONTA, '')}</b> | "
        #f"Registros reales cargados: <b>{len(dfp)}</b></span>",
        unsafe_allow_html=True
    )

    k1, k2, k3, k4, k5, k6, k7, k8, k9 = st.columns(9)

    k1.metric("Inicio producción", first_row[COL_FECHA].strftime("%d/%m/%Y"))
    k2.metric("Última producción", last_row[COL_FECHA].strftime("%d/%m/%Y"))
    k3.metric("Gasto Inicial", f"{first_row[COL_QO]:,.1f} bpd")
    k4.metric("Último Gasto Aceite", f"{last_row[COL_QO]:,.1f} bpd")
    k5.metric("Último Gasto Agua", f"{last_row[COL_QW]:,.1f} bpd")
    k6.metric("Último Gasto Gas", f"{last_row[COL_QG]:,.1f} mpcd")
    k7.metric("Acumulada Aceite", f"{dfp[COL_NP].iloc[-1]:,.2f} mbl")
    k8.metric("Acumulada Agua", f"{dfp[COL_WP].iloc[-1]:,.2f} mbl")
    k9.metric("Acumulada Gas", f"{dfp[COL_GP].iloc[-1]:,.2f} mmpc")

# =========================================================
# FUNCIÓN PARA GRÁFICAS COMPARATIVAS
# =========================================================
def comparative_plot(data, y_col, title, y_title, pozos_sel_comp, semilog=False, normalizar_tiempo=False):

    fig = go.Figure()
    df_promedio = pd.DataFrame()

    x_label = "Tiempo normalizado" if normalizar_tiempo else "Fecha"

    for pozo in pozos_sel_comp:
        dfi = data[data[COL_POZO].astype(str) == str(pozo)].copy()
        dfi = dfi.sort_values(COL_FECHA).reset_index(drop=True)

        if dfi.empty:
            continue

        dfi[COL_TIEMPO_NORM] = range(len(dfi))

        tmp = dfi[[COL_TIEMPO_NORM, y_col]].copy()
        tmp.columns = [COL_TIEMPO_NORM, pozo]

        if df_promedio.empty:
            df_promedio = tmp
        else:
            df_promedio = df_promedio.merge(
                tmp,
                on=COL_TIEMPO_NORM,
                how="outer"
            )

        if normalizar_tiempo:
            x_values = dfi[COL_TIEMPO_NORM]
            hover_x = "Mes normalizado: %{x}"
        else:
            x_values = dfi[COL_FECHA]
            hover_x = "Fecha: %{x|%d/%m/%Y}"

        y_values = dfi[y_col].copy()

        if semilog:
            y_values = y_values.replace(0, np.nan)

        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="lines+markers",
                name=str(pozo),
                line=dict(width=2.5),
                marker=dict(size=4),
                connectgaps=False,
                hovertemplate=
                    "<b>Pozo: %{fullData.name}</b><br>" +
                    hover_x + "<br>" +
                    f"{y_title}: " + "%{y:,.2f}<extra></extra>"
            )
        )

    # PROMEDIO SOLO CUANDO ESTÁ NORMALIZADO
    if normalizar_tiempo and not df_promedio.empty:

        cols_prom = [
            c for c in df_promedio.columns
            if c != COL_TIEMPO_NORM
        ]

        if semilog:
            df_promedio[cols_prom] = df_promedio[cols_prom].replace(0, np.nan)

        df_promedio["PROMEDIO"] = df_promedio[cols_prom].mean(axis=1, skipna=True)

        fig.add_trace(
            go.Scatter(
                x=df_promedio[COL_TIEMPO_NORM],
                y=df_promedio["PROMEDIO"],
                mode="lines",
                name="PROMEDIO",
                line=dict(
                    width=5,
                    color="black",
                    dash="dash"
                )
            )
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=18, family="Arial", color="#17202A")),
        template="plotly_white",
        hovermode="x unified",
        height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=35, r=35, t=60, b=35),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(
            family="Tahoma",
            size=16,
            color="black"
        )
    )

    fig.update_xaxes(
        title_text=f"<b>{x_label}</b>",
        tickformat="%d/%m/%Y" if not normalizar_tiempo else None,
        showgrid=True,
        gridcolor="#EAECEE",
        zeroline=False,
        tickfont=dict(size=18, color="black"),
        showline=True,
        linewidth=0.5,
        linecolor="black"
    )

    fig.update_yaxes(
        title_text=f"<b>{y_title}</b>",
        type="log" if semilog else "linear",
        tickvals=[0.1, 1, 10, 100, 1000, 10000, 100000] if semilog else None,
        ticktext=["0.1", "1", "10", "100", "1000","10000","100000"] if semilog else None,
        showgrid=True,
        gridcolor="#EAECEE",
        zeroline=False,
        separatethousands=True,
        tickfont=dict(size=18, color="black"),
        showline=True,
        linewidth=0.5,
        linecolor="black"
    )

    return fig

# =========================================================
# VISTA POZO INDIVIDUAL
# =========================================================
if vista == "Producción por pozo":

    fig1 = make_subplots(specs=[[{"secondary_y": True}]])

    fig1.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_QO],
            mode="lines+markers",
            name="Qo (bpd)",
            line=dict(width=3, color="#27AE60"),
            marker=dict(size=3),
            fill="tozeroy",
            fillcolor="rgba(39,174,96,0.25)",
            connectgaps=False
        ),
        secondary_y=False
    )

    fig1.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_WC],
            mode="lines+markers",
            name="% Agua",
            line=dict(width=2, color="#0000FF"),
            marker=dict(size=3),
            connectgaps=False
        ),
        secondary_y=False
    )

    fig1.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_NP],
            mode="lines+markers",
            name="Np (mbl)",
            line=dict(width=3, color="#008000"),
            marker=dict(size=3),
            connectgaps=False
        ),
        secondary_y=True
    )

    fig1.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_QG],
            mode="lines+markers",
            name="Qg (mpcd)",
            line=dict(width=3, color="#FF0000"),
            marker=dict(size=3),
            connectgaps=False
        ),
        secondary_y=True
    )

    fig1.update_layout(
        title="Gasto de aceite, % Agua, Acumulada de aceite y Gasto de gas",
        template="plotly_white",
        hovermode="x unified",
        height=520,
        legend=dict(orientation="h", y=1.02),
        margin=dict(l=35, r=35, t=60, b=35)
    )

    fig1.update_xaxes(title_text="<b>Fecha</b>", title_font=dict(size=22), 
    tickformat="%d/%m/%Y", tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
    linewidth=1,
    linecolor='black')

    fig1.update_yaxes(title_text="<b>Qo (bpd) / % Agua</b>",title_font=dict(size=22),
     secondary_y=False, tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
    linewidth=1,
    linecolor='black')

    fig1.update_yaxes(title_text="Np (mbl) / Qg (mpcd)", title_font=dict(size=22),
     secondary_y=True,tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
    linewidth=1,
    linecolor='black')

    st.plotly_chart(fig1, use_container_width=True)

    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

    fig2.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_QW],
            mode="lines+markers",
            name="Qw (bpd)",
            line=dict(width=3, color="#3498DB"),
            marker=dict(size=3),
            fill="tozeroy",
            fillcolor="rgba(52,152,219,0.20)",
            connectgaps=False
        ),
        secondary_y=False
    )

    fig2.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_WP],
            mode="lines+markers",
            name="Wp (mbl)",
            line=dict(width=3, color="#154360"),
            marker=dict(size=3),
            connectgaps=False
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

    fig2.update_xaxes(title_text="Fecha", tickformat="%d/%m/%Y", title_font=dict(size=22), tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
    linewidth=1,
    linecolor='black')
    fig2.update_yaxes(title_text="Qw (bpd)", title_font=dict(size=22),
     secondary_y=False, tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
    linewidth=1,
    linecolor='black')
    fig2.update_yaxes(title_text="Wp (mbl)", title_font=dict(size=22),
     secondary_y=True, tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
    linewidth=1,
    linecolor='black')

    st.plotly_chart(fig2, use_container_width=True)

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])

    
    fig3.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_RGA],
            mode="lines+markers",
            name="RGA (pc/bl)",
            line=dict(width=2, color="#FF0000"),
            marker=dict(size=3),
            fill="tozeroy",
            fillcolor="rgba(231,76,60,0.20)",
            connectgaps=False
        ),
        secondary_y=False
    )

    fig3.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_GP],
            mode="lines+markers",
            name="Gp (mmpc)",
            line=dict(width=3, color="#641E16"),
            marker=dict(size=3),
            connectgaps=False
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

    fig3.update_xaxes(title_text="Fecha", tickformat="%d/%m/%Y", title_font=dict(size=22), tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
    linewidth=1,
    linecolor='black')
    fig3.update_yaxes(title_text="RGA (pc/bl)", title_font=dict(size=22),
     secondary_y=False, tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
    linewidth=1,
    linecolor='black')
    fig3.update_yaxes(title_text="Gp (mmpc)", title_font=dict(size=22),
     secondary_y=True, tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
    linewidth=1,
    linecolor='black')

    st.plotly_chart(fig3, use_container_width=True)

    
# VISTA COMPARATIVO
# =========================================================
elif vista == "Comparativa por pozo":

    st.markdown(
        "<div class='section-title'>Comparativo de producción por pozos seleccionados</div>",
        unsafe_allow_html=True
    )

    pozos_comp = sorted(df_base_filtro[COL_POZO].dropna().astype(str).str.strip().unique())

    pozos_sel_comp = st.multiselect(
    "Selecciona pozos para comparar",
    pozos_comp,
    default=[str(pozo_sel).strip()] if str(pozo_sel).strip() in pozos_comp else []
    )

    modo_comparacion = st.radio(
        "Modo de comparación",
        ["Fecha real", "Normalizado a tiempo 0"],
        horizontal=True
    )

    normalizar_tiempo = (
        modo_comparacion == "Normalizado a tiempo 0"
    )

    modo_escala = st.radio(
    "Escala de gráficos",
    ["Semilog", "Lineal"],
    horizontal=True
    )

    usar_semilog = modo_escala == "Semilog"

    if pozos_sel_comp:

        df_comp_raw = df[
            df[COL_POZO].astype(str).str.strip().isin(pozos_sel_comp)
        ].copy()

        lista_pozos_completos = []

        for pozo in pozos_sel_comp:
            df_pozo_tmp = df_comp_raw[
                df_comp_raw[COL_POZO].astype(str).str.strip() == str(pozo).strip()
            ].copy()

            if not df_pozo_tmp.empty:
                df_pozo_tmp = completar_fechas_pozo(df_pozo_tmp)
                lista_pozos_completos.append(df_pozo_tmp)

        if lista_pozos_completos:

            df_comp_raw = pd.concat(lista_pozos_completos, ignore_index=True)

            df_comp = calcular_columnas_produccion(df_comp_raw)

            # Rango de fechas propio de los pozos seleccionados
            f_ini_comp = df_comp[COL_FECHA_FILTRO].min()
            f_fin_comp = df_comp[COL_FECHA_FILTRO].max()

            df_comp = df_comp[
                (df_comp[COL_FECHA_FILTRO] >= f_ini_comp) &
                (df_comp[COL_FECHA_FILTRO] <= f_fin_comp)
            ].copy()

            df_comp = df_comp.sort_values([COL_POZO, COL_FECHA]).reset_index(drop=True)

            st.plotly_chart(
                comparative_plot(
                    df_comp,
                    COL_QO,
                    "Comparativo semilog de producción de aceite por pozo",
                    "Qo (bpd)",
                    pozos_sel_comp,
                    semilog=usar_semilog,
                    normalizar_tiempo=normalizar_tiempo
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
                    semilog=usar_semilog,
                    normalizar_tiempo=normalizar_tiempo
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
                    #semilog=usar_semilog,
                    normalizar_tiempo=normalizar_tiempo
                ),
                use_container_width=True
            )

        else:
            st.warning("No hay datos disponibles para los pozos seleccionados.")

    else:
        st.info("Selecciona uno o más pozos para generar el comparativo.")


# VISTA MAPA DE BURBUJAS
# =========================================================
elif vista == "Mapa de burbujas":
    mapa_burbujas(df, df_coord)
elif vista == "Campañas 2011-2020":
    analisis_term()

#st.caption("Desarrollado en Python + Streamlit.")
