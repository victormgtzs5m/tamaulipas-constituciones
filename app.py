import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import plotly.express as px
import streamlit.components.v1 as components
from pathlib import Path
import os
import re
import unicodedata


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
st.set_page_config(
    page_title="Campo Tamaulipas Constituciones",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)
#st.cache_data.clear()
# =========================================================
# RUTA DE LA BASE DE DATOS
# Cambia esta ruta si tu archivo .db está en otra carpeta.
# =========================================================

# Ruta de la base datos
ruta_db = "prodcoord.db"

# Tablas"""  """
TABLA_PROD = "Produccion"
TABLA_COORD = "Coord"
TABLA_CONTORNO = "Contorno"
TABLA_ASIGNACION = "Asignacion"
TABLA_TERM = "TERM"
TABLA_RMA = "RMA"
TABLA_ESTADO_POZOS = "Estado"
TABLA_PRESIONES = "Presiones"
TABLA_OPERACION = "Operacion"
TABLA_INYECTORES = "Inyectores"
TABLA_EVENTOS = "Eventos"
TABLA_LOCALIZACIONES = "Localizaciones"
TABLA_INSTA = "Instalaciones"
TABLA_RESERVAS = "Reservas"

URL_MUESTREOS_AGUA = "https://raw.githubusercontent.com/victormgtzs5m/tamaulipas-constituciones/main/Muestreos.xlsx"
URL_SEGUIMIENTO = "https://raw.githubusercontent.com/victormgtzs5m/tamaulipas-constituciones/main/Seguimiento.xlsx"

#Leer archivo db
@st.cache_data(show_spinner=False)
def load_table(tabla):

    conn = sqlite3.connect(ruta_db)

    df = pd.read_sql(
        f"SELECT * FROM {tabla}",
        conn
    )

    conn.close()

    return df

# =========================================================
# COLUMNAS DE LA BASE NUEVA
# La base solo debe traer estas columnas:
# Terminacion, Fecha, Yacimiento, Conta, Dias, Aceite, Gas, Agua, Iny
# =========================================================
COL_POZO = "TERMINACION"
COL_POZO_FISICO = "POZO"
COL_FECHA = "FECHA"
COL_YAC = "YACIMIENTO"
COL_CONTA = "CONTA"
COL_DIAS = "DIAS"
COL_ACEITE = "ACEITE"
COL_GAS = "GAS"
COL_AGUA = "AGUA"
COL_INY = "INJ"

# Columnas calculadas para el visualizador
COL_ACEITE_BBL = "Aceite (bl)"
COL_AGUA_BBL = "Agua (bl)"
COL_GAS_PC = "Gas (pc)"
COL_INY_BBL = "Agua inyectada (bl)"

COL_QO = "Qo (bpd)"
COL_QW = "Qw (bpd)"
COL_QIN = "Qiny (bpd)"
COL_QG = "Qg (mpcd)"
COL_QG_PCD = "Qg (pcd)"

COL_NP = "Np (mbl)"
COL_WP = "Wp (mbl)"
COL_WINJ = "Winj (mbl)"
COL_GP = "Gp (mmpc)"

COL_WC = "%Agua"
COL_RGA = "RGA (pc/bl)"
COL_FECHA_FILTRO = "FECHA_FILTRO"

COL_TIEMPO_NORM = "Tiempo normalizado"


REQUIRED_COLS = [
    COL_POZO, COL_FECHA, COL_YAC, COL_CONTA,
    COL_DIAS, COL_ACEITE, COL_GAS, COL_AGUA, COL_INY
]

OPTIONAL_COLS = [
    COL_POZO_FISICO
]

# Factores de conversión
M3_A_BBL = 6.289810770
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
    
        /* Filtros multiselect */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        min-height: 44px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
    }

    /* Etiquetas seleccionadas */
    span[data-baseweb="tag"] {
    background-color: #1F4E79 !important;
    }

    /* Texto de filtros */
    div[data-baseweb="select"] span {
        font-weight: 600;
    }

    /* Botón X de cada etiqueta */
    span[data-baseweb="tag"] svg {
        fill: white !important;
    }
</style>
""", unsafe_allow_html=True)


def es_movil():
    return st.session_state.get("mobile_view", False)

def cargar_inyectores():
    df = load_table(TABLA_INYECTORES)

    if df.empty:
        return df

    df.columns = df.columns.str.strip()

    # Homologar columnas
    df["Pozo"] = df["Pozo"].astype(str).str.strip()
    df["TERMINACION"] = df["TERMINACION"].astype(str).str.strip()
    df["Yacimiento"] = df["Yacimiento"].astype(str).str.strip()

    # Vi en m3 a bls
    df["Vi"] = pd.to_numeric(df["Vi"], errors="coerce").fillna(0)
    df["VI_BLS"] = df["Vi"] * 6.28981

    return df

def inyeccion():
    st.markdown(
        "<div class='section-title'>Mapa de inyección de agua</div>",
        unsafe_allow_html=True
    )

    df_iny = cargar_inyectores()
    df_coord = load_table(TABLA_COORD)
    contorno, asignacion = load_contorno_asignacion()

    if df_iny.empty:
        st.warning("No existe información en la tabla Inyectores.")
        return

    if df_coord.empty:
        st.warning("No existe información en la tabla Coord.")
        return

    df_coord.columns = df_coord.columns.str.strip()

    df_iny["Pozo"] = df_iny["Pozo"].astype(str).str.strip()
    df_coord["Pozo"] = df_coord["Pozo"].astype(str).str.strip()

    coord_pozo = (
        df_coord
        .dropna(subset=["Fondo X UTM", "Fondo Y UTM"])
        .drop_duplicates(subset=["Pozo"], keep="first")
        [["Pozo", "Fondo X UTM", "Fondo Y UTM"]]
    )

    df_mapa = df_iny.merge(
        coord_pozo,
        on="Pozo",
        how="left"
    )

    df_mapa["Fondo X UTM"] = pd.to_numeric(df_mapa["Fondo X UTM"], errors="coerce")
    df_mapa["Fondo Y UTM"] = pd.to_numeric(df_mapa["Fondo Y UTM"], errors="coerce")
    df_mapa["VI_BLS"] = pd.to_numeric(df_mapa["VI_BLS"], errors="coerce").fillna(0)

    df_mapa = df_mapa.dropna(subset=["Fondo X UTM", "Fondo Y UTM"])

    if df_mapa.empty:
        st.warning("No hay pozos inyectores con coordenadas de fondo disponibles.")
        return

    c1, c2, c_zoom = st.columns([1.2, 1.8, 1.2])

    with c1:
        yacimientos = ["Todos"] + sorted(df_mapa["Yacimiento"].dropna().astype(str).unique())
        yacimiento_sel = st.selectbox(
            "Yacimiento",
            yacimientos,
            key="yac_inyeccion"
        )

    with c2:
        filtro_estado = st.radio(
            "Filtro de pozos",
            ["Todos", "Recibidos", "Funcionales", "Operando"],
            horizontal=True,
            key="filtro_estado_inyeccion"
        )

    df_plot = df_mapa.copy()

    if yacimiento_sel != "Todos":
        df_plot = df_plot[df_plot["Yacimiento"].astype(str) == str(yacimiento_sel)]

    if filtro_estado in ["Recibidos", "Funcionales", "Operando"]:
        df_plot[filtro_estado] = df_plot[filtro_estado].fillna("").astype(str).str.strip()
        df_plot = df_plot[df_plot[filtro_estado] != ""]

    if df_plot.empty:
        st.warning("No hay pozos para mostrar con los filtros seleccionados.")
        return

    with c_zoom:
        pozos_zoom_iny = sorted(df_plot["Pozo"].dropna().astype(str).unique())
        pozo_zoom_iny = st.selectbox(
            "Zoom a pozo",
            options=["Todos"] + pozos_zoom_iny,
            key=f"zoom_pozo_inyeccion_{yacimiento_sel}_{filtro_estado}"
        )

    c3, c4 = st.columns([1, 3])

    with c3:
        mostrar_nombres_iny = st.checkbox(
            "Mostrar nombres de pozos",
            value=True,
            key=f"mostrar_nombres_inyeccion_{yacimiento_sel}_{filtro_estado}"
        )

    with c4:
        c4_pozos, c4_m3, c4_bls = st.columns(3)

        with c4_pozos:
            st.caption("Pozos mostrados")
            st.markdown(
                f"<b style='color:#4B5563'>{df_plot['Pozo'].nunique():,.0f}</b> "
                "<span style='color:#6B7280'>pozos</span>",
                unsafe_allow_html=True
            )

        with c4_m3:
            st.caption("Volumen inyectado")
            st.markdown(
                f"<b style='color:#4B5563'>{df_plot['Vi'].sum()/1_000_000:,.2f}</b> "
                "<span style='color:#6B7280'>millones de m3</span>",
                unsafe_allow_html=True
            )

        with c4_bls:
            st.caption("Volumen inyectado")
            st.markdown(
                f"<b style='color:#4B5563'>{df_plot['VI_BLS'].sum()/1_000_000:,.2f}</b> "
                "<span style='color:#6B7280'>mmb</span>",
                unsafe_allow_html=True
            )

    fig = go.Figure()

    if not contorno.empty:
        fig.add_trace(go.Scatter(
            x=contorno["X"],
            y=contorno["Y"],
            mode="lines",
            name="Contorno",
            line=dict(color="black", width=2)
        ))

    if not asignacion.empty:
        if "ASIGNACION" in asignacion.columns:
            grupos_asig = asignacion.groupby("ASIGNACION")
        else:
            grupos_asig = [("Asignación", asignacion)]

        for nombre, grupo in grupos_asig:
            fig.add_trace(go.Scatter(
                x=grupo["X"],
                y=grupo["Y"],
                mode="lines",
                name=f"Asignación {nombre}",
                line=dict(width=2, dash="dot", color="red"),
                #opacity=1
            ))

    max_vi = df_plot["VI_BLS"].max()

    if max_vi > 0:
        size_burbuja = np.where(
            df_plot["VI_BLS"] > 0,
            12 + (df_plot["VI_BLS"] / max_vi) * 45,
            10
        )
    else:
        size_burbuja = 10

    fig.add_trace(go.Scatter(
        x=df_plot["Fondo X UTM"],
        y=df_plot["Fondo Y UTM"],
        mode="markers+text" if mostrar_nombres_iny else "markers",
        text=df_plot["Pozo"] if mostrar_nombres_iny else None,
        textposition="top center",
        textfont=dict(
            size=12,
            color="#1E88E5",
            family="Arial Black"
        ),
        marker=dict(
            size=size_burbuja,
            sizemode="diameter",
            color="#00ACC1",
            opacity=0.35,
            line=dict(
                color="#1E88E5",
                width=1.5
            )
        ),
        customdata=np.stack([
            df_plot["Pozo"],
            df_plot["TERMINACION"],
            df_plot["Yacimiento"],
            df_plot["Vi"],
            df_plot["VI_BLS"],
            df_plot["Estado"],
            df_plot["Estatus"]
        ], axis=-1),
        hovertemplate=
            "<b>%{customdata[0]}</b><br>" +
            "Terminación: %{customdata[1]}<br>" +
            "Yacimiento: %{customdata[2]}<br>" +
            "Vi: %{customdata[3]:,.0f} m³<br>" +
            "Vi: %{customdata[4]:,.0f} bls<br>" +
            "Estado: %{customdata[5]}<br>" +
            "Estatus: %{customdata[6]}<br>" +
            "<extra></extra>",
        name="Agua inyectada"
    ))

    if pozo_zoom_iny != "Todos":
        row_zoom_iny = df_plot[df_plot["Pozo"].astype(str) == str(pozo_zoom_iny)]

        if not row_zoom_iny.empty:
            x0 = row_zoom_iny["Fondo X UTM"].iloc[0]
            y0 = row_zoom_iny["Fondo Y UTM"].iloc[0]
            radio_zoom = 1000

            fig.update_xaxes(range=[x0 - radio_zoom, x0 + radio_zoom])
            fig.update_yaxes(range=[y0 - radio_zoom, y0 + radio_zoom])

            fig.add_trace(go.Scatter(
                x=[x0],
                y=[y0],
                mode="markers+text",
                text=[str(pozo_zoom_iny)],
                textposition="top center",
                textfont=dict(
                    size=16,
                    color="#D35400",
                    family="Arial Black"
                ),
                marker=dict(
                    size=22,
                    symbol="star",
                    color="#FFD700",
                    line=dict(color="black", width=2)
                ),
                name=f"Pozo: {pozo_zoom_iny}",
                hovertemplate=
                    "<b>Pozo:</b> %{text}<br>" +
                    "<extra></extra>",
                showlegend=True
            ))
 

    fig.update_layout(
        title=(
            "<b>Mapa de inyección - Campo completo</b>"
            if yacimiento_sel == "Todos"
            else f"<b>Mapa de inyección - {yacimiento_sel}</b>"
        ),
        height=950,
        xaxis_title="UTM X",
        yaxis_title="UTM Y",
        template="plotly_white",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            groupclick="togglegroup"
        ),
        margin=dict(l=20, r=20, t=70, b=20)
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black"
    )

    fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "displaylogo": False,
            "responsive": True,
            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d"
            ]
        }
    )

    st.markdown(
        "<div class='section-title'>Pozos inyectores mostrados en el mapa</div>",
        unsafe_allow_html=True
    )
    st.caption(f"Total de pozos en la tabla: {df_plot['Pozo'].nunique():,.0f}")

    st.dataframe(
        df_plot[[
            "Pozo",
            "TERMINACION",
            "Yacimiento",
            "Vi",
            "VI_BLS",
            "Estado",
            "Estatus",
            "Recibidos",
            "Funcionales",
            "Operando",
            "Fondo X UTM",
            "Fondo Y UTM"
        ]].sort_values("VI_BLS", ascending=False),
        use_container_width=True,
        hide_index=True,
        height=360
    )

def alta_operacion():

    st.markdown("<div class='section-title'>Alta diaria de operación</div>", unsafe_allow_html=True)


    with st.expander("➕ Alta diaria de operación", expanded=False):

        with st.form("form_alta_operacion"):

            fecha = st.date_input("Fecha de operación")

            c1, c2, c3 = st.columns(3)

            with c1:
                aceite = st.number_input("Aceite (bls)", min_value=0.0, step=1.0)
                agua_iny = st.number_input("Agua inyectada (bls)", min_value=0.0, step=1.0)
                gas_prod = st.number_input("Gas producido (MMPC)", min_value=0.0, step=0.001, format="%.3f")

            with c2:
                gas_cpg = st.number_input("Gas a CPG Arenque (MMPC)", min_value=0.0, step=0.001, format="%.3f")
                venteo = st.number_input("Venteo (MMPC)", min_value=0.0, step=0.001, format="%.3f")
                autoconsumo = st.number_input("Autoconsumo (MMPC)", min_value=0.0, step=0.001, format="%.3f")

            with c3:
                quema_bat = st.number_input("Quema Batería TC", min_value=0.0, step=0.001, format="%.3f")
                quema_ec = st.number_input("Quema EC T3", min_value=0.0, step=0.001, format="%.3f")
                gas_quema = st.number_input("Gas Quema (MMPC)", min_value=0.0, step=0.001, format="%.3f")

            guardar = st.form_submit_button("Guardar registro")

        if guardar:

            fecha_sql = pd.to_datetime(fecha).strftime("%Y-%m-%d")

            nuevo = pd.DataFrame([{
                "FECHA": fecha_sql,
                "ACEITE (BLS)": aceite,
                "AGUA INYECTADA (BLS)": agua_iny,
                "GAS PRODUCIDO (MMPC)": gas_prod,
                "GAS A CPG ARENQUE (MMPC)": gas_cpg,
                "VENTEO (MMPC)": venteo,
                "AUTOCONSUMO (MMPC)": autoconsumo,
                "QUEMA BATERIA TC": quema_bat,
                "QUEMA EC T3": quema_ec,
                "GAS QUEMA (MMPC)": gas_quema
            }])

            with sqlite3.connect(ruta_db) as conn:

                existe = pd.read_sql_query(
                    f"""
                    SELECT COUNT(*) AS n
                    FROM "{TABLA_OPERACION}"
                    WHERE FECHA = ?
                    """,
                    conn,
                    params=[fecha_sql]
                )["n"].iloc[0]

                if existe > 0:
                    st.warning("Ya existe un registro para esa fecha.")
                else:
                    nuevo.to_sql(
                        TABLA_OPERACION,
                        conn,
                        if_exists="append",
                        index=False
                    )

                    st.cache_data.clear()
                    st.success("Registro guardado correctamente.")
                    st.rerun()

     # =====================================================
    # ELIMINAR REGISTRO
    # =====================================================

    with st.expander("🗑️ Eliminar registro", expanded=False):

        try:

            with sqlite3.connect(ruta_db) as conn:

                fechas = pd.read_sql_query(
                f"""
                SELECT Fecha
                FROM "{TABLA_OPERACION}"
                ORDER BY Fecha DESC
                """,
                conn
            )["Fecha"].astype(str).tolist()

            if len(fechas) > 0:

                fecha_borrar = st.selectbox(
                    "Fecha a eliminar",
                    fechas,
                    key="fecha_borrar_operacion"
                )

                confirmar = st.checkbox(
                    "Confirmo eliminar este registro",
                    key="confirmar_borrado_operacion"
                )

                if st.button(
                    "Eliminar registro",
                    key="btn_eliminar_operacion"
                ):

                    if confirmar:

                        with sqlite3.connect(ruta_db) as conn:

                            conn.execute(
                            f"""
                            DELETE FROM "{TABLA_OPERACION}"
                            WHERE Fecha = ?
                            """,
                            [fecha_borrar]
                        )

                            conn.commit()

                        st.success(
                            f"Registro {fecha_borrar} eliminado correctamente."
                        )

                        st.cache_data.clear()
                        st.rerun()

                    else:

                        st.warning(
                            "Debe confirmar la eliminación."
                        )

            else:

                st.info("No existen registros para eliminar.")

        except Exception as e:

            st.error(f"Error al eliminar: {e}")
            
def kpi_card(titulo, valor, subtitulo="", color="#1F4E79"):
    components.html(
        f"""
        <div style="
            background:white;
            border-radius:10px;
            box-shadow:0 4px 14px rgba(0,0,0,0.12);
            overflow:hidden;
            border:1px solid #1F4E79;
            font-family:Arial, sans-serif;
            height:70px;
        ">
            <div style="
                background:{color};
                color:white;
                padding:8px 12px;
                font-size:10px;
                font-weight:700;
                letter-spacing:0.4px;
                text-transform:uppercase;
            ">
                {titulo}
            </div>

            <div style="
                padding:12px;
                display:flex;
                align-items:center;
                justify-content:space-between;
            ">
                <div style="
                    font-size:16px;
                    font-weight:800;
                    color:#111827;
                ">
                    {valor}
                    <span style="
                        font-size:12px;
                        font-weight:600;
                        color:#6B7280;
                    ">
                        {subtitulo}
                    </span>
                </div>               
            </div>
        </div>
        """,
        height=80
    )
# =========================================================
# FUNCIONES AUXILIARES
# =========================================================
def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte encabezados a mayúsculas para evitar errores por Fecha/FECHA, Aceite/ACEITE, etc."""
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df


def normalizar_clave_texto(serie) -> pd.Series:
    """Normaliza textos para comparar pozos/terminaciones sin depender de espacios o mayusculas."""
    return (
        serie.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"\s+", " ", regex=True)
    )


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

    for col in [COL_ACEITE, COL_GAS, COL_AGUA, COL_INY]:
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
    df[COL_INY_BBL] = df[COL_INY] * M3_A_BBL

    # Gastos promedio diarios
    dias_validos = df[COL_DIAS].replace(0, np.nan)
    df[COL_QO] = df[COL_ACEITE_BBL] / dias_validos
    df[COL_QIN] = df[COL_INY_BBL] / dias_validos
    df[COL_QW] = df[COL_AGUA_BBL] / dias_validos
    df[COL_QG_PCD] = df[COL_GAS_PC] / dias_validos
    df[COL_QG] = df[COL_QG_PCD] / 1000.0

    for col in [COL_QO, COL_QIN, COL_QW, COL_QG_PCD, COL_QG]:
        df[col] = df[col].replace([np.inf, -np.inf], np.nan).fillna(0)

    # Acumuladas por pozo usando únicamente registros reales de la base
    df[COL_NP] = df.groupby(COL_POZO)[COL_ACEITE_BBL].cumsum() / 1000.0
    df[COL_WP] = df.groupby(COL_POZO)[COL_AGUA_BBL].cumsum() / 1000.0
    df[COL_GP] = df.groupby(COL_POZO)[COL_GAS_PC].cumsum() / 1_000_000.0
    df[COL_WINJ] = df.groupby(COL_POZO)[COL_INY_BBL].cumsum() / 1000.0

    # RGA y corte de agua
    df[COL_RGA] = np.where(df[COL_QO] > 0, df[COL_QG_PCD] / df[COL_QO], 0)
    df[COL_WC] = np.where(
        (df[COL_QO] + df[COL_QW]) > 0,
        (df[COL_QW] / (df[COL_QO] + df[COL_QW])) * 100,
        0
    )

    return df.replace([np.inf, -np.inf], 0).fillna(0)


def agregar_pozo_fisico(df_base: pd.DataFrame, coord_base: pd.DataFrame) -> pd.DataFrame:
    """Agrega el nombre del pozo fisico, usando Produccion.POZO y Coord como respaldo."""
    df_out = df_base.copy()

    if COL_POZO_FISICO in df_out.columns:
        df_out["POZO_FISICO"] = df_out[COL_POZO_FISICO].astype(str).str.strip()
        sin_pozo = df_out["POZO_FISICO"].isna() | df_out["POZO_FISICO"].str.upper().isin(["", "NAN", "NONE"])
        df_out.loc[sin_pozo, "POZO_FISICO"] = df_out.loc[sin_pozo, COL_POZO].astype(str).str.strip()
    else:
        df_out["POZO_FISICO"] = df_out[COL_POZO].astype(str).str.strip()

    if coord_base.empty or COL_POZO not in coord_base.columns or COL_POZO_FISICO not in coord_base.columns:
        return df_out

    coord_pozo = (
        coord_base[[COL_POZO, COL_POZO_FISICO]]
        .dropna(subset=[COL_POZO])
        .copy()
    )
    coord_pozo[COL_POZO] = coord_pozo[COL_POZO].astype(str).str.strip()
    coord_pozo[COL_POZO_FISICO] = coord_pozo[COL_POZO_FISICO].astype(str).str.strip()
    coord_pozo = coord_pozo.drop_duplicates(subset=[COL_POZO])

    df_out = df_out.merge(
        coord_pozo,
        on=COL_POZO,
        how="left",
        suffixes=("", "_COORD")
    )

    col_coord = f"{COL_POZO_FISICO}_COORD" if COL_POZO_FISICO in df_base.columns else COL_POZO_FISICO
    if col_coord in df_out.columns:
        sin_pozo = df_out["POZO_FISICO"].isna() | df_out["POZO_FISICO"].astype(str).str.upper().isin(["", "NAN", "NONE"])
        df_out.loc[sin_pozo, "POZO_FISICO"] = df_out.loc[sin_pozo, col_coord]
        df_out = df_out.drop(columns=[col_coord])

    df_out["POZO_FISICO"] = df_out["POZO_FISICO"].fillna(df_out[COL_POZO]).astype(str).str.strip()

    return df_out


def preparar_historia_pozo_fisico(df_pozo_raw: pd.DataFrame):
    """Agrupa todas las terminaciones de un pozo fisico y calcula su historia total."""
    df_base = df_pozo_raw.copy().sort_values(COL_FECHA)

    if df_base.empty:
        return pd.DataFrame(), pd.DataFrame()

    pozo_fisico = (
        df_base["POZO_FISICO"].iloc[0]
        if "POZO_FISICO" in df_base.columns
        else df_base[COL_POZO].iloc[0]
    )

    df_base["VOL_PROD_YAC"] = (
        df_base[COL_ACEITE].fillna(0) +
        df_base[COL_AGUA].fillna(0) +
        df_base[COL_GAS].fillna(0)
    )
    df_base["VOL_INY_YAC"] = df_base[COL_INY].fillna(0)

    eventos_prod = (
        df_base[df_base["VOL_PROD_YAC"] > 0]
        .groupby(COL_YAC, as_index=False)
        .agg(
            FECHA_INICIO=(COL_FECHA, "min"),
            TERMINACIONES=(COL_POZO, lambda s: ", ".join(sorted(s.dropna().astype(str).unique())))
        )
    )
    eventos_prod["TIPO_EVENTO"] = "Producción"

    eventos_iny = (
        df_base[df_base["VOL_INY_YAC"] > 0]
        .groupby(COL_YAC, as_index=False)
        .agg(
            FECHA_INICIO=(COL_FECHA, "min"),
            TERMINACIONES=(COL_POZO, lambda s: ", ".join(sorted(s.dropna().astype(str).unique())))
        )
    )
    eventos_iny["TIPO_EVENTO"] = "Inyección"

    eventos_yac = (
        pd.concat([eventos_prod, eventos_iny], ignore_index=True)
        .sort_values(["FECHA_INICIO", "TIPO_EVENTO", COL_YAC])
        .reset_index(drop=True)
    )

    df_calc = calcular_columnas_produccion(df_base)

    def unir_unicos(serie):
        vals = [v for v in serie.dropna().astype(str).str.strip().unique() if v and v.upper() != "NAN"]
        return ", ".join(sorted(vals))

    df_hist = (
        df_calc
        .groupby(COL_FECHA, as_index=False)
        .agg(
            **{
                COL_DIAS: (COL_DIAS, "sum"),
                COL_ACEITE_BBL: (COL_ACEITE_BBL, "sum"),
                COL_AGUA_BBL: (COL_AGUA_BBL, "sum"),
                COL_GAS_PC: (COL_GAS_PC, "sum"),
                COL_INY_BBL: (COL_INY_BBL, "sum"),
                COL_QO: (COL_QO, "sum"),
                COL_QW: (COL_QW, "sum"),
                COL_QIN: (COL_QIN, "sum"),
                COL_QG_PCD: (COL_QG_PCD, "sum"),
                COL_QG: (COL_QG, "sum"),
                COL_YAC: (COL_YAC, unir_unicos),
                COL_POZO: (COL_POZO, unir_unicos),
                COL_CONTA: (COL_CONTA, unir_unicos),
            }
        )
        .sort_values(COL_FECHA)
    )

    fechas_completas = pd.DataFrame({
        COL_FECHA: pd.date_range(
            start=df_hist[COL_FECHA].min(),
            end=df_hist[COL_FECHA].max(),
            freq="MS"
        )
    })
    df_hist = fechas_completas.merge(df_hist, on=COL_FECHA, how="left")

    for col in [
        COL_DIAS, COL_ACEITE_BBL, COL_AGUA_BBL, COL_GAS_PC, COL_INY_BBL,
        COL_QO, COL_QW, COL_QIN, COL_QG_PCD, COL_QG
    ]:
        df_hist[col] = df_hist[col].fillna(0)

    for col in [COL_YAC, COL_POZO, COL_CONTA]:
        df_hist[col] = df_hist[col].fillna("")

    df_hist[COL_NP] = df_hist[COL_ACEITE_BBL].cumsum() / 1000.0
    df_hist[COL_WP] = df_hist[COL_AGUA_BBL].cumsum() / 1000.0
    df_hist[COL_GP] = df_hist[COL_GAS_PC].cumsum() / 1_000_000.0
    df_hist[COL_WINJ] = df_hist[COL_INY_BBL].cumsum() / 1000.0
    df_hist[COL_RGA] = np.where(df_hist[COL_QO] > 0, df_hist[COL_QG_PCD] / df_hist[COL_QO], 0)
    df_hist[COL_WC] = np.where(
        (df_hist[COL_QO] + df_hist[COL_QW]) > 0,
        (df_hist[COL_QW] / (df_hist[COL_QO] + df_hist[COL_QW])) * 100,
        0
    )
    df_hist[COL_FECHA_FILTRO] = df_hist[COL_FECHA]
    df_hist["POZO_FISICO"] = pozo_fisico

    return df_hist.replace([np.inf, -np.inf], 0).fillna(0), eventos_yac


def preparar_inyeccion_por_yacimiento(df_pozo_raw: pd.DataFrame) -> pd.DataFrame:
    """Calcula Qiny y Winj por yacimiento para el pozo/terminacion seleccionado."""
    columnas_salida = [COL_YAC, COL_FECHA, COL_INY_BBL, COL_QIN, COL_WINJ]

    if df_pozo_raw.empty:
        return pd.DataFrame(columns=columnas_salida)

    df_base = df_pozo_raw.copy().sort_values([COL_YAC, COL_FECHA])
    df_base[COL_INY] = pd.to_numeric(df_base[COL_INY], errors="coerce").fillna(0)
    df_base[COL_DIAS] = pd.to_numeric(df_base[COL_DIAS], errors="coerce").fillna(0)
    df_iny = df_base[df_base[COL_INY] > 0].copy()

    if df_iny.empty:
        return pd.DataFrame(columns=columnas_salida)

    df_iny[COL_INY_BBL] = df_iny[COL_INY] * M3_A_BBL
    dias_validos = df_iny[COL_DIAS].replace(0, np.nan)
    df_iny[COL_QIN] = (df_iny[COL_INY_BBL] / dias_validos).replace([np.inf, -np.inf], np.nan).fillna(0)

    df_iny_yac = (
        df_iny
        .groupby([COL_YAC, COL_FECHA], as_index=False)
        .agg(
            **{
                COL_INY_BBL: (COL_INY_BBL, "sum"),
                COL_QIN: (COL_QIN, "sum")
            }
        )
        .sort_values([COL_YAC, COL_FECHA])
    )
    df_iny_yac[COL_WINJ] = df_iny_yac.groupby(COL_YAC)[COL_INY_BBL].cumsum() / 1000.0

    fechas_completas = pd.DataFrame({
        COL_FECHA: pd.date_range(
            start=df_base[COL_FECHA].min(),
            end=df_base[COL_FECHA].max(),
            freq="MS"
        )
    })

    salida = []
    for yac, datos_yac in df_iny_yac.groupby(COL_YAC):
        datos_yac = datos_yac.sort_values(COL_FECHA).copy()
        completo_yac = fechas_completas.merge(datos_yac, on=COL_FECHA, how="left")
        completo_yac[COL_YAC] = yac
        completo_yac[COL_INY_BBL] = completo_yac[COL_INY_BBL].fillna(0)
        completo_yac[COL_WINJ] = completo_yac[COL_INY_BBL].cumsum() / 1000.0
        completo_yac.loc[completo_yac[COL_WINJ] <= 0, COL_WINJ] = np.nan
        completo_yac.loc[completo_yac[COL_INY_BBL] <= 0, COL_QIN] = np.nan
        salida.append(completo_yac)

    if not salida:
        return pd.DataFrame(columns=columnas_salida)

    return pd.concat(salida, ignore_index=True)


#Operacion Campo
@st.cache_data(show_spinner="Cargando datos de operación...")
def load_operacion() -> pd.DataFrame:
    op = load_table(TABLA_OPERACION)
    op = op.loc[:, ~op.columns.astype(str).str.startswith("Unnamed")]
    op = normalizar_columnas(op)

    cols_req = [
        "FECHA",
        "ACEITE (BLS)",
        "AGUA INYECTADA (BLS)",
        "GAS PRODUCIDO (MMPC)",
        "GAS A CPG ARENQUE (MMPC)",
        "VENTEO (MMPC)",
        "AUTOCONSUMO (MMPC)",
        "QUEMA BATERIA TC",
        "QUEMA EC T3",
        "GAS QUEMA (MMPC)"
    ]

    for c in cols_req:
        if c not in op.columns:
            st.error(f"No existe la columna '{c}' en la tabla Operacion.")
            st.write(op.columns.tolist())
            return pd.DataFrame()

    op["FECHA"] = convertir_fechas(op["FECHA"])

    for c in cols_req:
        if c != "FECHA":
            op[c] = pd.to_numeric(op[c], errors="coerce").fillna(0)

    op = op.dropna(subset=["FECHA"])
    op = op.sort_values("FECHA").reset_index(drop=True)

    return op

#Gráficos Operación Campo
def operacion_campo():

    st.markdown(
        "<div class='section-title'>Operación del campo</div>",
        unsafe_allow_html=True
    )

    alta_operacion()   

    op = load_operacion()

    if op.empty:
        st.warning("No hay datos en la tabla Operacion.")
        return

    min_date = op["FECHA"].min().date()
    max_date = op["FECHA"].max().date()

    rango = st.date_input(
        "Rango de fechas operación",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="rango_operacion"
    )

    if isinstance(rango, tuple) and len(rango) == 2:
        f_ini = pd.to_datetime(rango[0]).normalize()
        f_fin = pd.to_datetime(rango[1]).normalize()

        op = op[
            (op["FECHA"] >= f_ini) &
            (op["FECHA"] <= f_fin)
        ].copy()

    if op.empty:
        st.warning("No hay datos para el rango seleccionado.")
        return

    # =====================================================
    # GRÁFICO 1: ACEITE Y AGUA INYECTADA
    # =====================================================
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])

    fig1.add_trace(
        go.Bar(
            x=op["FECHA"],
            y=op["ACEITE (BLS)"],
            name="Aceite producido (bls)",
            text=op["ACEITE (BLS)"].round(0),
            textposition="outside",
            textfont=dict(size=10,color="green"),
            marker=dict(
                color="#00A65A",
                line=dict(color="black", width=1)
            ),
            opacity=0.85
        ),
        secondary_y=False
    )

    fig1.add_trace(
    go.Scatter(
        x=op["FECHA"],
        y=op["AGUA INYECTADA (BLS)"],
        mode="lines+markers+text",
        text=op["AGUA INYECTADA (BLS)"].round(0),
        textposition="bottom center",
        textfont=dict(size=10,color="blue"),
        name="Agua inyectada (bls)",
        line=dict(
            color="blue",
            width=3
        ),
        marker=dict(
            color="blue",
            size=1
        )
    ),
    secondary_y=True
    )

    fig1.update_layout(
        title="<b>Producción de aceite y agua inyectada</b>",
        template="plotly_white",
        height=600,
        barmode="group",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            font=dict(size=13, color="black", family="Arial Black")
        ),
        font=dict(size=14, color="black", family="Arial Black"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig1.update_xaxes(
        title_text="Fecha",
        tickformat="%d/%m/%Y",
        showline=True,
        linewidth=1,
        linecolor="black"
    )

    fig1.update_yaxes(
        title_text="Aceite producido (bls)",
        secondary_y=False,
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        
        linecolor="black"
    )

    fig1.update_yaxes(
        title_text="Agua inyectada (bls)",
        secondary_y=True,
        showgrid=False,
        showline=True,
        linewidth=1,
        rangemode="tozero",
        linecolor="black"
    )

    st.plotly_chart(fig1, use_container_width=True)

    # =====================================================
    # GRÁFICO 2: GAS PRODUCIDO, CPG Y GAS QUEMA
    # =====================================================
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

    # Gas producido (barras)
    fig2.add_trace(
        go.Bar(
            x=op["FECHA"],
            y=op["GAS PRODUCIDO (MMPC)"],
            name="Gas producido",
            text=op["GAS PRODUCIDO (MMPC)"].round(3),
            textposition="outside",
            textfont=dict(size=9),
            marker=dict(
                color="#C0392B",
                line=dict(color="black", width=1)
            ),
            opacity=0.75
        ),
        
    )

    # Gas a CPG Arenque
    fig2.add_trace(
        go.Scatter(
            x=op["FECHA"],
            y=op["GAS A CPG ARENQUE (MMPC)"],
            mode="lines+markers+text",
            name="Gas a CPG Arenque",
            text=op["GAS A CPG ARENQUE (MMPC)"].round(3),
            textposition="bottom center",
            textfont=dict(size=10,color="black"),
            line=dict(
                color="#7B241C",
                width=3
            ),
            marker=dict(
                size=3,
                color="#7B241C"
            )
        ),
        
    )

    # Gas Quema
    fig2.add_trace(
        go.Scatter(
            x=op["FECHA"],
            y=op["GAS QUEMA (MMPC)"],
            mode="lines+markers+text",
            name="Gas Quema",
            text=op["GAS QUEMA (MMPC)"].round(3),
            textfont=dict(size=10,color="black"),
            textposition="top center",
            line=dict(
                color="#FF0000",
                width=3
            ),
            marker=dict(
                size=3,
                color="#FF0000"
            )
        ),
        
    )

    fig2.update_layout(
        title="<b>Gas producido, gas enviado a CPG y gas quemado</b>",
        template="plotly_white",
        height=600,
        hovermode="x unified",

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            font=dict(
                size=13,
                color="black",
                family="Arial Black"
            )
        ),

        font=dict(
            size=14,
            color="black",
            family="Arial Black"
        ),

        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig2.update_xaxes(
        title_text="Fecha",
        tickformat="%d/%m/%Y",
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(
            size=12,
            color="black",
            family="Arial Black"
        )
    )

    fig2.update_yaxes(
        title_text="Gas producido (MMPC)",
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

    fig2.update_yaxes(
        title_text="Gas enviado / quemado (MMPC)",
        secondary_y=True,
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(
            size=12,
            color="black",
            family="Arial Black"
        )
    )

    st.plotly_chart(fig2, use_container_width=True)

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])

    # Venteo
    fig3.add_trace(
        go.Scatter(
            x=op["FECHA"],
            y=op["VENTEO (MMPC)"],
            name="Venteo",
            text=op["VENTEO (MMPC)"].round(1),
            textposition="bottom center",
            marker=dict(
                color="#C0392B",
                line=dict(color="black", width=1)
            ),
            opacity=0.75
        ),
        
    )

    # Autoconsumo
    fig3.add_trace(
        go.Scatter(
            x=op["FECHA"],
            y=op["AUTOCONSUMO (MMPC)"],
            mode="lines+markers",
            name="Autoconsumo",
            text=op["AUTOCONSUMO (MMPC)"].round(1),
            textposition="bottom center",
            line=dict(
                color="#7B241C",
                width=3
            ),
            marker=dict(
                size=3,
                color="#7B241C"
            )
        ),
        
    )

    fig3.add_trace(
    go.Bar(
        x=op["FECHA"],
        y=op["QUEMA BATERIA TC"],
        name="Quema Batería TC",
        marker=dict(
            color="orange",
            line=dict(
                color="black",
                width=1
            )
        ),
        opacity=0.8
    )
    )

    #Quema EC
    fig3.add_trace(
        go.Scatter(
            x=op["FECHA"],
            y=op["QUEMA EC T3"],
            mode="lines+markers",
            name="Quema EC T3",
            line=dict(
                color="#FF0000",
                width=3
            ),
            marker=dict(
                size=3,
                color="#FF0000"
            )
        ),
        
    )

    fig3.update_layout(
        title="<b>Venteo, Autoconsumo, Quema Batería TC y Quema EC T3</b>",
        template="plotly_white",
        height=600,
        hovermode="x unified",

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            font=dict(
                size=13,
                color="black",
                family="Arial Black"
            )
        ),

        font=dict(
            size=14,
            color="black",
            family="Arial Black"
        ),

        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig3.update_xaxes(
        title_text="Fecha",
        tickformat="%d/%m/%Y",
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(
            size=12,
            color="black",
            family="Arial Black"
        )
    )

    fig3.update_yaxes(
        title_text="Gas (MMPC)",
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

    fig3.update_yaxes(
        title_text="Gas (MMPC)",
        secondary_y=True,
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(
            size=12,
            color="black",
            family="Arial Black"
        )
    )

    st.plotly_chart(fig3, use_container_width=True)

@st.cache_data(show_spinner="Calculando producción...")
def load_prod_calc():
    df_base = load_data()
    return calcular_columnas_produccion(df_base.copy())


@st.cache_data(show_spinner="Preparando acumuladas para mapa...")
def preparar_acumuladas_mapa():

    prod = load_prod_calc().copy()

    prod["MES_OPERANDO"] = np.where(
        (prod[COL_QO] > 0) | (prod[COL_QW] > 0) | (prod[COL_QG] > 0),
        1,
        0
    )

    acum = (
        prod.groupby(COL_POZO, as_index=False)
        .agg(
            NP_BLS=(COL_ACEITE_BBL, "sum"),
            WP_BLS=(COL_AGUA_BBL, "sum"),
            GP_PC=(COL_GAS_PC, "sum"),
            WINJ_BLS=(COL_INY_BBL, "sum"),
            MESES_OPERANDO=("MES_OPERANDO", "sum")
        )
    )

    acum["NP_NORM_MB"] = np.where(
        acum["MESES_OPERANDO"] > 0,
        (acum["NP_BLS"] / 1000) / acum["MESES_OPERANDO"],
        0
    )

    return acum

@st.cache_data(show_spinner=False)
def preparar_datos_graficas_animadas_cache(pozo_sel, yac_mapa):
    if not pozo_sel:
        return pd.DataFrame(), pd.DataFrame()

    prod_pozo_raw = load_data().copy()
    prod_pozo_raw[COL_POZO] = prod_pozo_raw[COL_POZO].astype(str).str.strip()
    prod_pozo_raw[COL_FECHA] = pd.to_datetime(prod_pozo_raw[COL_FECHA], errors="coerce")
    prod_pozo_raw = prod_pozo_raw.dropna(subset=[COL_FECHA]).copy()
    prod_pozo_raw = prod_pozo_raw[
        prod_pozo_raw[COL_POZO] == str(pozo_sel).strip()
    ].copy()

    if yac_mapa != "Todos" and COL_YAC in prod_pozo_raw.columns:
        prod_pozo_raw = prod_pozo_raw[
            prod_pozo_raw[COL_YAC].astype(str) == str(yac_mapa)
        ].copy()

    if not prod_pozo_raw.empty:
        prod_pozo_raw = completar_fechas_pozo(prod_pozo_raw)
        prod_pozo = calcular_columnas_produccion(prod_pozo_raw)
        prod_pozo[COL_POZO] = prod_pozo[COL_POZO].astype(str).str.strip()
        prod_pozo[COL_FECHA] = pd.to_datetime(prod_pozo[COL_FECHA], errors="coerce")
        prod_pozo = prod_pozo.dropna(subset=[COL_FECHA]).sort_values(COL_FECHA)
    else:
        prod_pozo = pd.DataFrame()

    pres_pozo = load_presiones()
    if not pres_pozo.empty:
        pres_pozo["TERMINACION"] = pres_pozo["TERMINACION"].astype(str).str.strip()
        pres_pozo["POZO"] = pres_pozo["POZO"].astype(str).str.strip()
        pres_pozo = pres_pozo[
            (pres_pozo["TERMINACION"] == str(pozo_sel).strip()) |
            (pres_pozo["POZO"] == str(pozo_sel).strip())
        ].copy()

        if yac_mapa != "Todos" and "YACIMIENTO" in pres_pozo.columns:
            pres_pozo = pres_pozo[
                pres_pozo["YACIMIENTO"].astype(str) == str(yac_mapa)
            ].copy()

        pres_pozo["FECHA"] = pd.to_datetime(pres_pozo["FECHA"], errors="coerce")
        pres_pozo["PRESION"] = pd.to_numeric(pres_pozo["PRESION"], errors="coerce")
        pres_pozo = pres_pozo.dropna(subset=["FECHA", "PRESION"]).sort_values("FECHA")

    return prod_pozo, pres_pozo

@st.cache_data(show_spinner=False)
def load_contorno_asignacion():

    contorno = load_table(TABLA_CONTORNO)
    asignacion = load_table(TABLA_ASIGNACION)

    contorno = contorno.loc[:, ~contorno.columns.astype(str).str.startswith("Unnamed")]
    asignacion = asignacion.loc[:, ~asignacion.columns.astype(str).str.startswith("Unnamed")]

    contorno = normalizar_columnas(contorno)
    asignacion = normalizar_columnas(asignacion)

    return contorno, asignacion

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

    cols_carga = REQUIRED_COLS + [c for c in OPTIONAL_COLS if c in df.columns]
    df = df[cols_carga].copy()

    # Limpieza básica
    df[COL_POZO] = df[COL_POZO].astype(str).str.strip()
    if COL_POZO_FISICO in df.columns:
        df[COL_POZO_FISICO] = df[COL_POZO_FISICO].astype(str).str.strip()
    df[COL_YAC] = df[COL_YAC].astype(str).str.strip()
    df[COL_CONTA] = df[COL_CONTA].astype(str).str.strip()

    df[COL_FECHA] = convertir_fechas(df[COL_FECHA])
    df = df.dropna(subset=[COL_POZO, COL_FECHA])
    df = df[df[COL_POZO].str.upper().ne("NAN")]
    df[COL_FECHA] = df[COL_FECHA].dt.normalize()
    df[COL_FECHA_FILTRO] = df[COL_FECHA]

    for col in [COL_DIAS, COL_ACEITE, COL_GAS, COL_AGUA, COL_INY]:
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

    #for c in ["CIMA X UTM", "CIMA Y UTM", "RADIO DRENE"]:
    #    if c in coord.columns:
    #        coord[c] = pd.to_numeric(coord[c], errors="coerce")

    for c in [
        "CIMA X UTM", "CIMA Y UTM",
        "FONDO X UTM", "FONDO Y UTM",
        "RADIO DRENE"
    ]:
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

@st.cache_data(show_spinner="Cargando localizaciones...")
def load_localizaciones() -> pd.DataFrame:
    try:
        loc = load_table(TABLA_LOCALIZACIONES)
    except Exception as exc:
        st.warning(f"No se pudo cargar la tabla Localizaciones: {exc}")
        return pd.DataFrame()

    loc = loc.loc[:, ~loc.columns.astype(str).str.startswith("Unnamed")]
    loc = normalizar_columnas(loc)

    cols_req = ["POZO", "TERMINACION", "YACIMIENTO", "CATEGORIA", "FONDO X", "FONDO Y"]
    faltantes = [c for c in cols_req if c not in loc.columns]
    if faltantes:
        st.warning(
            "Faltan columnas en Localizaciones: "
            f"{faltantes}. Columnas leidas: {loc.columns.tolist()}"
        )
        return pd.DataFrame()

    loc = loc.copy()
    for col in ["POZO", "TERMINACION", "YACIMIENTO", "CATEGORIA"]:
        loc[col] = loc[col].astype(str).str.strip()

    loc["CATEGORIA"] = loc["CATEGORIA"].str.upper()
    loc["FONDO X"] = pd.to_numeric(loc["FONDO X"], errors="coerce")
    loc["FONDO Y"] = pd.to_numeric(loc["FONDO Y"], errors="coerce")
    loc = loc.dropna(subset=["POZO", "YACIMIENTO", "FONDO X", "FONDO Y"]).copy()

    if "COLUMNA 1" in loc.columns:
        loc["COLUMNA 1"] = loc["COLUMNA 1"].astype(str).str.strip()
    else:
        loc["COLUMNA 1"] = ""

    return loc.reset_index(drop=True)

@st.cache_data(show_spinner="Cargando instalaciones...")
def load_instalaciones_gis() -> pd.DataFrame:
    try:
        insta = load_table(TABLA_INSTA)
    except Exception as exc:
        st.warning(f"No se pudo cargar la tabla Instalaciones: {exc}")
        return pd.DataFrame()

    insta = insta.loc[:, ~insta.columns.astype(str).str.startswith("Unnamed")]
    insta = normalizar_columnas(insta)

    col_lon = "LON" if "LON" in insta.columns else "LONG"
    cols_req = ["ALIAS", "INSTALACION", "LAT", col_lon]
    faltantes = [c for c in cols_req if c not in insta.columns]
    if faltantes:
        st.warning(
            "Faltan columnas en Instalaciones: "
            f"{faltantes}. Columnas leidas: {insta.columns.tolist()}"
        )
        return pd.DataFrame()

    insta = insta.copy()
    insta["ALIAS"] = insta["ALIAS"].astype(str).str.strip()
    insta["INSTALACION"] = insta["INSTALACION"].astype(str).str.strip().str.upper()
    insta["INSTALACION"] = insta["INSTALACION"].map(
        lambda v: "".join(
            c for c in unicodedata.normalize("NFKD", str(v))
            if not unicodedata.combining(c)
        )
    )
    insta["LAT"] = pd.to_numeric(insta["LAT"], errors="coerce")
    insta["LON"] = pd.to_numeric(insta[col_lon], errors="coerce")

    if "CAMPO" in insta.columns:
        insta["CAMPO"] = insta["CAMPO"].astype(str).str.strip()
    else:
        insta["CAMPO"] = ""

    insta = insta.dropna(subset=["ALIAS", "INSTALACION", "LAT", "LON"]).copy()
    insta = insta[
        ~insta["ALIAS"].astype(str).str.upper().isin(["", "NAN", "NONE"])
    ].copy()

    return insta.reset_index(drop=True)

@st.cache_data(show_spinner="Cargando pozos intervenidos RMA...")
def load_rma_intervenidos() -> pd.DataFrame:
    rma = load_table(TABLA_RMA)
    rma = rma.loc[:, ~rma.columns.astype(str).str.startswith("Unnamed")]
    rma = normalizar_columnas(rma)

    if COL_POZO not in rma.columns:
        segunda_col = rma.columns[1]
        rma = rma.rename(columns={segunda_col: COL_POZO})

    rma[COL_POZO] = rma[COL_POZO].astype(str).str.strip()

    rma = rma[[COL_POZO]].dropna().drop_duplicates()
    rma["POZO_RMA"] = "Sí"

    return rma

@st.cache_data(show_spinner="Cargando presiones...")
def load_presiones() -> pd.DataFrame:
    pres = load_table(TABLA_PRESIONES)
    pres = pres.loc[:, ~pres.columns.astype(str).str.startswith("Unnamed")]
    pres = normalizar_columnas(pres)

    cols_req = ["TERMINACION", "POZO", "YACIMIENTO", "FECHA", "TEMPERATURA", "PRESION"]

    for c in cols_req:
        if c not in pres.columns:
            st.error(f"No existe la columna '{c}' en la tabla Presiones.")
            st.write(pres.columns.tolist())
            return pd.DataFrame()

    pres["TERMINACION"] = pres["TERMINACION"].astype(str).str.strip()
    pres["POZO"] = pres["POZO"].astype(str).str.strip()
    pres["YACIMIENTO"] = pres["YACIMIENTO"].astype(str).str.strip()

    pres["FECHA"] = convertir_fechas(pres["FECHA"])
    pres["TEMPERATURA"] = pd.to_numeric(pres["TEMPERATURA"], errors="coerce")
    pres["PRESION"] = pd.to_numeric(pres["PRESION"], errors="coerce")

    pres = pres.dropna(subset=["TERMINACION", "POZO", "YACIMIENTO", "FECHA", "PRESION"])

    return pres

@st.cache_data(show_spinner="Cargando muestreos de agua...")
def load_muestreos_agua() -> pd.DataFrame:
    cols_req = ["TERMINACION", "POZO", "FECHA MUESTREO", "% AGUA LAB"]

    def clave_columna(col):
        texto = str(col).strip().upper()
        texto = unicodedata.normalize("NFKD", texto)
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        texto = re.sub(r"[^A-Z0-9%]+", " ", texto)
        return re.sub(r"\s+", " ", texto).strip()

    try:
        muestreos = pd.read_excel(
            URL_MUESTREOS_AGUA,
            sheet_name="Pozos"
        )
    except Exception as exc:
        st.warning(f"No se pudo cargar Muestreos.xlsx desde GitHub: {exc}")
        return pd.DataFrame(columns=cols_req)

    muestreos = muestreos.loc[:, ~muestreos.columns.astype(str).str.startswith("Unnamed")]
    muestreos = normalizar_columnas(muestreos)

    columnas_por_clave = {clave_columna(c): c for c in muestreos.columns}
    candidatos = {
        "TERMINACION": ["TERMINACION"],
        "POZO": ["POZO"],
        "FECHA MUESTREO": [
            "FECHA MUESTREO",
            "FECHA DE MUESTREO",
            "FECHA MUESTRA",
            "FECHA DE MUESTRA",
        ],
        "% AGUA LAB": [
            "% AGUA LAB",
            "AGUA LAB %",
            "RESULTADO LAB AGUA %",
            "RESULTADO LAB AGUA",
            "AGUA %",
        ],
    }

    renombres = {}
    for col_salida, opciones in candidatos.items():
        for opcion in opciones:
            col_real = columnas_por_clave.get(clave_columna(opcion))
            if col_real is not None:
                renombres[col_real] = col_salida
                break

    muestreos = muestreos.rename(columns=renombres)

    faltantes = [c for c in cols_req if c not in muestreos.columns]
    if faltantes:
        st.warning(
            "Faltan columnas en Muestreos.xlsx: "
            f"{faltantes}. Columnas leidas: {muestreos.columns.tolist()}"
        )
        return pd.DataFrame(columns=cols_req)

    muestreos = muestreos[cols_req].copy()
    muestreos["TERMINACION"] = muestreos["TERMINACION"].astype(str).str.strip()
    muestreos["POZO"] = muestreos["POZO"].astype(str).str.strip()
    muestreos["FECHA MUESTREO"] = convertir_fechas(muestreos["FECHA MUESTREO"])
    muestreos["% AGUA LAB"] = pd.to_numeric(muestreos["% AGUA LAB"], errors="coerce")

    muestreos = muestreos.dropna(subset=["FECHA MUESTREO", "% AGUA LAB"])
    muestreos = muestreos[
        ~muestreos["TERMINACION"].str.upper().isin(["", "NAN", "NONE"])
    ].copy()

    return muestreos.sort_values(["POZO", "TERMINACION", "FECHA MUESTREO"]).reset_index(drop=True)

@st.cache_data(show_spinner="Cargando seguimiento de actividades...")
def load_seguimiento_actividades(cache_version=2) -> pd.DataFrame:
    cols_req = ["TERMINACION", "POZO", "FECHA", "ACTIVIDAD"]

    def clave_columna(col):
        texto = str(col).strip().upper()
        texto = unicodedata.normalize("NFKD", texto)
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        texto = re.sub(r"[^A-Z0-9]+", " ", texto)
        return re.sub(r"\s+", " ", texto).strip()

    try:
        seguimiento = pd.read_excel(URL_SEGUIMIENTO)
    except Exception as exc:
        st.warning(f"No se pudo cargar Seguimiento.xlsx desde GitHub: {exc}")
        return pd.DataFrame(columns=cols_req)

    seguimiento = seguimiento.loc[:, ~seguimiento.columns.astype(str).str.startswith("Unnamed")]
    seguimiento = normalizar_columnas(seguimiento)

    columnas_por_clave = {clave_columna(c): c for c in seguimiento.columns}
    candidatos = {
        "TERMINACION": ["TERMINACION", "TERMINACIÓN", "TERM"],
        "YACIMIENTO": ["YACIMIENTO", "YAC"],
        "POZO": ["POZO", "POZO FISICO", "NOMBRE POZO"],
        "FECHA": [
            "FECHA",
            "FECHA ACTIVIDAD",
            "FECHA DE ACTIVIDAD",
            "FECHA CADA ACTIVIDAD",
            "FECHA DE CADA ACTIVIDAD",
            "FECHA EVENTO",
            "FECHA DE EVENTO",
        ],
        "ACTIVIDAD": [
            "ACTIVIDAD",
            "ACTIVIDADES",
            "EVENTO",
            "EVENTOS",
            "DESCRIPCION",
            "DESCRIPCION ACTIVIDAD",
        ],
    }

    renombres = {}
    for col_salida, opciones in candidatos.items():
        for opcion in opciones:
            col_real = columnas_por_clave.get(clave_columna(opcion))
            if col_real is not None:
                renombres[col_real] = col_salida
                break

    seguimiento = seguimiento.rename(columns=renombres)

    faltantes = [c for c in cols_req if c not in seguimiento.columns]
    if faltantes:
        st.warning(
            "Faltan columnas en Seguimiento.xlsx: "
            f"{faltantes}. Columnas leidas: {seguimiento.columns.tolist()}"
        )
        return pd.DataFrame(columns=cols_req)

    if "YACIMIENTO" not in seguimiento.columns:
        seguimiento["YACIMIENTO"] = ""

    seguimiento = seguimiento[["TERMINACION", "POZO", "YACIMIENTO", "FECHA", "ACTIVIDAD"]].copy()
    seguimiento["TERMINACION"] = seguimiento["TERMINACION"].astype(str).str.strip()
    seguimiento["POZO"] = seguimiento["POZO"].astype(str).str.strip()
    seguimiento["YACIMIENTO"] = seguimiento["YACIMIENTO"].astype(str).str.strip()
    seguimiento["ACTIVIDAD"] = seguimiento["ACTIVIDAD"].astype(str).str.strip()
    seguimiento["FECHA"] = convertir_fechas(seguimiento["FECHA"])

    seguimiento = seguimiento.dropna(subset=["TERMINACION", "POZO", "FECHA", "ACTIVIDAD"])
    seguimiento = seguimiento[
        ~seguimiento["TERMINACION"].str.upper().isin(["", "NAN", "NONE"])
        & ~seguimiento["POZO"].str.upper().isin(["", "NAN", "NONE"])
        & ~seguimiento["ACTIVIDAD"].str.upper().isin(["", "NAN", "NONE"])
    ].copy()

    actividad_norm = (
        seguimiento["ACTIVIDAD"]
        .astype(str)
        .map(lambda v: unicodedata.normalize("NFKD", v))
        .map(lambda v: "".join(c for c in v if not unicodedata.combining(c)))
        .str.upper()
        .str.replace(r"[^A-Z0-9]+", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    patron_excluir = r"(MANTENIMIENTO|ECOMETRO|CALIBRACION|AJUSTE.*GAS|GAS.*AJUSTE)"
    seguimiento = seguimiento[
        ~actividad_norm.str.contains(patron_excluir, na=False, regex=True)
    ].copy()

    return seguimiento.sort_values(["POZO", "TERMINACION", "FECHA", "ACTIVIDAD"]).reset_index(drop=True)

@st.cache_data(show_spinner="Cargando estado de pozos...")
def load_estado_pozos() -> pd.DataFrame:
    estado = load_table(TABLA_ESTADO_POZOS)
    estado = estado.loc[:, ~estado.columns.astype(str).str.startswith("Unnamed")]
    estado = normalizar_columnas(estado)

    cols_req = ["POZO", "ESTADO", "SAP"]

    for c in cols_req:
        if c not in estado.columns:
            st.error(f"No existe la columna '{c}' en la tabla de estado de pozos.")
            st.write(estado.columns.tolist())
            return pd.DataFrame()

    estado["POZO"] = estado["POZO"].astype(str).str.strip()
    estado["ESTADO"] = estado["ESTADO"].astype(str).str.strip()
    estado["SAP"] = estado["SAP"].astype(str).str.strip()

    return estado[["POZO", "ESTADO", "SAP"]].drop_duplicates()

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

def estadistica():

    st.markdown(
        "<div class='section-title'>Estadística de producción acumulada por yacimiento</div>",
        unsafe_allow_html=True
    )

    prod = load_prod_calc().copy()
    #prod = calcular_columnas_produccion(df.copy())
    prod = prod.sort_values([COL_YAC, COL_POZO, COL_FECHA]).copy()

    prod["MES_CON_PROD"] = np.where(
        (prod[COL_QO] > 0) | (prod[COL_QW] > 0) | (prod[COL_QG] > 0),
        1,
        0
    )

    prod_prod = prod[prod["MES_CON_PROD"] == 1].copy()

    prod_prod["MES_PROD"] = (
        prod_prod
        .groupby(COL_POZO)
        .cumcount() + 1
    )

    c1, c2 = st.columns(2)

    with c1:
        yacs = sorted(prod_prod[COL_YAC].dropna().astype(str).unique())

        yacs_sel = st.multiselect(
            "Yacimientos",
            yacs,
            default=yacs,
            key="estadistica_yacs"
        )

    with c2:
        meses_np = st.selectbox(
            "Acumulada normalizada a:",
            ["Total", "12 meses", "36 meses", "60 meses"],
            index=0,
            key="estadistica_meses_np"
        )

    if yacs_sel:
        prod_prod = prod_prod[
            prod_prod[COL_YAC].astype(str).isin(yacs_sel)
        ].copy()

    if prod_prod.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    if meses_np == "12 meses":
        max_meses = 12
        nombre_np = "Np a 12 meses"

    elif meses_np == "36 meses":
        max_meses = 36
        nombre_np = "Np a 36 meses"

    elif meses_np == "60 meses":
        max_meses = 60
        nombre_np = "Np a 60 meses"

    else:
        max_meses = int(prod_prod["MES_PROD"].max())
        nombre_np = "Np total"

    # =====================================================
    # COMPLETAR CURVAS HASTA max_meses
    # Si un pozo no llega al mes filtrado, mantiene última Np
    # =====================================================
    curvas_completas = []

    for pozo, g in prod_prod.groupby(COL_POZO):

        g = g.sort_values("MES_PROD").copy()

        if g.empty:
            continue

        yac_pozo = g[COL_YAC].iloc[0]

        meses_base = pd.DataFrame({
            "MES_PROD": range(1, max_meses + 1)
        })

        g_full = meses_base.merge(
            g[[COL_POZO, COL_YAC, "MES_PROD", COL_NP, COL_WP, COL_GP]],
            on="MES_PROD",
            how="left"
        )

        g_full[COL_POZO] = pozo
        g_full[COL_YAC] = yac_pozo

        g_full[COL_NP] = g_full[COL_NP].ffill()
        g_full[COL_WP] = g_full[COL_WP].ffill()
        g_full[COL_GP] = g_full[COL_GP].ffill()

        g_full[[COL_NP, COL_WP, COL_GP]] = (
            g_full[[COL_NP, COL_WP, COL_GP]]
            .fillna(0)
        )

        curvas_completas.append(g_full)

    if not curvas_completas:
        st.warning("No hay curvas para graficar.")
        return

    prod_plot = pd.concat(curvas_completas, ignore_index=True)

    prod_plot = prod_plot[
        prod_plot[COL_YAC].astype(str).isin(yacs_sel)
    ].copy()

    # Meses reales de producción por pozo
    meses_reales = (
        prod_prod
        .groupby([COL_YAC, COL_POZO], as_index=False)
        .agg(
            MESES_PROD_REAL=("MES_PROD", "max")
        )
    )

    # =====================================================
    # RESUMEN POR POZO / YACIMIENTO
    # Este resumen impacta KPI y boxplots
    # =====================================================
    resumen = (
        prod_plot
        .sort_values([COL_POZO, "MES_PROD"])
        .groupby([COL_YAC, COL_POZO], as_index=False)
        .agg(
            NP_FINAL=(COL_NP, "last"),
            WP_FINAL=(COL_WP, "last"),
            GP_FINAL=(COL_GP, "last"),
            MESES_CONSIDERADOS=("MES_PROD", "max")
        )
    )

    resumen = resumen.merge(
        meses_reales,
        on=[COL_YAC, COL_POZO],
        how="left"
    )

    resumen = resumen[resumen["NP_FINAL"] > 0].copy()

    if resumen.empty:
        st.warning("No hay pozos con Np positiva para el filtro seleccionado.")
        return

    # =====================================================
    # KPI CARDS POR YACIMIENTO
    # =====================================================
    kpis = (
        resumen.groupby(COL_YAC, as_index=False)
        .agg(
            POZOS_PRODUCTORES=(COL_POZO, "nunique"),
            NP_PROM=("NP_FINAL", "mean"),
            NP_P50=("NP_FINAL", "median"),
            MESES_PROM=("MESES_PROD_REAL", "mean")
        )
    )

    cols = st.columns(len(kpis))

    for i, row in kpis.iterrows():
        with cols[i]:
            kpi_card(
                f"{row[COL_YAC]}",
                f"{row['POZOS_PRODUCTORES']:,.0f}",
                "pozos",
                #"#1F2937"
                "#1F77B4"
            )

    # =====================================================
    # CURVA PROMEDIO POR YACIMIENTO
    # =====================================================
    fig_curvas = go.Figure()

    for yac in yacs_sel:

        data_yac = prod_plot[
            prod_plot[COL_YAC].astype(str) == str(yac)
        ].copy()

        if data_yac.empty:
            continue

        prom_yac = (
            data_yac
            .groupby("MES_PROD", as_index=False)
            .agg(
                NP_PROM=(COL_NP, "mean"),
                NP_P50=(COL_NP, "median"),
                POZOS=(COL_POZO, "nunique")
            )
        )

        fig_curvas.add_trace(
            go.Scatter(
                x=prom_yac["MES_PROD"],
                y=prom_yac["NP_PROM"],
                mode="lines+markers",
                name=f"Promedio {yac}",
                line=dict(width=4),
                marker=dict(size=5),
                customdata=prom_yac[["POZOS", "NP_P50"]],
                hovertemplate=
                    f"<b>Yacimiento:</b> {yac}<br>" +
                    "<b>Mes producción:</b> %{x}<br>" +
                    "<b>Np promedio:</b> %{y:,.1f} mbl<br>" +
                    "<b>Np P50:</b> %{customdata[1]:,.1f} mbl<br>" +
                    "<b>Pozos considerados:</b> %{customdata[0]:,.0f}" +
                    "<extra></extra>"
            )
        )

    fig_curvas.update_layout(
        title=f"<b>Curva promedio de producción acumulada normalizada - {nombre_np}</b>",
        template="plotly_white",
        height=650,
        xaxis_title="Tiempo de producción, meses",
        yaxis_title="Np acumulada promedio (mbl)",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5
        ),
        font=dict(size=14, color="black", family="Arial Black"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig_curvas.update_xaxes(
        dtick=6,
        showline=True,
        linewidth=1,
        linecolor="black",
        showgrid=True,
        gridcolor="#EAECEE"
    )

    fig_curvas.update_yaxes(
        showline=True,
        linewidth=1,
        linecolor="black",
        showgrid=True,
        gridcolor="#EAECEE"
    )

    st.plotly_chart(fig_curvas, use_container_width=True)

    # =====================================================
    # BOXPLOT NP
    # =====================================================
    fig_box_np = px.box(
        resumen,
        x=COL_YAC,
        y="NP_FINAL",
        points="all",
        hover_name=COL_POZO,
        title=f"<b>Boxplot {nombre_np} por yacimiento</b>",
        template="plotly_white"
    )

    promedios_np = (
        resumen.groupby(COL_YAC, as_index=False)["NP_FINAL"]
        .mean()
    )

    fig_box_np.add_trace(
        go.Scatter(
            x=promedios_np[COL_YAC],
            y=promedios_np["NP_FINAL"],
            mode="markers+text",
            text=promedios_np["NP_FINAL"].round(1),
            textposition="top center",
            marker=dict(
                symbol="square",
                size=9,
                color="blue",
                line=dict(color="black", width=1)
            ),
            name="Promedio"
        )
    )

    fig_box_np.update_traces(
        marker=dict(
            size=7,
            opacity=0.70,
            line=dict(color="black", width=1)
        )
    )

    fig_box_np.update_layout(
        height=560,
        xaxis_title="Yacimiento",
        yaxis_title=f"{nombre_np} (mbl)",
        font=dict(size=14, color="black", family="Arial Black"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    # =====================================================
    # BOXPLOT MESES REALES PRODUCIENDO
    # =====================================================
    fig_box_meses = px.box(
        resumen,
        x=COL_YAC,
        y="MESES_PROD_REAL",
        points="all",
        hover_name=COL_POZO,
        title="<b>Meses reales con producción por yacimiento</b>",
        template="plotly_white"
    )

    promedios_meses = (
        resumen.groupby(COL_YAC, as_index=False)["MESES_PROD_REAL"]
        .mean()
    )

    fig_box_meses.add_trace(
        go.Scatter(
            x=promedios_meses[COL_YAC],
            y=promedios_meses["MESES_PROD_REAL"],
            mode="markers+text",
            text=promedios_meses["MESES_PROD_REAL"].round(1),
            textposition="top center",
            marker=dict(
                symbol="square",
                size=9,
                color="blue",
                line=dict(color="black", width=1)
            ),
            name="Promedio"
        )
    )

    fig_box_meses.update_traces(
        marker=dict(
            size=7,
            opacity=0.70,
            line=dict(color="black", width=1)
        )
    )

    fig_box_meses.update_layout(
        height=560,
        xaxis_title="Yacimiento",
        yaxis_title="Meses reales con producción",
        font=dict(size=14, color="black", family="Arial Black"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(fig_box_np, use_container_width=True)

    with col2:
        st.plotly_chart(fig_box_meses, use_container_width=True)

    with st.expander("Ver tabla estadística por pozo"):
        st.dataframe(
            resumen.sort_values([COL_YAC, "NP_FINAL"], ascending=[True, False]),
            use_container_width=True,
            height=400
        )

def seleccionar_presiones_mapa(
    pres: pd.DataFrame,
    fecha_ref,
    modo_presion="Cercana a fecha",
    ventana_meses=24,
    dias_promedio=30,
    ventana_anios_ultima=7
    ) -> pd.DataFrame:

    pres = pres.copy()
    fecha_ref = pd.to_datetime(fecha_ref).normalize()

    if modo_presion == "Última disponible":
        fecha_min = fecha_ref - pd.DateOffset(years=ventana_anios_ultima)

        pres = pres[
            (pres["FECHA"] <= fecha_ref) &
            (pres["FECHA"] >= fecha_min)
        ].copy()

        pres["DIF_DIAS"] = (pres["FECHA"] - fecha_ref).abs().dt.days

    else:
        pres["DIF_DIAS"] = (pres["FECHA"] - fecha_ref).abs().dt.days
        max_dias = int(ventana_meses * 30.4375)

        pres = pres[
            pres["DIF_DIAS"] <= max_dias
        ].copy()

    if pres.empty:
        return pd.DataFrame()

    pres = pres.sort_values(["TERMINACION", "YACIMIENTO", "DIF_DIAS"])

    salida = []

    for (terminacion, yac), g in pres.groupby(["TERMINACION", "YACIMIENTO"]):

        if modo_presion == "Última disponible":
            fecha_base = g["FECHA"].max()
        else:
            fecha_base = g.iloc[0]["FECHA"]

        g_cercanas = g[
            (g["FECHA"] - fecha_base).abs().dt.days <= dias_promedio
        ].copy()

        salida.append({
            "TERMINACION": terminacion,
            "YACIMIENTO": yac,
            "POZO": g_cercanas["POZO"].iloc[0],
            "FECHA_PRESION": g_cercanas["FECHA"].max(),
            "PRESION_MAPA": g_cercanas["PRESION"].mean(),
            "TEMPERATURA_MAPA": g_cercanas["TEMPERATURA"].mean(),
            "N_MEDICIONES": len(g_cercanas),
            "DIF_DIAS_REF": abs((g_cercanas["FECHA"].max() - fecha_ref).days)
        })

    return pd.DataFrame(salida)

from pyproj import Transformer

def convertir_utm_a_latlon(df_mapa, x_col, y_col):

    df_mapa = df_mapa.copy()

    #transformer = Transformer.from_crs(
    #    "EPSG:32614",   # UTM zona 14N WGS84
    #    "EPSG:4326",    # Lat/Lon
    #    always_xy=True
    #)

    transformer = Transformer.from_crs(
        "EPSG:26714",   # NAD27 / UTM zona 14N
        "EPSG:4326",    # Lat/Lon WGS84
        always_xy=True
    )

    df_mapa["LON"], df_mapa["LAT"] = transformer.transform(
        df_mapa[x_col].astype(float).values,
        df_mapa[y_col].astype(float).values
    )

    return df_mapa
#######Mapa con tiempo
#def mapa_burbujas(df_base: pd.DataFrame, df_coord: pd.DataFrame, modo_mapa="TERM"):


@st.cache_data(show_spinner="Cargando base Operativas...")
def load_operativas():

    posibles_archivos = [
        Path("Operativas.xlsx"),
        Path("operativas.xlsx"),
        Path("./Operativas.xlsx"),
        Path("./data/Operativas.xlsx"),
        Path("./Data/Operativas.xlsx")
    ]

    archivo_operativas = None

    for archivo in posibles_archivos:
        if archivo.exists():
            archivo_operativas = archivo
            break

    if archivo_operativas is None:
        st.error("No se encontró Operativas.xlsx. Revisa que esté en la misma carpeta que app.py o en /data.")
        st.write("Carpeta actual:", Path.cwd())
        st.write("Archivos detectados:", [p.name for p in Path.cwd().glob("*")])
        return pd.DataFrame()

    op = pd.read_excel(archivo_operativas)
    op = op.loc[:, ~op.columns.astype(str).str.startswith("Unnamed")]
    op = normalizar_columnas(op)

    cols_req = ["ALIAS", "SIST", "YACIMIENTO", "ESTADO"]

    faltantes = [c for c in cols_req if c not in op.columns]

    if faltantes:
        st.error(f"Faltan columnas en Operativas: {faltantes}")
        st.write(op.columns.tolist())
        return pd.DataFrame()

    op = op[cols_req].copy()

    op["ALIAS"] = op["ALIAS"].astype(str).str.strip()
    op["SIST"] = op["SIST"].astype(str).str.strip().str.upper()
    op["YACIMIENTO"] = op["YACIMIENTO"].astype(str).str.strip().str.upper()
    op["ESTADO"] = op["ESTADO"].astype(str).str.strip().str.upper()

    op = op[
        op["ALIAS"].notna() &
        op["ALIAS"].str.upper().ne("NAN") &
        op["ALIAS"].str.strip().ne("")
    ].copy()

    op = op.drop_duplicates(subset=["ALIAS"])

    return op

def crear_heatmap_kriging_burbujas(
        mapa,
        contorno,
        x_col,
        y_col,
        variable,
        grid_n=350
    ):

        try:
            from pykrige.ok import OrdinaryKriging
            from matplotlib.path import Path as MplPath

            datos = mapa.copy()
            contorno = normalizar_columnas(contorno.copy())

            if "ORDEN" in contorno.columns:
                contorno = contorno.sort_values("ORDEN")

            datos[x_col] = pd.to_numeric(datos[x_col], errors="coerce")
            datos[y_col] = pd.to_numeric(datos[y_col], errors="coerce")
            datos[variable] = pd.to_numeric(datos[variable], errors="coerce")

            contorno["X"] = pd.to_numeric(contorno["X"], errors="coerce")
            contorno["Y"] = pd.to_numeric(contorno["Y"], errors="coerce")

            datos = datos.dropna(subset=[x_col, y_col, variable]).copy()
            contorno = contorno.dropna(subset=["X", "Y"]).copy()

            datos = datos[datos[variable] > 0].copy()

            if variable in ["NP_BLS", "WP_BLS", "WINJ_BLS"]:
                datos["VALOR_KRIGING"] = datos[variable] / 1000
                unidad = "mbl"

            elif variable == "GP_PC":
                datos["VALOR_KRIGING"] = datos[variable] / 1_000_000
                unidad = "mmpc"

            else:
                datos["VALOR_KRIGING"] = datos[variable]
                unidad = ""

            if len(datos) < 4:
                st.warning(f"No hay suficientes pozos para interpolar. Pozos con dato: {len(datos)}")
                return None

            if datos["VALOR_KRIGING"].nunique() < 2:
                st.warning("La variable tiene muy poca variación; por eso el mapa se ve de un solo color.")
                return None

            x = datos[x_col].values.astype(float)
            y = datos[y_col].values.astype(float)
            z = datos["VALOR_KRIGING"].values.astype(float)

            xi = np.linspace(contorno["X"].min(), contorno["X"].max(), grid_n)
            yi = np.linspace(contorno["Y"].min(), contorno["Y"].max(), grid_n)

            OK = OrdinaryKriging(
                x,
                y,
                z,
                variogram_model="spherical",
                verbose=False,
                enable_plotting=False,
                nlags=4,
                weight=True
            )

            zi, ss = OK.execute("grid", xi, yi)
            zi = np.array(zi, dtype=float)

            XI, YI = np.meshgrid(xi, yi)

            poly = MplPath(contorno[["X", "Y"]].values)
            puntos_grid = np.vstack((XI.ravel(), YI.ravel())).T
            mask = poly.contains_points(puntos_grid).reshape(XI.shape)

            zi_masked = np.where(mask, zi, np.nan)

            
            zmin = np.nanpercentile(z, 5)
            zmax = np.nanpercentile(z, 95)

            #zmin = np.nanmin(z)
            #zmax = np.nanmax(z)

            zi_masked = np.clip(zi_masked, zmin, zmax)

            return xi, yi, zi_masked, datos, zmin, zmax, unidad

        except Exception as e:
            st.warning(f"No se pudo generar el heatmap con Kriging: {e}")
            return None

def mapa_burbujas(df_base: pd.DataFrame, df_coord: pd.DataFrame, modo_mapa="TERM", pozos_destacados=None, mostrar_instalaciones_gis=False):
    """Mapa de burbujas con opción Todos desde Operativas y mapas por yacimiento sin modificar."""

    st.markdown(
        "<div class='section-title'>Mapa</div>",
        unsafe_allow_html=True
    )

    coord = df_coord.copy()

    contorno, asignacion = load_contorno_asignacion()

    acum = preparar_acumuladas_mapa()

    mapa = coord.merge(acum, on=COL_POZO, how="left")

    estado_pozos = load_estado_pozos()

    if not estado_pozos.empty and "POZO" in mapa.columns:
        mapa = mapa.merge(
            estado_pozos,
            on="POZO",
            how="left"
        )

        mapa["ESTADO"] = mapa["ESTADO"].fillna("Sin estado")
        mapa["SAP"] = mapa["SAP"].fillna("Sin SAP")
    else:
        mapa["ESTADO"] = "Sin estado"
        mapa["SAP"] = "Sin SAP"

    ultimo_wc = calcular_ultimo_wc_mapa(df_base)

    mapa = mapa.merge(
        ultimo_wc,
        on=COL_POZO,
        how="left"
    )

    if modo_mapa == "RMA":

        rma = load_rma_intervenidos()

        if pozos_destacados is not None:
            pozos_destacados = [str(p).strip() for p in pozos_destacados]

            rma = rma[
                rma[COL_POZO].astype(str).str.strip().isin(pozos_destacados)
            ].copy()

        mapa = mapa.merge(
            rma,
            on=COL_POZO,
            how="left"
        )

        mapa["POZO_RMA"] = mapa["POZO_RMA"].fillna("No")
        mapa["PERFORADO_TERM"] = "No"

    else:

        term = load_term_perforados()

        mapa = mapa.merge(
            term,
            on=COL_POZO,
            how="left"
        )

        mapa["PERFORADO_TERM"] = mapa["PERFORADO_TERM"].fillna("No")
        mapa["POZO_RMA"] = "No"

    mapa["ULTIMO_WC"] = mapa["ULTIMO_WC"].fillna(0)

    cols_acum = [
        "NP_BLS",
        "WP_BLS",
        "GP_PC",
        "WINJ_BLS",
        "MESES_OPERANDO",
        "NP_NORM_MB"
    ]

    mapa[cols_acum] = mapa[cols_acum].fillna(0)

    if "RADIO DRENE" in mapa.columns:
        mapa["RADIO DRENE"] = pd.to_numeric(mapa["RADIO DRENE"], errors="coerce")
    else:
        mapa["RADIO DRENE"] = np.nan

    if "POZO" not in mapa.columns:
        mapa["POZO"] = mapa[COL_POZO]

    # =====================================================
    # FUNCIONES / COLORES
    # =====================================================
    def normalizar_estado(valor):
        v = str(valor).strip().upper()
        v = v.replace(".", "")
        v = " ".join(v.split())

        if v in ["OP", "OPERANDO"]:
            return "OP"
        elif v in ["NOP", "NO OPERANDO"]:
            return "NOP"
        elif v == "CCP":
            return "CCP"
        elif v == "CSP":
            return "CSP"
        elif v in ["INY", "INYECTOR", "INYECCION", "INYECCIÓN"]:
            return "INY"
        elif v in ["PROG TAPONAMIENTO", "PROG TAPONADO", "PROG. TAPONAMIENTO"]:
            return "PROG TAPONAMIENTO"
        elif v in ["TAPONADO", "TAP"]:
            return "TAPONADO"
        else:
            return "SIN ESTADO"

    mapa["ESTADO_MAPA"] = mapa["ESTADO"].apply(normalizar_estado)

    leyenda_estados = {
        "OP": "#00A65A",
        "NOP": "#000000",
        "CCP": "#FFD700",
        "CSP": "#DC143C",
        "INY": "#0000FF",
        "PROG TAPONAMIENTO": "#BA55D3",
        "TAPONADO": "#808080",
        "SIN ESTADO": "#7F8C8D"
    }

    leyenda_sap = {
        "BH": "#1F77B4",
        "BM": "#00A65A",
        "BN": "#F39C12",
        "CP": "#8E44AD",
        "F": "#E74C3C",
        "IA": "#000000",
        "SIN SAP": "#7F8C8D"
    }

    color_variable = {
        "NP_BLS": "green",
        "WP_BLS": "blue",
        "WINJ_BLS": "cyan",
        "GP_PC": "red",
        "ULTIMO_WC": "deepskyblue",
        "NP_NORM_MB": "orange"
    }

    # =====================================================
    # FILTROS
    # =====================================================
    if es_movil():
        c1 = st.container()
        c2 = st.container()
        c3 = st.container()
        c4 = st.container()
    else:
        c1, c2, c3, c4 = st.columns([1.3, 1.3, 1.3, 1.3])

    with c1:
        yacs_mapa = sorted(mapa[COL_YAC].dropna().astype(str).unique())

        yac_mapa = st.selectbox(
            "Yacimiento del mapa",
            options=["Todos"] + yacs_mapa,
            key=f"yac_mapa_burbujas_{modo_mapa}"
        )

    ver_todos_campo = yac_mapa == "Todos"
    usar_panel_filtros_mapa = (not ver_todos_campo) and (not es_movil())

    if usar_panel_filtros_mapa:
        panel_filtros_mapa, salida_mapa_burbujas = st.columns([0.24, 0.76], gap="medium")

        with panel_filtros_mapa:
            st.markdown(
                """
                <div class="map-filter-panel-marker"></div>
                <style>
                div[data-testid="column"]:has(.map-filter-panel-marker),
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) {
                    background: linear-gradient(180deg, #2F363D 0%, #252B31 100%);
                    border: 1px solid #1F252B;
                    border-radius: 8px;
                    padding: 12px 12px 18px 12px;
                    box-shadow: 0 10px 26px rgba(15, 23, 42, 0.22);
                }
                div[data-testid="column"]:has(.map-filter-panel-marker) .map-panel-title,
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) .map-panel-title {
                    background: #20262D;
                    border: 1px solid #111827;
                    border-radius: 6px;
                    color: #E5E7EB;
                    font-size: 15px;
                    font-weight: 800;
                    letter-spacing: .2px;
                    padding: 8px 10px;
                    margin-bottom: 10px;
                }
                div[data-testid="column"]:has(.map-filter-panel-marker) .map-panel-section,
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) .map-panel-section {
                    color: #AEB7C2;
                    font-size: 10px;
                    font-weight: 800;
                    text-transform: uppercase;
                    letter-spacing: .65px;
                    margin: 14px 0 6px 0;
                }
                div[data-testid="column"]:has(.map-filter-panel-marker) label,
                div[data-testid="column"]:has(.map-filter-panel-marker) p,
                div[data-testid="column"]:has(.map-filter-panel-marker) span,
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) label,
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) p,
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) span {
                    color: #DDE4EC !important;
                    font-family: "Segoe UI", Arial, sans-serif;
                    font-size: 12px;
                }
                div[data-testid="column"]:has(.map-filter-panel-marker) div[data-testid="stCheckbox"],
                div[data-testid="column"]:has(.map-filter-panel-marker) div[data-testid="stRadio"],
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) div[data-testid="stCheckbox"],
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) div[data-testid="stRadio"] {
                    margin-top: -3px;
                    margin-bottom: -4px;
                }
                div[data-testid="column"]:has(.map-filter-panel-marker) div[data-testid="stSelectbox"] label,
                div[data-testid="column"]:has(.map-filter-panel-marker) div[data-testid="stDateInput"] label,
                div[data-testid="column"]:has(.map-filter-panel-marker) div[data-testid="stRadio"] label,
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) div[data-testid="stSelectbox"] label,
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) div[data-testid="stDateInput"] label,
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) div[data-testid="stRadio"] label {
                    color: #F3F4F6 !important;
                    font-weight: 700;
                }
                div[data-testid="column"]:has(.map-filter-panel-marker) div[data-baseweb="select"] > div,
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) div[data-baseweb="select"] > div {
                    background-color: #1F252B !important;
                    border-color: #4B5563 !important;
                    border-radius: 6px;
                }
                div[data-testid="column"]:has(.map-filter-panel-marker) div[data-baseweb="select"] span,
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) div[data-baseweb="select"] span,
                div[data-testid="column"]:has(.map-filter-panel-marker) div[data-baseweb="select"] div,
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) div[data-baseweb="select"] div,
                div[data-testid="column"]:has(.map-filter-panel-marker) div[data-baseweb="select"] input,
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) div[data-baseweb="select"] input {
                    color: #F9FAFB !important;
                }
                div[data-testid="column"]:has(.map-filter-panel-marker) div[data-baseweb="select"] svg,
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) div[data-baseweb="select"] svg {
                    color: #F9FAFB !important;
                    fill: #F9FAFB !important;
                }
                div[data-testid="column"]:has(.map-filter-panel-marker) div[data-baseweb="input"] > div,
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) div[data-baseweb="input"] > div {
                    background-color: #FFFFFF;
                    border-color: #4B5563;
                    border-radius: 6px;
                }
                div[data-testid="column"]:has(.map-filter-panel-marker) hr,
                div[data-testid="stColumn"]:has(.map-filter-panel-marker) hr {
                    border-color: #46505A;
                    margin: 12px 0;
                }
                </style>
                <div class="map-panel-title">Mapa</div>
                """,
                unsafe_allow_html=True
            )
   
    else:
        panel_filtros_mapa = None
        salida_mapa_burbujas = st

    # =====================================================
    # SI ES TODOS: USAR OPERATIVAS + COORD SUPERFICIE
    # SI NO ES TODOS: MANTENER LÓGICA ACTUAL
    # =====================================================
    if ver_todos_campo:

        operativas = load_operativas()

        if operativas.empty:
            st.warning("No hay datos en Operativas para graficar.")
            return

        coord_superficie = coord.copy()
        coord_superficie = coord_superficie.loc[
            :,
            ~coord_superficie.columns.astype(str).str.startswith("Unnamed")
        ]
        coord_superficie = normalizar_columnas(coord_superficie)

        cols_coord_req = ["POZO", "SUP X UTM", "SUP Y UTM"]

        faltan_coord = [c for c in cols_coord_req if c not in coord_superficie.columns]

        if faltan_coord:
            st.error(f"Faltan columnas en Coord para mapa Todos: {faltan_coord}")
            st.write(coord_superficie.columns.tolist())
            return

        coord_superficie["POZO"] = coord_superficie["POZO"].astype(str).str.strip()

        coord_superficie = (
            coord_superficie[
                ["POZO", "SUP X UTM", "SUP Y UTM"]
            ]
            .dropna(subset=["POZO"])
            .drop_duplicates(subset=["POZO"])
            .copy()
        )

        mapa = operativas.merge(
            coord_superficie,
            left_on="ALIAS",
            right_on="POZO",
            how="left"
        )

        mapa["POZO"] = mapa["ALIAS"]
        mapa["SAP"] = mapa["SIST"]
        mapa[COL_YAC] = mapa["YACIMIENTO"]
        mapa["ESTADO_MAPA"] = mapa["ESTADO"].apply(normalizar_estado)

    else:

        mapa = mapa[mapa[COL_YAC].astype(str) == str(yac_mapa)].copy()

    # =====================================================
    # COORDENADAS
    # =====================================================
    if ver_todos_campo:
        x_col = "SUP X UTM"
        y_col = "SUP Y UTM"

        if x_col not in mapa.columns or y_col not in mapa.columns:
            st.error("No existen las columnas SUP X UTM y SUP Y UTM para el mapa Todos.")
            return

    #else:
    #    x_col = "CIMA X UTM"
    #    y_col = "CIMA Y UTM"
    #
    #    if x_col not in mapa.columns or y_col not in mapa.columns:
    #        st.error("No existen las columnas CIMA X UTM y CIMA Y UTM en la tabla Coord.")
    #        return
    #
    #mapa[x_col] = pd.to_numeric(mapa[x_col], errors="coerce")
    #mapa[y_col] = pd.to_numeric(mapa[y_col], errors="coerce")
    #mapa = mapa.dropna(subset=[x_col, y_col]).copy()

    else:
        cols_req = ["CIMA X UTM", "CIMA Y UTM", "FONDO X UTM", "FONDO Y UTM"]
        faltan = [c for c in cols_req if c not in mapa.columns]

        if faltan:
            st.error(f"Faltan columnas de coordenadas en Coord: {faltan}")
            st.write(mapa.columns.tolist())
            return

        for c in cols_req:
            mapa[c] = pd.to_numeric(mapa[c], errors="coerce")

        # Coordenada final para graficar:
        # Usa CIMA si existe; si no existe, usa FONDO.
        mapa["X_MAPA"] = mapa["CIMA X UTM"].fillna(mapa["FONDO X UTM"])
        mapa["Y_MAPA"] = mapa["CIMA Y UTM"].fillna(mapa["FONDO Y UTM"])

        mapa["ORIGEN_COORD"] = np.where(
            mapa["CIMA X UTM"].notna() & mapa["CIMA Y UTM"].notna(),
            "CIMA",
            "FONDO"
        )

        x_col = "X_MAPA"
        y_col = "Y_MAPA"

    mapa[x_col] = pd.to_numeric(mapa[x_col], errors="coerce")
    mapa[y_col] = pd.to_numeric(mapa[y_col], errors="coerce")
    mapa = mapa.dropna(subset=[x_col, y_col]).copy()

    def preparar_inyectores_operando_burbujas():
        iny = cargar_inyectores()

        if iny.empty or "Operando" not in iny.columns:
            return pd.DataFrame()

        iny = iny.copy()
        iny["Operando"] = iny["Operando"].fillna("").astype(str).str.strip()
        iny = iny[iny["Operando"] != ""].copy()

        if iny.empty:
            return pd.DataFrame()

        if not ver_todos_campo:
            iny = iny[
                iny["Yacimiento"].astype(str).str.upper() == str(yac_mapa).upper()
            ].copy()

        if iny.empty:
            return pd.DataFrame()

        coord_iny = coord.copy()
        coord_iny = coord_iny.loc[
            :,
            ~coord_iny.columns.astype(str).str.startswith("Unnamed")
        ]
        coord_iny = normalizar_columnas(coord_iny)

        cols_coord_iny = ["TERMINACION", "POZO", "CIMA X UTM", "CIMA Y UTM"]

        if any(c not in coord_iny.columns for c in cols_coord_iny) or "TERMINACION" not in iny.columns:
            return pd.DataFrame()

        iny["TERMINACION"] = iny["TERMINACION"].astype(str).str.strip()
        coord_iny["TERMINACION"] = coord_iny["TERMINACION"].astype(str).str.strip()
        coord_iny["POZO"] = coord_iny["POZO"].astype(str).str.strip()
        coord_iny = coord_iny[cols_coord_iny].drop_duplicates(subset=["TERMINACION"]).copy()

        coord_iny[x_col] = pd.to_numeric(coord_iny["CIMA X UTM"], errors="coerce")
        coord_iny[y_col] = pd.to_numeric(coord_iny["CIMA Y UTM"], errors="coerce")

        iny["POZO"] = iny["Pozo"].astype(str).str.strip()
        iny[COL_YAC] = iny["Yacimiento"]

        iny_mapa = iny.merge(
            coord_iny[["TERMINACION", "POZO", x_col, y_col]],
            on="TERMINACION",
            how="left"
        )
        iny_mapa["POZO"] = iny_mapa["POZO_y"].fillna(iny_mapa["POZO_x"])
        iny_mapa = iny_mapa.drop(columns=[c for c in ["POZO_x", "POZO_y"] if c in iny_mapa.columns])
        iny_mapa[x_col] = pd.to_numeric(iny_mapa[x_col], errors="coerce")
        iny_mapa[y_col] = pd.to_numeric(iny_mapa[y_col], errors="coerce")

        return iny_mapa.dropna(subset=[x_col, y_col]).copy()

    inyectores_operando_mapa = preparar_inyectores_operando_burbujas()

    colores_localizaciones = {
        "PND": "#00A65A",
        "PRB": "#FFD700",
        "POS": "#0057FF"
    }
    localizaciones_mapa = pd.DataFrame()
    filtro_localizaciones = "Ninguno"

    def preparar_localizaciones_burbujas(tipo_localizaciones):
        loc = load_localizaciones()

        if loc.empty or ver_todos_campo:
            return pd.DataFrame()

        loc = loc[
            loc["YACIMIENTO"].astype(str).str.upper() == str(yac_mapa).upper()
        ].copy()

        if loc.empty:
            return pd.DataFrame()

        if tipo_localizaciones == "196":
            col_196 = (
                loc["COLUMNA 1"]
                .dropna()
                .astype(str)
                .str.strip()
            )
            valores_196 = set(
                v.upper()
                for v in col_196
                if v and v.upper() not in ["NAN", "NONE"]
            )
            loc = loc[
                loc["COLUMNA 1"]
                .astype(str)
                .str.strip()
                .str.upper()
                .isin(valores_196)
            ].copy()

        loc[x_col] = pd.to_numeric(loc["FONDO X"], errors="coerce")
        loc[y_col] = pd.to_numeric(loc["FONDO Y"], errors="coerce")
        loc = loc.dropna(subset=[x_col, y_col]).copy()
        loc["COLOR_LOCALIZACION"] = loc["CATEGORIA"].map(colores_localizaciones).fillna("#7F8C8D")

        return loc

    def preparar_muestreos_agua_burbujas(mapa_base, fecha_inicio=None):
        muestreos = load_muestreos_agua()

        if muestreos.empty or ver_todos_campo:
            return pd.DataFrame()

        cols_mapa_req = ["TERMINACION", "POZO", COL_YAC, x_col, y_col]
        if any(c not in mapa_base.columns for c in cols_mapa_req):
            return pd.DataFrame()

        muestreos = muestreos.copy()
        muestreos["TERMINACION"] = muestreos["TERMINACION"].astype(str).str.strip()
        muestreos["% AGUA LAB"] = pd.to_numeric(muestreos["% AGUA LAB"], errors="coerce")
        muestreos["FECHA MUESTREO"] = convertir_fechas(muestreos["FECHA MUESTREO"])
        muestreos = muestreos.dropna(subset=["TERMINACION", "% AGUA LAB", "FECHA MUESTREO"])

        if fecha_inicio is not None:
            fecha_inicio = pd.to_datetime(fecha_inicio).normalize()
            muestreos = muestreos[muestreos["FECHA MUESTREO"] >= fecha_inicio].copy()

        if muestreos.empty:
            return pd.DataFrame()

        muestreos_ult = (
            muestreos.sort_values(["TERMINACION", "FECHA MUESTREO"])
            .groupby("TERMINACION", as_index=False)
            .tail(1)
        )

        coord_muestreos = (
            mapa_base[cols_mapa_req]
            .dropna(subset=["TERMINACION", x_col, y_col])
            .drop_duplicates(subset=["TERMINACION"])
            .copy()
        )
        coord_muestreos["TERMINACION"] = coord_muestreos["TERMINACION"].astype(str).str.strip()

        muestreos_mapa = muestreos_ult.merge(
            coord_muestreos,
            on="TERMINACION",
            how="inner",
            suffixes=("_MUESTREO", "")
        )

        if "POZO" not in muestreos_mapa.columns and "POZO_MUESTREO" in muestreos_mapa.columns:
            muestreos_mapa["POZO"] = muestreos_mapa["POZO_MUESTREO"]

        muestreos_mapa = muestreos_mapa[
            muestreos_mapa[COL_YAC].astype(str).str.upper() == str(yac_mapa).upper()
        ].copy()

        if muestreos_mapa.empty:
            return pd.DataFrame()

        max_agua_lab = muestreos_mapa["% AGUA LAB"].max()
        if max_agua_lab > 0:
            muestreos_mapa["SIZE_MUESTREO"] = 10 + (muestreos_mapa["% AGUA LAB"] / max_agua_lab) * 28
        else:
            muestreos_mapa["SIZE_MUESTREO"] = 10

        muestreos_mapa["ETIQUETA_MUESTREO"] = muestreos_mapa["% AGUA LAB"].map(lambda v: f"{v:,.1f}%")

        return muestreos_mapa.dropna(subset=[x_col, y_col]).copy()

    animar_key = f"modo_animado_burbujas_{modo_mapa}_{yac_mapa}"
    tipo_mapa_key = f"tipo_mapa_burbujas_{modo_mapa}_{yac_mapa}"
    solo_acum_key = f"solo_pozos_con_acum_mapa_{modo_mapa}"
    mostrar_valores_key = f"mostrar_valores_burbujas_{modo_mapa}"
    animar_tiempo_activo = bool(st.session_state.get(animar_key, False)) and not ver_todos_campo

    if animar_tiempo_activo:
        st.session_state[tipo_mapa_key] = "Mapa Burbujas"
        st.session_state[solo_acum_key] = False
        st.session_state[mostrar_valores_key] = False

    if usar_panel_filtros_mapa:
        with panel_filtros_mapa:
            #st.markdown("##### Tipo de mapa")
            #st.markdown("<div class='map-panel-section'>Tipo de mapa</div>", unsafe_allow_html=True)
            st.markdown(
                """
                <style>
                div[data-testid="stRadio"] {
                    margin-bottom: -1.2rem;
                }
                div[data-testid="stRadio"] ~ div[data-testid="stCheckbox"]:first-of-type {
                    margin-top: -0.9rem;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            if animar_tiempo_activo:
                opciones_tipo_mapa = ["Mapa Burbujas"]
            else:
                opciones_tipo_mapa = ["Mapa Burbujas", "Mapa GIS"]

            tipo_mapa = st.radio(
                "Tipo de mapa",
                opciones_tipo_mapa,
                horizontal=False,
                key=tipo_mapa_key
            )

            animar_tiempo = st.checkbox(
                "Modo animado",
                value=False,
                key=animar_key
            )

            if animar_tiempo:
                tipo_mapa = "Mapa Burbujas"
                solo_pozos_con_acum = False
                mostrar_etiquetas_burbujas = False

    control_variable_mapa = panel_filtros_mapa if usar_panel_filtros_mapa else c2

    with control_variable_mapa:

        if ver_todos_campo:

            variable = st.selectbox(
                "Variable de burbuja",
                ["ESTADO", "SAP"],
                format_func=lambda x: {
                    "ESTADO": "Estado de pozos",
                    "SAP": "SAP"
                }[x],
                key=f"variable_mapa_burbujas_{modo_mapa}_todos"
            )

        else:
            #st.markdown("##### Variable de burbuja")
            if usar_panel_filtros_mapa:
                st.markdown("<div class='map-panel-section'>Variable de burbuja</div>", unsafe_allow_html=True)

            variable = st.selectbox(
                "Variable de burbuja",
                ["NP_BLS", "WP_BLS", "WINJ_BLS", "GP_PC", "ULTIMO_WC", "NP_NORM_MB"],
                format_func=lambda x: {
                    "NP_BLS": "Aceite acumulado, Np [mb]",
                    "WP_BLS": "Agua acumulada, Wp [mb]",
                    "WINJ_BLS": "Agua inyectada acumulada, Winj [mb]",
                    "GP_PC": "Gas acumulado, Gp [mpc]",
                    "ULTIMO_WC": "Último % Agua [%]",
                    "NP_NORM_MB": "Producción Acumulada Normalizada [mb/mes]"
                }[x],
                key=f"variable_mapa_burbujas_{modo_mapa}"
            )

    control_zoom_mapa = c3 if ver_todos_campo else c2

    with control_zoom_mapa:
        pozos_mapa = sorted(mapa["POZO"].dropna().astype(str).unique())

        pozo_zoom = st.selectbox(
            "Zoom a pozo",
            options=["Todos"] + pozos_mapa,
            key=f"pozo_zoom_mapa_{modo_mapa}_{yac_mapa}"
        )

    control_perforados_mapa = panel_filtros_mapa if usar_panel_filtros_mapa else c4

    with control_perforados_mapa:

        if usar_panel_filtros_mapa:
            pass

        elif ver_todos_campo:

            yacs_operativas = sorted(
                mapa["YACIMIENTO"]
                .dropna()
                .astype(str)
                .str.upper()
                .unique()
            )

            filtro_yac_operativas = st.selectbox(
                "Yacimiento / unidad operativa",
                ["Todos"] + yacs_operativas,
                key=f"filtro_yac_operativas_{modo_mapa}_{yac_mapa}"
            )

            if filtro_yac_operativas != "Todos":
                mapa = mapa[
                    mapa["YACIMIENTO"].astype(str).str.upper() == str(filtro_yac_operativas)
                ].copy()

        elif modo_mapa == "RMA":
            st.markdown("##### Pozos RMA")

            filtro_term = st.selectbox(
                "Pozos intervenidos RMA",
                ["Todos", "Solo RMA", "Solo no RMA"],
                key=f"filtro_rma_mapa_{modo_mapa}_{yac_mapa}"
            )

            if filtro_term == "Solo RMA":
                mapa = mapa[mapa["POZO_RMA"] == "Sí"].copy()

            elif filtro_term == "Solo no RMA":
                mapa = mapa[mapa["POZO_RMA"] == "No"].copy()

        else:
            #st.markdown("##### Pozos perforados TERM")

            filtro_term = st.selectbox(
                "Pozos perforados históricos TERM",
                [
                    "Todos",
                    "Solo Campañas 2011-2020",
                    "315 Localizaciones",
                    "196 Localizaciones"
                ],
                key=f"filtro_term_mapa_{modo_mapa}_{yac_mapa}"
            )

            if filtro_term == "Solo Campañas 2011-2020":
                mapa = mapa[mapa["PERFORADO_TERM"] == "Sí"].copy()

            elif filtro_term == "315 Localizaciones":
                filtro_localizaciones = "315"
                localizaciones_mapa = preparar_localizaciones_burbujas(filtro_localizaciones)

            elif filtro_term == "196 Localizaciones":
                filtro_localizaciones = "196"
                localizaciones_mapa = preparar_localizaciones_burbujas(filtro_localizaciones)

    if usar_panel_filtros_mapa:
        control_opciones_mapa = panel_filtros_mapa
        resumen_tipo_mapa = salida_mapa_burbujas
    else:
        c5, c6 = st.columns([1, 3])
        control_opciones_mapa = c5
        resumen_tipo_mapa = c6

    filtro_solo_perforados_term = False
    mostrar_localizaciones_315 = False
    mostrar_localizaciones_196 = False
    mostrar_inyectores_operando = False
    mostrar_radio_drene = False
    mostrar_muestreos_agua = False
    fecha_inicio_muestreos_agua = None
    mostrar_perforados_term = False
    estados_activos_mapa = set(leyenda_estados.keys())

    with control_opciones_mapa:
        if usar_panel_filtros_mapa:
            #st.markdown("##### Opciones visuales")
            st.markdown("<div class='map-panel-section'>Filtros</div>", unsafe_allow_html=True)

            if modo_mapa != "RMA":
                #st.markdown("###### Pozos perforados TERM")

                filtro_solo_perforados_term = st.checkbox(
                    "Solo Campañas 2011-2020",
                    value=False,
                    key=f"filtro_term_solo_perf_chk_{modo_mapa}"
                )

                mostrar_localizaciones_315 = st.checkbox(
                    "315 Localizaciones",
                    value=False,
                    key=f"filtro_term_loc_315_chk_{modo_mapa}"
                )

                mostrar_localizaciones_196 = st.checkbox(
                    "196 Localizaciones",
                    value=False,
                    key=f"filtro_term_loc_196_chk_{modo_mapa}"
                )

                mostrar_inyectores_operando = st.checkbox(
                    "Inyectores Operando",
                    value=False,
                    key=f"mostrar_inyectores_operando_chk_{modo_mapa}"
                )

                mostrar_radio_drene = st.checkbox(
                    "Radios de drene",
                    value=False,
                    key=f"mostrar_radio_drene_chk_{modo_mapa}"
                )

                mostrar_muestreos_agua = st.checkbox(
                    "Muestreos % Agua",
                    value=False,
                    key=f"mostrar_muestreos_agua_chk_{modo_mapa}"
                )

                fecha_inicio_muestreos_agua = None
                if mostrar_muestreos_agua:
                    fecha_inicio_muestreos_agua = st.date_input(
                        "Muestreos desde",
                        value=pd.to_datetime("2026-05-23").date(),
                        key=f"fecha_inicio_muestreos_agua_{modo_mapa}"
                    )

                st.markdown("Estados de pozos")

                estados_activos_mapa = set()
                estados_panel_mapa = [
                    ("OP", "Op"),
                    ("CCP", "Ccp"),
                    ("CSP", "Csp"),
                    ("INY", "Iny"),
                    ("PROG TAPONAMIENTO", "Prog. Taponamiento"),
                    ("TAPONADO", "Taponado"),
                    ("SIN ESTADO", "Sin Estado"),
                ]

                for estado_key, estado_label in estados_panel_mapa:
                    if st.checkbox(
                        estado_label,
                        value=True,
                        key=f"estado_mapa_chk_{estado_key}_{modo_mapa}"
                    ):
                        estados_activos_mapa.add(estado_key)

                mostrar_perforados_term = st.checkbox(
                    "Campañas 2011-2020",
                    value=False,
                    key=f"mostrar_perforados_term_chk_{modo_mapa}"
                )

                st.markdown("---")

        mostrar_nombres = st.checkbox(
            "Mostrar nombres de pozos",
            value=True,
            key=f"mostrar_nombres_mapa_{modo_mapa}"
        )
        if animar_tiempo_activo:
            solo_pozos_con_acum = False
            mostrar_etiquetas_burbujas = False
        else:
            solo_pozos_con_acum = st.checkbox(
                "Solo pozos con producción",
                value=False,
                key=solo_acum_key
            )
            mostrar_etiquetas_burbujas = st.checkbox(
                "Mostrar valores de burbujas",
                value=False,
                disabled=ver_todos_campo,
                key=mostrar_valores_key
            )

    if usar_panel_filtros_mapa and modo_mapa != "RMA":
        if filtro_solo_perforados_term:
            mapa = mapa[mapa["PERFORADO_TERM"] == "Sí"].copy()

        locs_panel = []

        if mostrar_localizaciones_315:
            loc_315 = preparar_localizaciones_burbujas("315")
            if not loc_315.empty:
                locs_panel.append(loc_315)

        if mostrar_localizaciones_196:
            loc_196 = preparar_localizaciones_burbujas("196")
            if not loc_196.empty:
                locs_panel.append(loc_196)

        if locs_panel:
            filtro_localizaciones = "/".join(
                [
                    tipo
                    for tipo, activo in [
                        ("315", mostrar_localizaciones_315),
                        ("196", mostrar_localizaciones_196)
                    ]
                    if activo
                ]
            )
            localizaciones_mapa = pd.concat(locs_panel, ignore_index=True)

    if solo_pozos_con_acum and {"NP_BLS", "WINJ_BLS"}.issubset(mapa.columns):
        mapa = mapa[
            (pd.to_numeric(mapa["NP_BLS"], errors="coerce").fillna(0) > 0) |
            (pd.to_numeric(mapa["WINJ_BLS"], errors="coerce").fillna(0) > 0)
        ].copy()
    elif solo_pozos_con_acum:
        st.warning("No se encontraron columnas NP_BLS y WINJ_BLS para aplicar el filtro de acumuladas.")

    muestreos_agua_mapa = pd.DataFrame()
    if mostrar_muestreos_agua:
        muestreos_agua_mapa = preparar_muestreos_agua_burbujas(
            mapa,
            fecha_inicio=fecha_inicio_muestreos_agua
        )

    if "NP_BLS" in mapa.columns:
        pozos_np_mapa = mapa.loc[
            pd.to_numeric(mapa["NP_BLS"], errors="coerce").fillna(0) > 0,
            "POZO"
        ].dropna().astype(str).nunique()
    else:
        pozos_np_mapa = 0

    if "WINJ_BLS" in mapa.columns:
        pozos_iny_mapa = mapa.loc[
            pd.to_numeric(mapa["WINJ_BLS"], errors="coerce").fillna(0) > 0,
            "POZO"
        ].dropna().astype(str).nunique()
    else:
        pozos_iny_mapa = 0

    contadores_mapa = [
        ("Productores", pozos_np_mapa, "green"),
        ("Inyectores Históricos", pozos_iny_mapa, "blue"),
    ]

    if mostrar_muestreos_agua:
        contadores_mapa.append((
            "Muestreos % Agua",
            muestreos_agua_mapa["POZO"].dropna().astype(str).nunique() if not muestreos_agua_mapa.empty else 0,
            "#0057FF"
        ))

    if mostrar_inyectores_operando:
        contadores_mapa.append((
            "Iny. operando",
            inyectores_operando_mapa["POZO"].dropna().astype(str).nunique() if not inyectores_operando_mapa.empty else 0,
            "#0057FF"
        ))

    with resumen_tipo_mapa:
        if usar_panel_filtros_mapa:
            columnas_contadores = st.columns(len(contadores_mapa))
        else:
            c6_tipo, *columnas_contadores = st.columns([2.4] + [1] * len(contadores_mapa))

        if not usar_panel_filtros_mapa:
            with c6_tipo:
                if ver_todos_campo:
                    opciones_tipo_mapa = ["Mapa GIS"]
                elif animar_tiempo_activo:
                    opciones_tipo_mapa = ["Mapa Burbujas"]
                else:
                    opciones_tipo_mapa = ["Mapa Burbujas", "Mapa GIS"]

                tipo_mapa = st.radio(
                    "Tipo de mapa",
                    opciones_tipo_mapa,
                    horizontal=True,
                    key=tipo_mapa_key
                )

                animar_tiempo = st.checkbox(
                    "Modo animado",
                    value=False,
                    disabled=ver_todos_campo,
                    key=animar_key
                )

                if animar_tiempo and not ver_todos_campo:
                    tipo_mapa = "Mapa Burbujas"
                    solo_pozos_con_acum = False
                    mostrar_etiquetas_burbujas = False

        for col_contador, (titulo_contador, valor_contador, color_contador) in zip(columnas_contadores, contadores_mapa):
            with col_contador:
                st.markdown(
                    f"<div style='text-align:center; font-size:12px; color:#64748B;'>{titulo_contador}</div>"
                    f"<div style='text-align:center; font-size:22px; font-weight:800; color:{color_contador};'>{valor_contador:,.0f}</div>"
                    f"<div style='text-align:center; font-size:11px; color:#64748B;'>pozos</div>",
                    unsafe_allow_html=True
                )
        
    if mapa.empty:
        st.warning("No hay pozos para mostrar con los filtros seleccionados.")
        return

    # =====================================================
    # KPI CARDS SOLO PARA TODOS
    # =====================================================
    if ver_todos_campo:

        st.markdown(
            "<div class='section-title'>Resumen operativo de pozos</div>",
            unsafe_allow_html=True
        )

        if variable == "ESTADO":

            resumen_estado = (
                mapa.groupby("ESTADO", as_index=False)
                .agg(POZOS=("POZO", "nunique"))
            )

            estados_mostrar = ["NOP", "OP"]
            cols_kpi = st.columns(len(estados_mostrar))

            for i, edo in enumerate(estados_mostrar):

                valor = resumen_estado.loc[
                    resumen_estado["ESTADO"].astype(str).str.upper() == edo,
                    "POZOS"
                ]

                n = int(valor.iloc[0]) if not valor.empty else 0

                with cols_kpi[i]:
                    kpi_card(
                        edo,
                        f"{n:,.0f}",
                        "pozos",
                        #"#1F2937"
                        "#1F77B4"
                    )

        elif variable == "SAP":

            resumen_sap = (
                mapa.groupby("SAP", as_index=False)
                .agg(POZOS=("POZO", "nunique"))
            )

            saps_mostrar = ["BH", "BM", "BN", "CP", "F", "IA"]
            cols_kpi = st.columns(len(saps_mostrar))

            for i, sap in enumerate(saps_mostrar):

                valor = resumen_sap.loc[
                    resumen_sap["SAP"].astype(str).str.upper() == sap,
                    "POZOS"
                ]

                n = int(valor.iloc[0]) if not valor.empty else 0

                with cols_kpi[i]:
                    kpi_card(
                        sap,
                        f"{n:,.0f}",
                        "pozos",
                        #"#1F2937"
                        "#1F77B4"
                    )

        
    # =====================================================
    # TAMAÑO Y ETIQUETAS DE BURBUJAS
    # =====================================================
    mapa_uirevision = f"{modo_mapa}|{yac_mapa}|{tipo_mapa}|{variable}|{pozo_zoom}"
    color_burbuja = color_variable.get(variable, "green")

    if not ver_todos_campo and not animar_tiempo:

        mapa[variable] = pd.to_numeric(
            mapa[variable],
            errors="coerce"
        ).fillna(0)

        max_val = mapa[variable].max()

        if max_val > 0:

            mapa["SIZE"] = 18 + (mapa[variable] / max_val) * 80
        else:
            mapa["SIZE"] = 18

        if variable == "ULTIMO_WC":
            mapa["ETIQUETA_MAPA"] = mapa[variable].fillna(0).map(lambda x: f"{x:.1f}%")

        elif variable == "NP_NORM_MB":
            mapa["ETIQUETA_MAPA"] = mapa[variable].fillna(0).map(lambda x: f"{x:,.2f}")

        else:
            mapa["ETIQUETA_MAPA"] = mapa[variable].fillna(0).map(lambda x: f"{x/1000:,.1f}")

    else:
        mapa["SIZE"] = 8
        mapa["ETIQUETA_MAPA"] = ""

    def mostrar_tabla_pozos_mapa(datos_mapa: pd.DataFrame):
        if datos_mapa.empty:
            st.info("No hay pozos para mostrar en la tabla con los filtros actuales.")
            return

        columnas_preferidas = [
            "POZO",
            COL_YAC,
            "YACIMIENTO",
            "ESTADO",
            "SAP",
            "NP_BLS",
            "WP_BLS",
            "WINJ_BLS",
            "GP_PC",
            "ULTIMO_WC",
            "NP_NORM_MB",
            "MESES_OPERANDO",
            "RADIO DRENE",
            "ORIGEN_COORD",
            x_col,
            y_col
        ]

        columnas_tabla = []
        for col in columnas_preferidas:
            if col in datos_mapa.columns and col not in columnas_tabla:
                columnas_tabla.append(col)

        tabla = datos_mapa[columnas_tabla].copy()

        if "POZO" in tabla.columns:
            tabla = tabla.sort_values("POZO")

        st.markdown(
            "<div class='section-title'>Pozos mostrados en el mapa</div>",
            unsafe_allow_html=True
        )
        st.caption(f"Total de pozos en la tabla: {tabla['POZO'].nunique():,.0f}" if "POZO" in tabla.columns else "")
        st.dataframe(
            tabla,
            use_container_width=True,
            hide_index=True,
            height=360
        )

    @st.cache_data(show_spinner=False)
    def preparar_animacion_burbujas(
        datos_mapa: pd.DataFrame,
        yac_mapa_arg,
        x_col_arg,
        y_col_arg,
        usar_gis=False,
        ver_todos=False
    ):
        if ver_todos or datos_mapa.empty:
            return pd.DataFrame(), []

        prod_anim = load_prod_calc().copy()
        prod_anim = prod_anim[
            prod_anim[COL_YAC].astype(str) == str(yac_mapa_arg)
        ].copy()
        prod_anim = prod_anim[
            prod_anim[COL_POZO].astype(str).isin(datos_mapa[COL_POZO].astype(str))
        ].copy()

        if prod_anim.empty:
            return pd.DataFrame(), []

        prod_anim[COL_FECHA] = pd.to_datetime(prod_anim[COL_FECHA], errors="coerce")
        prod_anim = prod_anim.dropna(subset=[COL_FECHA]).copy()
        prod_anim[COL_FECHA] = prod_anim[COL_FECHA].dt.normalize()

        for col in [COL_ACEITE_BBL, COL_INY_BBL]:
            prod_anim[col] = pd.to_numeric(prod_anim[col], errors="coerce").fillna(0)

        prod_anim = prod_anim[
            (prod_anim[COL_ACEITE_BBL] > 0) |
            (prod_anim[COL_INY_BBL] > 0)
        ].copy()

        if prod_anim.empty:
            return pd.DataFrame(), []

        fechas_anim = sorted(prod_anim[COL_FECHA].unique())
        pozos_anim = sorted(datos_mapa[COL_POZO].dropna().astype(str).unique())

        base_anim = pd.MultiIndex.from_product(
            [fechas_anim, pozos_anim],
            names=[COL_FECHA, COL_POZO]
        ).to_frame(index=False)

        vol_anim = (
            prod_anim
            .groupby([COL_FECHA, COL_POZO], as_index=False)
            .agg(
                NP_MES=(COL_ACEITE_BBL, "sum"),
                WINJ_MES=(COL_INY_BBL, "sum")
            )
        )
        vol_anim[COL_POZO] = vol_anim[COL_POZO].astype(str)

        anim = base_anim.merge(vol_anim, on=[COL_FECHA, COL_POZO], how="left")
        anim[["NP_MES", "WINJ_MES"]] = anim[["NP_MES", "WINJ_MES"]].fillna(0)
        anim = anim.sort_values([COL_POZO, COL_FECHA])
        anim["NP_BLS_ANIM"] = anim.groupby(COL_POZO)["NP_MES"].cumsum()
        anim["WINJ_BLS_ANIM"] = anim.groupby(COL_POZO)["WINJ_MES"].cumsum()

        cols_coord_anim = [COL_POZO, "POZO", COL_YAC, x_col_arg, y_col_arg]
        if usar_gis:
            cols_coord_anim += ["LAT", "LON"]

        cols_coord_anim = [
            col for col in cols_coord_anim
            if col in datos_mapa.columns
        ]

        coords_anim = datos_mapa[cols_coord_anim].drop_duplicates(subset=[COL_POZO]).copy()
        coords_anim[COL_POZO] = coords_anim[COL_POZO].astype(str)
        anim = anim.merge(coords_anim, on=COL_POZO, how="left")
        anim = anim.dropna(subset=["LAT", "LON"] if usar_gis else [x_col_arg, y_col_arg]).copy()

        max_np_anim = anim["NP_BLS_ANIM"].max()
        max_iny_anim = anim["WINJ_BLS_ANIM"].max()
        anim["SIZE_NP_ANIM"] = np.where(
            max_np_anim > 0,
            14 + (anim["NP_BLS_ANIM"] / max_np_anim) * 75,
            14
        )
        anim["SIZE_INY_ANIM"] = np.where(
            max_iny_anim > 0,
            14 + (anim["WINJ_BLS_ANIM"] / max_iny_anim) * 75,
            14
        )
        anim["FECHA_TXT"] = anim[COL_FECHA].dt.strftime("%d/%m/%Y")
        anim["ETIQUETA_NP_ANIM"] = anim["NP_BLS_ANIM"].map(lambda v: f"{v/1000:,.1f}" if v > 0 else "")
        anim["ETIQUETA_INY_ANIM"] = anim["WINJ_BLS_ANIM"].map(lambda v: f"{v/1000:,.1f}" if v > 0 else "")
        anim["INYECTANDO_ANIM"] = anim["WINJ_MES"] > 0
        anim["COLOR_INY_ANIM"] = np.where(
            anim["INYECTANDO_ANIM"],
            "rgba(0, 92, 255, 0.32)",
            "rgba(115, 190, 255, 0.18)"
        )
        anim["BORDE_INY_ANIM"] = np.where(
            anim["INYECTANDO_ANIM"],
            "#001BFF",
            "rgba(115, 190, 255, 0.70)"
        )
        anim["ANCHO_BORDE_INY_ANIM"] = np.where(
            anim["INYECTANDO_ANIM"],
            3.2,
            1.2
        )

        return anim, fechas_anim

    def controles_animacion_burbujas():
        return dict(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    x=0.43,
                    y=1.10,
                    xanchor="center",
                    yanchor="top",
                    buttons=[
                        dict(
                            label="Play",
                            method="animate",
                            args=[None, {
                                "frame": {"duration": 650, "redraw": True},
                                "transition": {"duration": 250},
                                "fromcurrent": True,
                                "mode": "immediate"
                            }]
                        ),
                        dict(
                            label="Stop",
                            method="animate",
                            args=[[None], {
                                "frame": {"duration": 0, "redraw": False},
                                "transition": {"duration": 0},
                                "mode": "immediate"
                            }]
                        )
                    ]
                )
            ],
            sliders=[
                dict(
                    active=0,
                    x=0.01,
                    y=-0.03,
                    len=0.95,
                    currentvalue=dict(prefix="Fecha: "),
                    steps=[]
                )
            ]
        )

    def preparar_datos_graficas_animadas(pozo_sel):
        if not pozo_sel:
            return pd.DataFrame(), pd.DataFrame()

        prod_pozo_raw = df_base[
            df_base[COL_POZO].astype(str).str.strip() == str(pozo_sel).strip()
        ].copy()

        if yac_mapa != "Todos" and COL_YAC in prod_pozo_raw.columns:
            prod_pozo_raw = prod_pozo_raw[
                prod_pozo_raw[COL_YAC].astype(str) == str(yac_mapa)
            ].copy()

        if not prod_pozo_raw.empty:
            df_pozo_completo = completar_fechas_pozo(prod_pozo_raw)
            prod_pozo = calcular_columnas_produccion(df_pozo_completo)
            prod_pozo = prod_pozo.sort_values(COL_FECHA).reset_index(drop=True)
        else:
            prod_pozo = pd.DataFrame()

        pres_pozo = load_presiones()
        if not pres_pozo.empty:
            pres_pozo["TERMINACION"] = pres_pozo["TERMINACION"].astype(str).str.strip()
            pres_pozo["POZO"] = pres_pozo["POZO"].astype(str).str.strip()
            pres_pozo = pres_pozo[
                (pres_pozo["TERMINACION"] == str(pozo_sel).strip()) |
                (pres_pozo["POZO"] == str(pozo_sel).strip())
            ].copy()

            if yac_mapa != "Todos" and "YACIMIENTO" in pres_pozo.columns:
                pres_pozo = pres_pozo[
                    pres_pozo["YACIMIENTO"].astype(str) == str(yac_mapa)
                ].copy()

            pres_pozo["FECHA"] = pd.to_datetime(pres_pozo["FECHA"], errors="coerce")
            pres_pozo["PRESION"] = pd.to_numeric(pres_pozo["PRESION"], errors="coerce")
            pres_pozo = pres_pozo.dropna(subset=["FECHA", "PRESION"]).sort_values("FECHA")

        return prod_pozo, pres_pozo

    def pozos_disponibles_graficas_animadas(datos_mapa):
        cols_historia_anim = [
            col for col in ["NP_BLS", "WP_BLS", "GP_PC", "WINJ_BLS"]
            if col in datos_mapa.columns
        ]
        if not cols_historia_anim:
            return []

        datos = datos_mapa.copy()
        datos["TOTAL_HISTORIA_GRAF"] = (
            datos[cols_historia_anim]
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0)
            .sum(axis=1)
        )

        return sorted(
            datos.loc[
                datos["TOTAL_HISTORIA_GRAF"] > 0,
                COL_POZO
            ].dropna().astype(str).unique()
        )

    @st.fragment
    def graficas_pozo_animadas_fragment(pozos_graficas_anim):
        if not pozos_graficas_anim:
            st.caption("No hay pozos con historia de produccion o inyeccion para graficar.")
            return

        pozo_sel_graf = st.selectbox(
            "Pozo para graficas",
            pozos_graficas_anim,
            key=f"pozo_graficas_anim_burbujas_{modo_mapa}_{yac_mapa}"
        )

        prod_graf, pres_graf = preparar_datos_graficas_animadas(pozo_sel_graf)

        if prod_graf.empty:
            st.info("No hay historia para el pozo seleccionado.")
            return

        fechas_rango = list(pd.to_datetime(prod_graf[COL_FECHA], errors="coerce"))
        if not pres_graf.empty:
            fechas_rango.extend(pd.to_datetime(pres_graf["FECHA"], errors="coerce"))
        fechas_rango = [fecha for fecha in fechas_rango if pd.notna(fecha)]
        rango_x = [min(fechas_rango), max(fechas_rango)] if fechas_rango else None

        def formato_grafica(fig, titulo, y1, y2=None):
            fig.update_layout(
                title=dict(
                    text=f"<b>{titulo}</b>",
                    x=0.02,
                    xanchor="left",
                    font=dict(size=14, family="Arial Black", color="#111827")
                ),
                template="plotly_white",
                hovermode="x unified",
                height=255,
                plot_bgcolor="#F8F8FF",
                paper_bgcolor="white",
                font=dict(family="Arial", size=11, color="#111827"),
                margin=dict(l=45, r=45, t=55, b=38),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=10, family="Arial", color="#111827"),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="#D1D5DB",
                    borderwidth=1
                )
            )
            fig.update_xaxes(
                range=rango_x,
                title_text="<b>Fecha</b>",
                tickformat="%d/%m/%Y",
                showgrid=True,
                gridcolor="#E5E7EB",
                gridwidth=0.7,
                zeroline=False,
                showline=True,
                linewidth=1.2,
                linecolor="#111827",
                mirror=True,
                ticks="outside",
                tickfont=dict(size=10, color="#111827")
            )
            fig.update_yaxes(
                title_text=f"<b>{y1}</b>",
                showgrid=True,
                gridcolor="#E5E7EB",
                gridwidth=0.7,
                zeroline=False,
                separatethousands=True,
                showline=True,
                linewidth=1.2,
                linecolor="#111827",
                mirror=True,
                ticks="outside",
                tickfont=dict(size=10, color="#111827"),
                secondary_y=False
            )
            if y2:
                fig.update_yaxes(
                    title_text=f"<b>{y2}</b>",
                    showgrid=False,
                    zeroline=False,
                    separatethousands=True,
                    showline=True,
                    linewidth=1.2,
                    linecolor="#111827",
                    ticks="outside",
                    tickfont=dict(size=10, color="#111827"),
                    secondary_y=True
                )
            return fig

        fig_aceite = make_subplots(specs=[[{"secondary_y": True}]])
        fig_aceite.add_trace(go.Scatter(
            x=prod_graf[COL_FECHA],
            y=prod_graf[COL_QO],
            mode="lines+markers",
            name="Qo (bpd)",
            line=dict(width=2, color="#27AE60"),
            marker=dict(size=3),
            fill="tozeroy",
            fillcolor="rgba(39,174,96,0.18)",
            connectgaps=False,
            hovertemplate="<b>Fecha:</b> %{x|%d/%m/%Y}<br><b>Qo:</b> %{y:,.2f} bpd<extra></extra>"
        ), secondary_y=False)
        if not pres_graf.empty:
            fig_aceite.add_trace(go.Scatter(
                x=pres_graf["FECHA"],
                y=pres_graf["PRESION"],
                mode="markers",
                name="Presion",
                marker=dict(size=7, color="#8E44AD", symbol="diamond"),
                connectgaps=False,
                hovertemplate="<b>Fecha:</b> %{x|%d/%m/%Y}<br><b>Presion:</b> %{y:,.2f}<extra></extra>"
            ), secondary_y=True)
        st.plotly_chart(
            formato_grafica(fig_aceite, f"Aceite y presion - {pozo_sel_graf}", "Qo", "Presion"),
            use_container_width=True,
            config={"displaylogo": False}
        )

        fig_agua = make_subplots(specs=[[{"secondary_y": True}]])
        fig_agua.add_trace(go.Scatter(
            x=prod_graf[COL_FECHA],
            y=prod_graf[COL_WC],
            mode="lines+markers",
            name="% Agua",
            line=dict(width=2, color="#0000FF"),
            marker=dict(size=3),
            connectgaps=False,
            hovertemplate="<b>Fecha:</b> %{x|%d/%m/%Y}<br><b>% Agua:</b> %{y:,.2f}<extra></extra>"
        ), secondary_y=False)
        fig_agua.add_trace(go.Scatter(
            x=prod_graf[COL_FECHA],
            y=prod_graf[COL_QW],
            mode="lines+markers",
            name="Qw (bpd)",
            line=dict(width=2, color="#3498DB"),
            marker=dict(size=3),
            fill="tozeroy",
            fillcolor="rgba(52,152,219,0.16)",
            connectgaps=False,
            hovertemplate="<b>Fecha:</b> %{x|%d/%m/%Y}<br><b>Qw:</b> %{y:,.2f} bpd<extra></extra>"
        ), secondary_y=True)
        st.plotly_chart(
            formato_grafica(fig_agua, f"Corte de agua y agua - {pozo_sel_graf}", "% Agua", "Qw"),
            use_container_width=True,
            config={"displaylogo": False}
        )

        fig_gas = make_subplots(specs=[[{"secondary_y": True}]])
        fig_gas.add_trace(go.Scatter(
            x=prod_graf[COL_FECHA],
            y=prod_graf[COL_QG],
            mode="lines+markers",
            name="Qg (mpcd)",
            line=dict(width=2, color="#FF0000"),
            marker=dict(size=3),
            connectgaps=False,
            hovertemplate="<b>Fecha:</b> %{x|%d/%m/%Y}<br><b>Qg:</b> %{y:,.2f} mpcd<extra></extra>"
        ), secondary_y=False)
        fig_gas.add_trace(go.Scatter(
            x=prod_graf[COL_FECHA],
            y=prod_graf[COL_RGA],
            mode="lines+markers",
            name="RGA (pc/bl)",
            line=dict(width=2, color="#E67E22"),
            marker=dict(size=3),
            connectgaps=False,
            hovertemplate="<b>Fecha:</b> %{x|%d/%m/%Y}<br><b>RGA:</b> %{y:,.2f} pc/bl<extra></extra>"
        ), secondary_y=True)
        st.plotly_chart(
            formato_grafica(fig_gas, f"Gas y RGA - {pozo_sel_graf}", "Qg", "RGA"),
            use_container_width=True,
            config={"displaylogo": False}
        )

        fig_acum = make_subplots(specs=[[{"secondary_y": True}]])
        fig_acum.add_trace(go.Scatter(
            x=prod_graf[COL_FECHA],
            y=prod_graf[COL_NP],
            mode="lines+markers",
            name="Np (mbl)",
            line=dict(width=2, color="#008000"),
            marker=dict(size=3),
            connectgaps=False,
            hovertemplate="<b>Fecha:</b> %{x|%d/%m/%Y}<br><b>Np:</b> %{y:,.2f} mbl<extra></extra>"
        ), secondary_y=False)
        fig_acum.add_trace(go.Scatter(
            x=prod_graf[COL_FECHA],
            y=prod_graf[COL_WP],
            mode="lines+markers",
            name="Wp (mbl)",
            line=dict(width=2, color="#1E88E5"),
            marker=dict(size=3),
            connectgaps=False,
            hovertemplate="<b>Fecha:</b> %{x|%d/%m/%Y}<br><b>Wp:</b> %{y:,.2f} mbl<extra></extra>"
        ), secondary_y=False)
        fig_acum.add_trace(go.Scatter(
            x=prod_graf[COL_FECHA],
            y=prod_graf[COL_GP],
            mode="lines+markers",
            name="Gp (mmpc)",
            line=dict(width=2, color="#E53935"),
            marker=dict(size=3),
            connectgaps=False,
            hovertemplate="<b>Fecha:</b> %{x|%d/%m/%Y}<br><b>Gp:</b> %{y:,.2f} mmpc<extra></extra>"
        ), secondary_y=True)
        st.plotly_chart(
            formato_grafica(fig_acum, f"Acumuladas - {pozo_sel_graf}", "Np / Wp", "Gp"),
            use_container_width=True,
            config={"displaylogo": False}
        )

    # =====================================================
    # MAPA GIS
    # =====================================================
    if tipo_mapa == "Mapa GIS":

        mapa_gis = convertir_utm_a_latlon(mapa, x_col, y_col)

        if animar_tiempo and not ver_todos_campo:
            cols_anim_gis = [
                col for col in [COL_POZO, "POZO", COL_YAC, x_col, y_col, "LAT", "LON"]
                if col in mapa_gis.columns
            ]
            anim_gis, fechas_anim = preparar_animacion_burbujas(
                mapa_gis[cols_anim_gis].copy(),
                yac_mapa,
                x_col,
                y_col,
                usar_gis=True,
                ver_todos=ver_todos_campo
            )

            if anim_gis.empty or not fechas_anim:
                st.warning("No hay historia de aceite o inyección para animar con los filtros actuales.")
            else:
                fecha_ini_anim = fechas_anim[0]
                datos_ini = anim_gis[anim_gis[COL_FECHA] == fecha_ini_anim].copy()
                datos_np_ini = datos_ini[datos_ini["NP_BLS_ANIM"] > 0].copy()
                datos_iny_ini = datos_ini[datos_ini["WINJ_BLS_ANIM"] > 0].copy()

                fig_anim_gis = go.Figure()

                fig_anim_gis.add_trace(go.Scattermapbox(
                    lat=datos_np_ini["LAT"],
                    lon=datos_np_ini["LON"],
                    mode="markers+text" if mostrar_nombres else "markers",
                    text=datos_np_ini["POZO"] if mostrar_nombres else None,
                    textposition="top center",
                    marker=dict(
                        size=datos_np_ini["SIZE_NP_ANIM"],
                        color="green",
                        opacity=0.42
                    ),
                    name="Np acumulado",
                    customdata=datos_np_ini[["POZO", COL_YAC, "NP_BLS_ANIM", "WINJ_BLS_ANIM", "FECHA_TXT"]],
                    hovertemplate=
                        "<b>Pozo:</b> %{customdata[0]}<br>" +
                        "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                        "<b>Fecha:</b> %{customdata[4]}<br>" +
                        "<b>Np:</b> %{customdata[2]:,.0f} bls<br>" +
                        "<b>Winj:</b> %{customdata[3]:,.0f} bls<br>" +
                        "<extra></extra>"
                ))

                fig_anim_gis.add_trace(go.Scattermapbox(
                    lat=datos_iny_ini["LAT"],
                    lon=datos_iny_ini["LON"],
                    mode="markers+text" if mostrar_etiquetas_burbujas else "markers",
                    text=datos_iny_ini["ETIQUETA_INY_ANIM"] if mostrar_etiquetas_burbujas else None,
                    textposition="bottom center",
                    marker=dict(
                        size=datos_iny_ini["SIZE_INY_ANIM"],
                        color=datos_iny_ini["COLOR_INY_ANIM"],
                        opacity=0.70
                    ),
                    name="Winj acumulado",
                    customdata=datos_iny_ini[["POZO", COL_YAC, "NP_BLS_ANIM", "WINJ_BLS_ANIM", "FECHA_TXT", "WINJ_MES"]],
                    hovertemplate=
                        "<b>Pozo:</b> %{customdata[0]}<br>" +
                        "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                        "<b>Fecha:</b> %{customdata[4]}<br>" +
                        "<b>Np:</b> %{customdata[2]:,.0f} bls<br>" +
                        "<b>Winj:</b> %{customdata[3]:,.0f} bls<br>" +
                        "<b>Inyeccion del mes:</b> %{customdata[5]:,.0f} bls<br>" +
                        "<extra></extra>"
                ))

                if mostrar_inyectores_operando and not inyectores_operando_mapa.empty:
                    iny_gis = convertir_utm_a_latlon(inyectores_operando_mapa, x_col, y_col)
                    fig_anim_gis.add_trace(go.Scattermapbox(
                        lat=iny_gis["LAT"],
                        lon=iny_gis["LON"],
                        mode="markers",
                        marker=dict(size=18, color="#0057FF", opacity=0.95),
                        name="Inyectores operando",
                        customdata=iny_gis[["POZO", COL_YAC, "Operando", "VI_BLS"]],
                        hovertemplate=
                            "<b>Inyector operando:</b> %{customdata[0]}<br>" +
                            "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                            "<b>Operando:</b> %{customdata[2]}<br>" +
                            "<b>Vi:</b> %{customdata[3]:,.0f} bls<br>" +
                            "<extra></extra>"
                    ))

                frames_gis = []
                steps_gis = []
                for fecha_anim in fechas_anim:
                    datos_frame = anim_gis[anim_gis[COL_FECHA] == fecha_anim].copy()
                    datos_np = datos_frame[datos_frame["NP_BLS_ANIM"] > 0].copy()
                    datos_iny = datos_frame[datos_frame["WINJ_BLS_ANIM"] > 0].copy()
                    nombre_frame = pd.to_datetime(fecha_anim).strftime("%d/%m/%Y")

                    frames_gis.append(go.Frame(
                        name=nombre_frame,
                        traces=[0, 1],
                        data=[
                            go.Scattermapbox(
                                lat=datos_np["LAT"],
                                lon=datos_np["LON"],
                                mode="markers+text" if mostrar_nombres else "markers",
                                text=datos_np["POZO"] if mostrar_nombres else None,
                                textposition="top center",
                                marker=dict(size=datos_np["SIZE_NP_ANIM"], color="green", opacity=0.42),
                                customdata=datos_np[["POZO", COL_YAC, "NP_BLS_ANIM", "WINJ_BLS_ANIM", "FECHA_TXT"]]
                            ),
                            go.Scattermapbox(
                                lat=datos_iny["LAT"],
                                lon=datos_iny["LON"],
                                mode="markers+text" if mostrar_etiquetas_burbujas else "markers",
                                text=datos_iny["ETIQUETA_INY_ANIM"] if mostrar_etiquetas_burbujas else None,
                                textposition="bottom center",
                                marker=dict(size=datos_iny["SIZE_INY_ANIM"], color=datos_iny["COLOR_INY_ANIM"], opacity=0.70),
                                customdata=datos_iny[["POZO", COL_YAC, "NP_BLS_ANIM", "WINJ_BLS_ANIM", "FECHA_TXT", "WINJ_MES"]]
                            )
                        ]
                    ))
                    steps_gis.append(dict(
                        label=nombre_frame,
                        method="animate",
                        args=[[nombre_frame], {
                            "frame": {"duration": 0, "redraw": True},
                            "transition": {"duration": 0},
                            "mode": "immediate"
                        }]
                    ))

                fig_anim_gis.frames = frames_gis

                centro_gis_anim = dict(lat=mapa_gis["LAT"].mean(), lon=mapa_gis["LON"].mean())
                zoom_gis_anim = 12

                if pozo_zoom != "Todos" and "POZO" in mapa_gis.columns:
                    row_zoom_gis = mapa_gis[mapa_gis["POZO"].astype(str) == str(pozo_zoom)]
                    if not row_zoom_gis.empty:
                        centro_gis_anim = dict(
                            lat=row_zoom_gis["LAT"].iloc[0],
                            lon=row_zoom_gis["LON"].iloc[0]
                        )
                        zoom_gis_anim = 15

                fig_anim_gis.update_layout(
                    title=f"<b>Animación acumulada Np / Winj - {yac_mapa}</b>",
                    dragmode="pan",
                    mapbox=dict(style="open-street-map", center=centro_gis_anim, zoom=zoom_gis_anim),
                    height=850,
                    margin=dict(l=0, r=0, t=125, b=35),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    updatemenus=[
                        dict(
                            type="buttons",
                            direction="left",
                            x=0.43,
                            y=1.10,
                            xanchor="center",
                            yanchor="top",
                            buttons=[
                                dict(label="Play", method="animate", args=[None, {
                                    "frame": {"duration": 650, "redraw": True},
                                    "transition": {"duration": 250},
                                    "fromcurrent": True,
                                    "mode": "immediate"
                                }]),
                                dict(label="Stop", method="animate", args=[[None], {
                                    "frame": {"duration": 0, "redraw": False},
                                    "transition": {"duration": 0},
                                    "mode": "immediate"
                                }])
                            ]
                        )
                    ],
                    sliders=[
                        dict(
                            active=0,
                            x=0.01,
                            y=1.04,
                            len=0.95,
                            currentvalue=dict(prefix="Fecha: "),
                            steps=steps_gis
                        )
                    ]
                )

                salida_mapa_burbujas.plotly_chart(
                    fig_anim_gis,
                    use_container_width=True,
                    config={"scrollZoom": True, "displaylogo": False}
                )

                mostrar_tabla_pozos_mapa(mapa)

                return

        fig_gis = go.Figure()

        if not ver_todos_campo:

            mapa_burb = mapa_gis[mapa_gis[variable] > 0].copy()

            if not mapa_burb.empty:

                fig_gis.add_trace(
                    go.Scattermapbox(
                        lat=mapa_burb["LAT"],
                        lon=mapa_burb["LON"],
                        mode="markers+text" if mostrar_nombres else "markers",
                        text=mapa_burb["POZO"] if mostrar_nombres else None,
                        textposition="top center",
                        marker=dict(
                            size=mapa_burb["SIZE"],
                            color=color_burbuja,
                            opacity=0.45
                        ),
                        name="Producción acumulada",
                        customdata=mapa_burb[
                            ["POZO", COL_YAC, "NP_BLS", "WP_BLS", "WINJ_BLS", "GP_PC", "MESES_OPERANDO", "NP_NORM_MB"]
                        ],
                        hovertemplate=
                            "<b>Pozo:</b> %{customdata[0]}<br>" +
                            "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                            "<b>Np:</b> %{customdata[2]:,.0f} bls<br>" +
                            "<b>Wp:</b> %{customdata[3]:,.0f} bls<br>" +
                            "<b>Winj:</b> %{customdata[4]:,.0f} bls<br>" +
                            "<b>Gp:</b> %{customdata[5]:,.0f} pc<br>" +
                            "<b>Meses operando:</b> %{customdata[6]:,.0f}<br>" +
                            "<b>Np normalizada:</b> %{customdata[7]:,.2f} mb/mes<br>" +
                            "<extra></extra>"
                    )
                )

        if ver_todos_campo and variable == "SAP":

            mapa_gis["SAP_MAPA"] = (
                mapa_gis["SAP"]
                .astype(str)
                .str.strip()
                .str.upper()
                .replace({
                    "": "SIN SAP",
                    "NAN": "SIN SAP",
                    "NONE": "SIN SAP"
                })
            )

            for sap, color in leyenda_sap.items():

                tmp = mapa_gis[mapa_gis["SAP_MAPA"] == sap].copy()

                if tmp.empty:
                    continue

                fig_gis.add_trace(
                    go.Scattermapbox(
                        lat=tmp["LAT"],
                        lon=tmp["LON"],
                        mode="markers+text" if mostrar_nombres else "markers",
                        text=tmp["POZO"] if mostrar_nombres else None,
                        textposition="top center",
                        marker=dict(
                            size=9,
                            color=color
                        ),
                        name=sap,
                        customdata=tmp[["POZO", "YACIMIENTO", "ESTADO", "SAP"]],
                        hovertemplate=
                            "<b>Pozo:</b> %{customdata[0]}<br>" +
                            "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                            "<b>Estado:</b> %{customdata[2]}<br>" +
                            "<b>SAP:</b> %{customdata[3]}<br>" +
                            "<extra></extra>",
                        legendgroup=sap,
                        showlegend=True
                    )
                )

        else:

            for estado, color in leyenda_estados.items():

                if estado not in estados_activos_mapa:
                    continue

                tmp = mapa_gis[mapa_gis["ESTADO_MAPA"] == estado].copy()

                if tmp.empty:
                    continue

                fig_gis.add_trace(
                    go.Scattermapbox(
                        lat=tmp["LAT"],
                        lon=tmp["LON"],
                        mode="markers+text" if mostrar_nombres else "markers",
                        text=tmp["POZO"] if mostrar_nombres else None,
                        textposition="top center",
                        marker=dict(
                            size=9 if ver_todos_campo else 7,
                            color=color
                        ),
                        name=estado.title(),
                        customdata=tmp[["POZO", COL_YAC, "ESTADO", "SAP"]],
                        hovertemplate=
                            "<b>Pozo:</b> %{customdata[0]}<br>" +
                            "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                            "<b>Estado:</b> %{customdata[2]}<br>" +
                            "<b>SAP:</b> %{customdata[3]}<br>" +
                            "<extra></extra>",
                        legendgroup=estado,
                        showlegend=True
                    )
                )

        if not muestreos_agua_mapa.empty:
            muestreos_gis = convertir_utm_a_latlon(muestreos_agua_mapa, x_col, y_col)

            fig_gis.add_trace(go.Scattermapbox(
                lat=muestreos_gis["LAT"],
                lon=muestreos_gis["LON"],
                mode="markers",
                marker=dict(
                    size=muestreos_gis["SIZE_MUESTREO"] + 4,
                    color="#0057FF",
                    opacity=0.85
                ),
                name="Borde Muestreos % Agua",
                legendgroup="muestreos_agua",
                showlegend=False,
                hoverinfo="skip"
            ))

            fig_gis.add_trace(go.Scattermapbox(
                lat=muestreos_gis["LAT"],
                lon=muestreos_gis["LON"],
                mode="markers+text",
                text=muestreos_gis["ETIQUETA_MUESTREO"],
                textposition="bottom center",
                marker=dict(
                    size=muestreos_gis["SIZE_MUESTREO"],
                    color="#8EDBFF",
                    opacity=0.82
                ),
                name="Muestreos % Agua",
                legendgroup="muestreos_agua",
                customdata=muestreos_gis[["POZO", "TERMINACION", COL_YAC, "FECHA MUESTREO", "% AGUA LAB"]],
                hovertemplate=
                    "<b>Pozo:</b> %{customdata[0]}<br>" +
                    "<b>Terminación:</b> %{customdata[1]}<br>" +
                    "<b>Yacimiento:</b> %{customdata[2]}<br>" +
                    "<b>Fecha muestreo:</b> %{customdata[3]|%d/%m/%Y}<br>" +
                    "<b>% Agua Lab:</b> %{customdata[4]:,.1f}%<br>" +
                    "<extra></extra>",
                showlegend=True
            ))

        if not localizaciones_mapa.empty:
            loc_gis = convertir_utm_a_latlon(localizaciones_mapa, x_col, y_col)

            for categoria, color in colores_localizaciones.items():
                tmp_loc = loc_gis[loc_gis["CATEGORIA"].astype(str).str.upper() == categoria].copy()

                if tmp_loc.empty:
                    continue

                fig_gis.add_trace(go.Scattermapbox(
                    lat=tmp_loc["LAT"],
                    lon=tmp_loc["LON"],
                    mode="markers+text" if mostrar_nombres else "markers",
                    text=tmp_loc["POZO"] if mostrar_nombres else None,
                    textposition="bottom center",
                    marker=dict(
                        size=13,
                        color=color,
                        opacity=0.95
                    ),
                    name=f"Loc {filtro_localizaciones} {categoria}",
                    customdata=tmp_loc[["POZO", "TERMINACION", "YACIMIENTO", "CATEGORIA"]],
                    hovertemplate=
                        "<b>Localizacion:</b> %{customdata[0]}<br>" +
                        "<b>Terminacion:</b> %{customdata[1]}<br>" +
                        "<b>Yacimiento:</b> %{customdata[2]}<br>" +
                        "<b>Categoria:</b> %{customdata[3]}<br>" +
                        "<extra></extra>",
                    legendgroup=f"loc_{categoria}",
                    showlegend=True
                ))

        if mostrar_inyectores_operando and not inyectores_operando_mapa.empty:
            iny_gis = convertir_utm_a_latlon(inyectores_operando_mapa, x_col, y_col)

            fig_gis.add_trace(go.Scattermapbox(
                lat=iny_gis["LAT"],
                lon=iny_gis["LON"],
                mode="markers",
                marker=dict(
                    size=11 if ver_todos_campo else 18,
                    color="#0057FF",
                    opacity=0.95
                ),
                name="Inyectores operando",
                customdata=iny_gis[["POZO", COL_YAC, "Operando", "VI_BLS"]],
                hovertemplate=
                    "<b>Inyector operando:</b> %{customdata[0]}<br>" +
                    "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                    "<b>Operando:</b> %{customdata[2]}<br>" +
                    "<b>Vi:</b> %{customdata[3]:,.0f} bls<br>" +
                    "<extra></extra>",
                showlegend=True
            ))

        if ver_todos_campo and mostrar_instalaciones_gis:
            instalaciones_gis = load_instalaciones_gis()

            if not instalaciones_gis.empty:
                estilos_instalaciones = {
                    "BATERIA": {"color": "purple", "name": "Baterias"},
                    "SIACO": {"color": "cyan", "name": "SIACO"},
                    "COMPRESORA": {"color": "red", "name": "Compresora"},
                }

                for tipo_inst, estilo_inst in estilos_instalaciones.items():
                    tmp_inst = instalaciones_gis[
                        instalaciones_gis["INSTALACION"].astype(str).str.upper() == tipo_inst
                    ].copy()

                    if tmp_inst.empty:
                        continue

                    fig_gis.add_trace(go.Scattermapbox(
                        lat=tmp_inst["LAT"],
                        lon=tmp_inst["LON"],
                        mode="markers",
                        marker=dict(
                            size=18,
                            color="black",
                            opacity=0.95
                        ),
                        name=f"Borde {estilo_inst['name']}",
                        legendgroup=f"inst_{tipo_inst}",
                        showlegend=False,
                        hoverinfo="skip"
                    ))

                    fig_gis.add_trace(go.Scattermapbox(
                        lat=tmp_inst["LAT"],
                        lon=tmp_inst["LON"],
                        mode="markers+text" if mostrar_nombres else "markers",
                        text=tmp_inst["ALIAS"] if mostrar_nombres else None,
                        textposition="bottom center",
                        marker=dict(
                            size=14,
                            color=estilo_inst["color"],
                            opacity=0.95
                        ),
                        name=estilo_inst["name"],
                        customdata=tmp_inst[["ALIAS", "INSTALACION", "CAMPO"]],
                        hovertemplate=
                            "<b>Instalacion:</b> %{customdata[0]}<br>" +
                            "<b>Tipo:</b> %{customdata[1]}<br>" +
                            "<b>Campo:</b> %{customdata[2]}<br>" +
                            "<extra></extra>",
                        legendgroup=f"inst_{tipo_inst}",
                        showlegend=True
                    ))

        centro_gis = dict(
            lat=mapa_gis["LAT"].mean(),
            lon=mapa_gis["LON"].mean()
        )
        zoom_gis = 12

        if pozo_zoom != "Todos" and "POZO" in mapa_gis.columns:
            row_zoom_gis = mapa_gis[mapa_gis["POZO"].astype(str) == str(pozo_zoom)]

            if not row_zoom_gis.empty:
                lat0 = row_zoom_gis["LAT"].iloc[0]
                lon0 = row_zoom_gis["LON"].iloc[0]
                centro_gis = dict(lat=lat0, lon=lon0)
                zoom_gis = 15

                fig_gis.add_trace(go.Scattermapbox(
                    lat=[lat0],
                    lon=[lon0],
                    mode="markers+text",
                    text=[str(pozo_zoom)],
                    textposition="top center",
                    textfont=dict(
                        size=16,
                        color="#D35400",
                        family="Arial Black"
                    ),
                    marker=dict(
                        size=18,
                        symbol="star",
                        color="#FFD700"
                    ),
                    name=f"Pozo: {pozo_zoom}",
                    hovertemplate=
                        "<b>Pozo:</b> %{text}<br>" +
                        "<extra></extra>",
                    showlegend=True
                ))

        fig_gis.update_layout(
            title=(
                "<b>Mapa GIS operativo - Campo completo</b>"
                if ver_todos_campo
                else f"<b>Mapa GIS - {yac_mapa}</b>"
            ),
            dragmode="pan",
            mapbox=dict(
                style="open-street-map",
                center=centro_gis,
                zoom=zoom_gis
            ),
            height=850,
            uirevision=mapa_uirevision,
            margin=dict(l=0, r=0, t=60, b=0),
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

        salida_mapa_burbujas.plotly_chart(
            fig_gis,
            use_container_width=True,
            config={
                "scrollZoom": True,
                "displaylogo": False
            }
        )

        mostrar_tabla_pozos_mapa(mapa)

        return

    # =====================================================
    # MAPA UTM
    # =====================================================
    fig = go.Figure()

    # =====================================================
    # HEATMAP KRIGING
    # =====================================================
    if tipo_mapa == "Heatmap":

        resultado_heatmap = crear_heatmap_kriging_burbujas(
            mapa=mapa,
            contorno=contorno,
            x_col=x_col,
            y_col=y_col,
            variable=variable,
            grid_n=180
        )

        if resultado_heatmap is None:
            return

        xi, yi, zi_masked, datos_heat, zmin, zmax, unidad = resultado_heatmap
        #xi, yi, zi_masked, datos_heat = resultado_heatmap

        nombre_variable = {
            "NP_BLS": "Aceite acumulado Np",
            "WP_BLS": "Agua acumulada Wp",
            "WINJ_BLS": "Agua inyectada acumulada Winj",
            "GP_PC": "Gas acumulado Gp",
            "ULTIMO_WC": "% Agua",
            "NP_NORM_MB": "Np normalizada"
        }.get(variable, variable)

        fig_heat = go.Figure()

        # Contorno y asignación
        try:
            contorno_h = normalizar_columnas(contorno.copy())
            asignacion_h = normalizar_columnas(asignacion.copy())

            if "ORDEN" in contorno_h.columns:
                contorno_h = contorno_h.sort_values("ORDEN")

            if "ORDEN" in asignacion_h.columns:
                asignacion_h = asignacion_h.sort_values("ORDEN")

            contorno_h["X"] = pd.to_numeric(contorno_h["X"], errors="coerce")
            contorno_h["Y"] = pd.to_numeric(contorno_h["Y"], errors="coerce")

            asignacion_h["X"] = pd.to_numeric(asignacion_h["X"], errors="coerce")
            asignacion_h["Y"] = pd.to_numeric(asignacion_h["Y"], errors="coerce")

            contorno_h = contorno_h.dropna(subset=["X", "Y"])
            asignacion_h = asignacion_h.dropna(subset=["X", "Y"])

            contorno_plot = pd.concat(
                [contorno_h, contorno_h.iloc[[0]]],
                ignore_index=True
            )

            asignacion_plot = pd.concat(
                [asignacion_h, asignacion_h.iloc[[0]]],
                ignore_index=True
            )

        except Exception:
            contorno_plot = pd.DataFrame()
            asignacion_plot = pd.DataFrame()

        # Heatmap
        fig_heat.add_trace(
            go.Contour(
                x=xi,
                y=yi,
                z=zi_masked,
                zmin=zmin,
                zmax=zmax,
                colorscale="Turbo",
                opacity=0.80,
                contours=dict(
                    coloring="heatmap",
                    showlines=False,
                    showlabels=False
                ),
                line=dict(width=0),
                colorbar=dict(
                    title=f"{nombre_variable} {unidad}"
                ),
                name=f"Heatmap {nombre_variable}",
                hovertemplate=
                    f"<b>{nombre_variable}:</b> " +
                    "%{z:,.2f} " + unidad +
                    "<extra></extra>"
            )
        )
        

        # Contorno encima
        if not contorno_plot.empty:
            fig_heat.add_trace(go.Scatter(
                x=contorno_plot["X"],
                y=contorno_plot["Y"],
                mode="lines",
                name="Campo",
                line=dict(color="black", width=3),
                hoverinfo="skip"
            ))

        if not asignacion_plot.empty:
            fig_heat.add_trace(go.Scatter(
                x=asignacion_plot["X"],
                y=asignacion_plot["Y"],
                mode="lines",
                name="Asignación",
                line=dict(color="red", width=3, dash="dash"),
                hoverinfo="skip"
            ))

        # Puntos usados para interpolar
        fig_heat.add_trace(go.Scatter(
            x=datos_heat[x_col],
            y=datos_heat[y_col],
            mode="markers+text",
            text=datos_heat["POZO"] if mostrar_nombres else None,
            textposition="top center",
            textfont=dict(
                size=10,
                color="black",
                family="Arial"
            ),
            marker=dict(
                size=8,
                color="white",
                line=dict(color="black", width=1.5)
            ),
            name="Pozos usados",
            customdata=datos_heat[["POZO", COL_YAC, "VALOR_KRIGING"]],
            #customdata=datos_heat[["POZO", COL_YAC, variable]],
            hovertemplate=
                "<b>Pozo:</b> %{customdata[0]}<br>" +
                "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                f"<b>{nombre_variable}:</b> " + "%{customdata[2]:,.2f}<br>" +
                "<extra></extra>"
        ))

        fig_heat.update_layout(
            title=f"<b>Heatmap Kriging - {nombre_variable} - {yac_mapa}</b>",
            template="plotly_white",
            height=950,
            uirevision=mapa_uirevision,
            margin=dict(l=20, r=20, t=70, b=20),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        fig_heat.update_xaxes(
            title_text="UTM X",
            showgrid=True,
            gridcolor="#EAECEE",
            showline=True,
            linewidth=1,
            linecolor="black"
        )

        fig_heat.update_yaxes(
            title_text="UTM Y",
            scaleanchor="x",
            scaleratio=1,
            showgrid=True,
            gridcolor="#EAECEE",
            showline=True,
            linewidth=1,
            linecolor="black"
        )

        if pozo_zoom != "Todos" and "POZO" in datos_heat.columns:

            row_zoom = datos_heat[datos_heat["POZO"].astype(str) == str(pozo_zoom)]

            if not row_zoom.empty:
                x0 = row_zoom[x_col].iloc[0]
                y0 = row_zoom[y_col].iloc[0]

                radio_zoom = 1000

                fig_heat.update_xaxes(range=[x0 - radio_zoom, x0 + radio_zoom])
                fig_heat.update_yaxes(range=[y0 - radio_zoom, y0 + radio_zoom])

        fig_heat.update_layout(dragmode="pan")

        salida_mapa_burbujas.plotly_chart(
            fig_heat,
            use_container_width=True,
            config={
                "scrollZoom": True,
                "displaylogo": False,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"]
            }
        )

        mostrar_tabla_pozos_mapa(mapa)

        return

    try:
        contorno = contorno.copy()
        asignacion = asignacion.copy()

        contorno = normalizar_columnas(contorno)
        asignacion = normalizar_columnas(asignacion)

        if "ORDEN" in contorno.columns:
            contorno = contorno.sort_values("ORDEN")

        if "ORDEN" in asignacion.columns:
            asignacion = asignacion.sort_values("ORDEN")

        contorno["X"] = pd.to_numeric(contorno["X"], errors="coerce")
        contorno["Y"] = pd.to_numeric(contorno["Y"], errors="coerce")

        asignacion["X"] = pd.to_numeric(asignacion["X"], errors="coerce")
        asignacion["Y"] = pd.to_numeric(asignacion["Y"], errors="coerce")

        contorno = contorno.dropna(subset=["X", "Y"])
        asignacion = asignacion.dropna(subset=["X", "Y"])

        contorno_plot = pd.concat(
            [contorno, contorno.iloc[[0]]],
            ignore_index=True
        )

        asignacion_plot = pd.concat(
            [asignacion, asignacion.iloc[[0]]],
            ignore_index=True
        )

        fig.add_trace(go.Scatter(
            x=contorno_plot["X"],
            y=contorno_plot["Y"],
            mode="lines",
            name="Campo",
            line=dict(color="black", width=3),
            hoverinfo="skip"
        ))

        fig.add_trace(go.Scatter(
            x=asignacion_plot["X"],
            y=asignacion_plot["Y"],
            mode="lines",
            name="Asignación",
            line=dict(color="red", width=3, dash="dash"),
            hoverinfo="skip"
        ))

    except Exception as e:
        st.warning(f"No se pudo graficar contorno/asignación: {e}")


    if not ver_todos_campo and not animar_tiempo and mostrar_radio_drene:

        theta = np.linspace(0, 2 * np.pi, 90)
        radios_x = []
        radios_y = []
        radios_customdata = []

        for _, row in mapa.iterrows():

            radio = row.get("RADIO DRENE")

            if (
                pd.notna(radio) and radio > 0 and
                pd.notna(row.get(x_col)) and
                pd.notna(row.get(y_col))
            ):
                x0 = row[x_col]
                y0 = row[y_col]

                radios_x.extend((x0 + radio * np.cos(theta)).tolist() + [None])
                radios_y.extend((y0 + radio * np.sin(theta)).tolist() + [None])
                radios_customdata.extend(
                    [[row.get("POZO", ""), radio]] * len(theta) + [[None, None]]
                )

        if radios_x:
            fig.add_trace(go.Scatter(
                x=radios_x,
                y=radios_y,
                mode="lines",
                line=dict(width=2, color="black", dash="dash"),
                name="Radio de drene (m)",
                legendgroup="radios",
                showlegend=False,
                customdata=radios_customdata,
                hovertemplate=
                    "<b>Pozo:</b> %{customdata[0]}<br>" +
                    "<b>Radio de drene:</b> %{customdata[1]:,.0f} m<br>" +
                    "<extra></extra>"
            ))

    if animar_tiempo and not ver_todos_campo:
        cols_anim_utm = [
            col for col in [COL_POZO, "POZO", COL_YAC, x_col, y_col]
            if col in mapa.columns
        ]
        anim_utm, fechas_anim = preparar_animacion_burbujas(
            mapa[cols_anim_utm].copy(),
            yac_mapa,
            x_col,
            y_col,
            usar_gis=False,
            ver_todos=ver_todos_campo
        )

        if anim_utm.empty or not fechas_anim:
            st.warning("No hay historia de aceite o inyección para animar con los filtros actuales.")
        else:
            fecha_ini_anim = fechas_anim[0]
            datos_ini = anim_utm[anim_utm[COL_FECHA] == fecha_ini_anim].copy()
            datos_np_ini = datos_ini[datos_ini["NP_BLS_ANIM"] > 0].copy()
            datos_iny_ini = datos_ini[datos_ini["WINJ_BLS_ANIM"] > 0].copy()

            idx_np_anim = len(fig.data)
            idx_iny_anim = idx_np_anim + 1

            fig.add_trace(go.Scatter(
                x=datos_np_ini[x_col],
                y=datos_np_ini[y_col],
                mode="markers+text" if mostrar_nombres else "markers",
                text=datos_np_ini["POZO"] if mostrar_nombres else None,
                textposition="top center",
                marker=dict(
                    size=datos_np_ini["SIZE_NP_ANIM"],
                    sizemode="diameter",
                    color="green",
                    opacity=0.35,
                    line=dict(color="green", width=1.5)
                ),
                name="Np acumulado",
                customdata=datos_np_ini[["POZO", COL_YAC, "NP_BLS_ANIM", "WINJ_BLS_ANIM", "FECHA_TXT"]],
                hovertemplate=
                    "<b>Pozo:</b> %{customdata[0]}<br>" +
                    "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                    "<b>Fecha:</b> %{customdata[4]}<br>" +
                    "<b>Np:</b> %{customdata[2]:,.0f} bls<br>" +
                    "<b>Winj:</b> %{customdata[3]:,.0f} bls<br>" +
                    "<extra></extra>"
            ))

            fig.add_trace(go.Scatter(
                x=datos_iny_ini[x_col],
                y=datos_iny_ini[y_col],
                mode="markers+text" if mostrar_etiquetas_burbujas else "markers",
                text=datos_iny_ini["ETIQUETA_INY_ANIM"] if mostrar_etiquetas_burbujas else None,
                textposition="bottom center",
                marker=dict(
                    size=datos_iny_ini["SIZE_INY_ANIM"],
                    sizemode="diameter",
                    color=datos_iny_ini["COLOR_INY_ANIM"],
                    opacity=0.70,
                    line=dict(
                        color=datos_iny_ini["BORDE_INY_ANIM"],
                        width=datos_iny_ini["ANCHO_BORDE_INY_ANIM"]
                    )
                ),
                name="Winj acumulado",
                customdata=datos_iny_ini[["POZO", COL_YAC, "NP_BLS_ANIM", "WINJ_BLS_ANIM", "FECHA_TXT", "WINJ_MES"]],
                hovertemplate=
                    "<b>Pozo:</b> %{customdata[0]}<br>" +
                    "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                    "<b>Fecha:</b> %{customdata[4]}<br>" +
                    "<b>Np:</b> %{customdata[2]:,.0f} bls<br>" +
                    "<b>Winj:</b> %{customdata[3]:,.0f} bls<br>" +
                    "<b>Inyeccion del mes:</b> %{customdata[5]:,.0f} bls<br>" +
                    "<extra></extra>"
            ))

            frames_utm = []
            steps_utm = []
            for fecha_anim in fechas_anim:
                datos_frame = anim_utm[anim_utm[COL_FECHA] == fecha_anim].copy()
                datos_np = datos_frame[datos_frame["NP_BLS_ANIM"] > 0].copy()
                datos_iny = datos_frame[datos_frame["WINJ_BLS_ANIM"] > 0].copy()
                nombre_frame = pd.to_datetime(fecha_anim).strftime("%d/%m/%Y")

                frames_utm.append(go.Frame(
                    name=nombre_frame,
                    traces=[idx_np_anim, idx_iny_anim],
                    data=[
                        go.Scatter(
                            x=datos_np[x_col],
                            y=datos_np[y_col],
                            mode="markers+text" if mostrar_nombres else "markers",
                            text=datos_np["POZO"] if mostrar_nombres else None,
                            textposition="top center",
                            marker=dict(
                                size=datos_np["SIZE_NP_ANIM"],
                                sizemode="diameter",
                                color="green",
                                opacity=0.35,
                                line=dict(color="green", width=1.5)
                            ),
                            customdata=datos_np[["POZO", COL_YAC, "NP_BLS_ANIM", "WINJ_BLS_ANIM", "FECHA_TXT"]]
                        ),
                        go.Scatter(
                            x=datos_iny[x_col],
                            y=datos_iny[y_col],
                            mode="markers+text" if mostrar_etiquetas_burbujas else "markers",
                            text=datos_iny["ETIQUETA_INY_ANIM"] if mostrar_etiquetas_burbujas else None,
                            textposition="bottom center",
                            marker=dict(
                                size=datos_iny["SIZE_INY_ANIM"],
                                sizemode="diameter",
                                color=datos_iny["COLOR_INY_ANIM"],
                                opacity=0.70,
                                line=dict(
                                    color=datos_iny["BORDE_INY_ANIM"],
                                    width=datos_iny["ANCHO_BORDE_INY_ANIM"]
                                )
                            ),
                            customdata=datos_iny[["POZO", COL_YAC, "NP_BLS_ANIM", "WINJ_BLS_ANIM", "FECHA_TXT", "WINJ_MES"]]
                        )
                    ]
                ))
                steps_utm.append(dict(
                    label=nombre_frame,
                    method="animate",
                    args=[[nombre_frame], {
                        "frame": {"duration": 0, "redraw": False},
                        "transition": {"duration": 0},
                        "mode": "immediate"
                    }]
                ))

            fig.frames = frames_utm

            if mostrar_inyectores_operando and not inyectores_operando_mapa.empty:
                fig.add_trace(go.Scatter(
                    x=inyectores_operando_mapa[x_col],
                    y=inyectores_operando_mapa[y_col],
                    mode="markers",
                    marker=dict(
                        size=22,
                        symbol="circle-open",
                        color="#0057FF",
                        line=dict(color="#0057FF", width=4)
                    ),
                    name="Inyectores operando",
                    customdata=inyectores_operando_mapa[["POZO", COL_YAC, "Operando", "VI_BLS"]],
                    hovertemplate=
                        "<b>Inyector operando:</b> %{customdata[0]}<br>" +
                        "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                        "<b>Operando:</b> %{customdata[2]}<br>" +
                        "<b>Vi:</b> %{customdata[3]:,.0f} bls<br>" +
                        "<extra></extra>",
                    legendgroup="inyectores_operando",
                    showlegend=True
                ))

            fig.update_layout(
                title=f"<b>Animación acumulada Np / Winj - {yac_mapa}</b>",
                template="plotly_white",
                height=950,
                uirevision=mapa_uirevision,
                margin=dict(l=20, r=35, t=135, b=35),
                showlegend=True,
                hovermode="closest",
                plot_bgcolor="#F8F8FF",
                paper_bgcolor="white",
                font=dict(family="Arial", size=13, color="#111827"),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=12, family="Arial", color="#111827"),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="#D1D5DB",
                    borderwidth=1
                ),
                sliders=[
                    dict(
                        active=0,
                        x=0.01,
                        y=1.04,
                        len=0.95,
                        currentvalue=dict(prefix="Fecha: "),
                        steps=steps_utm
                    )
                ]
            )

            fig.update_layout(
                xaxis=dict(
                    domain=[0.0, 1.0],
                    title_text="UTM X",
                    showgrid=True,
                    gridcolor="#EAECEE",
                    showline=True,
                    linewidth=1,
                    linecolor="black"
                ),
                yaxis=dict(
                    domain=[0.0, 1.0],
                    title_text="UTM Y",
                    scaleanchor="x",
                    scaleratio=1,
                    showgrid=True,
                    gridcolor="#EAECEE",
                    showline=True,
                    linewidth=1,
                    linecolor="black"
                )
            )

            if pozo_zoom != "Todos" and "POZO" in mapa.columns:
                row_zoom = mapa[mapa["POZO"].astype(str) == str(pozo_zoom)]
                if not row_zoom.empty:
                    x0 = row_zoom[x_col].iloc[0]
                    y0 = row_zoom[y_col].iloc[0]
                    radio_zoom = 1000
                    fig.update_layout(
                        xaxis=dict(range=[x0 - radio_zoom, x0 + radio_zoom]),
                        yaxis=dict(range=[y0 - radio_zoom, y0 + radio_zoom])
                    )

            col_mapa_anim, col_graficas_anim = salida_mapa_burbujas.columns([2.2, 1], gap="small")

            with col_mapa_anim:
                fig.update_layout(dragmode="pan")
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={
                        "scrollZoom": True,
                        "displaylogo": False,
                        "modeBarButtonsToRemove": ["lasso2d", "select2d"]
                    }
                )

            with col_graficas_anim:
                graficas_pozo_animadas_fragment(
                    pozos_disponibles_graficas_animadas(mapa)
                )

            mostrar_tabla_pozos_mapa(mapa)

            return

    if not ver_todos_campo:

        mapa_burb = mapa[mapa[variable] > 0].copy()

        if not mapa_burb.empty:

            fig.add_trace(go.Scatter(
                x=mapa_burb[x_col],
                y=mapa_burb[y_col],
                mode="markers+text" if mostrar_etiquetas_burbujas else "markers",
                text=mapa_burb["ETIQUETA_MAPA"] if mostrar_etiquetas_burbujas else None,
                textposition="top center",
                textfont=dict(
                    size=15,
                    color=color_burbuja,
                    family="Arial Black"
                ),
                marker=dict(
                    size=mapa_burb["SIZE"],
                    sizemode="diameter",
                    color=color_burbuja,
                    opacity=0.35,
                    line=dict(
                        color=color_burbuja,
                        width=1.5
                    )
                ),
                customdata=mapa_burb[
                    ["POZO", COL_YAC, "NP_BLS", "WP_BLS", "WINJ_BLS", "GP_PC", "RADIO DRENE", "MESES_OPERANDO", "NP_NORM_MB"]
                ],
                hovertemplate=
                    "<b>Pozo:</b> %{customdata[0]}<br>" +
                    "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                    "<b>Np:</b> %{customdata[2]:,.0f} bls<br>" +
                    "<b>Wp:</b> %{customdata[3]:,.0f} bls<br>" +
                    "<b>Winj:</b> %{customdata[4]:,.0f} bls<br>" +
                    "<b>Gp:</b> %{customdata[5]:,.0f} pc<br>" +
                    "<b>Radio drene:</b> %{customdata[6]:,.0f} m<br>" +
                    "<b>Meses operando:</b> %{customdata[7]:,.0f}<br>" +
                    "<b>Np normalizada:</b> %{customdata[8]:,.2f} mb/mes<br>" +
                    "<extra></extra>",
                name="Producción acumulada",
                legendgroup="burbujas",
                showlegend=True
            ))

    if (not ver_todos_campo) and variable == "NP_BLS" and "WINJ_BLS" in mapa.columns:

        mapa_iny = mapa[mapa["WINJ_BLS"].fillna(0) > 0].copy()

        if not mapa_iny.empty:

            max_iny = mapa_iny["WINJ_BLS"].max()

            if max_iny > 0:

                mapa_iny["SIZE_INY"] = 18 + (mapa_iny["WINJ_BLS"] / max_iny) * 80

                fig.add_trace(go.Scatter(
                    x=mapa_iny[x_col],
                    y=mapa_iny[y_col],
                    mode="markers+text" if mostrar_etiquetas_burbujas else "markers",
                    text=(
                        mapa_iny["WINJ_BLS"].map(lambda x: f"{x/1000:,.1f}")
                        if mostrar_etiquetas_burbujas
                        else None
                    ),
                    textposition="bottom center",
                    textfont=dict(
                        size=15,
                        color="blue",
                        family="Arial Black"
                    ),
                    marker=dict(
                        size=mapa_iny["SIZE_INY"],
                        sizemode="diameter",
                        color="rgba(0, 120, 255, 0.20)",
                        line=dict(
                            color="blue",
                            width=1
                        )
                    ),
                    customdata=mapa_iny[
                        ["POZO", COL_YAC, "WINJ_BLS", "NP_BLS", "WP_BLS", "GP_PC"]
                    ],
                    hovertemplate=
                        "<b>Pozo:</b> %{customdata[0]}<br>" +
                        "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                        "<b>Winj:</b> %{customdata[2]:,.0f} bls<br>" +
                        "<b>Np:</b> %{customdata[3]:,.0f} bls<br>" +
                        "<b>Wp:</b> %{customdata[4]:,.0f} bls<br>" +
                        "<b>Gp:</b> %{customdata[5]:,.0f} pc<br>" +
                        "<extra></extra>",
                    name="Agua inyectada acumulada",
                    legendgroup="iny",
                    showlegend=True
                ))

    if mostrar_inyectores_operando and not inyectores_operando_mapa.empty:
        fig.add_trace(go.Scatter(
            x=inyectores_operando_mapa[x_col],
            y=inyectores_operando_mapa[y_col],
            mode="markers",
            marker=dict(
                size=22,
                symbol="circle-open",
                color="#0057FF",
                line=dict(color="#0057FF", width=4)
            ),
            name="Inyectores operando",
            customdata=inyectores_operando_mapa[["POZO", COL_YAC, "Operando", "VI_BLS"]],
            hovertemplate=
                "<b>Inyector operando:</b> %{customdata[0]}<br>" +
                "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                "<b>Operando:</b> %{customdata[2]}<br>" +
                "<b>Vi:</b> %{customdata[3]:,.0f} bls<br>" +
                "<extra></extra>",
            legendgroup="inyectores_operando",
            showlegend=True
        ))

    # =====================================================
    # PUNTOS POR ESTADO / SAP
    # =====================================================
    if ver_todos_campo and variable == "SAP":

        mapa["SAP_MAPA"] = (
            mapa["SAP"]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace({
                "": "SIN SAP",
                "NAN": "SIN SAP",
                "NONE": "SIN SAP"
            })
        )

        for sap, color in leyenda_sap.items():

            tmp = mapa[mapa["SAP_MAPA"] == sap].copy()

            if tmp.empty:
                continue

            fig.add_trace(go.Scatter(
                x=tmp[x_col],
                y=tmp[y_col],
                mode="markers",
                name=sap,
                marker=dict(
                    size=8,
                    color=color,
                    line=dict(color="black", width=1)
                ),
                customdata=tmp[["POZO", "YACIMIENTO", "ESTADO", "SAP"]],
                hovertemplate=
                    "<b>Pozo:</b> %{customdata[0]}<br>" +
                    "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                    "<b>Estado:</b> %{customdata[2]}<br>" +
                    "<b>SAP:</b> %{customdata[3]}<br>" +
                    "<extra></extra>",
                legendgroup=sap,
                showlegend=True
            ))

            if mostrar_nombres:

                fig.add_trace(go.Scatter(
                    x=tmp[x_col],
                    y=tmp[y_col],
                    mode="text",
                    text=tmp["POZO"],
                    textposition="top center",
                    textfont=dict(
                        color="black",
                        size=10,
                        family="Arial"
                    ),
                    name=f"Nombres {sap}",
                    legendgroup=sap,
                    showlegend=False,
                    hoverinfo="skip"
                ))

    else:

        for estado, color in leyenda_estados.items():

            if estado not in estados_activos_mapa:
                continue

            tmp = mapa[mapa["ESTADO_MAPA"] == estado].copy()

            if tmp.empty:
                continue

            fig.add_trace(go.Scatter(
                x=tmp[x_col],
                y=tmp[y_col],
                mode="markers",
                name=estado.title(),
                marker=dict(
                    size=8 if ver_todos_campo else 7,
                    color=color,
                    line=dict(color="black", width=1)
                ),
                customdata=tmp[["POZO", COL_YAC, "ESTADO", "SAP"]],
                hovertemplate=
                    "<b>Pozo:</b> %{customdata[0]}<br>" +
                    "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                    "<b>Estado:</b> %{customdata[2]}<br>" +
                    "<b>SAP:</b> %{customdata[3]}<br>" +
                    "<extra></extra>",
                legendgroup=estado,
                showlegend=True
            ))

            if mostrar_nombres:

                fig.add_trace(go.Scatter(
                    x=tmp[x_col],
                    y=tmp[y_col],
                    mode="text",
                    text=tmp["POZO"],
                    textposition="top center",
                    textfont=dict(
                        color="black",
                        size=10 if ver_todos_campo else 12,
                        family="Arial"
                    ),
                    name=f"Nombres {estado.title()}",
                    legendgroup=estado,
                    showlegend=False,
                    hoverinfo="skip"
                ))

    if not ver_todos_campo and not muestreos_agua_mapa.empty:

        fig.add_trace(go.Scatter(
            x=muestreos_agua_mapa[x_col],
            y=muestreos_agua_mapa[y_col],
            mode="markers+text",
            text=muestreos_agua_mapa["ETIQUETA_MUESTREO"],
            textposition="bottom center",
            textfont=dict(
                size=11,
                color="#0057FF",
                family="Arial Black"
            ),
            marker=dict(
                size=muestreos_agua_mapa["SIZE_MUESTREO"],
                sizemode="diameter",
                symbol="circle",
                color="#8EDBFF",
                opacity=0.82,
                line=dict(color="#0057FF", width=2)
            ),
            name="Muestreos % Agua",
            customdata=muestreos_agua_mapa[["POZO", "TERMINACION", COL_YAC, "FECHA MUESTREO", "% AGUA LAB"]],
            hovertemplate=
                "<b>Pozo:</b> %{customdata[0]}<br>" +
                "<b>Terminación:</b> %{customdata[1]}<br>" +
                "<b>Yacimiento:</b> %{customdata[2]}<br>" +
                "<b>Fecha muestreo:</b> %{customdata[3]|%d/%m/%Y}<br>" +
                "<b>% Agua Lab:</b> %{customdata[4]:,.1f}%<br>" +
                "<extra></extra>",
            legendgroup="muestreos_agua",
            showlegend=True
        ))

    if not ver_todos_campo and not localizaciones_mapa.empty:

        for categoria, color in colores_localizaciones.items():
            tmp_loc = localizaciones_mapa[
                localizaciones_mapa["CATEGORIA"].astype(str).str.upper() == categoria
            ].copy()

            if tmp_loc.empty:
                continue

            fig.add_trace(go.Scatter(
                x=tmp_loc[x_col],
                y=tmp_loc[y_col],
                mode="markers+text" if mostrar_nombres else "markers",
                text=tmp_loc["POZO"] if mostrar_nombres else None,
                textposition="bottom center",
                marker=dict(
                    size=12,
                    symbol="diamond",
                    color=color,
                    line=dict(color="black", width=1)
                ),
                name=f"Loc {filtro_localizaciones} {categoria}",
                customdata=tmp_loc[["POZO", "TERMINACION", "YACIMIENTO", "CATEGORIA"]],
                hovertemplate=
                    "<b>Localizacion:</b> %{customdata[0]}<br>" +
                    "<b>Terminacion:</b> %{customdata[1]}<br>" +
                    "<b>Yacimiento:</b> %{customdata[2]}<br>" +
                    "<b>Categoria:</b> %{customdata[3]}<br>" +
                    "<extra></extra>",
                legendgroup=f"loc_{categoria}",
                showlegend=True
            ))

    if not ver_todos_campo and (modo_mapa == "RMA" or mostrar_perforados_term):

        if modo_mapa == "RMA":
            mapa_destacado = mapa[mapa["POZO_RMA"] == "Sí"].copy()
            nombre_destacado = "Pozos intervenidos RMA"
            color_destacado = "red"
        else:
            mapa_destacado = mapa[mapa["PERFORADO_TERM"] == "Sí"].copy()
            nombre_destacado = "Perforados TERM 2011-2020"
            color_destacado = "red"

        if not mapa_destacado.empty:

            fig.add_trace(go.Scatter(
                x=mapa_destacado[x_col],
                y=mapa_destacado[y_col],
                mode="markers",
                marker=dict(
                    size=6,
                    symbol="circle",
                    color=color_destacado,
                ),
                name=nombre_destacado,
                hovertemplate=
                    "<b>Pozo:</b> %{customdata[0]}<br>" +
                    "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                    "<extra></extra>",
                customdata=mapa_destacado[["POZO", COL_YAC]],
                showlegend=True
            ))

    if not ver_todos_campo and mostrar_radio_drene:

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
        title=(
            "<b>Mapa operativo de pozos - Campo completo</b>"
            if ver_todos_campo
            else f"<b>Tamaulipas-Constituciones - {yac_mapa}</b>"
        ),
        dragmode="pan",
        template="plotly_white",
        height=950,
        uirevision=mapa_uirevision,
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

    fig.update_xaxes(
        title_text="UTM X",
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black"
    )

    fig.update_yaxes(
        title_text="UTM Y",
        scaleanchor="x",
        scaleratio=1,
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black"
    )

    if pozo_zoom != "Todos" and "POZO" in mapa.columns:

        row_zoom = mapa[mapa["POZO"].astype(str) == str(pozo_zoom)]

        if not row_zoom.empty:
            x0 = row_zoom[x_col].iloc[0]
            y0 = row_zoom[y_col].iloc[0]

            radio_zoom = 1000

            fig.update_xaxes(range=[x0 - radio_zoom, x0 + radio_zoom])
            fig.update_yaxes(range=[y0 - radio_zoom, y0 + radio_zoom])

            fig.add_trace(go.Scatter(
                x=[x0],
                y=[y0],
                mode="markers+text",
                text=[str(pozo_zoom)],
                textposition="top center",
                textfont=dict(
                    size=16,
                    color="#D35400",
                    family="Arial Black"
                ),
                marker=dict(
                    size=18,
                    symbol="star",
                    color="#FFD700",
                    line=dict(color="black", width=2)
                ),
                name=f"Pozo: {pozo_zoom}",
                hovertemplate=
                    "<b>Pozo:</b> %{text}<br>" +
                    "<extra></extra>",
                showlegend=True
            ))

    salida_mapa_burbujas.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"]
        }
    )

    mostrar_tabla_pozos_mapa(mapa)
####Termina Mapa Burbujas


def mapa_burbujas_rma_modulo(
    rma_filtrada: pd.DataFrame,
    df_coord_base: pd.DataFrame,
    col_anio: str,
    col_yac: str,
    col_yac_rma: str,
    col_qoi: str,
    col_np_rma: str,
    col_meses_activos: str,
    rma_solo_ubicacion: pd.DataFrame | None = None,
    yac_mapa_default: str = "Todos"
):
    """Mapa exclusivo para el modulo RMA 2011-2020, sin modificar mapa_burbujas general."""
    st.markdown(
        "<div class='section-title'>Mapa de burbujas RMA 2011-2020</div>",
        unsafe_allow_html=True
    )

    if rma_filtrada.empty:
        st.warning("No hay RMA para mostrar en el mapa con los filtros seleccionados.")
        return

    coord = df_coord_base.copy()
    coord = coord.loc[:, ~coord.columns.astype(str).str.startswith("Unnamed")]
    coord = normalizar_columnas(coord)

    cols_coord_req = [COL_POZO, "CIMA X UTM", "CIMA Y UTM", "FONDO X UTM", "FONDO Y UTM"]
    faltan_coord = [c for c in cols_coord_req if c not in coord.columns]

    if faltan_coord:
        st.error(f"Faltan columnas en Coord para el mapa RMA: {faltan_coord}")
        st.write(coord.columns.tolist())
        return

    coord[COL_POZO] = coord[COL_POZO].astype(str).str.strip()

    for c in ["CIMA X UTM", "CIMA Y UTM", "FONDO X UTM", "FONDO Y UTM"]:
        coord[c] = pd.to_numeric(coord[c], errors="coerce")

    coord["X_MAPA"] = coord["CIMA X UTM"].fillna(coord["FONDO X UTM"])
    coord["Y_MAPA"] = coord["CIMA Y UTM"].fillna(coord["FONDO Y UTM"])

    cols_coord_mapa = [COL_POZO, "X_MAPA", "Y_MAPA"]
    for c in ["POZO", COL_YAC]:
        if c in coord.columns and c not in cols_coord_mapa:
            cols_coord_mapa.append(c)

    coord_mapa = (
        coord[cols_coord_mapa]
        .dropna(subset=[COL_POZO, "X_MAPA", "Y_MAPA"])
        .drop_duplicates(subset=[COL_POZO])
        .copy()
    )

    if coord_mapa.empty:
        st.warning("No hay coordenadas disponibles en Coord para construir el mapa RMA.")
        return

    rma_mapa = rma_filtrada.copy()
    rma_mapa[COL_POZO] = rma_mapa[COL_POZO].astype(str).str.strip()
    col_nombre_pozo_rma = COL_POZO_FISICO if COL_POZO_FISICO in rma_mapa.columns else COL_POZO
    rma_mapa["POZO_NOMBRE_RMA_BASE"] = rma_mapa[col_nombre_pozo_rma].astype(str).str.strip()
    rma_mapa["POZO_NOMBRE_RMA_BASE"] = rma_mapa["POZO_NOMBRE_RMA_BASE"].where(
        ~rma_mapa["POZO_NOMBRE_RMA_BASE"].str.upper().isin(["", "NAN", "NONE"]),
        rma_mapa[COL_POZO].astype(str).str.strip()
    )

    for c in [col_qoi, col_np_rma, col_meses_activos]:
        rma_mapa[c] = pd.to_numeric(rma_mapa[c], errors="coerce").fillna(0)

    if col_anio in rma_mapa.columns:
        rma_mapa[col_anio] = pd.to_numeric(rma_mapa[col_anio], errors="coerce")

    yacs_rma = (
        rma_mapa[col_yac]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
        if col_yac in rma_mapa.columns
        else []
    )
    yacs_coord = (
        coord_mapa[COL_YAC]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
        if COL_YAC in coord_mapa.columns
        else []
    )
    yacs_intervencion_mapa = (
        rma_mapa[col_yac_rma]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
        if col_yac_rma in rma_mapa.columns
        else []
    )
    yacs_mapa = sorted({
        y for y in yacs_rma + yacs_intervencion_mapa + yacs_coord
        if y and y.upper() not in ["NAN", "NONE"]
    })

    opciones_yac_mapa = ["Todos"] + yacs_mapa
    if yac_mapa_default not in opciones_yac_mapa:
        yac_mapa_default = "Todos"

    c1, c2, c3, c4 = st.columns([1.2, 1.3, 1.5, 1.3])
    key_yac_mapa_rma = "rma_mapa_yacimiento"
    st.session_state[key_yac_mapa_rma] = yac_mapa_default

    with c1:
        yac_mapa = st.selectbox(
            "Yacimiento del mapa",
            opciones_yac_mapa,
            index=opciones_yac_mapa.index(yac_mapa_default),
            key=key_yac_mapa_rma
        )

    rma_fil_mapa = rma_mapa.copy()
    coord_fil_mapa = coord_mapa.copy()

    if yac_mapa != "Todos":
        clave_yac = normalizar_clave_texto(pd.Series([yac_mapa])).iloc[0]

        if col_yac_rma in rma_fil_mapa.columns:
            rma_fil_mapa = rma_fil_mapa[
                normalizar_clave_texto(rma_fil_mapa[col_yac_rma]) == clave_yac
            ].copy()
        elif col_yac in rma_fil_mapa.columns:
            rma_fil_mapa = rma_fil_mapa[
                normalizar_clave_texto(rma_fil_mapa[col_yac]) == clave_yac
            ].copy()

        if COL_YAC in coord_fil_mapa.columns:
            coord_fil_mapa = coord_fil_mapa[
                normalizar_clave_texto(coord_fil_mapa[COL_YAC]) == clave_yac
            ].copy()

    def unir_unicos_mapa(serie):
        vals = [
            v for v in serie.dropna().astype(str).str.strip().unique()
            if v and v.upper() not in ["NAN", "NONE"]
        ]
        return ", ".join(sorted(vals))

    agregaciones = {
        "NP_RMA_MB": (col_np_rma, "sum"),
        "QOI_RMA_BPD": (col_qoi, "mean"),
        "MESES_ACTIVOS_RMA": (col_meses_activos, "sum"),
        "RMA_EVENTOS": (COL_POZO, "size"),
        "POZO_NOMBRE_RMA": ("POZO_NOMBRE_RMA_BASE", unir_unicos_mapa),
    }

    if col_yac in rma_fil_mapa.columns:
        agregaciones["YACIMIENTO_RMA_ORIGEN"] = (col_yac, unir_unicos_mapa)
    if col_yac_rma in rma_fil_mapa.columns:
        agregaciones["INTERVENCIONES_RMA"] = (col_yac_rma, unir_unicos_mapa)
    if col_anio in rma_fil_mapa.columns:
        agregaciones["ANIOS_RMA"] = (col_anio, lambda s: ", ".join(sorted(s.dropna().astype(int).astype(str).unique())))

    if rma_fil_mapa.empty:
        rma_resumen = pd.DataFrame(columns=[COL_POZO] + list(agregaciones.keys()))
    else:
        rma_resumen = (
            rma_fil_mapa
            .groupby(COL_POZO, as_index=False)
            .agg(**agregaciones)
        )

    mapa_rma = rma_resumen.merge(
        coord_mapa,
        on=COL_POZO,
        how="left",
        suffixes=("", "_COORD")
    )

    mapa_rma = mapa_rma.dropna(subset=["X_MAPA", "Y_MAPA"]).copy()
    mapa_rma["POZO_MAPA"] = mapa_rma["POZO_NOMBRE_RMA"].astype(str).str.strip()
    mapa_rma["POZO_MAPA"] = mapa_rma["POZO_MAPA"].where(
        ~mapa_rma["POZO_MAPA"].str.upper().isin(["", "NAN", "NONE"]),
        mapa_rma[COL_POZO].astype(str)
    )

    mapa_rma_ubicacion = pd.DataFrame()
    if rma_solo_ubicacion is not None and not rma_solo_ubicacion.empty:
        rma_ubic = rma_solo_ubicacion.copy()
        rma_ubic[COL_POZO] = rma_ubic[COL_POZO].astype(str).str.strip()
        col_nombre_ubic = COL_POZO_FISICO if COL_POZO_FISICO in rma_ubic.columns else COL_POZO
        rma_ubic["POZO_NOMBRE_RMA"] = rma_ubic[col_nombre_ubic].astype(str).str.strip()
        rma_ubic["POZO_NOMBRE_RMA"] = rma_ubic["POZO_NOMBRE_RMA"].where(
            ~rma_ubic["POZO_NOMBRE_RMA"].str.upper().isin(["", "NAN", "NONE"]),
            rma_ubic[COL_POZO].astype(str).str.strip()
        )

        if yac_mapa != "Todos":
            clave_yac_ubic = normalizar_clave_texto(pd.Series([yac_mapa])).iloc[0]
            if col_yac_rma in rma_ubic.columns:
                rma_ubic = rma_ubic[
                    normalizar_clave_texto(rma_ubic[col_yac_rma]) == clave_yac_ubic
                ].copy()
            elif col_yac in rma_ubic.columns:
                rma_ubic = rma_ubic[
                    normalizar_clave_texto(rma_ubic[col_yac]) == clave_yac_ubic
                ].copy()

        if not rma_ubic.empty:
            agregaciones_ubic = {
                "POZO_MAPA": ("POZO_NOMBRE_RMA", unir_unicos_mapa),
                "RMA_UBIC_EVENTOS": (COL_POZO, "size"),
            }
            if col_yac in rma_ubic.columns:
                agregaciones_ubic["YACIMIENTO_RMA_ORIGEN"] = (col_yac, unir_unicos_mapa)
            if col_yac_rma in rma_ubic.columns:
                agregaciones_ubic["INTERVENCIONES_RMA"] = (col_yac_rma, unir_unicos_mapa)

            rma_ubic_resumen = (
                rma_ubic
                .groupby(COL_POZO, as_index=False)
                .agg(**agregaciones_ubic)
            )

            mapa_rma_ubicacion = rma_ubic_resumen.merge(
                coord_mapa,
                on=COL_POZO,
                how="left",
                suffixes=("", "_COORD")
            ).dropna(subset=["X_MAPA", "Y_MAPA"]).copy()

    with c2:
        variable = st.selectbox(
            "Variable de burbuja",
            ["NP_RMA_MB", "QOI_RMA_BPD", "MESES_ACTIVOS_RMA"],
            format_func=lambda x: {
                "NP_RMA_MB": "Acumulada aceite [mb]",
                "QOI_RMA_BPD": "Gasto Inicial [bpd]",
                "MESES_ACTIVOS_RMA": "Meses activos"
            }[x],
            key="rma_mapa_variable"
        )

    with c3:
        alcance_mapa = st.selectbox(
            "Pozos intervenidos RMA",
            ["Solo RMA filtrados", "Todos los pozos del yacimiento"],
            key="rma_mapa_alcance"
        )

    if alcance_mapa == "Todos los pozos del yacimiento":
        datos_zoom_partes = [
            coord_fil_mapa.rename(columns={COL_POZO: "POZO_MAPA"})[["POZO_MAPA", "X_MAPA", "Y_MAPA"]],
            mapa_rma[["POZO_MAPA", "X_MAPA", "Y_MAPA"]]
        ]
        if not mapa_rma_ubicacion.empty:
            datos_zoom_partes.append(mapa_rma_ubicacion[["POZO_MAPA", "X_MAPA", "Y_MAPA"]])

        datos_zoom = pd.concat(
            datos_zoom_partes,
            ignore_index=True
        ).drop_duplicates(subset=["POZO_MAPA"])
    else:
        datos_zoom_partes = [mapa_rma[["POZO_MAPA", "X_MAPA", "Y_MAPA"]].copy()]
        if not mapa_rma_ubicacion.empty:
            datos_zoom_partes.append(mapa_rma_ubicacion[["POZO_MAPA", "X_MAPA", "Y_MAPA"]])
        datos_zoom = pd.concat(datos_zoom_partes, ignore_index=True).drop_duplicates(subset=["POZO_MAPA"])

    pozos_zoom = sorted(datos_zoom["POZO_MAPA"].dropna().astype(str).unique())

    with c4:
        pozo_zoom = st.selectbox(
            "Zoom a pozo",
            ["Todos"] + pozos_zoom,
            key=f"rma_mapa_zoom_{yac_mapa}_{alcance_mapa}"
        )

    if mapa_rma.empty and mapa_rma_ubicacion.empty and alcance_mapa != "Todos los pozos del yacimiento":
        st.warning("Los pozos RMA filtrados no tienen coordenadas disponibles en Coord.")
        return

    colores_variable = {
        "NP_RMA_MB": "#00A65A",
        "QOI_RMA_BPD": "#FF7F0E",
        "MESES_ACTIVOS_RMA": "#E53935"
    }

    etiquetas_variable = {
        "NP_RMA_MB": "Acumulada aceite, Np RMA (mb)",
        "QOI_RMA_BPD": "Gasto inicial, Qoi (bpd)",
        "MESES_ACTIVOS_RMA": "Meses activo"
    }

    if not mapa_rma.empty:
        mapa_rma[variable] = pd.to_numeric(mapa_rma[variable], errors="coerce").fillna(0)
        mapa_rma["VALOR_VARIABLE"] = mapa_rma[variable]
        max_val = mapa_rma[variable].max()
        mapa_rma["SIZE_BURBUJA"] = np.where(
            max_val > 0,
            18 + (mapa_rma[variable] / max_val) * 70,
            22
        )
        mapa_rma["ETIQUETA_VALOR"] = mapa_rma[variable].map(lambda x: f"{x:,.1f}")
        mapa_rma["ETIQUETA_POZO_VALOR"] = (
            mapa_rma["POZO_MAPA"].astype(str)
            + "<br>"
            + mapa_rma["ETIQUETA_VALOR"].astype(str)
        )

    fig = go.Figure()

    try:
        contorno, asignacion = load_contorno_asignacion()
        contorno = normalizar_columnas(contorno.copy())
        asignacion = normalizar_columnas(asignacion.copy())

        if "ORDEN" in contorno.columns:
            contorno = contorno.sort_values("ORDEN")
        if "ORDEN" in asignacion.columns:
            asignacion = asignacion.sort_values("ORDEN")

        for base_borde in [contorno, asignacion]:
            if "X" in base_borde.columns:
                base_borde["X"] = pd.to_numeric(base_borde["X"], errors="coerce")
            if "Y" in base_borde.columns:
                base_borde["Y"] = pd.to_numeric(base_borde["Y"], errors="coerce")

        if {"X", "Y"}.issubset(contorno.columns):
            contorno = contorno.dropna(subset=["X", "Y"])
            if not contorno.empty:
                contorno_plot = pd.concat([contorno, contorno.iloc[[0]]], ignore_index=True)
                fig.add_trace(go.Scatter(
                    x=contorno_plot["X"],
                    y=contorno_plot["Y"],
                    mode="lines",
                    name="Campo",
                    line=dict(color="black", width=3),
                    hoverinfo="skip"
                ))

        if {"X", "Y"}.issubset(asignacion.columns):
            asignacion = asignacion.dropna(subset=["X", "Y"])
            if not asignacion.empty:
                asignacion_plot = pd.concat([asignacion, asignacion.iloc[[0]]], ignore_index=True)
                fig.add_trace(go.Scatter(
                    x=asignacion_plot["X"],
                    y=asignacion_plot["Y"],
                    mode="lines",
                    name="Asignacion",
                    line=dict(color="red", width=3, dash="dash"),
                    hoverinfo="skip"
                ))

    except Exception as exc:
        st.warning(f"No se pudo graficar contorno/asignacion: {exc}")

    if alcance_mapa == "Todos los pozos del yacimiento" and not coord_fil_mapa.empty:
        coord_contexto = coord_fil_mapa.copy()
        coord_contexto["POZO_MAPA"] = coord_contexto[COL_POZO].astype(str)

        fig.add_trace(go.Scatter(
            x=coord_contexto["X_MAPA"],
            y=coord_contexto["Y_MAPA"],
            mode="markers",
            name="Todos los pozos del yacimiento",
            marker=dict(
                size=8,
                symbol="circle",
                color="rgba(120,120,120,0.35)",
                line=dict(color="rgba(80,80,80,0.8)", width=0.7)
            ),
            customdata=coord_contexto[["POZO_MAPA"]],
            hovertemplate="<b>Pozo:</b> %{customdata[0]}<extra></extra>"
        ))

    if not mapa_rma.empty:
        custom_cols = ["POZO_MAPA", "VALOR_VARIABLE", "NP_RMA_MB", "QOI_RMA_BPD", "MESES_ACTIVOS_RMA", "RMA_EVENTOS"]
        for c in ["YACIMIENTO_RMA_ORIGEN", "INTERVENCIONES_RMA", "ANIOS_RMA"]:
            if c not in mapa_rma.columns:
                mapa_rma[c] = ""
            custom_cols.append(c)

        fig.add_trace(go.Scatter(
            x=mapa_rma["X_MAPA"],
            y=mapa_rma["Y_MAPA"],
            mode="markers",
            name=f"Burbuja {etiquetas_variable[variable]}",
            marker=dict(
                size=mapa_rma["SIZE_BURBUJA"],
                symbol="circle",
                color=colores_variable.get(variable, "#1F77B4"),
                opacity=0.35,
                line=dict(color=colores_variable.get(variable, "#1F77B4"), width=1.2)
            ),
            customdata=mapa_rma[custom_cols],
            hovertemplate=(
                "<b>Pozo:</b> %{customdata[0]}<br>" +
                f"<b>{etiquetas_variable[variable]}:</b> " + "%{customdata[1]:,.2f}<br>" +
                "<b>Np RMA:</b> %{customdata[2]:,.2f} mb<br>" +
                "<b>Qoi:</b> %{customdata[3]:,.2f} bpd<br>" +
                "<b>Meses activo:</b> %{customdata[4]:,.1f}<br>" +
                "<b>Eventos RMA:</b> %{customdata[5]:,.0f}<br>" +
                "<b>Origen:</b> %{customdata[6]}<br>" +
                "<b>Intervencion:</b> %{customdata[7]}<br>" +
                "<b>Anio:</b> %{customdata[8]}<br>" +
                "<extra></extra>"
            )
        ))

        fig.add_trace(go.Scatter(
            x=mapa_rma["X_MAPA"],
            y=mapa_rma["Y_MAPA"],
            mode="markers+text",
            text=mapa_rma["ETIQUETA_POZO_VALOR"],
            textposition="bottom center",
            textfont=dict(size=10, color="#111827", family="Arial Black"),
            name="Pozo RMA",
            marker=dict(
                size=6,
                symbol="square",
                color="red",
                opacity=1,
                line=dict(color="black", width=2)
            ),
            customdata=mapa_rma[custom_cols],
            hovertemplate=(
                "<b>Pozo:</b> %{customdata[0]}<br>" +
                f"<b>{etiquetas_variable[variable]}:</b> " + "%{customdata[1]:,.2f}<br>" +
                "<b>Np RMA:</b> %{customdata[2]:,.2f} mb<br>" +
                "<b>Qoi:</b> %{customdata[3]:,.2f} bpd<br>" +
                "<b>Meses activo:</b> %{customdata[4]:,.1f}<br>" +
                "<b>Intervencion:</b> %{customdata[7]}<br>" +
                "<extra></extra>"
            )
        ))

    if not mapa_rma_ubicacion.empty:
        for col_tmp in ["YACIMIENTO_RMA_ORIGEN", "INTERVENCIONES_RMA"]:
            if col_tmp not in mapa_rma_ubicacion.columns:
                mapa_rma_ubicacion[col_tmp] = ""

        fig.add_trace(go.Scatter(
            x=mapa_rma_ubicacion["X_MAPA"],
            y=mapa_rma_ubicacion["Y_MAPA"],
            mode="markers+text",
            text=mapa_rma_ubicacion["POZO_MAPA"],
            textposition="top center",
            textfont=dict(size=10, color="#111827", family="Arial Black"),
            name="RMA solo ubicacion",
            marker=dict(
                size=12,
                symbol="star",
                color="#FFD700",
                line=dict(color="black", width=1)
            ),
            customdata=mapa_rma_ubicacion[
                ["POZO_MAPA", "YACIMIENTO_RMA_ORIGEN", "INTERVENCIONES_RMA", "RMA_UBIC_EVENTOS"]
            ],
            hovertemplate=(
                "<b>Pozo:</b> %{customdata[0]}<br>" +
                "<b>Origen:</b> %{customdata[1]}<br>" +
                "<b>Intervencion:</b> %{customdata[2]}<br>" +
                "<b>Eventos RMA sin datos:</b> %{customdata[3]:,.0f}<br>" +
                "<extra></extra>"
            )
        ))

    fig.update_layout(
        title=f"<b>Mapa RMA 2011-2020 - {yac_mapa}</b>",
        dragmode="pan",
        template="plotly_white",
        height=1350,
        margin=dict(l=20, r=20, t=70, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig.update_xaxes(
        title_text="UTM X",
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black"
    )

    fig.update_yaxes(
        title_text="UTM Y",
        scaleanchor="x",
        scaleratio=1,
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black"
    )

    if pozo_zoom != "Todos":
        row_zoom = datos_zoom[datos_zoom["POZO_MAPA"].astype(str) == str(pozo_zoom)]
        if not row_zoom.empty:
            x0 = row_zoom["X_MAPA"].iloc[0]
            y0 = row_zoom["Y_MAPA"].iloc[0]
            radio_zoom = 1000
            fig.update_xaxes(range=[x0 - radio_zoom, x0 + radio_zoom])
            fig.update_yaxes(range=[y0 - radio_zoom, y0 + radio_zoom])

            fig.add_trace(go.Scatter(
                x=[x0],
                y=[y0],
                mode="markers+text",
                text=[str(pozo_zoom)],
                textposition="top center",
                marker=dict(
                    size=18,
                    symbol="star",
                    color="#FFD700",
                    line=dict(color="black", width=2)
                ),
                name=f"Zoom: {pozo_zoom}",
                hovertemplate="<b>Pozo:</b> %{text}<extra></extra>"
            ))

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"]
        }
    )

    if not mapa_rma.empty:
        tabla_cols = [
            "POZO_MAPA",
            "YACIMIENTO_RMA_ORIGEN",
            "INTERVENCIONES_RMA",
            "ANIOS_RMA",
            "NP_RMA_MB",
            "QOI_RMA_BPD",
            "MESES_ACTIVOS_RMA",
            "RMA_EVENTOS"
        ]
        st.markdown("<div class='section-title'>Pozos RMA mostrados en el mapa</div>", unsafe_allow_html=True)
        st.dataframe(
            mapa_rma[[c for c in tabla_cols if c in mapa_rma.columns]]
            .rename(columns={
                "POZO_MAPA": "Pozo / Terminacion",
                "YACIMIENTO_RMA_ORIGEN": "Origen",
                "INTERVENCIONES_RMA": "Intervencion",
                "ANIOS_RMA": "Anio",
                "NP_RMA_MB": "Np RMA (mb)",
                "QOI_RMA_BPD": "Qoi (bpd)",
                "MESES_ACTIVOS_RMA": "Meses activo",
                "RMA_EVENTOS": "Eventos RMA"
            }),
            use_container_width=True,
            height=320
        )


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

        pozos_sel = st.multiselect(
            "Pozo / Terminación",
            pozos,
            default=pozos,
            key="term_pozos_sel"
    )

    if pozos_sel:
        term_f = term_f[term_f[COL_POZO].astype(str).isin(pozos_sel)].copy()

    if term_f.empty:
        st.warning("No hay datos con los filtros seleccionados.")
        return


    # =========================
    # MÉTRICAS
    # =========================

    # Qoi válidos
    qoi_validos = pd.to_numeric(
        term_f[col_qoi],
        errors="coerce"
    )

    qoi_exitosos = qoi_validos[qoi_validos > 0]

    p50_qoi = (
        np.nanpercentile(qoi_exitosos, 50)
        if len(qoi_exitosos) > 0
        else 0
    )

    pozos_sin_exito = (
        term_f[qoi_validos.fillna(0) <= 0][COL_POZO]
        .nunique()
    )

    # Calcular Np total para los pozos filtrados en TERM
    df_prod_kpi = load_prod_calc().copy()
    #df_prod_kpi = calcular_columnas_produccion(df.copy())

    poz_term_f = term_f[COL_POZO].dropna().astype(str).unique().tolist()

    np_kpi = (
        df_prod_kpi[
            df_prod_kpi[COL_POZO].astype(str).isin(poz_term_f)
        ]
        .sort_values([COL_POZO, COL_FECHA])
        .groupby(COL_POZO, as_index=False)
        .agg(NP_FINAL=(COL_NP, "last"))
    )

    np_validos = pd.to_numeric(
        np_kpi["NP_FINAL"],
        errors="coerce"
    )

    np_exitosos = np_validos[np_validos > 0]

    p50_np = (
        np.nanpercentile(np_exitosos, 50)
        if len(np_exitosos) > 0
        else 0
    )

    pozos_totales = term_f[COL_POZO].nunique()

    fracaso_pct = (
        100 * pozos_sin_exito / pozos_totales
        if pozos_totales > 0
        else 0
    )

    # =========================
    # KPI CARDS
    # =========================

    st.markdown("""
    <div style="
    background-color:#F8F9FA;
    border:1px solid #D6DBDF;
    border-radius:10px;
    padding:12px;
    "
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        kpi_card(
            "Pozos terminados",
            f"{pozos_totales:,.0f}",
            "",
            #"#1F2937"
            "#1F77B4"
        )

    with m2:
        kpi_card(
            "Qoi promedio",
            f"{qoi_validos.mean():,.1f}",
            "bpd",
            #"#1F2937"
            "#1F77B4"
        )

    with m3:
        kpi_card(
            "P50 Qoi",
            f"{p50_qoi:,.1f}",
            "bpd",
            #"#1F2937"
            "#1F77B4"
        )

    with m4:
        kpi_card(
            "P50 Np",
            f"{p50_np:,.1f}",
            "mbl",
            #"#1F2937"
            "#1F77B4"
        )

    with m5:
        kpi_card(
            "Sin Éxito",
            f"{fracaso_pct:.1f}",
            f"% | {pozos_sin_exito} pozos",
            #"#B91C1C"
            "#1F77B4"
        )

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

    #fig1.add_trace(go.Bar(
    #    x=term_f["POZO_CAMP"],
    #    #x=term_f[COL_POZO],
    #    y=term_f[col_qoi_prog],
    #    name="Qo programa (bpd)",
    #    marker=dict(
    #        color="#1F4E79",
    #        line=dict(color="#0B1F33", width=1.5)
    #    ),
    #    opacity=0.88,
    #    text=term_f[col_qoi_prog].round(1),
    #    textposition="outside"
    #))

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
        height=600,
        title="<b>Qoi por pozo (bpd)</b>",
        xaxis=dict(
        tickangle=-75,
        categoryorder="array",
        categoryarray=term_f["POZO_CAMP"]
        ),
        xaxis_title="Terminación",
        yaxis_title="Qoi (bpd)",
        barmode="group",
        #height=560,
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
        #dtick=1,
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
        # =========================
        # 3. BOXPLOT QOI POR CAMPAÑA + TOTAL
        # =========================

        term_qoi_box = term_f.copy()

        term_qoi_box[col_qoi] = pd.to_numeric(
            term_qoi_box[col_qoi],
            errors="coerce"
        )

        term_qoi_box = term_qoi_box[
            term_qoi_box[col_qoi].notna() &
            (term_qoi_box[col_qoi] > 0)
        ].copy()

        term_qoi_box["ANIO_BOX"] = term_qoi_box[col_anio].astype(int).astype(str)

        term_qoi_total = term_qoi_box.copy()
        term_qoi_total["ANIO_BOX"] = "TOTAL"

        term_qoi_box = pd.concat(
            [term_qoi_box, term_qoi_total],
            ignore_index=True
        )

        orden_box_qoi = (
            sorted(
                term_qoi_box.loc[
                    term_qoi_box["ANIO_BOX"] != "TOTAL",
                    "ANIO_BOX"
                ].dropna().astype(str).unique().tolist()
            )
            + ["TOTAL"]
        )

        fig3 = px.box(
            term_qoi_box,
            x="ANIO_BOX",
            y=col_qoi,
            points="all",
            hover_name=COL_POZO,
            title="<b>Modelo estadístico Qoi por campaña</b>",
            template="plotly_white",
            category_orders={
                "ANIO_BOX": orden_box_qoi
            }
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

        #medianas = term_f.groupby(col_anio, as_index=False)[col_qoi].median()
        medianas = term_qoi_box.groupby("ANIO_BOX", as_index=False)[col_qoi].median()

        fig3.add_trace(go.Scatter(
            x=medianas["ANIO_BOX"],
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
    #df_prod_term = calcular_columnas_produccion(df.copy())
    df_prod_term = prod = load_prod_calc().copy()

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

        # =====================================================
    # POZOS ADICIONALES DESDE TABLA_PROD PARA SCATTER NP
    # =====================================================

    # Pozos de producción filtrados por el yacimiento seleccionado en TERM
    df_prod_yac_extra = df_prod_term.copy()

    if yac_sel:
        df_prod_yac_extra = df_prod_yac_extra[
            df_prod_yac_extra[COL_YAC].astype(str).isin(yac_sel)
        ].copy()

    pozos_term_actuales = term_f[COL_POZO].dropna().astype(str).unique().tolist()

    pozos_prod_extra = sorted(
        df_prod_yac_extra[COL_POZO]
        .dropna()
        .astype(str)
        .unique()
    )

    pozos_extra_sel = st.multiselect(
        "Agregar pozos adicionales desde producción",
        options=[p for p in pozos_prod_extra if p not in pozos_term_actuales],
        default=[],
        key="pozos_extra_np_scatter_term"
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

        # Pozos TERM + pozos adicionales seleccionados desde producción
        pozos_term_np = term_np[COL_POZO].dropna().astype(str).unique().tolist()

        pozos_scatter_np = list(
            dict.fromkeys(
                pozos_term_np + pozos_extra_sel
            )
        )

        df_scatter_np = df_prod_np[
            df_prod_np[COL_POZO].astype(str).isin(pozos_scatter_np)
        ].copy()


        #################
        # Agregar año/campaña para pozos TERM
        df_scatter_np = df_scatter_np.merge(
            term_np[[COL_POZO, col_anio]].drop_duplicates(),
            on=COL_POZO,
            how="left"
        )

        # Los pozos adicionales no tienen campaña TERM
        df_scatter_np[col_anio] = df_scatter_np[col_anio].fillna("Extra PROD")

        df_scatter_np["TIPO_POZO"] = np.where(
        df_scatter_np[col_anio] == "Extra PROD",
        "Extra PROD",
        "TERM"
        )

        df_scatter_np["POZO_LEYENDA"] = np.where(
            df_scatter_np[col_anio].astype(str) == "Extra PROD",
            df_scatter_np[COL_POZO].astype(str) + " | Extra PROD",
            df_scatter_np[COL_POZO].astype(str) + " | " + df_scatter_np[col_anio].astype(str)
        )

        fig4 = px.scatter(
            df_scatter_np,
            x="MES_PROD_TERM",
            y=COL_NP,
            color="TIPO_POZO",
            symbol=COL_POZO,
            hover_name=COL_POZO,
            hover_data={
                col_anio: True,
                "MES_PROD_TERM": True,
                COL_NP: ":,.1f"
            },
            color_discrete_map={
                "TERM": "#1F77B4",       # azul
                "Extra PROD": "#808080" # gris
            },
            title=f"<b>Comportamiento de {nombre_np} por tiempo de producción</b>",
            template="plotly_white"
        )   

        for trace in fig4.data:

            if "Extra PROD" in trace.name:

                trace.line.color = "gray"
                trace.marker.color = "gray"

            else:

                trace.line.width = 2

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

    #Aqui debo corregir las terminaciones
    resumen_np = term_np.groupby(col_anio, as_index=False).agg(
        NP_PROM=("NP_FINAL", "mean"),
        POZOS=(COL_POZO, "nunique")
    )

    fig5 = go.Figure()

    # =========================
    # 5. BOXPLOT NP RMA ERROR
    # =========================

    #medianas_np = term_np.groupby("ANIO_BOX", as_index=False)["NP_FINAL"].median()
    medianas_np = term_np.groupby(col_anio, as_index=False)["NP_FINAL"].median()

    resumen_np = term_np.groupby(col_anio, as_index=False).agg(
    NP_PROM=("NP_FINAL", "mean"),
    POZOS=(COL_POZO, "nunique")
    )

    # =========================
    # 4.2 MEJOR DISTRIBUCIÓN AJUSTADA NP - TODOS LOS POZOS
    # =========================

    term_np_dist = term_np.copy()

    term_np_dist["NP_FINAL"] = pd.to_numeric(
        term_np_dist["NP_FINAL"],
        errors="coerce"
    )

    term_np_dist = term_np_dist[
        term_np_dist["NP_FINAL"].notna() &
        (term_np_dist["NP_FINAL"] > 0)
    ].copy()

    datos = term_np_dist["NP_FINAL"].dropna().values.astype(float)

    fig5 = go.Figure()

    if len(datos) >= 3:

        try:
            from scipy import stats

            distribuciones = {
                "Normal": stats.norm,
                "Lognormal": stats.lognorm,
                "Gamma": stats.gamma,
                "Weibull": stats.weibull_min,
                "Exponencial": stats.expon
            }

            resultados = []

            for nombre, dist in distribuciones.items():

                try:
                    # Para distribuciones positivas se fija loc=0
                    if nombre in ["Lognormal", "Gamma", "Weibull", "Exponencial"]:
                        params = dist.fit(datos, floc=0)
                    else:
                        params = dist.fit(datos)

                    pdf_vals = dist.pdf(datos, *params)
                    pdf_vals = np.where(pdf_vals <= 0, 1e-12, pdf_vals)

                    log_likelihood = np.sum(np.log(pdf_vals))
                    k = len(params)
                    n = len(datos)

                    aic = 2 * k - 2 * log_likelihood
                    bic = k * np.log(n) - 2 * log_likelihood

                    ks_stat, ks_pvalue = stats.kstest(
                        datos,
                        dist.cdf,
                        args=params
                    )

                    resultados.append({
                        "Distribución": nombre,
                        "Dist": dist,
                        "Params": params,
                        "AIC": aic,
                        "BIC": bic,
                        "KS": ks_stat,
                        "PValue": ks_pvalue
                    })

                except Exception:
                    continue

            if len(resultados) == 0:
                raise ValueError("No se pudo ajustar ninguna distribución.")

            resultados_df = pd.DataFrame(resultados).sort_values("AIC")
            mejor = resultados_df.iloc[0]

            mejor_nombre = mejor["Distribución"]
            mejor_dist = mejor["Dist"]
            mejor_params = mejor["Params"]

            # Histograma normalizado
            fig5.add_trace(go.Histogram(
                x=datos,
                histnorm="probability density",
                nbinsx=15,
                name="Datos observados",
                opacity=0.55,
                marker=dict(
                    color="#F4B183",
                    line=dict(color="black", width=1)
                )
            ))

            # Curva de mejor ajuste
            x_grid = np.linspace(
                datos.min() * 0.90,
                datos.max() * 1.10,
                400
            )

            x_grid = x_grid[x_grid > 0]

            y_fit = mejor_dist.pdf(x_grid, *mejor_params)

            fig5.add_trace(go.Scatter(
                x=x_grid,
                y=y_fit,
                mode="lines",
                name=f"Mejor ajuste: {mejor_nombre}",
                line=dict(
                    color="#C55A11",
                    width=4
                )
            ))

            # Estadísticos
            p10 = np.percentile(datos, 10)
            p50 = np.percentile(datos, 50)
            p90 = np.percentile(datos, 90)
            media = np.mean(datos)

            for valor, nombre_linea, color_linea in [
                (p10, "P10", "#1F77B4"),
                (p50, "P50", "#000000"),
                (p90, "P90", "#2CA02C"),
                #(media, "Media", "#D62728")
            ]:
                fig5.add_vline(
                    x=valor,
                    line_width=2,
                    line_dash="dash",
                    line_color=color_linea,
                    annotation_text=f"{nombre_linea}: {valor:,.1f}",
                    annotation_position="top"
                )

            fig5.update_layout(
                title=(
                    f"<b>Mejor distribución ajustada de {nombre_np}</b><br>"
                    f"<sup>Distribución seleccionada: {mejor_nombre} | "
                    f"AIC: {mejor['AIC']:.1f} | KS: {mejor['KS']:.3f}</sup>"
                ),
                height=520,
                template="plotly_white",
                xaxis_title=f"{nombre_np}",
                yaxis_title="Densidad probabilística",
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.05,
                    xanchor="center",
                    x=0.5
                ),
                font=dict(
                    size=14,
                    color="black",
                    family="Arial Black"
                ),
                plot_bgcolor="white",
                paper_bgcolor="white",
                bargap=0.05
            )

        except Exception as e:

            st.warning(f"No se pudo ajustar la distribución: {e}")

            fig5.add_trace(go.Histogram(
                x=datos,
                nbinsx=15,
                name="Datos observados",
                marker=dict(
                    color="#F4B183",
                    line=dict(color="black", width=1)
                )
            ))

            fig5.update_layout(
                title=f"<b>Histograma de {nombre_np}</b>",
                height=520,
                template="plotly_white",
                xaxis_title=f"{nombre_np}",
                yaxis_title="Frecuencia de pozos",
                font=dict(
                    size=14,
                    color="black",
                    family="Arial Black"
                ),
                plot_bgcolor="white",
                paper_bgcolor="white"
            )

    else:

        fig5.add_annotation(
            text="No hay suficientes datos para ajustar una distribución.",
            x=0.5,
            y=0.5,
            showarrow=False,
            xref="paper",
            yref="paper",
            font=dict(size=16, color="black")
        )

        fig5.update_layout(
            title=f"<b>Distribución de {nombre_np}</b>",
            height=520,
            template="plotly_white"
        )

    fig5.update_xaxes(
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

    # =====================================================
    # AGREGAR POZOS EXTRA PROD SOLO AL BOXPLOT / VIOLIN NP
    # =====================================================
    extra_np_box = np_pozo[
        np_pozo[COL_POZO].astype(str).isin(pozos_extra_sel)
    ].copy()

    extra_np_box[col_anio] = "Extra PROD"
    extra_np_box[col_qoi] = np.nan

    extra_np_box = extra_np_box.rename(
        columns={
            "NP_FINAL": "NP_FINAL"
        }
    )

    # Base original: campañas + pozos extra
    term_np_box = pd.concat(
        [
            term_np[[COL_POZO, col_anio, "NP_FINAL"]],
            extra_np_box[[COL_POZO, col_anio, "NP_FINAL"]]
        ],
        ignore_index=True
    )

    term_np_box["NP_FINAL"] = pd.to_numeric(
        term_np_box["NP_FINAL"],
        errors="coerce"
    )

    term_np_box = term_np_box[
        term_np_box["NP_FINAL"].notna() &
        (term_np_box["NP_FINAL"] > 0)
    ].copy()

    # Convertir año a texto
    term_np_box["ANIO_BOX"] = term_np_box[col_anio].astype(str)

    # Crear TOTAL con todas las muestras filtradas
    term_np_total = term_np_box.copy()
    term_np_total["ANIO_BOX"] = "TOTAL"

    # Unir campañas + TOTAL
    term_np_box = pd.concat(
        [term_np_box, term_np_total],
        ignore_index=True
    )

    orden_box_np = (
        sorted(
            term_np_box.loc[
                term_np_box["ANIO_BOX"] != "TOTAL",
                "ANIO_BOX"
            ].dropna().astype(str).unique().tolist()
        )
        + ["TOTAL"]
    )

    fig6 = px.box(
        term_np_box,
        x="ANIO_BOX",
        y="NP_FINAL",
        points="all",
        hover_name=COL_POZO,
        title="<b>Modelo estadístico Np por campaña / total filtrado</b>",
        template="plotly_white",
        category_orders={
            "ANIO_BOX": orden_box_np
        }
    )

    promedios_np = (
        term_np_box
        .groupby("ANIO_BOX", as_index=False)["NP_FINAL"]
        .mean()
    )

    fig6.add_trace(
        go.Scatter(
        x=promedios_np["ANIO_BOX"],
        y=promedios_np["NP_FINAL"],
        mode="markers+text",
        text=promedios_np["NP_FINAL"].round(1),
        textposition="top center",
        textfont=dict(
            size=10,
            color="blue"
        ),
        marker=dict(
            symbol="square",
            size=8,
            color="blue",
            line=dict(color="black", width=1)
        ),
        name="Promedio",
        )
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

    #medianas_np = term_np.groupby(col_anio, as_index=False)["NP_FINAL"].median()
    medianas_np = term_np_box.groupby("ANIO_BOX", as_index=False)["NP_FINAL"].median()

    fig6.add_trace(go.Scatter(
        x=medianas_np["ANIO_BOX"],
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

@st.cache_data(show_spinner="Calculando producción total del campo...")
def preparar_resumen_campo(df_base: pd.DataFrame):

    prod = calcular_columnas_produccion(df_base.copy())
    prod = prod.sort_values([COL_FECHA, COL_YAC, COL_POZO]).copy()

    prod["POZO_ACTIVO"] = np.where(
        (prod[COL_QO] > 0) | (prod[COL_QW] > 0) | (prod[COL_QG] > 0),
        1,
        0
    )

    # =========================
    # TOTAL CAMPO
    # =========================
    total = (
        prod.groupby(COL_FECHA, as_index=False)
        .agg(
            QO_TOTAL=(COL_QO, "sum"),
            QW_TOTAL=(COL_QW, "sum"),
            QIN_TOTAL=(COL_QIN, "sum"),
            QG_TOTAL=(COL_QG, "sum"),
            QG_PCD_TOTAL=(COL_QG_PCD, "sum"),
            ACEITE_BBL=(COL_ACEITE_BBL, "sum"),
            AGUA_BBL=(COL_AGUA_BBL, "sum"),
            GAS_PC=(COL_GAS_PC, "sum"),
            POZOS_ACTIVOS=(COL_POZO, lambda x: x[prod.loc[x.index, "POZO_ACTIVO"] == 1].nunique())
        )
        .sort_values(COL_FECHA)
    )

    total["RGA_TOTAL"] = np.where(
        total["QO_TOTAL"] > 0,
        total["QG_PCD_TOTAL"] / total["QO_TOTAL"],
        0
    )

    total["WC_TOTAL"] = np.where(
        (total["QO_TOTAL"] + total["QW_TOTAL"]) > 0,
        total["QW_TOTAL"] / (total["QO_TOTAL"] + total["QW_TOTAL"]) * 100,
        0
    )

    total["NP_TOTAL"] = total["ACEITE_BBL"].cumsum() / 1000
    total["WP_TOTAL"] = total["AGUA_BBL"].cumsum() / 1000
    total["GP_TOTAL"] = total["GAS_PC"].cumsum() / 1_000_000

    # =========================
    # POR YACIMIENTO
    # =========================
    yac = (
        prod.groupby([COL_FECHA, COL_YAC], as_index=False)
        .agg(
            QO_TOTAL=(COL_QO, "sum"),
            QW_TOTAL=(COL_QW, "sum"),
            QIN_TOTAL=(COL_QIN, "sum"),
            QG_TOTAL=(COL_QG, "sum"),
            QG_PCD_TOTAL=(COL_QG_PCD, "sum"),
            ACEITE_BBL=(COL_ACEITE_BBL, "sum"),
            AGUA_BBL=(COL_AGUA_BBL, "sum"),
            GAS_PC=(COL_GAS_PC, "sum"),
            POZOS_ACTIVOS=(COL_POZO, lambda x: x[prod.loc[x.index, "POZO_ACTIVO"] == 1].nunique())
        )
        .sort_values([COL_YAC, COL_FECHA])
    )

    yac["RGA_TOTAL"] = np.where(
        yac["QO_TOTAL"] > 0,
        yac["QG_PCD_TOTAL"] / yac["QO_TOTAL"],
        0
    )

    yac["WC_TOTAL"] = np.where(
        (yac["QO_TOTAL"] + yac["QW_TOTAL"]) > 0,
        yac["QW_TOTAL"] / (yac["QO_TOTAL"] + yac["QW_TOTAL"]) * 100,
        0
    )

    yac["NP_TOTAL"] = yac.groupby(COL_YAC)["ACEITE_BBL"].cumsum() / 1000
    yac["WP_TOTAL"] = yac.groupby(COL_YAC)["AGUA_BBL"].cumsum() / 1000
    yac["GP_TOTAL"] = yac.groupby(COL_YAC)["GAS_PC"].cumsum() / 1_000_000

    return total, yac

def produccion_total_campo():

    st.markdown(
        "<div class='section-title'>Producción total del campo / por yacimiento</div>",
        unsafe_allow_html=True
    )

    # Cálculo pesado cacheado
    total_all, yac_all = preparar_resumen_campo(df)

    # =========================
    # FILTRO YACIMIENTO
    # =========================
    yacs_disponibles = sorted(
        yac_all[COL_YAC].dropna().astype(str).unique()
    )

    yacs_sel = st.multiselect(
        "Yacimientos",
        yacs_disponibles,
        default=yacs_disponibles,
        key="filtro_yac_prod_total"
    )

    yac = yac_all.copy()

    if yacs_sel:
        yac = yac[
            yac[COL_YAC].astype(str).isin(yacs_sel)
        ].copy()

    if yac.empty:
        st.warning("No hay datos para los yacimientos seleccionados.")
        return

    # Recalcular total campo con los yacimientos seleccionados
    total = (
        yac.groupby(COL_FECHA, as_index=False)
        .agg(
            QO_TOTAL=("QO_TOTAL", "sum"),
            QW_TOTAL=("QW_TOTAL", "sum"),
            QIN_TOTAL=("QIN_TOTAL", "sum"),
            QG_TOTAL=("QG_TOTAL", "sum"),
            QG_PCD_TOTAL=("QG_PCD_TOTAL", "sum"),
            ACEITE_BBL=("ACEITE_BBL", "sum"),
            AGUA_BBL=("AGUA_BBL", "sum"),
            GAS_PC=("GAS_PC", "sum"),
            POZOS_ACTIVOS=("POZOS_ACTIVOS", "sum")
        )
        .sort_values(COL_FECHA)
    )

    total["RGA_TOTAL"] = np.where(
        total["QO_TOTAL"] > 0,
        total["QG_PCD_TOTAL"] / total["QO_TOTAL"],
        0
    )

    total["WC_TOTAL"] = np.where(
        (total["QO_TOTAL"] + total["QW_TOTAL"]) > 0,
        total["QW_TOTAL"] / (total["QO_TOTAL"] + total["QW_TOTAL"]) * 100,
        0
    )

    total["NP_TOTAL"] = total["ACEITE_BBL"].cumsum() / 1000
    total["WP_TOTAL"] = total["AGUA_BBL"].cumsum() / 1000
    total["GP_TOTAL"] = total["GAS_PC"].cumsum() / 1_000_000

    # =========================
    # KPI CARDS PRODUCCIÓN CAMPO
    # =========================

    total_kpi = total.sort_values(COL_FECHA).copy()

    # Último registro con producción real
    prod_total_kpi = (
        total_kpi["QO_TOTAL"].fillna(0) +
        total_kpi["QW_TOTAL"].fillna(0) +
        total_kpi["QG_TOTAL"].fillna(0)
    )

    total_kpi_prod = total_kpi[prod_total_kpi > 0].copy()

    if total_kpi_prod.empty:
        total_kpi_prod = total_kpi.copy()

    last_campo = total_kpi_prod.iloc[-1]

    st.markdown("""
    <div style="
    background-color:#F8F9FA;
    border:1px solid #D6DBDF;
    border-radius:10px;
    </div>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4, k5, k6, k7, k8, k9 = st.columns(9)

    with k1:
        kpi_card("Producción Aceite", f"{last_campo['QO_TOTAL']:,.1f}", "bpd", "#1F77B4")

    with k2:
        kpi_card("Producción Agua", f"{last_campo['QW_TOTAL']:,.1f}", "bpd", "#1F77B4")

    with k3:
        kpi_card("Producción Gas", f"{last_campo['QG_TOTAL']/1000:,.2f}", "mmpcd", "#1F77B4")

    with k4:
        kpi_card("Pozos Activos", f"{last_campo['POZOS_ACTIVOS']:,.0f}", "", "#1F77B4")

    with k5:
        kpi_card("RGA Actual", f"{last_campo['RGA_TOTAL']:,.0f}", "pc/bl", "#1F77B4")

    with k6:
        kpi_card("% Agua Actual", f"{last_campo['WC_TOTAL']:,.1f}", "%", "#1F77B4")

    with k7:
        kpi_card("Acumulada Aceite", f"{last_campo['NP_TOTAL']/1000:,.2f}", "mmb", "#1F77B4")

    with k8:
        kpi_card("Acumulada Agua", f"{last_campo['WP_TOTAL']/1000:,.2f}", "mmb", "#1F77B4")

    with k9:
        kpi_card("Acumulada Gas", f"{last_campo['GP_TOTAL']/1000:,.2f}", "mmmpc", "#1F77B4")

    fecha_min_graficas = total[COL_FECHA].min()
    fecha_max_graficas = total[COL_FECHA].max()

    # =========================
    # GRÁFICO 1: Qo, Qw, Qg y pozos activos
    # =========================
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])

    fig1.add_trace(go.Scatter(
        x=total[COL_FECHA],
        y=total["QO_TOTAL"],
        mode="lines",
        name="Qo total",
        line=dict(color="#00A65A", width=3)
    ), secondary_y=False)

    fig1.add_trace(go.Scatter(
        x=total[COL_FECHA],
        y=total["QW_TOTAL"],
        mode="lines",
        name="Qw total",
        line=dict(color="#1E88E5", width=3)
    ), secondary_y=False)

    fig1.add_trace(go.Scatter(
        x=total[COL_FECHA],
        y=total["QG_TOTAL"],
        mode="lines",
        name="Qg total",
        line=dict(color="#E53935", width=3)
    ), secondary_y=False)

    fig1.add_trace(go.Bar(
        x=total[COL_FECHA],
        y=total["POZOS_ACTIVOS"],
        name="Pozos activos",
        marker=dict(color="rgba(0,0,0,0.35)"),
        opacity=0.45
    ), secondary_y=True)

    fig1.update_layout(
        title="<b>Producción de aceite, agua, gas y pozos activos</b>",
        template="plotly_white",
        #height=alto_grafico,
        height=600,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            font=dict(size=13, color="black", family="Arial Black")
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Arial"
        ),
        font=dict(size=14, color="black", family="Arial Black"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig1.update_xaxes(
        title_text="Fecha",
        tickformat="%d/%m/%Y",
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black",
        range=[fecha_min_graficas, fecha_max_graficas]
    )

    fig1.update_yaxes(
        title_text="Qo / Qw (bpd) y Qg (mpcd)",
        secondary_y=False,
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black"
    )

    fig1.update_yaxes(
        title_text="Pozos activos",
        secondary_y=True,
        showgrid=False
    )

    #st.plotly_chart(fig1, use_container_width=True)

    # =========================
    # GRÁFICO 2: RGA y % Agua
    # =========================
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

    fig2.add_trace(go.Scatter(
        x=total[COL_FECHA],
        y=total["RGA_TOTAL"],
        mode="lines",
        name="RGA total",
        line=dict(color="#E53935", width=3)
    ), secondary_y=False)

    fig2.add_trace(go.Scatter(
        x=total[COL_FECHA],
        y=total["WC_TOTAL"],
        mode="lines",
        name="% Agua total",
        line=dict(color="#1E88E5", width=3)
    ), secondary_y=True)

    fig2.update_layout(
        title="<b>RGA y corte de agua</b>",
        template="plotly_white",
        height=600,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            font=dict(size=13, color="black", family="Arial Black")
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Arial"
        ),
        font=dict(size=14, color="black", family="Arial Black"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig2.update_xaxes(
        title_text="Fecha",
        tickformat="%d/%m/%Y",
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black",
        range=[fecha_min_graficas, fecha_max_graficas]
    )

    fig2.update_yaxes(
        title_text="RGA (pc/bl)",
        secondary_y=False,
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black"
    )

    fig2.update_yaxes(
        title_text="% Agua",
        secondary_y=True,
        showgrid=False
    )

    #st.plotly_chart(fig2, use_container_width=True)

    # =========================
    # GRÁFICO 3: Acumuladas Np, Wp, Gp
    # =========================
    fig_iny = go.Figure()

    fig_iny.add_trace(go.Scatter(
        x=total[COL_FECHA],
        y=total["QIN_TOTAL"],
        mode="lines",
        name="Qiny total",
        line=dict(color="#00ACC1", width=3),
        fill="tozeroy",
        fillcolor="rgba(0, 172, 193, 0.25)",
        hovertemplate=
            "<b>Fecha:</b> %{x|%d/%m/%Y}<br>" +
            "<b>Qiny:</b> %{y:,.1f} bpd<br>" +
            "<extra></extra>"
    ))

    fig_iny.update_layout(
        title="<b>Agua de inyeccion</b>",
        template="plotly_white",
        height=520,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            font=dict(size=13, color="black", family="Arial Black")
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Arial"
        ),
        font=dict(size=14, color="black", family="Arial Black"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig_iny.update_xaxes(
        title_text="Fecha",
        tickformat="%d/%m/%Y",
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black",
        range=[fecha_min_graficas, fecha_max_graficas]
    )

    fig_iny.update_yaxes(
        title_text="Qiny (bpd)",
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black"
    )

    fig3 = go.Figure()

    fig3.add_trace(go.Scatter(
        x=total[COL_FECHA],
        y=total["NP_TOTAL"],
        mode="lines",
        name="Np total",
        line=dict(color="#00A65A", width=3)
    ))

    fig3.add_trace(go.Scatter(
        x=total[COL_FECHA],
        y=total["WP_TOTAL"],
        mode="lines",
        name="Wp total",
        line=dict(color="#1E88E5", width=3)
    ))

    fig3.add_trace(go.Scatter(
        x=total[COL_FECHA],
        y=total["GP_TOTAL"],
        mode="lines",
        name="Gp total",
        line=dict(color="#E53935", width=3)
    ))

    fig3.update_layout(
        title="<b>Producción acumulada de aceite, agua y gas</b>",
        template="plotly_white",
        height=600,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.3,
            font=dict(size=13, color="black", family="Arial Black")
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Arial"
        ),
        font=dict(size=14, color="black", family="Arial Black"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig3.update_xaxes(
        title_text="Fecha",
        tickformat="%d/%m/%Y",
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black",
        range=[fecha_min_graficas, fecha_max_graficas]
    )

    fig3.update_yaxes(
        title_text="Np / Wp (mbl) y Gp (mmpc)",
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black"
    )

    total_export = total.copy()
    yac_export = yac.copy()

    total_export["FECHA"] = pd.to_datetime(total_export[COL_FECHA]).dt.strftime("%d/%m/%Y")
    yac_export["FECHA"] = pd.to_datetime(yac_export[COL_FECHA]).dt.strftime("%d/%m/%Y")

    total_export = total_export.rename(columns={
        "QO_TOTAL": "Qo total (bpd)",
        "QW_TOTAL": "Qw total (bpd)",
        "QIN_TOTAL": "Qiny total (bpd)",
        "QG_TOTAL": "Qg total (mpcd)",
        "POZOS_ACTIVOS": "Pozos activos",
        "RGA_TOTAL": "RGA (pc/bl)",
        "WC_TOTAL": "% Agua",
        "NP_TOTAL": "Np (mbl)",
        "WP_TOTAL": "Wp (mbl)",
        "GP_TOTAL": "Gp (mmpc)"
    })

    yac_export = yac_export.rename(columns={
        COL_YAC: "Yacimiento",
        "QO_TOTAL": "Qo total (bpd)",
        "QW_TOTAL": "Qw total (bpd)",
        "QIN_TOTAL": "Qiny total (bpd)",
        "QG_TOTAL": "Qg total (mpcd)",
        "POZOS_ACTIVOS": "Pozos activos",
        "RGA_TOTAL": "RGA (pc/bl)",
        "WC_TOTAL": "% Agua",
        "NP_TOTAL": "Np (mbl)",
        "WP_TOTAL": "Wp (mbl)",
        "GP_TOTAL": "Gp (mmpc)"
    })

    cols_total = [
        "FECHA",
        "Qo total (bpd)",
        "Qw total (bpd)",
        "Qiny total (bpd)",
        "Qg total (mpcd)",
        "Pozos activos",
        "RGA (pc/bl)",
        "% Agua",
        "Np (mbl)",
        "Wp (mbl)",
        "Gp (mmpc)"
    ]

    cols_yac = [
        "FECHA",
        "Yacimiento",
        "Qo total (bpd)",
        "Qw total (bpd)",
        "Qiny total (bpd)",
        "Qg total (mpcd)",
        "Pozos activos",
        "RGA (pc/bl)",
        "% Agua",
        "Np (mbl)",
        "Wp (mbl)",
        "Gp (mmpc)"
    ]

    total_export = total_export[[c for c in cols_total if c in total_export.columns]]
    yac_export = yac_export[[c for c in cols_yac if c in yac_export.columns]]

    #st.plotly_chart(fig3, use_container_width=True)

    # =====================================================
    # LAYOUT: 3 GRÁFICOS A LA IZQUIERDA + BURBUJAS A LA DERECHA
    # =====================================================

    col_graficas, col_burbujas = st.columns([4, 1.4], gap="small")

    with col_graficas:

        st.plotly_chart(
            fig1,
            use_container_width=True,
            config={"displaylogo": False}
        )

        st.plotly_chart(
            fig2,
            use_container_width=True,
            config={"displaylogo": False}
        )

        st.plotly_chart(
            fig_iny,
            use_container_width=True,
            config={"displaylogo": False}
        )

        st.plotly_chart(
            fig3,
            use_container_width=True,
            config={"displaylogo": False}
        )


    with col_burbujas:

        st.markdown(
            "<div class='section-title'>Acumuladas por yacimiento</div>",
            unsafe_allow_html=True
        )

        variable_burbuja_yac = st.radio(
            "Variable",
            ["NP_TOTAL", "WP_TOTAL", "GP_TOTAL"],
            format_func=lambda x: {
                "NP_TOTAL": "Aceite (mmb)",
                "WP_TOTAL": "Agua (mmb)",
                "GP_TOTAL": "Gas (mmmpc)"
            }[x],
            horizontal=True,
            key="variable_burbuja_yac_prod_campo"
        )

        orden_final = ["KTS", "KTIA", "KTIB", "JSA", "JAR"]

        yac_burb = (
            yac.sort_values([COL_YAC, COL_FECHA])
            .groupby(COL_YAC, as_index=False)
            .tail(1)
            .copy()
        )

        yac_burb["YAC_LABEL"] = (
            yac_burb[COL_YAC]
            .astype(str)
            .str.upper()
            .str.strip()
            .replace({
                "KTIAB": "KTIB",
                "JURASICO ARENISCAS": "JAR",
                "JURÁSICO ARENISCAS": "JAR",
                "ARENISCA": "JAR",
                "ARENISCAS": "JAR",
                "JAR": "JAR"
            })
        )

        yac_burb["ORDEN"] = yac_burb["YAC_LABEL"].apply(
            lambda x: orden_final.index(x) if x in orden_final else 999
        )

        yac_burb = yac_burb.sort_values("ORDEN").copy()

        max_val = yac_burb[variable_burbuja_yac].max()

        if max_val > 0:
            yac_burb["SIZE"] = 30 + (yac_burb[variable_burbuja_yac] / max_val) * 85
        else:
            yac_burb["SIZE"] = 30

        if variable_burbuja_yac == "NP_TOTAL":
            titulo_var = "Np"
            unidad_var = "mbl"
            color_burbuja = "#00A65A"

        elif variable_burbuja_yac == "WP_TOTAL":
            titulo_var = "Wp"
            unidad_var = "mbl"
            color_burbuja = "#1E88E5"

        else:
            titulo_var = "Gp"
            unidad_var = "mmpc"
            color_burbuja = "#E53935"

        yac_burb["ETIQUETA"] = yac_burb[variable_burbuja_yac].map(
            lambda x: f"{x/1000:,.3f}"
        )

        fig4 = go.Figure()

        fig4.add_trace(
            go.Scatter(
                x=[1] * len(yac_burb),
                y=yac_burb["YAC_LABEL"],
                mode="markers+text",
                text=yac_burb["ETIQUETA"],
                textposition="top center",
                textfont=dict(
                    color="black",
                    size=11,
                    family="Arial Black"
                ),
                marker=dict(
                    size=yac_burb["SIZE"],
                    sizemode="diameter",
                    color=color_burbuja,
                    opacity=0.85,
                    line=dict(color="black", width=2)
                ),
                customdata=yac_burb[
                    [
                        COL_YAC,
                        "QO_TOTAL",
                        "QW_TOTAL",
                        "QG_TOTAL",
                        "POZOS_ACTIVOS",
                        "RGA_TOTAL",
                        "WC_TOTAL",
                        "NP_TOTAL",
                        "WP_TOTAL",
                        "GP_TOTAL"
                    ]
                ],
                hovertemplate=
                    "<b>Yacimiento:</b> %{customdata[0]}<br>" +
                    "<b>Qo:</b> %{customdata[1]:,.1f} bpd<br>" +
                    "<b>Qw:</b> %{customdata[2]:,.1f} bpd<br>" +
                    "<b>Qg:</b> %{customdata[3]:,.1f} mpcd<br>" +
                    "<b>Pozos activos:</b> %{customdata[4]:,.0f}<br>" +
                    "<b>RGA:</b> %{customdata[5]:,.0f} pc/bl<br>" +
                    "<b>% Agua:</b> %{customdata[6]:,.1f}%<br>" +
                    "<b>Np:</b> %{customdata[7]:,.1f} mbl<br>" +
                    "<b>Wp:</b> %{customdata[8]:,.1f} mbl<br>" +
                    "<b>Gp:</b> %{customdata[9]:,.1f} mmpc<br>" +
                    "<extra></extra>",
                name=titulo_var
            )
        )

        fig4.update_layout(
            title=f"<b>{titulo_var} por yacimiento</b>",
            template="plotly_white",
            height=600 * 3,
            margin=dict(l=10, r=10, t=60, b=20),
            showlegend=False,
            font=dict(
                size=12,
                color="black",
                family="Arial Black"
            ),
            plot_bgcolor="white",
            paper_bgcolor="white"
        )

        fig4.update_xaxes(
            visible=False,
            range=[0.5, 1.5]
        )

        fig4.update_yaxes(
            title_text="",
            categoryorder="array",
            categoryarray=list(reversed(orden_final)),
            showline=False,
            showgrid=False,
            tickfont=dict(
                size=13,
                color="black",
                family="Arial Black"
            )
        )

        st.plotly_chart(
            fig4,
            use_container_width=True,
            config={"displaylogo": False}
        )




    # =====================================================
    # TABLAS DE DATOS USADOS EN LAS GRAFICAS
    # =====================================================
    st.markdown(
        "<div class='section-title'>Datos usados para las graficas</div>",
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs(["Total campo", "Por yacimiento"])

    with tab1:
        st.dataframe(
            total_export,
            use_container_width=True,
            height=420
        )

        st.download_button(
            label="Descargar datos total campo CSV",
            data=total_export.to_csv(index=False).encode("utf-8-sig"),
            file_name="datos_produccion_total_campo.csv",
            mime="text/csv"
        )

    with tab2:
        st.dataframe(
            yac_export,
            use_container_width=True,
            height=420
        )

        st.download_button(
            label="Descargar datos por yacimiento CSV",
            data=yac_export.to_csv(index=False).encode("utf-8-sig"),
            file_name="datos_produccion_por_yacimiento.csv",
            mime="text/csv"
        )

#Análisis RMA
def analisis_rma():
    st.markdown("<div class='section-title'>Análisis estadístico de reparaciones mayores RMA</div>", unsafe_allow_html=True)

    rma = load_table(TABLA_RMA)
    rma = normalizar_columnas(rma)
    rma = rma.loc[:, ~rma.columns.astype(str).str.startswith("UNNAMED")]

    col_anio = "AÑO"
    col_qoi_prog = "QO PROG"
    col_qoi = "QOI"
    col_yac = "YACIMIENTO"
    col_yac_rma = "YACIMIENTO RMA"
    col_np_rma = "NP (MB)"
    col_meses_activos = "MESES ACTIVO"

    if COL_POZO not in rma.columns:
        segunda_col = rma.columns[1]
        rma = rma.rename(columns={segunda_col: COL_POZO})

    rma[COL_POZO] = rma[COL_POZO].astype(str).str.strip()

    cols_necesarias = [
        col_anio, col_qoi_prog, col_qoi,
        col_yac, col_yac_rma, COL_POZO,
        col_np_rma, col_meses_activos
    ]

    for c in cols_necesarias:
        if c not in rma.columns:
            st.error(f"No existe la columna '{c}' en RMA. Revisa el encabezado exacto.")
            st.write(rma.columns.tolist())
            return

    rma[col_anio] = pd.to_numeric(rma[col_anio], errors="coerce")
    rma[col_qoi_prog] = pd.to_numeric(rma[col_qoi_prog], errors="coerce")
    rma[col_qoi] = pd.to_numeric(rma[col_qoi], errors="coerce")
    rma[col_np_rma] = pd.to_numeric(rma[col_np_rma], errors="coerce")
    rma[col_meses_activos] = pd.to_numeric(rma[col_meses_activos], errors="coerce")

    cols_datos_analisis_rma = [col_anio, col_qoi, col_np_rma, col_meses_activos]
    mask_solo_ubicacion_rma = rma[cols_datos_analisis_rma].isna().any(axis=1)
    rma_solo_ubicacion_base = rma[mask_solo_ubicacion_rma].copy()
    rma = rma[~mask_solo_ubicacion_rma].copy()

    if rma.empty:
        st.warning("No hay RMA con datos completos para graficar. Las RMA sin datos solo se muestran en el mapa.")
        return

    rma[col_anio] = pd.to_numeric(rma[col_anio], errors="coerce")
    rma[col_qoi_prog] = pd.to_numeric(rma[col_qoi_prog], errors="coerce")
    rma[col_qoi] = pd.to_numeric(rma[col_qoi], errors="coerce")
    rma[col_np_rma] = pd.to_numeric(rma[col_np_rma],errors="coerce").fillna(0)
    rma[col_meses_activos] = pd.to_numeric(rma[col_meses_activos],errors="coerce").fillna(0)

    rma["DIF_QOI"] = rma[col_qoi] - rma[col_qoi_prog]
    rma["CUMPLIMIENTO_QOI_%"] = np.where(
        rma[col_qoi_prog] > 0,
        rma[col_qoi] / rma[col_qoi_prog] * 100,
        np.nan
    )

    # =========================
    # FILTROS
    # =========================
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        anios = sorted(rma[col_anio].dropna().astype(int).unique())
        anio_sel = st.multiselect(
            "Año RMA",
            anios,
            default=anios,
            key="rma_anio"
        )

    rma_f = rma[rma[col_anio].astype("Int64").isin(anio_sel)].copy()
    rma_solo_ubicacion_f = rma_solo_ubicacion_base.copy()

    with c2:
        yacs = sorted(rma_f[col_yac].dropna().astype(str).unique())
        yac_sel = st.multiselect(
            "Origen",
            yacs,
            default=yacs,
            key="rma_yac"
        )

    if yac_sel:
        rma_f = rma_f[rma_f[col_yac].astype(str).isin(yac_sel)].copy()
        if col_yac in rma_solo_ubicacion_f.columns:
            rma_solo_ubicacion_f = rma_solo_ubicacion_f[
                rma_solo_ubicacion_f[col_yac].astype(str).isin(yac_sel)
            ].copy()

    with c3:
        yacs_rma = sorted(rma_f[col_yac_rma].dropna().astype(str).unique())
        yac_rma_sel = st.multiselect(
            "Intervención",
            yacs_rma,
            default=yacs_rma,
            key="rma_yac_rma"
        )

    if yac_rma_sel:
        rma_f = rma_f[rma_f[col_yac_rma].astype(str).isin(yac_rma_sel)].copy()
        if col_yac_rma in rma_solo_ubicacion_f.columns:
            rma_solo_ubicacion_f = rma_solo_ubicacion_f[
                rma_solo_ubicacion_f[col_yac_rma].astype(str).isin(yac_rma_sel)
            ].copy()

    yac_mapa_default_rma = (
        str(yac_rma_sel[0]).strip()
        if len(yac_rma_sel) == 1
        else "Todos"
    )

    with c4:
        pozos = sorted(rma_f[COL_POZO].dropna().astype(str).unique())

        pozos_sel_rma = st.multiselect(
            "Terminación",
            pozos,
            default=pozos,
            key="rma_pozos_sel"
    )

    if pozos_sel_rma:
        rma_f = rma_f[rma_f[COL_POZO].astype(str).isin(pozos_sel_rma)].copy()

    if rma_f.empty:
        st.warning("No hay datos con los filtros seleccionados.")
        return

    col_rma_graficas, col_rma_mapa_grande = st.columns([1.35, 1], gap="medium")

    with col_rma_mapa_grande:
        df_coord_rma = df_coord.copy()

        if df_coord_rma.empty:
            st.warning("Los pozos seleccionados en RMA no tienen coordenadas en Coord.")
        else:
            mapa_burbujas_rma_modulo(
                rma_f,
                df_coord_rma,
                col_anio,
                col_yac,
                col_yac_rma,
                col_qoi,
                col_np_rma,
                col_meses_activos,
                rma_solo_ubicacion=rma_solo_ubicacion_f,
                yac_mapa_default=yac_mapa_default_rma
            )

    # =========================
    # MÉTRICAS
    # =========================
    m1, m2 = col_rma_graficas.columns(2)

    m1.metric("RMA analizadas", f"{rma_f[COL_POZO].nunique():,.0f}")
    m2.metric("Qoi promedio", f"{rma_f[col_qoi].mean():,.1f} bpd")

    rma_f = rma_f.sort_values([col_anio, COL_POZO])

    rma_f["POZO_CAMP"] = (
        rma_f[col_anio].astype(int).astype(str)
        + " | "
        + rma_f[COL_POZO].astype(str)
    )

    # =========================
    # 1. QO PROG VS QOI
    # =========================
    fig1 = go.Figure()

    #fig1.add_trace(go.Bar(
    #    x=rma_f["POZO_CAMP"],
    #    y=rma_f[col_qoi_prog],
    #    name="Qo programa (bpd)",
    #    marker=dict(
    #        color="#1F4E79",
    #        line=dict(color="#0B1F33", width=1.5)
    #    ),
    #    opacity=0.88,
    #    text=rma_f[col_qoi_prog].round(1),
    #    textposition="outside"
    #))

    fig1.add_trace(go.Bar(
        x=rma_f["POZO_CAMP"],
        y=rma_f[col_qoi],
        name="Qoi real (bpd)",
        marker=dict(
            color="#00A65A",
            line=dict(color="#006B3A", width=1.5)
        ),
        opacity=0.95,
        text=rma_f[col_qoi].round(1),
        textposition="outside"
    ))

    fig1.update_layout(
        title="<b>RMA: Qoi(bpd)</b>",
        xaxis=dict(
            tickangle=-75,
            categoryorder="array",
            categoryarray=rma_f["POZO_CAMP"]
        ),
        yaxis_title="Qoi (bpd)",
        barmode="group",
        #height=560,
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
        font=dict(size=14, color="black", family="Arial Black"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig1.update_xaxes(
        title_text="Año | Terminación",
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(size=11, color="black", family="Tahoma")
    )

    fig1.update_yaxes(
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(size=12, color="black", family="Arial Black")
    )

    col_rma_graficas.plotly_chart(fig1, use_container_width=True)

    # =========================
    # 2. QOI PROMEDIO POR AÑO
    # =========================
    resumen_anio = rma_f.groupby(col_anio, as_index=False).agg(
        QOI_PROM=(col_qoi, "mean"),
        POZOS=(COL_POZO, "nunique")
    )

    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

    fig2.add_trace(
        go.Bar(
            x=resumen_anio[col_anio],
            y=resumen_anio["QOI_PROM"],
            name="Qoi promedio",
            marker=dict(
                color="#14A1FF",
                line=dict(color="#000000", width=1.5)
            ),
            text=resumen_anio["QOI_PROM"].round(1),
            textposition="outside",
            textfont=dict(size=13, color="#000000", family="Tahoma"),
            opacity=0.65
        ),
        secondary_y=False
    )

    for x, y, p in zip(
        resumen_anio[col_anio],
        resumen_anio["QOI_PROM"],
        resumen_anio["POZOS"]
    ):
        fig2.add_annotation(
            x=x,
            y=y * 0.05,
            text=f"<b>{p} pozos</b>",
            showarrow=False,
            font=dict(size=12, color="black", family="Arial Black")
        )

    fig2.update_layout(
        title="<b>RMA: Qoi promedio y pozos por año</b>",
        height=520,
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.15,
            xanchor="center",
            x=0.5
        ),
        font=dict(size=14, color="black", family="Arial Black"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig2.update_xaxes(
        title_text="Año",
        dtick=1,
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(size=12, color="black", family="Arial Black")
    )

    fig2.update_yaxes(
        title_text="Qoi promedio (bpd)",
        secondary_y=False,
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(size=12, color="black", family="Arial Black")
    )

    fig2.update_yaxes(
        title_text="Número de pozos",
        secondary_y=True,
        showgrid=False,
        tickfont=dict(size=12, color="black", family="Arial Black")
    )

    # =========================
    # BOXPLOT QOI + TOTAL FILTRO
    # =========================

    rma_box_qoi = rma_f.copy()

    rma_box_qoi["ANIO_BOX"] = rma_box_qoi[col_anio].astype(int).astype(str)

    rma_total_qoi = rma_f.copy()
    rma_total_qoi["ANIO_BOX"] = "TOTAL"

    rma_box_qoi = pd.concat(
        [rma_box_qoi, rma_total_qoi],
        ignore_index=True
    )

    orden_box_qoi = (
        sorted(rma_f[col_anio].dropna().astype(int).astype(str).unique().tolist())
        + ["TOTAL"]
    )

    fig3 = px.box(
        rma_box_qoi,
        x="ANIO_BOX",
        y=col_qoi,
        points="all",
        hover_name=COL_POZO,
        title="<b>RMA: Modelo estadístico Qoi</b>",
        template="plotly_white",
        category_orders={
            "ANIO_BOX": orden_box_qoi
        }
    )

    promedios_rma = (
    rma_box_qoi
    .groupby("ANIO_BOX", as_index=False)[col_qoi]
    .mean()
    )

    fig3.add_trace(
        go.Scatter(
            x=promedios_rma["ANIO_BOX"],
            y=promedios_rma[col_qoi],
            mode="markers+text",
            text=promedios_rma[col_qoi].round(1),
            textposition="top center",
            textfont=dict(
                size=10,
                color="blue"
            ),
            marker=dict(
                symbol="square",
                size=8,
                color="blue",
                line=dict(color="black", width=1)
            ),
            name="Promedio"
        )
    )


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

    #medianas = rma_box_qoi.groupby(col_anio, as_index=False)[col_qoi].median()
    medianas = rma_box_qoi.groupby("ANIO_BOX", as_index=False)[col_qoi].median()

    fig3.add_trace(go.Scatter(
        x=medianas["ANIO_BOX"],
        y=medianas[col_qoi],
        mode="text",
        text=medianas[col_qoi].round(1),
        textposition="top center",
        textfont=dict(size=10, color="black"),
        name="Mediana",
        showlegend=False
    ))

    fig3.update_layout(
        height=520,
        xaxis_title="Año / Total filtrado",
        #xaxis_title="Año",
        yaxis_title="Qoi por RMA (bpd)",
        xaxis=dict(
        categoryorder="array",
        categoryarray=orden_box_qoi
        ),
        font=dict(size=14, color="black", family="Arial Black"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig3.update_xaxes(
        dtick=1,
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(size=12, color="black", family="Arial Black")
    )

    fig3.update_yaxes(
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(size=12, color="black", family="Arial Black")
    )

    colg1, colg2 = col_rma_graficas.columns(2)

    with colg1:
        st.plotly_chart(fig2, use_container_width=True)

    with colg2:
        st.plotly_chart(fig3, use_container_width=True)

    # 4. QOI VS NP DESDE TABLA RMA
    # =========================
    st.markdown("<div class='section-title'>RMA: Análisis de producción acumulada</div>", unsafe_allow_html=True)
    #rma_np["ANIO_BOX"] = rma_np[col_anio].astype(int).astype(str)
    #rma_total_meses = rma_np.copy()
    ####################################################
    rma_np = rma_f.copy()

    rma_np["NP_FINAL"] = pd.to_numeric(
        rma_np[col_np_rma],
        errors="coerce"
    )

    rma_np["MESES_ACTIVOS"] = pd.to_numeric(
        rma_np[col_meses_activos],
        errors="coerce"
    )

    rma_np = rma_np[
        (rma_np["NP_FINAL"].notna()) &
        (rma_np["MESES_ACTIVOS"].notna()) &
        (rma_np["NP_FINAL"] > 0) &
        (rma_np["MESES_ACTIVOS"] > 0)
    ].copy()

    rma_np = rma_np.sort_values([col_anio, COL_POZO])

    rma_np["POZO_CAMP"] = (
        rma_np[col_anio].astype(int).astype(str)
        + " | "
        + rma_np[COL_POZO].astype(str)
    )

    rma_np["ANIO_BOX"] = rma_np[col_anio].astype(int).astype(str)

    # TOTAL para Np
    rma_total_np = rma_np.copy()
    rma_total_np["ANIO_BOX"] = "TOTAL"

    rma_box_np = pd.concat(
        [rma_np, rma_total_np],
        ignore_index=True
    )

    orden_box_np = (
        sorted(rma_np["ANIO_BOX"].dropna().unique().tolist())
        + ["TOTAL"]
    )

    # TOTAL para meses activos
    rma_total_meses = rma_np.copy()
    rma_total_meses["ANIO_BOX"] = "TOTAL"

    rma_box_meses = pd.concat(
        [rma_np, rma_total_meses],
        ignore_index=True
    )

    orden_box_meses = (
        sorted(rma_np["ANIO_BOX"].dropna().unique().tolist())
        + ["TOTAL"]
    )
    

    #################################################################
    fig4 = make_subplots(specs=[[{"secondary_y": True}]])

    fig4.add_trace(
        go.Bar(
            x=rma_np["POZO_CAMP"],
            y=rma_np[col_qoi],
            name="Qoi (bpd)",
            marker=dict(
                color="#00A65A",
                line=dict(color="#000000", width=1.5)
            ),
            text=rma_np[col_qoi].round(1),
            textposition="outside",
            textfont=dict(size=12, color="black", family="Tahoma"),
            opacity=0.80
        ),
        secondary_y=False
    )

    fig4.add_trace(
        go.Scatter(
            x=rma_np["POZO_CAMP"],
            y=rma_np["NP_FINAL"],
            name="Np RMA (mb)",
            mode="lines+markers+text",
            line=dict(color="#1F4E79", width=3),
            marker=dict(
                size=9,
                color="#1F4E79",
                line=dict(color="white", width=1)
            ),
            text=rma_np["NP_FINAL"].round(1),
            textposition="top center",
            textfont=dict(size=11, color="black", family="Tahoma")
        ),
        secondary_y=True
    )

    fig4.update_layout(
        title="<b>RMA: Qoi y Np RMA por pozo</b>",
        xaxis=dict(
            tickangle=-75,
            categoryorder="array",
            categoryarray=rma_np["POZO_CAMP"]
        ),
        height=650,
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.12,
            xanchor="center",
            x=0.5
        ),
        font=dict(size=14, color="black", family="Arial Black"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig4.update_xaxes(
        title_text="Año | Terminación",
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(size=11, color="black", family="Tahoma")
    )

    fig4.update_yaxes(
        title_text="Qoi (bpd)",
        secondary_y=False,
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(size=12, color="black", family="Arial Black")
    )

    fig4.update_yaxes(
        title_text="Np RMA (mb)",
        secondary_y=True,
        showgrid=False,
        tickfont=dict(size=12, color="black", family="Arial Black")
    )

    col_rma_graficas.plotly_chart(fig4, use_container_width=True)

    # =========================
    # 5. NP PROMEDIO
    # =========================
    #resumen_np = rma_np.groupby(col_anio, as_index=False).agg(
    #    NP_PROM=("NP_FINAL", "mean"),
    #    MESES_ACTIVOS_PROM=("MESES_ACTIVOS", "mean"),
    #    POZOS=(COL_POZO, "nunique")
    #)

    fig5 = go.Figure()

    # =========================
    # 5. BOXPLOT NP RMA
    # =========================
    
    medianas_np = rma_box_np.groupby("ANIO_BOX", as_index=False)["NP_FINAL"].median()

    fig5 = px.box(
        rma_box_np,
        x="ANIO_BOX",
        y="NP_FINAL",
        points="all",
        hover_name=COL_POZO,
        title="<b>RMA: Modelo estadístico Np</b>",
        template="plotly_white",
        category_orders={
            "ANIO_BOX": orden_box_np
        }
    )

    
    promedios_rma = (
        rma_box_np
        .groupby("ANIO_BOX", as_index=False)["NP_FINAL"]
        .mean()
    )

    fig5.add_trace(
        go.Scatter(
        x=promedios_rma["ANIO_BOX"],
        y=promedios_rma["NP_FINAL"],
        mode="markers+text",
        text=promedios_rma["NP_FINAL"].round(1),
        textposition="top center",
        textfont=dict(
            size=10,
            color="blue"
        ),
        marker=dict(
            symbol="square",
            size=8,
            color="blue",
            line=dict(color="black", width=1)
        ),
        name="Promedio",
        )
    )


    fig5.update_traces(
        marker=dict(
            color="#228B22",
            size=7,
            opacity=0.70,
            line=dict(color="black", width=1)
        ),
        line=dict(color="#145A32", width=1.5),
        fillcolor="rgba(34,139,34,0.25)"
    )

    medianas_np = rma_box_np.groupby("ANIO_BOX", as_index=False)["NP_FINAL"].median()
    
    fig5.add_trace(go.Scatter(
        x=medianas_np["ANIO_BOX"],
        y=medianas_np["NP_FINAL"],
        mode="text",
        text=medianas_np["NP_FINAL"].round(1),
        textposition="top center",
        textfont=dict(
            size=10,
            color="black",
            family="Arial Black"
        ),
        name="Mediana Np",
        showlegend=False
    ))

    fig5.update_layout(
        height=520,
        xaxis_title="Año / Total filtrado",
        yaxis_title="Np RMA (mb)",
        xaxis=dict(
            categoryorder="array",
            categoryarray=orden_box_np
        ),
        font=dict(size=14, color="black", family="Arial Black"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    anios_np_box = sorted(rma_np[col_anio].dropna().astype(int).unique())

    fig5.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=orden_box_np,
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(size=12, color="black", family="Arial Black")
    )

    fig5.update_yaxes(
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(size=12, color="black", family="Arial Black")
    )


    # =========================
    # 6. BOXPLOT MESES ACTIVOS
    # =========================
    #rma_np["ANIO_BOX"] = rma_np[col_anio].astype(int).astype(str)
    
    medianas_meses = rma_box_meses.groupby("ANIO_BOX", as_index=False)["MESES_ACTIVOS"].median()

    fig6 = px.box(
        rma_box_meses,
        x="ANIO_BOX",
        y="MESES_ACTIVOS",
        points="all",
        hover_name=COL_POZO,
        title="<b>RMA: Modelo estadístico meses activos</b>",
        template="plotly_white",
        category_orders={
            "ANIO_BOX": orden_box_meses
        }
    )

    fig6.update_traces(
        marker=dict(
            color="#FF4500",
            size=7,
            opacity=0.70,
            line=dict(color="black", width=1)
        ),
        line=dict(color="#A93226", width=1.5),
        fillcolor="rgba(255,69,0,0.25)"
    )

    #medianas_meses = rma_np.groupby(col_anio, as_index=False)["MESES_ACTIVOS"].median()

    fig6.add_trace(go.Scatter(
        x=medianas_meses["ANIO_BOX"],
        y=medianas_meses["MESES_ACTIVOS"],
        mode="text",
        text=medianas_meses["MESES_ACTIVOS"].round(1),
        textposition="top center",
        textfont=dict(
            size=10,
            color="black",
            family="Arial Black"
        ),
        name="Mediana meses activos",
        showlegend=False
    ))

    fig6.update_layout(
        height=520,
        xaxis_title="Año",
        yaxis_title="Meses activos",
        font=dict(size=14, color="black", family="Arial Black"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    anios_meses_box = sorted(rma_np[col_anio].dropna().astype(int).unique())

    fig6.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=orden_box_meses,
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(size=12, color="black", family="Arial Black")
    )

    fig6.update_yaxes(
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black",
        tickfont=dict(size=12, color="black", family="Arial Black")
    )

    colnp1, colnp2 = col_rma_graficas.columns(2)

    with colnp1:
        st.plotly_chart(fig5, use_container_width=True)

    with colnp2:
        st.plotly_chart(fig6, use_container_width=True)


def mapa_presion():

    st.markdown(
        "<div class='section-title'>Filtros Mapa de Presión</div>",
        unsafe_allow_html=True
    )

    pres = load_presiones()
    coord = df_coord.copy()

    if pres.empty:
        st.warning("No hay datos de presión cargados.")
        return

    # =========================
    # PANEL LATERAL + FILTROS BASE
    # =========================
    col_panel_presion, col_mapa_presion = st.columns([0.24, 0.76], gap="medium")

    with col_panel_presion:
        #st.markdown("#### Controles del mapa")
        st.markdown(
            """
            <div class="presion-filter-panel-marker"></div>
            <style>
            div[data-testid="column"]:has(.presion-filter-panel-marker),
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) {
                background: linear-gradient(180deg, #2F363D 0%, #252B31 100%);
                border: 1px solid #1F252B;
                border-radius: 8px;
                padding: 12px 12px 18px 12px;
                box-shadow: 0 10px 26px rgba(15, 23, 42, 0.22);
            }
            div[data-testid="column"]:has(.presion-filter-panel-marker) .presion-panel-title,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) .presion-panel-title {
                background: #20262D;
                border: 1px solid #111827;
                border-radius: 6px;
                color: #E5E7EB;
                font-size: 15px;
                font-weight: 800;
                letter-spacing: .2px;
                padding: 8px 10px;
                margin-bottom: 10px;
            }
            div[data-testid="column"]:has(.presion-filter-panel-marker) .presion-panel-section,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) .presion-panel-section {
                color: #AEB7C2;
                font-size: 10px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: .65px;
                margin: 14px 0 6px 0;
            }
            div[data-testid="column"]:has(.presion-filter-panel-marker) label,
            div[data-testid="column"]:has(.presion-filter-panel-marker) p,
            div[data-testid="column"]:has(.presion-filter-panel-marker) span,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) label,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) p,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) span {
                color: #DDE4EC !important;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 12px;
            }
            div[data-testid="column"]:has(.presion-filter-panel-marker) div[data-testid="stCheckbox"],
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) div[data-testid="stCheckbox"] {
                margin-top: -3px;
                margin-bottom: -4px;
            }
            div[data-testid="column"]:has(.presion-filter-panel-marker) div[data-testid="stSelectbox"] label,
            div[data-testid="column"]:has(.presion-filter-panel-marker) div[data-testid="stDateInput"] label,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) div[data-testid="stSelectbox"] label,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) div[data-testid="stDateInput"] label {
                color: #F3F4F6 !important;
                font-weight: 700;
            }
            div[data-testid="column"]:has(.presion-filter-panel-marker) div[data-baseweb="select"] > div,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) div[data-baseweb="select"] > div {
                background-color: #1F252B !important;
                border-color: #4B5563 !important;
                border-radius: 6px;
            }
            div[data-testid="column"]:has(.presion-filter-panel-marker) div[data-baseweb="select"] span,
            div[data-testid="column"]:has(.presion-filter-panel-marker) div[data-baseweb="select"] div,
            div[data-testid="column"]:has(.presion-filter-panel-marker) div[data-baseweb="select"] input,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) div[data-baseweb="select"] span,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) div[data-baseweb="select"] div,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) div[data-baseweb="select"] input {
                color: #F9FAFB !important;
            }
            div[data-testid="column"]:has(.presion-filter-panel-marker) div[data-baseweb="select"] svg,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) div[data-baseweb="select"] svg {
                color: #F9FAFB !important;
                fill: #F9FAFB !important;
            }
            div[data-testid="column"]:has(.presion-filter-panel-marker) div[data-baseweb="input"] > div,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) div[data-baseweb="input"] > div {
                background-color: #1F252B !important;
                border-color: #4B5563 !important;
                border-radius: 6px;
            }
            div[data-testid="column"]:has(.presion-filter-panel-marker) div[data-baseweb="input"] input,
            div[data-testid="column"]:has(.presion-filter-panel-marker) div[data-baseweb="input"] div,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) div[data-baseweb="input"] input,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) div[data-baseweb="input"] div {
                color: #F9FAFB !important;
            }
            div[data-testid="column"]:has(.presion-filter-panel-marker) div[data-baseweb="input"] svg,
            div[data-testid="stColumn"]:has(.presion-filter-panel-marker) div[data-baseweb="input"] svg {
                color: #F9FAFB !important;
                fill: #F9FAFB !important;
            }
            </style>
            <div class="presion-panel-title">Presiones</div>
            """,
            unsafe_allow_html=True
        )

        yacs = sorted(pres["YACIMIENTO"].dropna().astype(str).unique())
        yac_sel = st.selectbox(
            "Yacimiento",
            yacs,
            key="yac_mapa_presion"
        )

        pres_yac = pres[pres["YACIMIENTO"].astype(str) == str(yac_sel)].copy()
        fecha_min = pres_yac["FECHA"].min().date()
        fecha_max = pres_yac["FECHA"].max().date()
        key_fecha_presion = "fecha_ref_mapa_presion"

        if key_fecha_presion in st.session_state:
            fecha_actual = pd.to_datetime(st.session_state[key_fecha_presion]).date()
            if fecha_actual < fecha_min or fecha_actual > fecha_max:
                st.session_state[key_fecha_presion] = fecha_max

        fecha_ref = st.date_input(
            "Fecha referencia",
            value=fecha_max,
            min_value=fecha_min,
            max_value=fecha_max,
            key=key_fecha_presion
        )

        st.markdown("<div class='presion-panel-section'>Filtros</div>", unsafe_allow_html=True)

        mostrar_np = st.checkbox(
            "Producción Acumulada Aceite (mb)",
            value=False,
            key="mostrar_np_mapa_presion"
        )

        mostrar_gp = st.checkbox(
            "Producción acumulada de gas",
            value=False,
            key="mostrar_gp_mapa_presion"
        )

        mostrar_wp = st.checkbox(
            "Producción acumulada de agua",
            value=False,
            key="mostrar_wp_mapa_presion"
        )

        mostrar_winj = st.checkbox(
            "Agua inyectada acumulada",
            value=False,
            key="mostrar_winj_mapa_presion"
        )

        mostrar_rga = st.checkbox(
            "Última RGA",
            value=False,
            key="mostrar_rga_mapa_presion"
        )

        mostrar_estado = st.checkbox(
            "Estados del pozo",
            value=False,
            key="mostrar_estado_mapa_presion"
        )

        mostrar_campanias = st.checkbox(
            "Campañas 2011-2020",
            value=False,
            key="mostrar_campanias_mapa_presion"
        )

        #st.markdown("<div class='presion-panel-section'>Capas adicionales</div>", unsafe_allow_html=True)

        mostrar_loc_315_presion = st.checkbox(
            "315 Localizaciones",
            value=False,
            key="mostrar_loc_315_mapa_presion"
        )

        mostrar_loc_196_presion = st.checkbox(
            "196 Localizaciones",
            value=False,
            key="mostrar_loc_196_mapa_presion"
        )

        mostrar_inyectores_operando_presion = st.checkbox(
            "Inyectores Operando",
            value=False,
            key="mostrar_inyectores_operando_mapa_presion"
        )

        mostrar_radios_drene_presion = st.checkbox(
            "Radios de drene",
            value=False,
            key="mostrar_radios_drene_mapa_presion"
        )

        mostrar_muestreos_agua_presion = st.checkbox(
            "Muestreos % Agua",
            value=False,
            key="mostrar_muestreos_agua_mapa_presion"
        )

        fecha_inicio_muestreos_presion = None
        if mostrar_muestreos_agua_presion:
            fecha_inicio_muestreos_presion = st.date_input(
                "Muestreos desde",
                value=pd.to_datetime("2026-05-23").date(),
                key="fecha_inicio_muestreos_mapa_presion"
            )

        st.caption("La presión usa internamente la última disponible y promedia ±30 días.")

    pres = pres_yac.copy()
    modo_presion = "Última disponible"
    dias_promedio = 30

    pres_mapa = seleccionar_presiones_mapa(
        pres,
        fecha_ref=fecha_ref,
        modo_presion=modo_presion,
        ventana_meses=24,
        dias_promedio=dias_promedio,
        ventana_anios_ultima=7
    )

    if pres_mapa.empty:
        st.warning("No hay presiones cercanas a la fecha seleccionada. Cambia a 'Última disponible' o ajusta la fecha.")
        return

    # =========================
    # UNIR COORDENADAS
    # =========================
    coord["TERMINACION"] = coord["TERMINACION"].astype(str).str.strip()
    coord["POZO"] = coord["POZO"].astype(str).str.strip()

    coord_merge = coord[
    [
            "TERMINACION",
            "POZO",
            "CIMA X UTM",
            "CIMA Y UTM"
        ]
    ].drop_duplicates()

    pres_mapa = pres_mapa.merge(
        coord_merge,
        on=["TERMINACION", "POZO"],
        how="left"
    )

    pres_mapa = pres_mapa.dropna(
        subset=["CIMA X UTM", "CIMA Y UTM", "PRESION_MAPA"]
    )

    # =========================
    # BASE TODOS LOS POZOS + ACUMULADAS
    # =========================
    #prod_calc = calcular_columnas_produccion(df.copy())
    prod_calc = load_prod_calc().copy()

    acum_pozos = (
        prod_calc.groupby(COL_POZO, as_index=False)
        .agg({
            COL_ACEITE_BBL: "sum",
            COL_AGUA_BBL: "sum",
            COL_GAS_PC: "sum",
            COL_INY_BBL: "sum"
        })
        .rename(columns={
            COL_ACEITE_BBL: "NP_BLS",
            COL_AGUA_BBL: "WP_BLS",
            COL_GAS_PC: "GP_PC",
            COL_INY_BBL: "WINJ_BLS"
        })
    )

    rga_ult = (
        prod_calc.sort_values([COL_POZO, COL_FECHA])
        .dropna(subset=[COL_RGA])
    )
    rga_ult = rga_ult[rga_ult[COL_RGA] > 0]
    rga_ult = (
        rga_ult.groupby(COL_POZO, as_index=False)
        .tail(1)[[COL_POZO, COL_RGA]]
        .rename(columns={COL_RGA: "ULTIMA_RGA"})
    )

    acum_pozos = acum_pozos.merge(
        rga_ult,
        on=COL_POZO,
        how="left"
    )

    mapa_todos = coord.merge(
        acum_pozos,
        on=COL_POZO,
        how="left"
    )

    mapa_todos = mapa_todos[
        mapa_todos["YACIMIENTO"].astype(str) == str(yac_sel)
    ].copy()

    mapa_todos[["NP_BLS", "WP_BLS", "GP_PC", "WINJ_BLS", "ULTIMA_RGA"]] = mapa_todos[
        ["NP_BLS", "WP_BLS", "GP_PC", "WINJ_BLS", "ULTIMA_RGA"]
    ].fillna(0)

    mapa_todos = mapa_todos.dropna(
        subset=["CIMA X UTM", "CIMA Y UTM"]
    )

    def preparar_localizaciones_presion(tipo_localizaciones):
        loc = load_localizaciones()

        if loc.empty:
            return pd.DataFrame()

        loc = loc[
            loc["YACIMIENTO"].astype(str).str.upper() == str(yac_sel).upper()
        ].copy()

        if loc.empty:
            return pd.DataFrame()

        if tipo_localizaciones == "196":
            valores_196 = set(
                v.upper()
                for v in loc["COLUMNA 1"].dropna().astype(str).str.strip()
                if v and v.upper() not in ["NAN", "NONE"]
            ) if "COLUMNA 1" in loc.columns else set()

            if valores_196:
                loc = loc[
                    loc["COLUMNA 1"].astype(str).str.strip().str.upper().isin(valores_196)
                ].copy()

        loc["X_MAPA_PRESION"] = pd.to_numeric(loc["FONDO X"], errors="coerce")
        loc["Y_MAPA_PRESION"] = pd.to_numeric(loc["FONDO Y"], errors="coerce")
        loc = loc.dropna(subset=["X_MAPA_PRESION", "Y_MAPA_PRESION"]).copy()

        return loc

    def preparar_inyectores_operando_presion():
        iny = cargar_inyectores()

        if iny.empty or "Operando" not in iny.columns:
            return pd.DataFrame()

        iny = iny.copy()
        iny["Operando"] = iny["Operando"].fillna("").astype(str).str.strip()
        iny = iny[iny["Operando"] != ""].copy()

        if iny.empty:
            return pd.DataFrame()

        iny = iny[
            iny["Yacimiento"].astype(str).str.upper() == str(yac_sel).upper()
        ].copy()

        if iny.empty or "TERMINACION" not in iny.columns:
            return pd.DataFrame()

        coord_iny = coord[["TERMINACION", "POZO", "CIMA X UTM", "CIMA Y UTM"]].copy()
        coord_iny["TERMINACION"] = coord_iny["TERMINACION"].astype(str).str.strip()
        coord_iny = coord_iny.drop_duplicates(subset=["TERMINACION"])

        iny["TERMINACION"] = iny["TERMINACION"].astype(str).str.strip()
        iny["POZO_INY"] = iny["Pozo"].astype(str).str.strip()

        iny_mapa = iny.merge(
            coord_iny,
            on="TERMINACION",
            how="left"
        )
        iny_mapa["POZO"] = iny_mapa["POZO"].fillna(iny_mapa["POZO_INY"])
        iny_mapa["CIMA X UTM"] = pd.to_numeric(iny_mapa["CIMA X UTM"], errors="coerce")
        iny_mapa["CIMA Y UTM"] = pd.to_numeric(iny_mapa["CIMA Y UTM"], errors="coerce")

        return iny_mapa.dropna(subset=["CIMA X UTM", "CIMA Y UTM"]).copy()

    def preparar_muestreos_agua_presion():
        muestreos = load_muestreos_agua()

        if muestreos.empty:
            return pd.DataFrame()

        muestreos = muestreos.copy()
        muestreos["TERMINACION"] = muestreos["TERMINACION"].astype(str).str.strip()
        muestreos["% AGUA LAB"] = pd.to_numeric(muestreos["% AGUA LAB"], errors="coerce")
        muestreos["FECHA MUESTREO"] = convertir_fechas(muestreos["FECHA MUESTREO"])
        muestreos = muestreos.dropna(subset=["TERMINACION", "% AGUA LAB", "FECHA MUESTREO"])

        if fecha_inicio_muestreos_presion is not None:
            fecha_ini = pd.to_datetime(fecha_inicio_muestreos_presion).normalize()
            muestreos = muestreos[muestreos["FECHA MUESTREO"] >= fecha_ini].copy()

        if muestreos.empty:
            return pd.DataFrame()

        muestreos_ult = (
            muestreos.sort_values(["TERMINACION", "FECHA MUESTREO"])
            .groupby("TERMINACION", as_index=False)
            .tail(1)
        )

        coord_muestreos = mapa_todos[
            ["TERMINACION", "POZO", "YACIMIENTO", "CIMA X UTM", "CIMA Y UTM"]
        ].drop_duplicates(subset=["TERMINACION"]).copy()
        coord_muestreos["TERMINACION"] = coord_muestreos["TERMINACION"].astype(str).str.strip()

        muestreos_mapa = muestreos_ult.merge(
            coord_muestreos,
            on="TERMINACION",
            how="inner",
            suffixes=("_MUESTREO", "")
        )

        muestreos_mapa = muestreos_mapa[
            muestreos_mapa["YACIMIENTO"].astype(str).str.upper() == str(yac_sel).upper()
        ].copy()

        if muestreos_mapa.empty:
            return pd.DataFrame()

        max_agua = muestreos_mapa["% AGUA LAB"].max()
        muestreos_mapa["SIZE_MUESTREO"] = np.where(
            max_agua > 0,
            10 + (muestreos_mapa["% AGUA LAB"] / max_agua) * 28,
            10
        )
        muestreos_mapa["ETIQUETA_MUESTREO"] = muestreos_mapa["% AGUA LAB"].map(lambda v: f"{v:,.1f}%")

        return muestreos_mapa.dropna(subset=["CIMA X UTM", "CIMA Y UTM"]).copy()

    localizaciones_presion = []
    if mostrar_loc_315_presion:
        loc_315_presion = preparar_localizaciones_presion("315")
        if not loc_315_presion.empty:
            loc_315_presion["TIPO_LOCALIZACION"] = "315"
            localizaciones_presion.append(loc_315_presion)

    if mostrar_loc_196_presion:
        loc_196_presion = preparar_localizaciones_presion("196")
        if not loc_196_presion.empty:
            loc_196_presion["TIPO_LOCALIZACION"] = "196"
            localizaciones_presion.append(loc_196_presion)

    localizaciones_presion = (
        pd.concat(localizaciones_presion, ignore_index=True)
        if localizaciones_presion else pd.DataFrame()
    )

    inyectores_operando_presion = (
        preparar_inyectores_operando_presion()
        if mostrar_inyectores_operando_presion else pd.DataFrame()
    )

    muestreos_agua_presion = (
        preparar_muestreos_agua_presion()
        if mostrar_muestreos_agua_presion else pd.DataFrame()
    )

    if pres_mapa.empty:
        st.warning("Las presiones seleccionadas no tienen coordenadas en Coord.")
        return

        # =========================
    # KPI: POZOS CON PRESIÓN EN MAPA
    # =========================
    n_pozos_presion = pres_mapa["POZO"].nunique()
    n_terminaciones_presion = pres_mapa["TERMINACION"].nunique()
    n_mediciones_prom = pres_mapa["N_MEDICIONES"].sum()

    with col_mapa_presion:
        k1, k2, k3 = st.columns(3)

        with k1:
            st.metric("Pozos con presión en mapa", f"{n_pozos_presion:,.0f}")

        with k2:
            st.metric("Terminaciones graficadas", f"{n_terminaciones_presion:,.0f}")

        with k3:
            st.metric("Mediciones usadas/promediadas", f"{n_mediciones_prom:,.0f}")
    # =========================
    # ESTADO DE POZOS
    # =========================
    try:
        estado = load_estado_pozos()

        if not estado.empty:
            pres_mapa = pres_mapa.merge(
                estado,
                on="POZO",
                how="left"
            )
        else:
            pres_mapa["ESTADO"] = "Sin estado"
            pres_mapa["SAP"] = "Sin SAP"

    except Exception:
        pres_mapa["ESTADO"] = "Sin estado"
        pres_mapa["SAP"] = "Sin SAP"

    pres_mapa["ESTADO"] = pres_mapa["ESTADO"].fillna("Sin estado")
    pres_mapa["SAP"] = pres_mapa["SAP"].fillna("Sin SAP")

    # =========================
    # CAMPAÑAS 2011-2020
    # =========================
    if mostrar_campanias:
        term = load_term_perforados()

        pres_mapa = pres_mapa.merge(
            term,
            on="TERMINACION",
            how="left"
        )

        pres_mapa["PERFORADO_TERM"] = pres_mapa["PERFORADO_TERM"].fillna("No")
    else:
        pres_mapa["PERFORADO_TERM"] = "No"

    # =========================
    # CONTORNO
    # =========================
    contorno = load_table(TABLA_CONTORNO)
    asignacion = load_table(TABLA_ASIGNACION)

    contorno = contorno.sort_values("Orden")
    asignacion = asignacion.sort_values("Orden")

    contorno_plot = pd.concat(
        [contorno, contorno.iloc[[0]]],
        ignore_index=True
    )

    asignacion_plot = pd.concat(
        [asignacion, asignacion.iloc[[0]]],
        ignore_index=True
    )

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=contorno_plot["X"],
        y=contorno_plot["Y"],
        mode="lines",
        name="Campo",
        line=dict(color="black", width=3),
        hoverinfo="skip"
    ))

    fig.add_trace(go.Scatter(
        x=asignacion_plot["X"],
        y=asignacion_plot["Y"],
        mode="lines",
        name="Asignación",
        line=dict(color="red", width=3, dash="dash"),
        hoverinfo="skip"
    ))

    # HEAT MAP PRESIÓN CON KRIGING
    # =========================
    try:
        from pykrige.ok import OrdinaryKriging
        from matplotlib.path import Path

        x = pres_mapa["CIMA X UTM"].values.astype(float)
        y = pres_mapa["CIMA Y UTM"].values.astype(float)
        z = pres_mapa["PRESION_MAPA"].values.astype(float)

        if len(pres_mapa) >= 3:

            xi = np.linspace(contorno["X"].min(), contorno["X"].max(), 180)
            yi = np.linspace(contorno["Y"].min(), contorno["Y"].max(), 180)

            OK = OrdinaryKriging(
                x, y, z,
                variogram_model="spherical",
                verbose=False,
                enable_plotting=False,
                nlags=2,
                weight=True,
            )

            zi, ss = OK.execute("grid", xi, yi)
            zi = np.array(zi, dtype=float)

            XI, YI = np.meshgrid(xi, yi)

            poly = Path(contorno[["X", "Y"]].values)
            puntos_grid = np.vstack((XI.ravel(), YI.ravel())).T
            mask = poly.contains_points(puntos_grid).reshape(XI.shape)

            # Recortar fuera del contorno
            #zi_masked = np.where(mask, zi, np.nan)
            #p50 = np.nanpercentile(z, 50)

            #zi = np.where(np.isnan(zi), p50, zi)

            # Aquí se recorta al contorno
            zi_masked = np.where(mask, zi, np.nan)
            #zi_masked = np.where(mask, zi, np.nan)

            fig.add_trace(go.Contour(
                x=xi,
                y=yi,
                z=zi_masked,
                colorscale="Turbo",
                opacity=0.75,
                contours=dict(
                    coloring="heatmap",
                    showlines=False
                ),
                line=dict(width=0),
                colorbar=dict(title="Presión"),
                name="Kriging presión",
                hovertemplate="<b>Presión Kriging:</b> %{z:,.1f}<extra></extra>"
            ))

    except Exception as e:
        st.warning(f"No se pudo interpolar con Kriging: {e}")

        # =========================
    # TODOS LOS POZOS DEL YACIMIENTO
    # =========================
    fig.add_trace(go.Scatter(
        x=mapa_todos["CIMA X UTM"],
        y=mapa_todos["CIMA Y UTM"],
        mode="markers+text",
        text=mapa_todos["POZO"],
        textposition="top center",
        textfont=dict(
            size=10,
            color="black",
            family="Arial"
        ),
        marker=dict(
            size=6,
            symbol="circle",
            color="white",
            line=dict(color="black", width=1.2),
            opacity=1
        ),
        name="Todos los pozos",
        customdata=mapa_todos[
            ["POZO", "TERMINACION", "YACIMIENTO", "NP_BLS", "WP_BLS", "GP_PC"]
        ],
        hovertemplate=
            "<b>Pozo:</b> %{customdata[0]}<br>" +
            "<b>Terminación:</b> %{customdata[1]}<br>" +
            "<b>Yacimiento:</b> %{customdata[2]}<br>" +
            "<b>Np:</b> %{customdata[3]:,.0f} bls<br>" +
            "<b>Wp:</b> %{customdata[4]:,.0f} bls<br>" +
            "<b>Gp:</b> %{customdata[5]:,.0f} pc<br>" +
            "<extra></extra>",
        showlegend=True
    ))

    if mostrar_np:
        # =========================
        # BURBUJA DE ACEITE ACUMULADO
        # =========================
        mapa_np = mapa_todos[mapa_todos["NP_BLS"] > 0].copy()

        max_np = mapa_np["NP_BLS"].max()

        if max_np > 0:
            mapa_np["SIZE_NP"] = 12 + (mapa_np["NP_BLS"] / max_np) * 70
        else:
            mapa_np["SIZE_NP"] = 12

        mapa_np["ETIQUETA_NP"] = mapa_np["NP_BLS"].map(lambda x: f"{x/1000:,.1f}")

        fig.add_trace(go.Scatter(
            x=mapa_np["CIMA X UTM"],
            y=mapa_np["CIMA Y UTM"],
            mode="markers+text",
            text=mapa_np["ETIQUETA_NP"],
            textposition="bottom center",
            textfont=dict(
                size=10,
                color="black",
                family="Arial"
            ),
            marker=dict(
                size=mapa_np["SIZE_NP"],
                sizemode="diameter",
                color="green",
                opacity=0.45,
                line=dict(color="black", width=1)
            ),
            name="Np (mb)",
            customdata=mapa_np[
                ["POZO", "TERMINACION", "YACIMIENTO", "NP_BLS"]
            ],
            hovertemplate=
                "<b>Pozo:</b> %{customdata[0]}<br>" +
                "<b>Terminación:</b> %{customdata[1]}<br>" +
                "<b>Yacimiento:</b> %{customdata[2]}<br>" +
                "<b>Np:</b> %{customdata[3]:,.0f} bls<br>" +
                "<extra></extra>",
            showlegend=True
        ))

    def agregar_burbuja_variable_mapa(
        df_mapa,
        columna_valor,
        nombre_capa,
        color,
        unidad,
        divisor_etiqueta=1.0,
        decimales_etiqueta=1,
        opacidad=0.45
    ):
        mapa_var = df_mapa[df_mapa[columna_valor] > 0].copy()

        if mapa_var.empty:
            return

        max_valor = mapa_var[columna_valor].max()

        if max_valor > 0:
            mapa_var["SIZE_VAR"] = 12 + (mapa_var[columna_valor] / max_valor) * 70
        else:
            mapa_var["SIZE_VAR"] = 12

        mapa_var["ETIQUETA_VAR"] = mapa_var[columna_valor].map(
            lambda x: f"{x / divisor_etiqueta:,.{decimales_etiqueta}f}"
        )

        fig.add_trace(go.Scatter(
            x=mapa_var["CIMA X UTM"],
            y=mapa_var["CIMA Y UTM"],
            mode="markers+text",
            text=mapa_var["ETIQUETA_VAR"],
            textposition="bottom center",
            textfont=dict(
                size=10,
                color="black",
                family="Arial"
            ),
            marker=dict(
                size=mapa_var["SIZE_VAR"],
                sizemode="diameter",
                color=color,
                opacity=opacidad,
                line=dict(color="black", width=1)
            ),
            name=nombre_capa,
            customdata=mapa_var[
                ["POZO", "TERMINACION", "YACIMIENTO", columna_valor]
            ],
            hovertemplate=
                "<b>Pozo:</b> %{customdata[0]}<br>" +
                "<b>Terminación:</b> %{customdata[1]}<br>" +
                "<b>Yacimiento:</b> %{customdata[2]}<br>" +
                f"<b>{nombre_capa}:</b> " + "%{customdata[3]:,.1f} " + unidad + "<br>" +
                "<extra></extra>",
            showlegend=True
        ))

    if mostrar_gp:
        agregar_burbuja_variable_mapa(
            mapa_todos,
            "GP_PC",
            "Producción acumulada de gas",
            "#8E44AD",
            "pc",
            divisor_etiqueta=1_000_000,
            decimales_etiqueta=1
        )

    if mostrar_wp:
        agregar_burbuja_variable_mapa(
            mapa_todos,
            "WP_BLS",
            "Producción acumulada de agua",
            "#1F77B4",
            "bls",
            divisor_etiqueta=1000,
            decimales_etiqueta=1
        )

    if mostrar_winj:
        agregar_burbuja_variable_mapa(
            mapa_todos,
            "WINJ_BLS",
            "Agua inyectada acumulada",
            "#00AEEF",
            "bls",
            divisor_etiqueta=1000,
            decimales_etiqueta=1
        )

    if mostrar_rga:
        agregar_burbuja_variable_mapa(
            mapa_todos,
            "ULTIMA_RGA",
            "Última RGA",
            "#FF7F0E",
            "pc/bl",
            divisor_etiqueta=1,
            decimales_etiqueta=0,
            opacidad=0.55
        )

    # =========================
    # PUNTOS DE PRESIÓN
    # =========================
    if mostrar_radios_drene_presion and "RADIO DRENE" in mapa_todos.columns:
        mapa_radios = mapa_todos.copy()
        mapa_radios["RADIO DRENE"] = pd.to_numeric(mapa_radios["RADIO DRENE"], errors="coerce")
        mapa_radios = mapa_radios[mapa_radios["RADIO DRENE"] > 0].copy()

        theta = np.linspace(0, 2 * np.pi, 90)
        radios_x, radios_y, radios_customdata = [], [], []

        for _, row in mapa_radios.iterrows():
            x0 = row["CIMA X UTM"]
            y0 = row["CIMA Y UTM"]
            radio = row["RADIO DRENE"]

            radios_x.extend((x0 + radio * np.cos(theta)).tolist() + [None])
            radios_y.extend((y0 + radio * np.sin(theta)).tolist() + [None])
            radios_customdata.extend(
                [[row.get("POZO", ""), radio]] * len(theta) + [[None, None]]
            )

        if radios_x:
            fig.add_trace(go.Scatter(
                x=radios_x,
                y=radios_y,
                mode="lines",
                line=dict(width=2, color="black", dash="dash"),
                name="Radios de drene",
                customdata=radios_customdata,
                hovertemplate=
                    "<b>Pozo:</b> %{customdata[0]}<br>" +
                    "<b>Radio de drene:</b> %{customdata[1]:,.0f} m<br>" +
                    "<extra></extra>",
                showlegend=True
            ))

    if not localizaciones_presion.empty:
        colores_localizaciones_presion = {
            "PND": "#00A65A",
            "PRB": "#FFD700",
            "POS": "#0057FF"
        }

        for tipo_loc in localizaciones_presion["TIPO_LOCALIZACION"].dropna().astype(str).unique():
            loc_tipo = localizaciones_presion[
                localizaciones_presion["TIPO_LOCALIZACION"].astype(str) == str(tipo_loc)
            ].copy()

            for categoria, color in colores_localizaciones_presion.items():
                tmp_loc = loc_tipo[
                    loc_tipo["CATEGORIA"].astype(str).str.upper() == categoria
                ].copy()

                if tmp_loc.empty:
                    continue

                fig.add_trace(go.Scatter(
                    x=tmp_loc["X_MAPA_PRESION"],
                    y=tmp_loc["Y_MAPA_PRESION"],
                    mode="markers+text",
                    text=tmp_loc["POZO"],
                    textposition="bottom center",
                    marker=dict(
                        size=12,
                        symbol="diamond",
                        color=color,
                        line=dict(color="black", width=1)
                    ),
                    name=f"{tipo_loc} Localizaciones {categoria}",
                    customdata=tmp_loc[["POZO", "TERMINACION", "YACIMIENTO", "CATEGORIA"]],
                    hovertemplate=
                        "<b>Localización:</b> %{customdata[0]}<br>" +
                        "<b>Terminación:</b> %{customdata[1]}<br>" +
                        "<b>Yacimiento:</b> %{customdata[2]}<br>" +
                        "<b>Categoría:</b> %{customdata[3]}<br>" +
                        "<extra></extra>",
                    showlegend=True
                ))

    if not inyectores_operando_presion.empty:
        fig.add_trace(go.Scatter(
            x=inyectores_operando_presion["CIMA X UTM"],
            y=inyectores_operando_presion["CIMA Y UTM"],
            mode="markers",
            marker=dict(
                size=22,
                symbol="circle-open",
                color="#0057FF",
                line=dict(color="#0057FF", width=4)
            ),
            name="Inyectores Operando",
            customdata=inyectores_operando_presion[["POZO", "Yacimiento", "Operando", "VI_BLS"]],
            hovertemplate=
                "<b>Inyector operando:</b> %{customdata[0]}<br>" +
                "<b>Yacimiento:</b> %{customdata[1]}<br>" +
                "<b>Operando:</b> %{customdata[2]}<br>" +
                "<b>Vi:</b> %{customdata[3]:,.0f} bls<br>" +
                "<extra></extra>",
            showlegend=True
        ))

    if not muestreos_agua_presion.empty:
        fig.add_trace(go.Scatter(
            x=muestreos_agua_presion["CIMA X UTM"],
            y=muestreos_agua_presion["CIMA Y UTM"],
            mode="markers+text",
            text=muestreos_agua_presion["ETIQUETA_MUESTREO"],
            textposition="bottom center",
            textfont=dict(
                size=11,
                color="#0057FF",
                family="Arial Black"
            ),
            marker=dict(
                size=muestreos_agua_presion["SIZE_MUESTREO"],
                sizemode="diameter",
                symbol="circle",
                color="#8EDBFF",
                opacity=0.82,
                line=dict(color="#0057FF", width=2)
            ),
            name="Muestreos % Agua",
            customdata=muestreos_agua_presion[["POZO", "TERMINACION", "YACIMIENTO", "FECHA MUESTREO", "% AGUA LAB"]],
            hovertemplate=
                "<b>Pozo:</b> %{customdata[0]}<br>" +
                "<b>Terminación:</b> %{customdata[1]}<br>" +
                "<b>Yacimiento:</b> %{customdata[2]}<br>" +
                "<b>Fecha muestreo:</b> %{customdata[3]|%d/%m/%Y}<br>" +
                "<b>% Agua Lab:</b> %{customdata[4]:,.1f}%<br>" +
                "<extra></extra>",
            showlegend=True
        ))

    fig.add_trace(go.Scatter(
        x=pres_mapa["CIMA X UTM"],
        y=pres_mapa["CIMA Y UTM"],
        mode="markers+text",
        text=pres_mapa["POZO"],
        textposition="bottom center",
        textfont=dict(
            size=8,
            color="black",
            family="Arial Black"
        ),
        marker=dict(
            size=9,
            color=pres_mapa["PRESION_MAPA"],
            colorscale="Turbo",
            showscale=False,
            colorbar=dict(title="Presión"),
            line=dict(color="black", width=1)
        ),
        name="Presión medida",
        customdata=pres_mapa[
            [
                "POZO",
                "TERMINACION",
                "YACIMIENTO",
                "FECHA_PRESION",
                "PRESION_MAPA",
                "TEMPERATURA_MAPA",
                "N_MEDICIONES",
                "DIF_DIAS_REF",
                "ESTADO",
                "SAP"
            ]
        ],
        hovertemplate=
            "<b>Pozo:</b> %{customdata[0]}<br>" +
            "<b>Terminación:</b> %{customdata[1]}<br>" +
            "<b>Yacimiento:</b> %{customdata[2]}<br>" +
            "<b>Fecha presión:</b> %{customdata[3]|%d/%m/%Y}<br>" +
            "<b>Presión:</b> %{customdata[4]:,.1f}<br>" +
            "<b>Temperatura:</b> %{customdata[5]:,.1f}<br>" +
            "<b>Mediciones promedio:</b> %{customdata[6]}<br>" +
            "<b>Días vs ref.:</b> %{customdata[7]}<br>" +
            "<b>Estado:</b> %{customdata[8]}<br>" +
            "<b>SAP:</b> %{customdata[9]}<br>" +
            "<extra></extra>",
        showlegend=True
    ))

    if mostrar_estado:
        # =========================
        # ESTADO DE POZOS
        # =========================
        color_estado = {
            "OPERANDO": "#000000",
            "CCP": "#FFD700",
            "CSP": "#DC143C",
            "INY": "#0000FF",
            "PROG. TAPONAMIENTO": "#BA55D3",
            "TAPONADO": "#808080"
        }

        pres_mapa["COLOR_ESTADO"] = (
            pres_mapa["ESTADO"]
            .astype(str)
            .str.upper()
            .map(color_estado)
            .fillna("#7F8C8D")
        )

        fig.add_trace(go.Scatter(
            x=pres_mapa["CIMA X UTM"],
            y=pres_mapa["CIMA Y UTM"],
            mode="markers",
            marker=dict(
                size=8,
                symbol="circle",
                color=pres_mapa["COLOR_ESTADO"],
                line=dict(color="white", width=1.2),
                opacity=1
            ),
            name="Estado del pozo",
            customdata=pres_mapa[["POZO", "ESTADO", "SAP"]],
            hovertemplate=
                "<b>Pozo:</b> %{customdata[0]}<br>" +
                "<b>Estado:</b> %{customdata[1]}<br>" +
                "<b>SAP:</b> %{customdata[2]}<br>" +
                "<extra></extra>",
            showlegend=True
        ))

    if mostrar_campanias:
        # =========================
        # POZOS CAMPAÑAS 2011-2020
        # =========================
        mapa_term = pres_mapa[pres_mapa["PERFORADO_TERM"] == "Sí"].copy()

        fig.add_trace(go.Scatter(
            x=mapa_term["CIMA X UTM"],
            y=mapa_term["CIMA Y UTM"],
            mode="markers",
            marker=dict(
                size=17,
                symbol="circle-open",
                color="red",
                line=dict(color="red", width=3)
            ),
            name="Campañas 2011-2020",
            customdata=mapa_term[["POZO", "TERMINACION"]],
            hovertemplate=
                "<b>Pozo:</b> %{customdata[0]}<br>" +
                "<b>Terminación:</b> %{customdata[1]}<br>" +
                "<extra></extra>",
            showlegend=True
        ))

    fig.update_layout(
        title=f"<b>Mapa de presión - {yac_sel}</b>",
        template="plotly_white",
        height=750,
        margin=dict(l=20, r=20, t=70, b=20),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=13, color="black", family="Arial Black")
        ),
        font=dict(size=13, color="black", family="Arial Black"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig.update_xaxes(
        title_text="UTM X",
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black"
    )

    fig.update_yaxes(
        title_text="UTM Y",
        scaleanchor="x",
        scaleratio=1,
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black"
    )

    with col_mapa_presion:
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "scrollZoom": True,
                "displaylogo": False,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"]
            }
        )

        with st.expander("Ver datos usados para el mapa de presión"):
            st.dataframe(
                pres_mapa.sort_values("PRESION_MAPA", ascending=False),
                use_container_width=True,
                height=350
            )
def reservas():
    def _normalizar_txt_reservas(valor):
        valor = "" if pd.isna(valor) else str(valor)
        valor = unicodedata.normalize("NFKD", valor)
        valor = "".join(c for c in valor if not unicodedata.combining(c))
        return valor.strip().upper()

    def _preparar_tabla_reservas():
        raw = load_table(TABLA_RESERVAS).copy()
        if raw.empty:
            return pd.DataFrame()

        # La hoja Reservas puede venir con encabezados reales en la primera fila
        # cuando Excel genera columnas tipo "Unnamed".
        cols_norm = [_normalizar_txt_reservas(c) for c in raw.columns]
        if not any("YACIMIENTO" in c for c in cols_norm):
            fila_header = None
            for idx, row in raw.iterrows():
                valores = [_normalizar_txt_reservas(v) for v in row.tolist()]
                if any("YACIMIENTO" in v for v in valores) and any(v == "CAT" for v in valores):
                    fila_header = idx
                    break

            if fila_header is not None:
                nuevos_cols = [
                    str(v).strip() if pd.notna(v) and str(v).strip() else f"COL_{i}"
                    for i, v in enumerate(raw.iloc[fila_header].tolist())
                ]
                raw = raw.iloc[fila_header + 1:].copy()
                raw.columns = nuevos_cols

        mapa_cols = {}
        for col in raw.columns:
            n = _normalizar_txt_reservas(col)
            if "YACIMIENTO" in n:
                mapa_cols[col] = "Yacimiento"
            elif n == "CAT" or "CATEGORIA" in n:
                mapa_cols[col] = "Cat"
            elif "ORIGINAL" in n and ("MMB" in n or "ACEITE" in n or "PETROLEO" in n):
                mapa_cols[col] = "Original aceite (mmb)"
            elif "ORIGINAL" in n and ("MMMPC" in n or "GAS" in n):
                mapa_cols[col] = "Original gas (mmmpc)"
            elif "ORIGINAL" not in n and ("MMB" in n or "ACEITE" in n or "PETROLEO" in n):
                mapa_cols[col] = "Reserva aceite (mmb)"
            elif "ORIGINAL" not in n and ("MMMPC" in n or "GAS" in n):
                mapa_cols[col] = "Reserva gas (mmmpc)"

        df_res = raw.rename(columns=mapa_cols)
        df_res = df_res.loc[:, ~df_res.columns.duplicated()].copy()
        columnas_req = ["Yacimiento", "Cat", "Reserva aceite (mmb)", "Reserva gas (mmmpc)"]
        if not all(c in df_res.columns for c in columnas_req):
            st.error(
                "No pude identificar todas las columnas de Reservas. "
                "Se requieren: Yacimiento, Cat, Reserva (mmb) y Reserva (mmmpc)."
            )
            st.dataframe(raw.head(20), use_container_width=True)
            return pd.DataFrame()

        columnas_opt = ["Original aceite (mmb)", "Original gas (mmmpc)"]
        for col_opt in columnas_opt:
            if col_opt not in df_res.columns:
                df_res[col_opt] = 0

        df_res = df_res[columnas_req + columnas_opt].copy()
        df_res["Yacimiento"] = df_res["Yacimiento"].astype(str).str.strip()
        df_res["Cat"] = df_res["Cat"].astype(str).str.strip().str.upper()
        df_res["Reserva aceite (mmb)"] = pd.to_numeric(df_res["Reserva aceite (mmb)"], errors="coerce").fillna(0)
        df_res["Reserva gas (mmmpc)"] = pd.to_numeric(df_res["Reserva gas (mmmpc)"], errors="coerce").fillna(0)
        df_res["Original aceite (mmb)"] = pd.to_numeric(df_res["Original aceite (mmb)"], errors="coerce").fillna(0)
        df_res["Original gas (mmmpc)"] = pd.to_numeric(df_res["Original gas (mmmpc)"], errors="coerce").fillna(0)
        df_res = df_res[(df_res["Yacimiento"].ne("")) & (df_res["Cat"].ne(""))].copy()
        return df_res

    colores_cat = {
        "PDP": "#008A2E",
        "PDNP": "#7CB342",
        "PND": "#F2A900",
        "PB": "#FF4B00",
        "POS": "#9E9E9E",
        "1P": "#4F9F38",
        "2P": "#FF4B00",
        "3P": "#8E24AA",
    }
    definiciones = {
        "PDP": "Probadas Desarrolladas Produciendo",
        "PDNP": "Probadas Desarrolladas No Produciendo",
        "PND": "Probadas No Desarrolladas",
        "PB": "Probables",
        "POS": "Posibles",
    }
    orden_base = ["PDP", "PDNP", "PND", "PB", "POS"]

    def _valor_cat(df_cat, cat, col_valor):
        s = df_cat.loc[df_cat["Cat"].eq(cat), col_valor]
        return float(s.iloc[0]) if not s.empty else 0.0

    def _totales_desde_base(df_cat, col_valor):
        vals = {cat: _valor_cat(df_cat, cat, col_valor) for cat in orden_base}
        vals["1P"] = _valor_cat(df_cat, "1P", col_valor) or (vals["PDP"] + vals["PDNP"] + vals["PND"])
        vals["2P"] = _valor_cat(df_cat, "2P", col_valor) or (vals["1P"] + vals["PB"])
        vals["3P"] = _valor_cat(df_cat, "3P", col_valor) or (vals["2P"] + vals["POS"])
        return vals

    def _totales_originales(df_cat, col_valor):
        vals = {cat: _valor_cat(df_cat, cat, col_valor) for cat in ["1P", "2P", "3P"]}
        if not any(vals.values()):
            vals_reserva = _totales_desde_base(df_cat, col_valor)
            vals = {cat: vals_reserva.get(cat, 0) for cat in ["1P", "2P", "3P"]}
        return vals

    def _fig_reserva_yacimiento(yacimiento, df_yac, col_valor, unidad, y_max=None):
        vals = _totales_desde_base(df_yac, col_valor)
        y_vals = [vals[c] for c in orden_base] + [vals["3P"]]
        medidas = ["relative", "relative", "relative", "relative", "relative", "total"]
        x_vals = orden_base + ["3P TOTAL"]
        colores = [colores_cat[c] for c in orden_base] + [colores_cat["3P"]]

        bases, altos, acumulados = [], [], []
        acumulado = 0.0
        for valor, medida in zip(y_vals, medidas):
            if medida == "total":
                bases.append(0)
                altos.append(valor)
                acumulado = valor
            else:
                bases.append(acumulado)
                altos.append(valor)
                acumulado += valor
            acumulados.append(acumulado)

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=x_vals,
                y=altos,
                base=bases,
                marker=dict(
                    color=colores,
                    opacity=0.96,
                    line=dict(color="rgba(255,255,255,0.95)", width=1.2),
                ),
                text=[f"{v:,.3f}" for v in y_vals],
                textposition="outside",
                textfont=dict(color="#111827", size=11, family="Segoe UI"),
                customdata=np.array(y_vals).reshape(-1, 1),
                hovertemplate="<b>%{x}</b><br>Reserva: %{customdata[0]:,.3f} " + unidad + "<extra></extra>",
            )
        )
        for i in range(len(x_vals) - 1):
            fig.add_shape(
                type="line",
                xref="x", yref="y",
                x0=i + 0.36, x1=i + 0.64,
                y0=acumulados[i], y1=acumulados[i],
                line=dict(color="rgba(50,50,50,0.35)", width=1, dash="dot"),
            )
        fig.update_layout(
            title=dict(
                text="",
                font=dict(size=13, color="#FFFFFF"),
            ),
            height=315,
            margin=dict(l=42, r=18, t=92, b=44),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#F8FAFC",
            font=dict(size=10, color="#0B1F4D", family="Segoe UI"),
            showlegend=False,
            bargap=0.32,
            hoverlabel=dict(bgcolor="#252B31", font=dict(color="#FFFFFF")),
        )
        fig.update_xaxes(
            tickfont=dict(size=9, color="#0B1F4D"),
            showline=True,
            linewidth=1,
            linecolor="rgba(11,31,77,0.25)",
        )
        fig.update_yaxes(
            title=unidad,
            gridcolor="rgba(11,31,77,0.10)",
            zerolinecolor="rgba(11,31,77,0.25)",
            range=[0, y_max] if y_max else None,
            rangemode="tozero" if not y_max else None,
            showline=True,
            linewidth=1,
            linecolor="rgba(11,31,77,0.25)",
        )
        fig.add_shape(
            type="rect",
            xref="paper", yref="paper",
            x0=0, x1=1, y0=1.03, y1=1.32,
            fillcolor="#061B65",
            line=dict(color="#061B65"),
            layer="below",
        )
        fig.add_annotation(
            x=0.5, y=1.235,
            xref="paper", yref="paper",
            text=f"<b>{yacimiento.upper()}</b> | Reserva ({unidad})",
            showarrow=False,
            font=dict(size=13, color="#FFFFFF", family="Segoe UI"),
            align="center",
        )
        fig.add_annotation(
            x=0.5, y=1.105,
            xref="paper", yref="paper",
            text=f"<b>3P = {vals['3P']:,.3f} {unidad}</b>",
            showarrow=False,
            font=dict(size=13, color="#FFFFFF", family="Segoe UI"),
            align="center",
        )
        return fig

    def _fig_resumen_total(titulo, x_vals, y_vals, medidas, colores, unidad, y_max=None):
        bases, altos, acumulados = [], [], []
        acumulado = 0.0
        for valor, medida in zip(y_vals, medidas):
            if medida == "total":
                bases.append(0)
                altos.append(valor)
                acumulado = valor
            else:
                bases.append(acumulado)
                altos.append(valor)
                acumulado += valor
            acumulados.append(acumulado)

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=x_vals,
                y=altos,
                base=bases,
                marker=dict(
                    color=colores,
                    opacity=0.96,
                    line=dict(color="rgba(255,255,255,0.95)", width=1.2),
                ),
                text=[f"{v:,.3f}" for v in y_vals],
                textposition="outside",
                textfont=dict(color="#111827", size=11, family="Segoe UI"),
                customdata=np.array(y_vals).reshape(-1, 1),
                hovertemplate="<b>%{x}</b><br>Reserva: %{customdata[0]:,.3f} " + unidad + "<extra></extra>",
            )
        )
        for i in range(len(x_vals) - 1):
            fig.add_shape(
                type="line",
                xref="x", yref="y",
                x0=i + 0.36, x1=i + 0.64,
                y0=acumulados[i], y1=acumulados[i],
                line=dict(color="rgba(50,50,50,0.38)", width=1, dash="dot"),
            )
        fig.update_layout(
            title=dict(text=titulo, x=0.5, font=dict(size=15, color=colores[-1])),
            height=270,
            margin=dict(l=42, r=18, t=58, b=44),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#F8FAFC",
            font=dict(size=10, color="#0B1F4D", family="Segoe UI"),
            showlegend=False,
            bargap=0.34,
            hoverlabel=dict(bgcolor="#252B31", font=dict(color="#FFFFFF")),
        )
        fig.update_yaxes(
            title=unidad,
            gridcolor="rgba(11,31,77,0.10)",
            range=[0, y_max] if y_max else None,
            rangemode="tozero" if not y_max else None,
            showline=True,
            linewidth=1,
            linecolor="rgba(11,31,77,0.25)",
        )
        fig.update_xaxes(
            tickfont=dict(size=9, color="#0B1F4D"),
            showline=True,
            linewidth=1,
            linecolor="rgba(11,31,77,0.25)",
        )
        return fig

    df_reservas = _preparar_tabla_reservas()
    if df_reservas.empty:
        st.warning("No hay datos disponibles en la tabla Reservas.")
        return

    st.markdown(
        """
        <style>
        .reservas-hero {
            background: linear-gradient(90deg, #F8FAFC 0%, #FFFFFF 45%, #F8FAFC 100%);
            border: 1px solid #E5E7EB;
            border-radius: 14px;
            padding: 10px 14px;
            margin-bottom: 10px;
            text-align: center;
        }
        .reservas-hero h1 {
            color: #061B65;
            margin: 0;
            font-size: 28px;
            line-height: 1.0;
            font-weight: 900;
            letter-spacing: .8px;
        }
        .reservas-hero p {
            color: #4B5563;
            margin: 2px 0 0 0;
            font-size: 16px;
            font-weight: 750;
        }
        .reservas-card {
            border-radius: 12px;
            color: white;
            padding: 16px 18px;
            text-align: center;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.12);
            min-height: 88px;
        }
        .reservas-card .label {font-size: 13px; font-weight: 800;}
        .reservas-card .value {font-size: 28px; font-weight: 900; line-height: 1.0;}
        .reservas-card .unit {font-size: 12px; font-weight: 800;}
        .reservas-general-label {
            background: linear-gradient(135deg, #061B65, #0B2C83);
            border-radius: 12px;
            color: white;
            padding: 16px 18px;
            min-height: 88px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            font-size: 18px;
            font-weight: 900;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.12);
        }
        .reservas-yac-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 14px;
            padding: 10px 10px 4px 10px;
            margin-bottom: 10px;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.07);
        }
        .reservas-yac-title {
            background: linear-gradient(90deg, #061B65, #0B2C83);
            color: white;
            border-radius: 10px;
            padding: 8px 10px;
            text-align: center;
            font-size: 13px;
            font-weight: 900;
            letter-spacing: .2px;
            margin-bottom: 8px;
        }
        .reservas-chip-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 5px;
            margin-bottom: 6px;
        }
        .reservas-chip {
            border-radius: 8px;
            padding: 5px 4px;
            color: white;
            text-align: center;
            line-height: 1.05;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.18);
        }
        .reservas-chip .cat {font-size: 10px; font-weight: 900;}
        .reservas-chip .val {font-size: 11px; font-weight: 900;}
        .reservas-chip .unit {font-size: 8px; font-weight: 800;}
        .reservas-table-wrap {
            border: 1px solid #1F252B;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
            margin-bottom: 14px;
        }
        table.reservas-table {
            width: 100%;
            border-collapse: collapse;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 13px;
            background: #FFFFFF;
        }
        table.reservas-table thead th {
            background: linear-gradient(90deg, #2F363D 0%, #252B31 100%);
            color: #FFFFFF;
            font-weight: 850;
            text-align: center;
            padding: 9px 10px;
            border: 1px solid #1F252B;
        }
        table.reservas-table tbody td {
            padding: 8px 10px;
            border: 1px solid #E5E7EB;
            color: #111827;
            text-align: right;
        }
        table.reservas-table tbody td:first-child,
        table.reservas-table tbody td:nth-child(2) {
            text-align: left;
            font-weight: 650;
        }
        table.reservas-table tbody tr:nth-child(even) {
            background: #F8FAFC;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    fluido_actual = st.session_state.get("reservas_fluido", "Aceite")
    tipo_volumen_actual = st.session_state.get("reservas_tipo_volumen", "Reserva")
    fluido = fluido_actual
    titulo_banner_reservas = "RESERVAS POR YACIMIENTO" if tipo_volumen_actual == "Reserva" else "VOLUMEN ORIGINAL POR YACIMIENTO"
    subtitulo_actual = (
        "Millones de barriles de petróleo (mmb)"
        if fluido_actual == "Aceite"
        else "Miles de millones de pies cúbicos (mmmpc)"
    )

    st.markdown(
        f"""
        <div class="reservas-hero">
            <h1>{titulo_banner_reservas}</h1>
            <p>{subtitulo_actual}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1.25, 1.45, 2.3])
    with col_ctrl1:
        fluido = st.radio(
            "Filtro Fluido",
            ["Aceite", "Gas"],
            horizontal=True,
            key="reservas_fluido"
        )
    with col_ctrl2:
        tipo_volumen = st.radio(
            "Categoría",
            ["Reserva", "Volumen original"],
            horizontal=True,
            key="reservas_tipo_volumen"
        )

    if tipo_volumen == "Volumen original":
        col_valor = "Original aceite (mmb)" if fluido == "Aceite" else "Original gas (mmmpc)"
    else:
        col_valor = "Reserva aceite (mmb)" if fluido == "Aceite" else "Reserva gas (mmmpc)"
    unidad = "mmb" if fluido == "Aceite" else "mmmpc"

    def _mostrar_tabla_reservas(df_tabla, columnas_numericas=None, columnas_pct=None):
        df_html = df_tabla.copy()
        columnas_numericas = columnas_numericas or []
        columnas_pct = columnas_pct or []
        for col in columnas_numericas:
            if col in df_html.columns:
                df_html[col] = pd.to_numeric(df_html[col], errors="coerce").map(
                    lambda v: "" if pd.isna(v) else f"{v:,.3f}"
                )
        for col in columnas_pct:
            if col in df_html.columns:
                df_html[col] = pd.to_numeric(df_html[col], errors="coerce").map(
                    lambda v: "" if pd.isna(v) else f"{v:,.1f}%"
                )
        html_tabla = df_html.to_html(index=False, escape=False, classes="reservas-table", border=0)
        st.markdown(f"<div class='reservas-table-wrap'>{html_tabla}</div>", unsafe_allow_html=True)

    if tipo_volumen == "Volumen original":
        yac_original = []
        for yac in df_reservas["Yacimiento"].dropna().unique():
            vals_yac = _totales_originales(df_reservas[df_reservas["Yacimiento"].eq(yac)], col_valor)
            yac_original.append({"Yacimiento": yac, **vals_yac})

        df_yac_original = pd.DataFrame(yac_original).sort_values("3P", ascending=False).reset_index(drop=True)
        vals_total_original = {
            "1P": float(df_yac_original["1P"].sum()) if "1P" in df_yac_original.columns else 0,
            "2P": float(df_yac_original["2P"].sum()) if "2P" in df_yac_original.columns else 0,
            "3P": float(df_yac_original["3P"].sum()) if "3P" in df_yac_original.columns else 0,
        }

        st.markdown("### Volumen original por campo")
        col_lbl, col_1p, col_2p, col_3p = st.columns([0.9, 1.15, 1.15, 1.15])
        with col_lbl:
            st.markdown("<div class='reservas-general-label'>VOLUMEN<br>ORIGINAL</div>", unsafe_allow_html=True)

        cards_original = [
            (col_1p, "Original 1P", vals_total_original["1P"], "#67A83B"),
            (col_2p, "Original 2P", vals_total_original["2P"], "#FF4B00"),
            (col_3p, "Original 3P", vals_total_original["3P"], "#8E24AA"),
        ]
        for col, label, val, color in cards_original:
            with col:
                st.markdown(
                    f"""
                    <div class="reservas-card" style="background: linear-gradient(135deg, {color}, {color}CC);">
                        <div class="label">{label}</div>
                        <div class="value">{val:,.3f}</div>
                        <div class="unit">{unidad}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("### Volumen original por yacimiento")
        _mostrar_tabla_reservas(
            df_yac_original[["Yacimiento", "1P", "2P", "3P"]],
            columnas_numericas=["1P", "2P", "3P"],
        )
        st.caption("Volumen original mostrado únicamente para categorías 1P, 2P y 3P.")
        return

    resumen_base = (
        df_reservas[df_reservas["Cat"].isin(orden_base)]
        .groupby("Cat", as_index=False)[col_valor]
        .sum()
    )
    vals_total = {cat: float(resumen_base.loc[resumen_base["Cat"].eq(cat), col_valor].sum()) for cat in orden_base}
    vals_total["1P"] = vals_total["PDP"] + vals_total["PDNP"] + vals_total["PND"]
    vals_total["2P"] = vals_total["1P"] + vals_total["PB"]
    vals_total["3P"] = vals_total["2P"] + vals_total["POS"]
    y_max_resumen_total = vals_total["3P"] * 1.18 if vals_total["3P"] else 1

    st.markdown("### Resumen general")
    col_lbl, col_1p, col_2p, col_3p = st.columns([0.9, 1.15, 1.15, 1.15])
    with col_lbl:
        st.markdown("<div class='reservas-general-label'>RESUMEN<br>GENERAL</div>", unsafe_allow_html=True)
    resumen_cards = [
        (col_1p, "1P (PDP+PDNP+PND)", vals_total["1P"], "#67A83B"),
        (col_2p, "2P (1P+PB)", vals_total["2P"], "#FF4B00"),
        (col_3p, "3P (2P+POS)", vals_total["3P"], "#8E24AA"),
    ]
    for col, label, val, color in resumen_cards:
        with col:
            st.markdown(
                f"""
                <div class="reservas-card" style="background: linear-gradient(135deg, {color}, {color}CC);">
                    <div class="label">{label}</div>
                    <div class="value">{val:,.3f}</div>
                    <div class="unit">{unidad}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    yac_resumen = []
    for yac in df_reservas["Yacimiento"].dropna().unique():
        vals_yac = _totales_desde_base(df_reservas[df_reservas["Yacimiento"].eq(yac)], col_valor)
        yac_resumen.append({"Yacimiento": yac, **vals_yac})
    df_yac_resumen = pd.DataFrame(yac_resumen).sort_values("3P", ascending=False).reset_index(drop=True)
    yacimientos = df_yac_resumen["Yacimiento"].tolist()
    y_max_yacimientos = float(df_yac_resumen["3P"].max()) * 1.18 if not df_yac_resumen.empty else 1

    def _mostrar_tabla_reservas(df_tabla, columnas_numericas=None, columnas_pct=None):
        df_html = df_tabla.copy()
        columnas_numericas = columnas_numericas or []
        columnas_pct = columnas_pct or []
        for col in columnas_numericas:
            if col in df_html.columns:
                df_html[col] = pd.to_numeric(df_html[col], errors="coerce").map(
                    lambda v: "" if pd.isna(v) else f"{v:,.3f}"
                )
        for col in columnas_pct:
            if col in df_html.columns:
                df_html[col] = pd.to_numeric(df_html[col], errors="coerce").map(
                    lambda v: "" if pd.isna(v) else f"{v:,.1f}%"
                )
        html_tabla = df_html.to_html(index=False, escape=False, classes="reservas-table", border=0)
        st.markdown(f"<div class='reservas-table-wrap'>{html_tabla}</div>", unsafe_allow_html=True)

    st.markdown("### Resumen general por yacimiento")
    columnas_resumen_yac = ["Yacimiento", "PDP", "PDNP", "PND", "1P", "PB", "2P", "POS", "3P"]
    _mostrar_tabla_reservas(
        df_yac_resumen[columnas_resumen_yac],
        columnas_numericas=["PDP", "PDNP", "PND", "1P", "PB", "2P", "POS", "3P"],
    )

    st.markdown("### Resumen total por categoría")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        st.plotly_chart(
            _fig_resumen_total(
                f"<b>1P (PDP + PDNP + PND)</b><br>{vals_total['1P']:,.3f} {unidad}",
                ["PDP", "PDNP", "PND", "1P TOTAL"],
                [vals_total["PDP"], vals_total["PDNP"], vals_total["PND"], vals_total["1P"]],
                ["relative", "relative", "relative", "total"],
                [colores_cat["PDP"], colores_cat["PDNP"], colores_cat["PND"], colores_cat["1P"]],
                unidad,
                y_max_resumen_total,
            ),
            use_container_width=True
        )
    with c2:
        st.plotly_chart(
            _fig_resumen_total(
                f"<b>2P (1P + PB)</b><br>{vals_total['2P']:,.3f} {unidad}",
                ["1P TOTAL", "PB", "2P TOTAL"],
                [vals_total["1P"], vals_total["PB"], vals_total["2P"]],
                ["relative", "relative", "total"],
                [colores_cat["1P"], colores_cat["PB"], colores_cat["2P"]],
                unidad,
                y_max_resumen_total,
            ),
            use_container_width=True
        )
    with c3:
        st.plotly_chart(
            _fig_resumen_total(
                f"<b>3P (2P + POS)</b><br>{vals_total['3P']:,.3f} {unidad}",
                ["2P TOTAL", "POS", "3P TOTAL"],
                [vals_total["2P"], vals_total["POS"], vals_total["3P"]],
                ["relative", "relative", "total"],
                [colores_cat["2P"], colores_cat["POS"], colores_cat["3P"]],
                unidad,
                y_max_resumen_total,
            ),
            use_container_width=True
        )

    st.markdown("### Reservas por yacimiento")
    cols_por_fila = min(3, max(1, len(yacimientos)))
    for inicio in range(0, len(yacimientos), cols_por_fila):
        cols_yac = st.columns(cols_por_fila)
        for col, yac in zip(cols_yac, yacimientos[inicio:inicio + cols_por_fila]):
            df_yac = df_reservas[df_reservas["Yacimiento"].eq(yac)]
            with col:
                fig_y = _fig_reserva_yacimiento(yac, df_yac, col_valor, unidad, y_max_yacimientos)
                st.plotly_chart(fig_y, use_container_width=True)

    tabla_desglose = pd.DataFrame({
        "Categoría": orden_base,
        "Definición": [definiciones[c] for c in orden_base],
        f"Total ({unidad})": [vals_total[c] for c in orden_base],
    })
    total_3p = vals_total["3P"] if vals_total["3P"] else 1
    tabla_desglose["% del total 3P"] = tabla_desglose[f"Total ({unidad})"] / total_3p * 100

    col_tabla = st.container()
    with col_tabla:
        st.markdown("### Desglose total por categoría (3P)")
        _mostrar_tabla_reservas(
            tabla_desglose,
            columnas_numericas=[f"Total ({unidad})"],
            columnas_pct=["% del total 3P"],
        )
    st.caption("Notas: 1P = PDP + PDNP + PND  |  2P = 1P + PB  |  3P = 2P + POS")


# =========================================================
# SELECTOR GENERAL DE MÓDULO
# =========================================================

st.markdown(
    """
    <div class="main-module-nav-marker"></div>
    <style>
    div[data-testid="stElementContainer"]:has(.st-key-vista_principal) {
        width: 100% !important;
        max-width: 100% !important;
    }
    .st-key-vista_principal {
        background: linear-gradient(90deg, #2F363D 0%, #252B31 100%);
        border: 1px solid #1F252B;
        border-radius: 12px;
        padding: 12px 14px 10px 14px;
        margin: 4px 0 18px 0;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.18);
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box;
    }
    .st-key-vista_principal > label {
        color: #AEB7C2 !important;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .7px;
        margin-bottom: 8px;
    }
    .st-key-vista_principal label,
    .st-key-vista_principal p,
    .st-key-vista_principal span {
        color: #E5E7EB !important;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 13px;
        font-weight: 650;
    }
    .st-key-vista_principal [role="radiogroup"] {
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
        width: 100% !important;
        max-width: 100% !important;
    }
    .st-key-vista_principal [role="radio"] {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 999px;
        padding: 6px 10px;
        transition: all .15s ease-in-out;
    }
    .st-key-vista_principal [role="radio"][aria-checked="true"] {
        background: rgba(255,255,255,0.14);
        border-color: rgba(255,255,255,0.35);
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.12);
    }
    div[data-testid="stRadio"]:has(input[aria-label="Producción por pozo"]),
    div[data-testid="stRadio"]:has(input[aria-label="Mapa"]),
    div[data-testid="stRadio"]:has(input[aria-label="Presiones"]) {
        background: linear-gradient(90deg, #2F363D 0%, #252B31 100%);
        border: 1px solid #1F252B;
        border-radius: 12px;
        padding: 12px 14px 10px 14px;
        margin: 4px 0 18px 0;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.18);
    }
    div[data-testid="stRadio"]:has(input[aria-label="Producción por pozo"]) > label,
    div[data-testid="stRadio"]:has(input[aria-label="Mapa"]) > label,
    div[data-testid="stRadio"]:has(input[aria-label="Presiones"]) > label {
        color: #AEB7C2 !important;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .7px;
        margin-bottom: 8px;
    }
    div[data-testid="stRadio"]:has(input[aria-label="Producción por pozo"]) label,
    div[data-testid="stRadio"]:has(input[aria-label="Mapa"]) label,
    div[data-testid="stRadio"]:has(input[aria-label="Presiones"]) label,
    div[data-testid="stRadio"]:has(input[aria-label="Producción por pozo"]) p,
    div[data-testid="stRadio"]:has(input[aria-label="Mapa"]) p,
    div[data-testid="stRadio"]:has(input[aria-label="Presiones"]) p,
    div[data-testid="stRadio"]:has(input[aria-label="Producción por pozo"]) span,
    div[data-testid="stRadio"]:has(input[aria-label="Mapa"]) span,
    div[data-testid="stRadio"]:has(input[aria-label="Presiones"]) span {
        color: #E5E7EB !important;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 13px;
        font-weight: 650;
    }
    div[data-testid="stRadio"]:has(input[aria-label="Producción por pozo"]) [role="radiogroup"],
    div[data-testid="stRadio"]:has(input[aria-label="Mapa"]) [role="radiogroup"],
    div[data-testid="stRadio"]:has(input[aria-label="Presiones"]) [role="radiogroup"] {
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
    }
    div[data-testid="stRadio"]:has(input[aria-label="Producción por pozo"]) [role="radio"],
    div[data-testid="stRadio"]:has(input[aria-label="Mapa"]) [role="radio"],
    div[data-testid="stRadio"]:has(input[aria-label="Presiones"]) [role="radio"] {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 999px;
        padding: 6px 10px;
        transition: all .15s ease-in-out;
    }
    div[data-testid="stRadio"]:has(input[aria-label="Producción por pozo"]) [role="radio"][aria-checked="true"],
    div[data-testid="stRadio"]:has(input[aria-label="Mapa"]) [role="radio"][aria-checked="true"],
    div[data-testid="stRadio"]:has(input[aria-label="Presiones"]) [role="radio"][aria-checked="true"] {
        background: rgba(255,255,255,0.14);
        border-color: rgba(255,255,255,0.35);
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.12);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2F363D 0%, #252B31 100%);
        border-right: 1px solid #1F252B;
        box-shadow: 10px 0 24px rgba(15, 23, 42, 0.10);
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem;
    }
    section[data-testid="stSidebar"] .nav-sidebar-title {
        background: #20262D;
        border: 1px solid #111827;
        border-radius: 8px;
        color: #E5E7EB;
        font-size: 15px;
        font-weight: 850;
        letter-spacing: .2px;
        padding: 10px 12px;
        margin: 0 0 12px 0;
        font-family: "Segoe UI", Arial, sans-serif;
    }
    section[data-testid="stSidebar"] .nav-sidebar-section {
        color: #AEB7C2;
        font-size: 10px;
        font-weight: 850;
        text-transform: uppercase;
        letter-spacing: .7px;
        margin: 10px 0 8px 2px;
        font-family: "Segoe UI", Arial, sans-serif;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > label {
        display: none;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] p,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] span {
        color: #E5E7EB !important;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 13px;
        font-weight: 700;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] {
        gap: 4px;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radio"] {
        width: 100%;
        background: rgba(255,255,255,0.045);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        padding: 7px 10px;
        margin: 2px 0;
        transition: all .15s ease-in-out;
        justify-content: flex-start;
        align-items: center;
        text-align: left;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radio"] > div {
        margin-left: 0 !important;
        padding-left: 0 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radio"] p {
        margin-left: 0 !important;
        text-align: left !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radio"][aria-checked="true"] {
        background: rgba(255,255,255,0.14);
        border-color: rgba(255,255,255,0.35);
        box-shadow: inset 3px 0 0 #FF4B4B;
    }
    </style>
    <div class="nav-sidebar-title">Tamaulipas-Constituciones</div>
    <div class="nav-sidebar-section">Panel de Navegación</div>
    """,
    unsafe_allow_html=True
)

vista = st.radio(
    "Seleccionar opción",
    [
        "Producción por pozo",
        "Comparativa por pozo",
        "Mapa",
        "Campañas 2011-2020",
        "RMA 2011-2020",
        "Operación Campo",
        "Producción Campo",
        "Presiones",
        "Estadística",
        "Inyección",
        "Reservas"
    ],
    horizontal=True,
    key="vista_principal"
    )

# =========================================================
# FILTROS SOLO PARA PRODUCCIÓN POR POZO Y COMPARATIVA
# =========================================================
if vista in ["Producción por pozo", "Comparativa por pozo"]:

    st.markdown("<div class='filter-box'>", unsafe_allow_html=True)

    if vista == "Producción por pozo":
        f1, f_modo, f2 = st.columns([1.4, 1.5, 2.1])
    else:
        f1, f2 = st.columns([1.7, 2.3])

    with f1:
        yacs = sorted(df[COL_YAC].dropna().astype(str).unique())
        yac_sel = st.multiselect(
            "Filtro por Yacimiento",
            yacs,
            default=yacs,
            key="prod_yac_sel"
        )

    if vista == "Producción por pozo":
        with f_modo:
            modo_vista_pozo = st.radio(
                "Tipo de historia",
                ["Por terminación", "Historia completa por pozo"],
                horizontal=False,
                key="prod_modo_historia_pozo"
            )
    else:
        modo_vista_pozo = "Por terminación"

    df_prod_pozo_fisico = agregar_pozo_fisico(df, df_coord)
    df_base_filtro = (
        df_prod_pozo_fisico[df_prod_pozo_fisico[COL_YAC].astype(str).isin(yac_sel)].copy()
        if yac_sel else df_prod_pozo_fisico.copy()
    )

    if vista == "Producción por pozo":
        with f2:
            col_selector_pozo = (
                "POZO_FISICO"
                if modo_vista_pozo == "Historia completa por pozo"
                else COL_POZO
            )
            etiqueta_selector_pozo = (
                "Pozo"
                if col_selector_pozo == "POZO_FISICO"
                else "Pozo / Terminación"
            )

            pozos = sorted(df_base_filtro[col_selector_pozo].dropna().astype(str).unique())

            if not pozos:
                st.warning("No hay pozos para el yacimiento seleccionado.")
                st.stop()

            pozo_sel = st.selectbox(
                etiqueta_selector_pozo,
                pozos,
                key="prod_pozo_sel"
            )
            mostrar_seguimiento_pozo = st.checkbox(
                "Mostrar seguimiento",
                value=False,
                key="prod_mostrar_seguimiento_pozo"
            )

        # Base real del pozo seleccionado.
        if modo_vista_pozo == "Historia completa por pozo":
            df_pozo_raw = df_prod_pozo_fisico[
                df_prod_pozo_fisico["POZO_FISICO"].astype(str) == str(pozo_sel)
            ].copy()
        else:
            df_pozo_raw = df[
                df[COL_POZO].astype(str) == str(pozo_sel)
            ].copy()
    else:
        with f2:
            st.caption("Selecciona los pozos a comparar en el panel inferior.")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# BASE DE PRODUCCIÓN SIN FILTRO DE FECHAS
# Solo aplica para Producción por pozo y Comparativa
# =========================================================
if vista == "Producción por pozo":

    eventos_yac_historia = pd.DataFrame()

    if vista == "Producción por pozo" and modo_vista_pozo == "Historia completa por pozo":
        dfp_full, eventos_yac_historia = preparar_historia_pozo_fisico(df_pozo_raw)
    else:
        df_pozo_completo = completar_fechas_pozo(df_pozo_raw)
        dfp_full = calcular_columnas_produccion(df_pozo_completo)

    # Ya no se filtra por rango de fechas.
    # Se usa toda la historia disponible del pozo.
    dfp = dfp_full.copy()

    dfp = dfp.sort_values(COL_FECHA).reset_index(drop=True)

    if dfp.empty:
        st.warning("No hay datos para el pozo seleccionado.")
        st.stop()

    prod_total = (
        dfp[[COL_ACEITE_BBL, COL_AGUA_BBL, COL_GAS_PC, COL_INY_BBL]]
        .fillna(0)
        .sum(axis=1)
    )

    df_prod = dfp[prod_total > 0].copy()

    if df_prod.empty:
        df_prod = dfp.copy()

    first_row = df_prod.iloc[0]
    last_row = df_prod.iloc[-1]

    muestreos_agua = load_muestreos_agua()
    if modo_vista_pozo == "Historia completa por pozo":
        clave_pozo_sel = normalizar_clave_texto(pd.Series([pozo_sel])).iloc[0]
        claves_terminaciones_pozo = set(
            normalizar_clave_texto(df_pozo_raw[COL_POZO].dropna()).tolist()
        )
        clave_muestreos_pozo = normalizar_clave_texto(muestreos_agua["POZO"])
        clave_muestreos_terminacion = normalizar_clave_texto(muestreos_agua["TERMINACION"])
        df_muestreos_pozo = muestreos_agua[
            (clave_muestreos_pozo == clave_pozo_sel) |
            (clave_muestreos_terminacion.isin(claves_terminaciones_pozo))
        ].copy()
    else:
        clave_pozo_sel = normalizar_clave_texto(pd.Series([pozo_sel])).iloc[0]
        clave_muestreos_terminacion = normalizar_clave_texto(muestreos_agua["TERMINACION"])
        df_muestreos_pozo = muestreos_agua[
            clave_muestreos_terminacion == clave_pozo_sel
        ].copy()

    df_muestreos_pozo = df_muestreos_pozo.sort_values("FECHA MUESTREO").reset_index(drop=True)

    if mostrar_seguimiento_pozo:
        seguimiento_actividades = load_seguimiento_actividades()
        if not seguimiento_actividades.empty:
            clave_seg_terminacion = normalizar_clave_texto(seguimiento_actividades["TERMINACION"])
            clave_seg_pozo = normalizar_clave_texto(seguimiento_actividades["POZO"])
            clave_pozo_sel_seg = normalizar_clave_texto(pd.Series([pozo_sel])).iloc[0]

            if modo_vista_pozo == "Historia completa por pozo":
                claves_terminaciones_seguimiento = set(
                    normalizar_clave_texto(df_pozo_raw[COL_POZO].dropna()).tolist()
                )
                df_seguimiento_pozo = seguimiento_actividades[
                    clave_seg_terminacion.isin(claves_terminaciones_seguimiento) |
                    (clave_seg_pozo == clave_pozo_sel_seg)
                ].copy()
            else:
                df_seguimiento_pozo = seguimiento_actividades[
                    clave_seg_terminacion == clave_pozo_sel_seg
                ].copy()
        else:
            df_seguimiento_pozo = pd.DataFrame(columns=["TERMINACION", "YACIMIENTO", "POZO", "FECHA", "ACTIVIDAD"])
    else:
        df_seguimiento_pozo = pd.DataFrame(columns=["TERMINACION", "YACIMIENTO", "POZO", "FECHA", "ACTIVIDAD"])

    df_seguimiento_pozo = df_seguimiento_pozo.sort_values("FECHA").reset_index(drop=True)
# =========================================================
# KPIs
# =========================================================
if vista == "Producción por pozo":

    yacs_prod_txt = first_row.get(COL_YAC, "")
    yacs_iny_txt = "-"
    if modo_vista_pozo == "Historia completa por pozo":
        df_yacs_info = df_pozo_raw.copy()
        for col in [COL_ACEITE, COL_AGUA, COL_GAS, COL_INY]:
            df_yacs_info[col] = pd.to_numeric(df_yacs_info[col], errors="coerce").fillna(0)

        yacs_prod = [
            y for y in df_yacs_info.loc[
                (df_yacs_info[COL_ACEITE] > 0) |
                (df_yacs_info[COL_AGUA] > 0) |
                (df_yacs_info[COL_GAS] > 0),
                COL_YAC
            ].dropna().astype(str).str.strip().unique()
            if y and y.upper() not in ["NAN", "NONE"]
        ]
        yacs_iny = [
            y for y in df_yacs_info.loc[
                df_yacs_info[COL_INY] > 0,
                COL_YAC
            ].dropna().astype(str).str.strip().unique()
            if y and y.upper() not in ["NAN", "NONE"]
        ]

        yacs_prod_txt = ", ".join(sorted(set(yacs_prod))) if yacs_prod else "-"
        yacs_iny_txt = ", ".join(sorted(set(yacs_iny))) if yacs_iny else "-"

    st.markdown(
        f"<span class='small-note'>Pozo seleccionado: <b>{pozo_sel}</b> | "
        f"Producción: <b>{yacs_prod_txt}</b> | "
        f"Inyeccción: <b>{yacs_iny_txt}</b> | ",
        #f"Conta: <b>{first_row.get(COL_CONTA, '')}</b> | "
        #f"Registros reales cargados: <b>{len(dfp)}</b></span>",
        unsafe_allow_html=True
    )

    k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11 = st.columns(11)

    with k1:
        kpi_card(
            "Inicio producción",
            first_row[COL_FECHA].strftime("%d/%m/%Y"),
            "",
            #"#1F2937",
            "#1F77B4",
        )

    qo_validos = dfp[dfp[COL_QO] > 0]

    if not qo_validos.empty:
        ultimo_qo = qo_validos[COL_QO].iloc[-1]
        fecha_ultimo_qo = qo_validos[COL_FECHA].iloc[-1]
    else:
        ultimo_qo = 0
        fecha_ultimo_qo = None

    with k2:

        fecha_txt = (
            fecha_ultimo_qo.strftime("%d/%m/%Y")
            if fecha_ultimo_qo is not None
            else "-"
        )

        kpi_card(
            "Última producción",
            fecha_txt,
            "",
            #"#374151",
            "#1F77B4",
        )

    with k3:
        kpi_card(
            "Gasto inicial",
            f"{first_row[COL_QO]:,.1f}",
            "bpd",
            #"#1F2937",
            "#1F77B4",
        )

    # Último Qo mayor que cero
    qo_validos = dfp[dfp[COL_QO] > 0]
    qw_validos = dfp[dfp[COL_QW] > 0]
    qg_validos = dfp[dfp[COL_QG] > 0]
    aguaporc_validos = dfp[dfp[COL_WC] > 0]
    rga_validos = dfp[dfp[COL_RGA] > 0]

    ultimo_qo = (
        qo_validos[COL_QO].iloc[-1]
        if not qo_validos.empty
        else 0
    )

    ultimo_qw = (
        qw_validos[COL_QW].iloc[-1]
        if not qw_validos.empty
        else 0
    )

    ultimo_qg = (
        qg_validos[COL_QG].iloc[-1]
        if not qg_validos.empty
        else 0
    )

    ultimo_wcp = (
        aguaporc_validos[COL_WC].iloc[-1]
        if not aguaporc_validos.empty
        else 0
    )

    ultimo_rga = (
        rga_validos[COL_RGA].iloc[-1]
        if not rga_validos.empty
        else 0
    )

    with k4:
        kpi_card(
            "Último Gasto Aceite",
            f"{ultimo_qo:,.2f}",
            "bpd",
            #"#1F2937",
            "#1F77B4",
        )

    with k5:
        kpi_card(
            "Último Gasto Agua",
            f"{ultimo_qw:,.2f}",
            "bpd",
            #"#1F2937",
            "#1F77B4",
        )

    with k6:
        kpi_card(
            "% Agua",
            f"{ultimo_wcp:,.2f}",
            "%",
            #"#1F2937",
            "#1F77B4",
        )

    with k7:
        kpi_card(
            "Último Gasto Gas",
            f"{ultimo_qg:,.2f}",
            "mpcd",
            #"#1F2937",
            "#1F77B4",
        )

    with k8:
        kpi_card(
            "RGA",
            f"{ultimo_rga:,.2f}",
            "mpcd",
           # "#1F2937",
            "#1F77B4",
        )

    with k9:
        kpi_card(
            "Acumulada Aceite",
            f"{dfp[COL_NP].iloc[-1]:,.2f}",
            "mbl",
           # "#1F2937",
            "#1F77B4",
        )

    with k10:
        kpi_card(
            "Acumulada Agua",
            f"{dfp[COL_WP].iloc[-1]:,.2f}",
            "mbl",
            #"#1F2937",
            "#1F77B4",
        )

    with k11:
        kpi_card(
            "Acumulada Gas",
            f"{dfp[COL_GP].iloc[-1]:,.2f}",
            "mmpc",
            #"#1F2937",
            "#1F77B4",
        )

# =========================================================
# Comparativa FUNCIÓN PARA GRÁFICAS COMPARATIVAS
# =========================================================
def comparative_plot(data, y_col, title, y_title, pozos_sel_comp, semilog=False, normalizar_tiempo=False):

    fig = go.Figure()
    df_promedio = pd.DataFrame()

    x_label = "Tiempo normalizado" if normalizar_tiempo else "Fecha"

    for pozo in pozos_sel_comp:
        dfi = data[data[COL_POZO].astype(str) == str(pozo)].copy()
        dfi = dfi.sort_values(COL_FECHA).reset_index(drop=True)

        dfi_plot = dfi.copy()
        dfi_plot[y_col] = dfi_plot[y_col].replace(0, np.nan)

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

        y_values = dfi_plot[y_col].copy()

        if semilog:
            y_values = y_values.replace(0, np.nan)

        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="lines",
                name=str(pozo),
                line=dict(width=2.8),
                marker=dict(
                    size=1,
                    line=dict(color="white", width=0.8)
                ),
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
        title=dict(
            text=f"<b>{title}</b>",
            x=0.02,
            xanchor="left",
            font=dict(size=20, family="Arial Black", color="#111827")
        ),
        template="plotly_white",
        hovermode="x unified",
        height=450,
        plot_bgcolor="#F8F8FF",
        paper_bgcolor="white",
        font=dict(family="Arial", size=13, color="#111827"),
        margin=dict(l=70, r=40, t=90, b=70),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(
                size=14,
                family="Arial",
                color="#111827"
            ),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#D1D5DB",
            borderwidth=1
        )
    )

    fig.update_xaxes(
        title_text=f"<b>{x_label}</b>",
        tickformat="%d/%m/%Y" if not normalizar_tiempo else None,
        showgrid=True,
        gridcolor="#E5E7EB",
        gridwidth=0.7,
        zeroline=False,
        showline=True,
        linewidth=1.2,
        linecolor="#111827",
        mirror=True,
        ticks="outside",
        tickfont=dict(size=18, color="#111827"),
        title=dict(
        text=f"<b>{x_label}</b>",
        font=dict(
            size=18,
            color="#374151"
        )
    ),
        rangeslider=dict(visible=False)
    )

    fig.update_yaxes(
        title_text=f"<b>{y_title}</b>",
        type="log" if semilog else "linear",
        tickvals=[0.1, 1, 10, 100, 1000, 10000, 100000] if semilog else None,
        ticktext=["0.1", "1", "10", "100", "1,000", "10,000", "100,000"] if semilog else None,
        showgrid=True,
        gridcolor="#E5E7EB",
        gridwidth=0.7,
        zeroline=False,
        separatethousands=True,
        showline=True,
        linewidth=1.2,
        linecolor="#111827",
        mirror=True,
        ticks="outside",
        tickfont=dict(size=18, color="#111827"),
        title=dict(
            text=f"<b>{y_title}</b>",
            font=dict(
                size=18,
                color="#374151"
            )
        ),
    )

    return fig

# =========================================================
# VISTA POZO INDIVIDUAL
# =========================================================
if vista == "Producción por pozo":

    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    dfp["QB"] = dfp[COL_QO] + dfp[COL_QW]

    def marcar_inicios_yacimiento(fig):
        if eventos_yac_historia.empty:
            return

        colores_yac = [
            "#7E57C2",
            "#F39C12",
            "#16A085",
            "#C0392B",
            "#2E86C1",
            "#6D4C41"
        ]
        yacs_eventos = list(eventos_yac_historia[COL_YAC].astype(str).drop_duplicates())
        color_por_yac = {
            yac: colores_yac[i % len(colores_yac)]
            for i, yac in enumerate(yacs_eventos)
        }
        eventos_ordenados = eventos_yac_historia.copy()
        eventos_ordenados["FECHA_ETIQUETA"] = pd.to_datetime(
            eventos_ordenados["FECHA_INICIO"]
        ).dt.normalize()
        eventos_ordenados = eventos_ordenados.sort_values(
            ["FECHA_ETIQUETA", "TIPO_EVENTO", COL_YAC]
        )
        niveles_por_fecha = {}

        for i, (_, evento) in enumerate(eventos_ordenados.iterrows()):
            yac_txt = str(evento[COL_YAC])
            tipo_evento = str(evento.get("TIPO_EVENTO", "Producción"))
            fecha_inicio = evento["FECHA_INICIO"]
            fecha_etiqueta = evento["FECHA_ETIQUETA"]
            color = color_por_yac.get(yac_txt, colores_yac[i % len(colores_yac)])
            es_inyeccion = tipo_evento == "Inyección"
            texto_evento = "Iny" if es_inyeccion else "Prod"
            nivel_fecha = niveles_por_fecha.get(fecha_etiqueta, 0)
            niveles_por_fecha[fecha_etiqueta] = nivel_fecha + 1
            y_etiqueta = -0.11 - (nivel_fecha * 0.09)

            fig.add_vline(
                x=fecha_inicio,
                line_width=2,
                line_dash="dot" if es_inyeccion else "dash",
                line_color=color
            )
            fig.add_annotation(
                x=fecha_inicio,
                y=y_etiqueta,
                xref="x",
                yref="paper",
                text=f"{texto_evento} {yac_txt}",
                showarrow=False,
                font=dict(size=12, color=color, family="Arial Black"),
                bgcolor="rgba(255,255,255,0.85)",
                bordercolor=color,
                borderwidth=1,
                yanchor="top"
            )

    def marcar_eventos_seguimiento(fig):
        if df_seguimiento_pozo.empty:
            return

        eventos = df_seguimiento_pozo.copy()
        eventos["FECHA_EVENTO"] = pd.to_datetime(eventos["FECHA"]).dt.normalize()
        eventos = eventos.sort_values(["FECHA_EVENTO", "ACTIVIDAD"]).reset_index(drop=True)

        colores_evento = [
            "#111827",
            "#7C3AED",
            "#F97316",
            "#0891B2",
            "#BE123C",
            "#4B5563",
        ]
        niveles_por_fecha = {}

        for i, (_, evento) in enumerate(eventos.iterrows()):
            fecha_evento = evento["FECHA_EVENTO"]
            actividad = str(evento["ACTIVIDAD"]).strip()
            terminacion_evento = str(evento.get("TERMINACION", "")).strip()
            pozo_evento = str(evento.get("POZO", "")).strip()
            yac_evento = str(evento.get("YACIMIENTO", "")).strip()
            color = colores_evento[i % len(colores_evento)]
            nivel_fecha = niveles_por_fecha.get(fecha_evento, 0)
            niveles_por_fecha[fecha_evento] = nivel_fecha + 1
            y_etiqueta = 0.96 - (nivel_fecha * 0.075)
            y_etiqueta = max(y_etiqueta, 0.70)

            fig.add_vline(
                x=fecha_evento,
                line_width=1.25,
                line_dash="dot",
                line_color=color,
                opacity=0.38,
            )
            continue
            fig.add_annotation(
                x=fecha_evento,
                y=y_etiqueta,
                xref="x",
                yref="paper",
                text=f"📌 {actividad}",
                showarrow=True,
                arrowhead=2,
                arrowsize=0.7,
                arrowwidth=1,
                arrowcolor=color,
                ax=0,
                ay=-22,
                font=dict(size=11, color="#FFFFFF", family="Arial"),
                bgcolor=color,
                bordercolor="#FFFFFF",
                borderwidth=1,
                borderpad=4,
                align="center",
                hovertext=(
                    f"Actividad: {actividad}<br>"
                    f"Fecha: {fecha_evento:%d/%m/%Y}<br>"
                    f"Terminación: {terminacion_evento}<br>"
                    f"Pozo: {pozo_evento}<br>"
                    f"Yacimiento: {yac_evento}"
                ),
            )

        fig.add_trace(
            go.Scatter(
                x=eventos["FECHA_EVENTO"],
                y=[0] * len(eventos),
                mode="markers",
                name="Seguimiento",
                marker=dict(
                    symbol="diamond",
                    size=9,
                    color="#111827",
                    line=dict(color="#FFFFFF", width=1.2),
                ),
                customdata=eventos[["ACTIVIDAD", "TERMINACION", "POZO", "YACIMIENTO"]],
                hovertemplate=
                    "<b>Actividad:</b> %{customdata[0]}<br>" +
                    "<b>Fecha:</b> %{x|%d/%m/%Y}<br>" +
                    "<b>Terminación:</b> %{customdata[1]}<br>" +
                    "<b>Pozo:</b> %{customdata[2]}<br>" +
                    "<b>Yacimiento:</b> %{customdata[3]}<br>" +
                    "<extra></extra>",
                showlegend=True,
            ),
            secondary_y=False
        )

    fig1.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_QO],
            mode="lines+markers",
            name="Qo (bpd)",
            line=dict(width=2, color="#27AE60"),
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
            line=dict(width=2, color="#008000"),
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
            line=dict(width=2, color="#FF0000"),
            marker=dict(size=3),
            connectgaps=False
        ),
        secondary_y=True
    )

    fig1.add_trace(go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp["QB"],

            name="Qb (bpd)",

            mode="lines",

            line=dict(
                color="#000000",
                width=2,
                dash="dot"
            ),

            connectgaps=False
    ))

    fig1.update_layout(
        title="Gasto de aceite, % Agua, Acumulada de aceite y Gasto de gas",
        template="plotly_white",
        hovermode="x unified",
        #height=520,
        height=500,
        legend=dict(orientation="h", y=1.02, font=dict(
        size=14,
        color="black",
        family="Arial Black"
        )),
        margin=dict(l=35, r=35, t=60, b=150)
    )

    fig1.update_xaxes(title_text="<b>Fecha</b>", title_font=dict(size=22), 
        tickformat="%d/%m/%Y", tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
        linewidth=1,
        linecolor='black')

    fig1.update_yaxes(title_text="<b>Qo (bpd) / Qb (bpd) / % Agua</b>",title_font=dict(size=22),
        secondary_y=False, tickfont=dict(
        size=16,
        color="black",      
        family="Arial Black"
        ),showline=True,
        linewidth=1,
        showgrid=False,      # quita líneas horizontales
        zeroline=True,       # deja línea en cero
        zerolinewidth=1,
        zerolinecolor="black",
        linecolor='black')

    fig1.update_yaxes(title_text="Np (mbl) / Qg (mpcd)", title_font=dict(size=22),
        secondary_y=True,tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
        linewidth=1,
        showgrid=False,      # quita líneas horizontales
        zeroline=True,       # deja línea en cero
        zerolinewidth=1,
        zerolinecolor="black",
        linecolor='black')

    marcar_inicios_yacimiento(fig1)
    marcar_eventos_seguimiento(fig1)

    st.plotly_chart(fig1, use_container_width=True)

    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    df_iny_yac = preparar_inyeccion_por_yacimiento(df_pozo_raw)
    yacs_iny_graf = (
        sorted(df_iny_yac[COL_YAC].dropna().astype(str).unique())
        if COL_YAC in df_iny_yac.columns and not df_iny_yac.empty
        else []
    )
    colores_iny_yac = [
        "#00ACC1",
        "#8E44AD",
        "#F39C12",
        "#16A085",
        "#D35400",
        "#2E86C1"
    ]

    fig2.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_QW],
            mode="lines+markers",
            name="Qw (bpd)",
            line=dict(width=2, color="#3498DB"),
            marker=dict(size=3),
            fill="tozeroy",
            fillcolor="rgba(52,152,219,0.20)",
            connectgaps=False
        ),
        secondary_y=False
    )

    if not df_muestreos_pozo.empty:
        fig2.add_trace(
            go.Scatter(
                x=df_muestreos_pozo["FECHA MUESTREO"],
                y=df_muestreos_pozo["% AGUA LAB"],
                mode="markers",
                name="% Agua Lab",
                marker=dict(
                    size=6,
                    color="#0000FF",
                    symbol="circle",
                    line=dict(color="black", width=1)
                ),
                customdata=df_muestreos_pozo[["TERMINACION", "POZO"]],
                hovertemplate=
                    "<b>% Agua Lab:</b> %{y:,.2f}%<br>" +
                    "<b>Fecha:</b> %{x|%d/%m/%Y}<br>" +
                    "<b>Terminacion:</b> %{customdata[0]}<br>" +
                    "<b>Pozo:</b> %{customdata[1]}<br>" +
                    "<extra></extra>"
            ),
            secondary_y=False
        )

    fig2.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_WP],
            mode="lines+markers",
            name="Wp (mbl)",
            line=dict(width=2, color="#154360"),
            marker=dict(size=3),
            connectgaps=False
        ),
        secondary_y=True
    )

    fig2.update_layout(
        title="Producción Agua / Muestreos % Agua / Acumulada de Agua",
        template="plotly_white",
        hovermode="x unified",
        height=520,
        legend=dict(orientation="h", y=1.02,  font=dict(
        size=14,
        color="black",
        family="Arial Black"
        )),
        margin=dict(l=35, r=35, t=60, b=150)
    )

    fig2.update_xaxes(title_text="Fecha", tickformat="%d/%m/%Y", title_font=dict(size=22), tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
        linewidth=1,
        linecolor='black')

    fig2.update_yaxes(title_text="Qw (bpd) / % Agua", title_font=dict(size=22),
        secondary_y=False, tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
        showgrid=False,      # quita líneas horizontales
        zeroline=True,       # deja línea en cero
        zerolinewidth=1,
        zerolinecolor="black",
        linewidth=1,   
        range=[0, None],    
        linecolor='black')

    fig2.update_yaxes(title_text="Wp (mbl)", title_font=dict(size=22),
        secondary_y=True, tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
        linewidth=1,
        showgrid=False,      # quita líneas horizontales
        zeroline=True,       # deja línea en cero
        zerolinewidth=1,
        range=[0, None],
        zerolinecolor="black",
        linecolor='black')

    marcar_inicios_yacimiento(fig2)

    st.plotly_chart(fig2, use_container_width=True)

    fig_iny = make_subplots(specs=[[{"secondary_y": True}]])

    fig_iny.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_QIN],
            mode="lines+markers",
            name="Qiny total (bpd)",
            line=dict(width=3, color="cyan"),
            marker=dict(size=3),
            fill="tozeroy",
            fillcolor="rgba(0,172,193,0.18)",
            connectgaps=False
        ),
        secondary_y=False
    )

    for i, yac in enumerate(yacs_iny_graf):
        dfi_yac = df_iny_yac[df_iny_yac[COL_YAC].astype(str) == yac].copy()
        color_yac = colores_iny_yac[i % len(colores_iny_yac)]

        fig_iny.add_trace(
            go.Scatter(
                x=dfi_yac[COL_FECHA],
                y=dfi_yac[COL_QIN],
                mode="lines+markers",
                name=f"Qiny {yac} (bpd)",
                line=dict(width=2, color=color_yac, dash="dash"),
                marker=dict(size=4),
                connectgaps=False,
                hovertemplate=
                    "<b>Fecha:</b> %{x|%d/%m/%Y}<br>" +
                    f"<b>Yacimiento:</b> {yac}<br>" +
                    "<b>Qiny:</b> %{y:,.1f} bpd<br>" +
                    "<extra></extra>"
            ),
            secondary_y=False
        )

    fig_iny.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_WINJ],
            mode="lines+markers",
            name="Winj total (mbl)",
            line=dict(width=3, color="#00ACC1"),
            marker=dict(size=3),
            connectgaps=False
        ),
        secondary_y=True
    )

    for i, yac in enumerate(yacs_iny_graf):
        dfi_yac = df_iny_yac[df_iny_yac[COL_YAC].astype(str) == yac].copy()
        color_yac = colores_iny_yac[i % len(colores_iny_yac)]

        fig_iny.add_trace(
            go.Scatter(
                x=dfi_yac[COL_FECHA],
                y=dfi_yac[COL_WINJ],
                mode="lines+markers",
                name=f"Winj {yac} (mbl)",
                line=dict(width=2, color=color_yac, dash="dot"),
                marker=dict(size=4),
                connectgaps=False,
                hovertemplate=
                    "<b>Fecha:</b> %{x|%d/%m/%Y}<br>" +
                    f"<b>Yacimiento:</b> {yac}<br>" +
                    "<b>Winj:</b> %{y:,.1f} mbl<br>" +
                    "<extra></extra>"
            ),
            secondary_y=True
        )

    fig_iny.update_layout(
        title="Agua inyectada y acumulada de inyección",
        template="plotly_white",
        hovermode="x unified",
        height=520,
        legend=dict(orientation="h", y=1.02,  font=dict(
        size=14,
        color="black",
        family="Arial Black"
        )),
        margin=dict(l=35, r=35, t=60, b=150)
    )

    fig_iny.update_xaxes(title_text="Fecha", tickformat="%d/%m/%Y", title_font=dict(size=22), tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
        linewidth=1,
        linecolor='black')

    fig_iny.update_yaxes(title_text="Qiny (bpd)", title_font=dict(size=22),
        secondary_y=False, tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
        showgrid=False,
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor="black",
        linewidth=1,
        range=[0, None],
        linecolor='black')

    fig_iny.update_yaxes(title_text="Winj (mbl)", title_font=dict(size=22),
        secondary_y=True, tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
        linewidth=1,
        showgrid=False,
        zeroline=True,
        zerolinewidth=1,
        range=[0, None],
        zerolinecolor="black",
        linecolor='black')

    marcar_inicios_yacimiento(fig_iny)

    st.plotly_chart(fig_iny, use_container_width=True)

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
            line=dict(width=2, color="#641E16"),
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
        legend=dict(orientation="h", y=1.02,  font=dict(
        size=14,
        color="black",
        family="Arial Black"
        )),
        margin=dict(l=35, r=35, t=60, b=150)
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
        range=[0, None],
        showgrid=False,      # quita líneas horizontales
        zeroline=True,       # deja línea en cero
        zerolinewidth=1,
        zerolinecolor="black",
        linecolor='black')

    fig3.update_yaxes(title_text="Gp (mmpc)", title_font=dict(size=22),
        secondary_y=True, tickfont=dict(
        size=16,
        color="black",
        family="Arial Black"
        ),showline=True,
        linewidth=1,
        showgrid=False,      # quita líneas horizontales
        zeroline=True,       # deja línea en cero
        zerolinewidth=1,
        zerolinecolor="black",
        linecolor='black')

    marcar_inicios_yacimiento(fig3)

    st.plotly_chart(fig3, use_container_width=True)

    # =====================================================
# TABLA PRODUCCIÓN DEL POZO
# =====================================================

    st.markdown(
        """
        <div style="
            background-color:#F8F9F9;
            padding:10px;
            border-radius:8px;
            border:1px solid #D5D8DC;
            margin-top:10px;
        ">
        <h4 style='color:#1F618D;'>
        Tabla histórica de producción
        </h4>
        </div>
        """,
        unsafe_allow_html=True
    )

    cols_tabla = [
        COL_FECHA,
        COL_DIAS,
        COL_QO,
        COL_QW,
        COL_QIN,
        COL_QG,
        COL_WC,
        COL_RGA,
        COL_NP,
        COL_WP,
        COL_WINJ,
        COL_GP
    ]

    # Solo columnas que existan
    cols_tabla = [
        c for c in cols_tabla
        if c in dfp.columns
    ]

    tabla_pozo = (
        dfp[cols_tabla]
        .sort_values(COL_FECHA, ascending=False)
        .copy()
    )

    # Formato numérico
    tabla_pozo = tabla_pozo.style.format({
        COL_QO: "{:,.1f}",
        COL_QW: "{:,.1f}",
        COL_QIN: "{:,.1f}",
        COL_QG: "{:,.1f}",
        COL_WC: "{:,.1f}",
        COL_RGA: "{:,.0f}",
        COL_NP: "{:,.1f}",
        COL_WP: "{:,.1f}",
        COL_WINJ: "{:,.1f}",
        COL_GP: "{:,.1f}",
    })

    st.dataframe(
        tabla_pozo,
        use_container_width=True,
        height=350
    )
    
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
    default=[pozos_comp[0]] if pozos_comp else []
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
            colores_comp = px.colors.qualitative.Plotly
            color_por_pozo_comp = {
                str(pozo).strip(): colores_comp[i % len(colores_comp)]
                for i, pozo in enumerate(pozos_sel_comp)
            }

            st.plotly_chart(
                comparative_plot(
                    df_comp,
                    COL_QO,
                    "Producción de aceite por pozo",
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
                    "RGA por pozo",
                    "RGA (pc/bl)",
                    pozos_sel_comp,
                    semilog=usar_semilog,
                    normalizar_tiempo=normalizar_tiempo
                ),
                use_container_width=True
            )

            # =========================
            # =========================
            # 3. COMPARATIVO %Agua
            # =========================
            fig_agua = make_subplots(specs=[[{"secondary_y": False}]])

            for pozo in pozos_sel_comp:

                dfi = df_comp[
                    df_comp[COL_POZO].astype(str).str.strip() == str(pozo).strip()
                ].copy()

                dfi = dfi.sort_values(COL_FECHA).reset_index(drop=True)

                if dfi.empty:
                    continue

                dfi[COL_TIEMPO_NORM] = range(len(dfi))

                if normalizar_tiempo:
                    x_values = dfi[COL_TIEMPO_NORM]
                    hover_x = "Mes normalizado: %{x}"
                    x_title = "Tiempo normalizado, meses"
                else:
                    x_values = dfi[COL_FECHA]
                    hover_x = "Fecha: %{x|%d/%m/%Y}"
                    x_title = "Fecha"

                fig_agua.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=dfi[COL_WC].replace(0, np.nan),
                        mode="lines+markers",
                        name=f"{pozo}",
                        line=dict(width=3),
                        marker=dict(size=4),
                        connectgaps=False,
                        hovertemplate=
                            f"<b>Pozo: {pozo}</b><br>" +
                            hover_x + "<br>" +
                            "% Agua: %{y:,.1f}%<extra></extra>"
                    ),
                    secondary_y=False
                )

            fig_agua.update_layout(
                title=dict(
                    text=f"<b>Corte de agua por pozo</b>",
                    x=0.02,
                    xanchor="left",
                    font=dict(size=20, family="Arial Black", color="#111827")
                ),
                template="plotly_white",
                hovermode="x unified",
                height=450,
                plot_bgcolor="#F8F8FF",
                paper_bgcolor="white",
                font=dict(family="Arial", size=13, color="#111827"),
                margin=dict(l=70, r=40, t=90, b=70),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5,
                    font=dict(
                        size=14,
                        family="Arial",
                        color="#111827"
                    ),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="#D1D5DB",
                    borderwidth=1
                )
            )

            fig_agua.update_xaxes(
                title_text=f"<b>{x_title}</b>",
                tickformat="%d/%m/%Y" if not normalizar_tiempo else None,
                showgrid=True,
                gridcolor="#E5E7EB",
                gridwidth=0.7,
                zeroline=False,
                showline=True,
                linewidth=1.2,
                linecolor="#111827",
                mirror=True,
                ticks="outside",
                tickfont=dict(size=18, color="#111827"),
                title=dict(
                text=f"<b>{x_title}</b>",
                font=dict(
                    size=18,
                    color="#374151"
                )
            ),
                rangeslider=dict(visible=False)
            )

            fig_agua.update_yaxes(
                title_text=f"<b>Corte de agua (%)</b>",
                
                showgrid=True,
                gridcolor="#E5E7EB",
                gridwidth=0.7,
                zeroline=False,
                separatethousands=True,
                showline=True,
                linewidth=1.2,
                linecolor="#111827",
                mirror=True,
                ticks="outside",
                tickfont=dict(size=18, color="#111827"),
                title=dict(
                    text=f"<b>Corte de agua (%)</b>",
                    font=dict(
                        size=18,
                        color="#374151"
                    )
                ),
            )
            if not normalizar_tiempo:
                fecha_min = df_comp[COL_FECHA].min()
                fecha_max = df_comp[COL_FECHA].max()
                fig_agua.update_xaxes(range=[fecha_min, fecha_max])
            
            st.plotly_chart(fig_agua, use_container_width=True)

            # =========================
            # 4. COMPARATIVO AGUA DE INYECCIÓN
            # =========================
            fig_iny = go.Figure()

            for pozo in pozos_sel_comp:

                dfi = df_comp[
                    df_comp[COL_POZO].astype(str).str.strip() == str(pozo).strip()
                ].copy()

                dfi = dfi.sort_values(COL_FECHA).reset_index(drop=True)

                if dfi.empty:
                    continue

                dfi[COL_TIEMPO_NORM] = range(len(dfi))

                if normalizar_tiempo:
                    x_values = dfi[COL_TIEMPO_NORM]
                    hover_x = "Mes normalizado: %{x}"
                    x_title = "Tiempo normalizado, meses"
                else:
                    x_values = dfi[COL_FECHA]
                    hover_x = "Fecha: %{x|%d/%m/%Y}"
                    x_title = "Fecha"

                fig_iny.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=dfi[COL_QIN].replace(0, np.nan),
                        mode="lines+markers",
                        name=f"{pozo}",
                        line=dict(width=3),
                        marker=dict(size=4),
                        connectgaps=False,
                        hovertemplate=
                            f"<b>Pozo: {pozo}</b><br>" +
                            hover_x + "<br>" +
                            "Qiny: %{y:,.2f} bpd<extra></extra>"
                    )
                )

            fig_iny.update_layout(
                title=dict(
                    text=f"<b>Agua Inyectada (bpd)</b>",
                    x=0.02,
                    xanchor="left",
                    font=dict(size=20, family="Arial Black", color="#111827")
                ),
                template="plotly_white",
                hovermode="x unified",
                height=450,
                plot_bgcolor="#F8F8FF",
                paper_bgcolor="white",
                font=dict(family="Arial", size=13, color="#111827"),
                margin=dict(l=70, r=40, t=90, b=70),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5,
                    font=dict(
                        size=14,
                        family="Arial",
                        color="#111827"
                    ),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="#D1D5DB",
                    borderwidth=1
                )
            )

            fig_iny.update_xaxes(
                title_text=f"<b>{x_title}</b>",
                tickformat="%d/%m/%Y" if not normalizar_tiempo else None,
                showgrid=True,
                gridcolor="#E5E7EB",
                gridwidth=0.7,
                zeroline=False,
                showline=True,
                linewidth=1.2,
                linecolor="#111827",
                mirror=True,
                ticks="outside",
                tickfont=dict(size=18, color="#111827"),
                title=dict(
                text=f"<b>{x_title}</b>",
                font=dict(
                    size=18,
                    color="#374151"
                )
            ),
                rangeslider=dict(visible=False)
            )

            fig_iny.update_yaxes(
                title_text=f"<b>Agua Inyectada (bpd)</b>",
                
                showgrid=True,
                gridcolor="#E5E7EB",
                gridwidth=0.7,
                zeroline=False,
                separatethousands=True,
                showline=True,
                linewidth=1.2,
                linecolor="#111827",
                mirror=True,
                ticks="outside",
                tickfont=dict(size=18, color="#111827"),
                title=dict(
                    text=f"<b>Agua Inyectada (bpd)</b>",
                    font=dict(
                        size=18,
                        color="#374151"
                    )
                ),
            )

            if not normalizar_tiempo:
                fecha_min = df_comp[COL_FECHA].min()
                fecha_max = df_comp[COL_FECHA].max()
                fig_iny.update_xaxes(range=[fecha_min, fecha_max])
            st.plotly_chart(fig_iny, use_container_width=True)

            # =========================
            # 5. COMPARATIVO PRESIÓN
            # =========================
            pres_comp = load_presiones()

            if not pres_comp.empty:
                pres_comp = pres_comp[
                    pres_comp["TERMINACION"].astype(str).str.strip().isin(pozos_sel_comp)
                ].copy()

                pres_comp["FECHA"] = pd.to_datetime(pres_comp["FECHA"], errors="coerce")
                pres_comp["PRESION"] = pd.to_numeric(pres_comp["PRESION"], errors="coerce")
                pres_comp = pres_comp.dropna(subset=["FECHA", "PRESION"]).copy()
                pres_comp = pres_comp.sort_values(["TERMINACION", "FECHA"])

                if not pres_comp.empty:
                    fig_pres = go.Figure()

                    for pozo in pozos_sel_comp:
                        dfi_pres = pres_comp[
                            pres_comp["TERMINACION"].astype(str).str.strip() == str(pozo).strip()
                        ].copy()

                        if dfi_pres.empty:
                            continue

                        if normalizar_tiempo:
                            dfi_pres[COL_TIEMPO_NORM] = range(len(dfi_pres))
                            x_values = dfi_pres[COL_TIEMPO_NORM]
                            hover_x = "Medición normalizada: %{x}"
                            x_title = "Tiempo normalizado, mediciones"
                        else:
                            x_values = dfi_pres["FECHA"]
                            hover_x = "Fecha: %{x|%d/%m/%Y}"
                            x_title = "Fecha"

                        fig_pres.add_trace(
                            go.Scatter(
                                x=x_values,
                                y=dfi_pres["PRESION"],
                                mode="markers",
                                name=f"{pozo}",
                                marker=dict(
                                    size=7,
                                    color=color_por_pozo_comp.get(str(pozo).strip())
                                ),
                                connectgaps=False,
                                hovertemplate=
                                    f"<b>Pozo: {pozo}</b><br>" +
                                    hover_x + "<br>" +
                                    "Presión: %{y:,.2f}<extra></extra>"
                            )
                        )

                    fig_pres.update_layout(
                        title=dict(
                            text="<b>Presión por pozo</b>",
                            x=0.02,
                            xanchor="left",
                            font=dict(size=20, family="Arial Black", color="#111827")
                        ),
                        template="plotly_white",
                        hovermode="x unified",
                        height=450,
                        plot_bgcolor="#F8F8FF",
                        paper_bgcolor="white",
                        font=dict(family="Arial", size=13, color="#111827"),
                        margin=dict(l=70, r=40, t=90, b=70),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=14, family="Arial", color="#111827"),
                            bgcolor="rgba(255,255,255,0.8)",
                            bordercolor="#D1D5DB",
                            borderwidth=1
                        )
                    )

                    fig_pres.update_xaxes(
                        title_text=f"<b>{x_title}</b>",
                        tickformat="%d/%m/%Y" if not normalizar_tiempo else None,
                        showgrid=True,
                        gridcolor="#E5E7EB",
                        gridwidth=0.7,
                        zeroline=False,
                        showline=True,
                        linewidth=1.2,
                        linecolor="#111827",
                        mirror=True,
                        ticks="outside",
                        tickfont=dict(size=18, color="#111827"),
                        title=dict(
                            text=f"<b>{x_title}</b>",
                            font=dict(size=18, color="#374151")
                        ),
                        rangeslider=dict(visible=False)
                    )

                    fig_pres.update_yaxes(
                        title_text="<b>Presión</b>",
                        showgrid=True,
                        gridcolor="#E5E7EB",
                        gridwidth=0.7,
                        zeroline=False,
                        separatethousands=True,
                        showline=True,
                        linewidth=1.2,
                        linecolor="#111827",
                        mirror=True,
                        ticks="outside",
                        tickfont=dict(size=18, color="#111827"),
                        title=dict(
                            text="<b>Presión</b>",
                            font=dict(size=18, color="#374151")
                        )
                    )

                    if not normalizar_tiempo:
                        fig_pres.update_xaxes(range=[fecha_min, fecha_max])

                    st.plotly_chart(fig_pres, use_container_width=True)
                else:
                    st.info("No hay datos de presión para los pozos seleccionados.")
            else:
                st.info("No hay datos disponibles en la tabla Presiones.")

        else:
            st.warning("No hay datos disponibles para los pozos seleccionados.")

    else:
        st.info("Selecciona uno o más pozos para generar el comparativo.")


# VISTA MAPA DE BURBUJAS
# =========================================================
elif vista == "Mapa":
    mapa_burbujas(df, df_coord, mostrar_instalaciones_gis=True)
elif vista == "Campañas 2011-2020":
    analisis_term()
elif vista == "RMA 2011-2020":
    analisis_rma()
elif vista == "Producción Campo":
    produccion_total_campo()
elif vista == "Presiones":
    mapa_presion()
elif vista == "Operación Campo":
    operacion_campo()
elif vista == "Estadística":
    estadistica()
elif vista == "Inyección":
    inyeccion()
elif vista == "Reservas":
    reservas()

#st.caption("Desarrollado en Python + Streamlit.")
