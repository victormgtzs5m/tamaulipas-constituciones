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

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
st.set_page_config(
    page_title="Campo Tamaulipas Constituciones",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.cache_data.clear()
# =========================================================
# RUTA DE LA BASE DE DATOS
# Cambia esta ruta si tu archivo .db está en otra carpeta.
# =========================================================

# Ruta de la base datos
ruta_db = "prodcoord.db"

# Tablas
TABLA_PROD = "Produccion"
TABLA_COORD = "Coord"
TABLA_CONTORNO = "Contorno"
TABLA_ASIGNACION = "Asignacion"
TABLA_TERM = "TERM"
TABLA_RMA = "RMA"
TABLA_ESTADO_POZOS = "Estado"
TABLA_PRESIONES = "Presiones"
TABLA_OPERACION = "Operacion"
TABLA_EVENTOS = "Eventos"

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

    transformer = Transformer.from_crs(
        "EPSG:32614",   # UTM zona 14N WGS84
        "EPSG:4326",    # Lat/Lon
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
                nlags=6,
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

            #zi_masked = np.clip(zi_masked, zmin, zmax)

            return xi, yi, zi_masked, datos, zmin, zmax, unidad

        except Exception as e:
            st.warning(f"No se pudo generar el heatmap con Kriging: {e}")
            return None

def mapa_burbujas(df_base: pd.DataFrame, df_coord: pd.DataFrame, modo_mapa="TERM", pozos_destacados=None):
    """Mapa de burbujas con opción Todos desde Operativas y mapas por yacimiento sin modificar."""

    st.markdown(
        "<div class='section-title'>Mapa de burbujas y radios de drene</div>",
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

    else:
        x_col = "CIMA X UTM"
        y_col = "CIMA Y UTM"

        if x_col not in mapa.columns or y_col not in mapa.columns:
            st.error("No existen las columnas CIMA X UTM y CIMA Y UTM en la tabla Coord.")
            return

    mapa[x_col] = pd.to_numeric(mapa[x_col], errors="coerce")
    mapa[y_col] = pd.to_numeric(mapa[y_col], errors="coerce")
    mapa = mapa.dropna(subset=[x_col, y_col]).copy()

    with c2:

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

    with c3:
        pozos_mapa = sorted(mapa["POZO"].dropna().astype(str).unique())

        pozo_zoom = st.selectbox(
            "Zoom a pozo",
            options=["Todos"] + pozos_mapa,
            key=f"pozo_zoom_mapa_{modo_mapa}_{yac_mapa}"
        )

    with c4:

        if ver_todos_campo:

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

            filtro_term = st.selectbox(
                "Pozos perforados históricos TERM",
                ["Todos", "Solo perforados 2011-2020", "Solo no perforados"],
                key=f"filtro_term_mapa_{modo_mapa}_{yac_mapa}"
            )

            if filtro_term == "Solo perforados 2011-2020":
                mapa = mapa[mapa["PERFORADO_TERM"] == "Sí"].copy()

            elif filtro_term == "Solo no perforados":
                mapa = mapa[mapa["PERFORADO_TERM"] == "No"].copy()

    c5, c6 = st.columns([1, 3])

    with c5:
        mostrar_nombres = st.checkbox(
            "Mostrar nombres de pozos",
            value=True,
            key=f"mostrar_nombres_mapa_{modo_mapa}_{yac_mapa}"
        )

    with c6:

        opciones_tipo_mapa = ["Mapa UTM", "Mapa GIS"]

        if not ver_todos_campo:
            opciones_tipo_mapa.append("Heatmap")

        tipo_mapa = st.radio(
            "Tipo de mapa",
            opciones_tipo_mapa,
            horizontal=True,
            key=f"tipo_mapa_burbujas_{modo_mapa}_{yac_mapa}"
        )
        

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
    color_burbuja = color_variable.get(variable, "green")

    if not ver_todos_campo:

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

    # =====================================================
    # MAPA GIS
    # =====================================================
    if tipo_mapa == "Mapa GIS":

        mapa_gis = convertir_utm_a_latlon(mapa, x_col, y_col)

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

        fig_gis.update_layout(
            title=(
                "<b>Mapa GIS operativo - Campo completo</b>"
                if ver_todos_campo
                else f"<b>Mapa GIS de burbujas - {yac_mapa}</b>"
            ),
            mapbox=dict(
                style="open-street-map",
                center=dict(
                    lat=mapa_gis["LAT"].mean(),
                    lon=mapa_gis["LON"].mean()
                ),
                zoom=12
            ),
            height=850,
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

        st.plotly_chart(
            fig_gis,
            use_container_width=True,
            config={
                "scrollZoom": True,
                "displaylogo": False
            }
        )

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

        st.plotly_chart(
            fig_heat,
            use_container_width=True,
            config={
                "scrollZoom": True,
                "displaylogo": False,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"]
            }
        )

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


    if not ver_todos_campo:

        theta = np.linspace(0, 2 * np.pi, 180)

        for _, row in mapa.iterrows():

            radio = row.get("RADIO DRENE")

            if (
                pd.notna(radio) and radio > 0 and
                pd.notna(row.get(x_col)) and
                pd.notna(row.get(y_col))
            ):
                x0 = row[x_col]
                y0 = row[y_col]

                fig.add_trace(go.Scatter(
                    x=x0 + radio * np.cos(theta),
                    y=y0 + radio * np.sin(theta),
                    mode="lines",
                    line=dict(width=2, color="black", dash="dash"),
                    name="Radio de drene (m)",
                    legendgroup="radios",
                    showlegend=False,
                    hovertemplate=
                        "<b>Pozo:</b> " + str(row.get("POZO", "")) + "<br>" +
                        "<b>Radio drene:</b> " + f"{radio:,.0f} m" +
                        "<extra></extra>",
                ))

    if not ver_todos_campo:

        mapa_burb = mapa[mapa[variable] > 0].copy()

        if not mapa_burb.empty:

            fig.add_trace(go.Scatter(
                x=mapa_burb[x_col],
                y=mapa_burb[y_col],
                mode="markers+text",
                text=mapa_burb["ETIQUETA_MAPA"],
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
                    mode="markers+text",
                    text=mapa_iny["WINJ_BLS"].map(lambda x: f"{x/1000:,.1f}"),
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

    if not ver_todos_campo:

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

    if not ver_todos_campo:

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
            else f"<b>Mapa de burbujas - {yac_mapa}</b>"
        ),
        template="plotly_white",
        height=950,
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

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"]
        }
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
        linecolor="black"
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
        linecolor="black"
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
        linecolor="black"
    )

    fig3.update_yaxes(
        title_text="Np / Wp (mbl) y Gp (mmpc)",
        showgrid=True,
        gridcolor="#EAECEE",
        showline=True,
        linewidth=1,
        linecolor="black"
    )

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
        # TABLAS DE DATOS USADOS EN LAS GRÁFICAS
        # =====================================================

        st.markdown(
            "<div class='section-title'>Datos usados para las gráficas</div>",
            unsafe_allow_html=True
        )

        total_export = total.copy()
        yac_export = yac.copy()

        total_export["FECHA"] = pd.to_datetime(total_export[COL_FECHA]).dt.strftime("%d/%m/%Y")
        yac_export["FECHA"] = pd.to_datetime(yac_export[COL_FECHA]).dt.strftime("%d/%m/%Y")

        total_export = total_export.rename(columns={
            "QO_TOTAL": "Qo total (bpd)",
            "QW_TOTAL": "Qw total (bpd)",
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

    # =========================
    # MÉTRICAS
    # =========================
    m1, m2 = st.columns(2)

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

    st.plotly_chart(fig1, use_container_width=True)

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

    colg1, colg2 = st.columns(2)

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

    st.plotly_chart(fig4, use_container_width=True)

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

    colnp1, colnp2 = st.columns(2)

    with colnp1:
        st.plotly_chart(fig5, use_container_width=True)

    with colnp2:
        st.plotly_chart(fig6, use_container_width=True)


     # =========================
    # =========================
    # MAPA DE BURBUJAS FILTRADO CON RMA
    # =========================

    pozos_rma = rma_f[COL_POZO].dropna().astype(str).unique().tolist()

    df_mapa_rma = df.copy()
    df_coord_rma = df_coord.copy()

    if df_coord_rma.empty:
        st.warning("Los pozos seleccionados en RMA no tienen coordenadas en Coord.")
    else:

        #mapa_burbujas(df_mapa_rma, df_coord_rma, modo_mapa="RMA")
        mapa_burbujas(
            df_mapa_rma,
            df_coord_rma,
            modo_mapa="RMA",
            pozos_destacados=pozos_rma
        )
        #mapa_burbujas(df_mapa_rma, df_coord_rma)

def mapa_presion():

    st.markdown(
        "<div class='section-title'>Mapa de presión, estado de pozos y campañas 2011-2020</div>",
        unsafe_allow_html=True
    )

    pres = load_presiones()
    coord = df_coord.copy()

    if pres.empty:
        st.warning("No hay datos de presión cargados.")
        return

    # =========================
    # FILTROS
    # =========================
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        yacs = sorted(pres["YACIMIENTO"].dropna().astype(str).unique())
        yac_sel = st.selectbox(
            "Yacimiento",
            yacs,
            key="yac_mapa_presion"
        )

    pres = pres[pres["YACIMIENTO"].astype(str) == str(yac_sel)].copy()

    with c2:
        fecha_ref = st.date_input(
            "Fecha referencia",
            value=pres["FECHA"].max().date(),
            key="fecha_ref_mapa_presion"
        )

    with c3:
        modo_presion = st.selectbox(
            "Modo presión",
            ["Última disponible"],
            key="modo_mapa_presion"
        )

    with c4:
        dias_promedio = st.number_input(
            "Promediar ± días",
            min_value=0,
            max_value=60,
            value=30,
            step=1,
            key="dias_prom_mapa_presion"
        )

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
            COL_GAS_PC: "sum"
        })
        .rename(columns={
            COL_ACEITE_BBL: "NP_BLS",
            COL_AGUA_BBL: "WP_BLS",
            COL_GAS_PC: "GP_PC"
        })
    )

    mapa_todos = coord.merge(
        acum_pozos,
        on=COL_POZO,
        how="left"
    )

    mapa_todos = mapa_todos[
        mapa_todos["YACIMIENTO"].astype(str) == str(yac_sel)
    ].copy()

    mapa_todos[["NP_BLS", "WP_BLS", "GP_PC"]] = mapa_todos[
        ["NP_BLS", "WP_BLS", "GP_PC"]
    ].fillna(0)

    mapa_todos = mapa_todos.dropna(
        subset=["CIMA X UTM", "CIMA Y UTM"]
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
    term = load_term_perforados()

    pres_mapa = pres_mapa.merge(
        term,
        on="TERMINACION",
        how="left"
    )

    pres_mapa["PERFORADO_TERM"] = pres_mapa["PERFORADO_TERM"].fillna("No")

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
                nlags=4,
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

    # =========================
    # PUNTOS DE PRESIÓN
    # =========================
    fig.add_trace(go.Scatter(
        x=pres_mapa["CIMA X UTM"],
        y=pres_mapa["CIMA Y UTM"],
        mode="markers+text",
        text=pres_mapa["POZO"],
        textposition="bottom center",
        textfont=dict(
            size=12,
            color="black",
            family="Arial Black"
        ),
        marker=dict(
            size=14,
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
# =========================================================
# SELECTOR GENERAL DE MÓDULO
# =========================================================

vista = st.radio(
    "Seleccionar opción",
    [
        "Producción por pozo",
        "Comparativa por pozo",
        "Mapa de burbujas",
        "Campañas 2011-2020",
        "RMA 2011-2020",
        "Operación Campo",
        "Producción Campo",
        "Presiones",
        "Estadística"
    ],
    horizontal=True,
    key="vista_principal"
    )

# =========================================================
# FILTROS SOLO PARA PRODUCCIÓN POR POZO Y COMPARATIVA
# =========================================================
if vista in ["Producción por pozo", "Comparativa por pozo"]:

    st.markdown("<div class='filter-box'>", unsafe_allow_html=True)

    f1, f2 = st.columns([1.7, 2.3])

    with f1:
        yacs = sorted(df[COL_YAC].dropna().astype(str).unique())
        yac_sel = st.multiselect(
            "Filtro por Yacimiento",
            yacs,
            default=yacs,
            key="prod_yac_sel"
        )

    df_base_filtro = (
        df[df[COL_YAC].astype(str).isin(yac_sel)].copy()
        if yac_sel else df.copy()
    )

    with f2:
        pozos = sorted(df_base_filtro[COL_POZO].dropna().astype(str).unique())

        if not pozos:
            st.warning("No hay pozos para el yacimiento seleccionado.")
            st.stop()

        pozo_sel = st.selectbox(
            "Pozo / Terminación",
            pozos,
            key="prod_pozo_sel"
        )

    # Base real del pozo seleccionado.
    df_pozo_raw = df[
        df[COL_POZO].astype(str) == str(pozo_sel)
    ].copy()

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# BASE DE PRODUCCIÓN SIN FILTRO DE FECHAS
# Solo aplica para Producción por pozo y Comparativa
# =========================================================
if vista in ["Producción por pozo", "Comparativa por pozo"]:

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
# FUNCIÓN PARA GRÁFICAS COMPARATIVAS
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
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,  font=dict(
        size=14,
        color="black",
        family="Arial"
        )),
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
    dfp["QB"] = dfp[COL_QO] + dfp[COL_QW]

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

    st.plotly_chart(fig1, use_container_width=True)

    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

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

    fig2.add_trace(
        go.Scatter(
            x=dfp[COL_FECHA],
            y=dfp[COL_QIN],
            mode="lines+markers",
            name="Qiny (bpd)",
            line=dict(width=2, color="cyan"),
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
            line=dict(width=2, color="#154360"),
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
        legend=dict(orientation="h", y=1.02,  font=dict(
        size=14,
        color="black",
        family="Arial Black"
        )),
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
        COL_QG,
        COL_WC,
        COL_RGA,
        COL_NP,
        COL_WP,
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
        COL_QG: "{:,.1f}",
        COL_WC: "{:,.1f}",
        COL_RGA: "{:,.0f}",
        COL_NP: "{:,.1f}",
        COL_WP: "{:,.1f}",
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

            # =========================
            # =========================
            # 3. COMPARATIVO Qw + %Agua
            # =========================
            fig_agua = make_subplots(specs=[[{"secondary_y": True}]])

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

                #fig_agua.add_trace(
                #    go.Scatter(
                #        x=x_values,
                #        y=dfi[COL_QW].replace(0, np.nan),
                #        mode="lines+markers",
                #        name=f"{pozo} | Qw",
                #        line=dict(width=3),
                #        marker=dict(size=4),
                #        connectgaps=False,
                #        hovertemplate=
                #            f"<b>Pozo: {pozo}</b><br>" +
                #            hover_x + "<br>" +
                #            "Qw: %{y:,.2f} bpd<extra></extra>"
                #    ),
                #    secondary_y=False
                #)

                fig_agua.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=dfi[COL_WC].replace(0, np.nan),
                        mode="lines+markers",
                        name=f"{pozo} | % Agua",
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
                title="<b>Comparativo de agua producida y corte de agua por pozo</b>",
                template="plotly_white",
                hovermode="x unified",
                height=520,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=14, color="black", family="Arial")
                ),
                margin=dict(l=35, r=35, t=60, b=35),
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="Tahoma", size=16, color="black")
            )

            fig_agua.update_xaxes(
                title_text=f"<b>{x_title}</b>",
                tickformat="%d/%m/%Y" if not normalizar_tiempo else None,
                showgrid=True,
                gridcolor="#EAECEE",
                zeroline=False,
                tickfont=dict(size=18, color="black"),
                showline=True,
                linewidth=0.5,
                linecolor="black"
            )

            fig_agua.update_yaxes(
                title_text="<b>Agua producida, Qw (bpd)</b>",
                secondary_y=False,
                showgrid=True,
                gridcolor="#EAECEE",
                zeroline=False,
                separatethousands=True,
                tickfont=dict(size=18, color="black"),
                showline=True,
                linewidth=0.5,
                linecolor="black"
            )

            fig_agua.update_yaxes(
                title_text="<b>Corte de agua (%)</b>",
                secondary_y=True,
                range=[0, 100],
                showgrid=False,
                zeroline=False,
                tickfont=dict(size=18, color="black"),
                showline=True,
                linewidth=0.5,
                linecolor="black"
            )

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
                        name=f"{pozo} | Qiny",
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
                title="<b>Comparativo de agua de inyección por pozo</b>",
                template="plotly_white",
                hovermode="x unified",
                height=520,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=14, color="black", family="Arial")
                ),
                margin=dict(l=35, r=35, t=60, b=35),
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="Tahoma", size=16, color="black")
            )

            fig_iny.update_xaxes(
                title_text=f"<b>{x_title}</b>",
                tickformat="%d/%m/%Y" if not normalizar_tiempo else None,
                showgrid=True,
                gridcolor="#EAECEE",
                zeroline=False,
                tickfont=dict(size=18, color="black"),
                showline=True,
                linewidth=0.5,
                linecolor="black"
            )

            fig_iny.update_yaxes(
                title_text="<b>Agua inyectada, Qiny (bpd)</b>",
                showgrid=True,
                gridcolor="#EAECEE",
                zeroline=False,
                separatethousands=True,
                tickfont=dict(size=18, color="black"),
                showline=True,
                linewidth=0.5,
                linecolor="black"
            )

            st.plotly_chart(fig_iny, use_container_width=True)

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

#st.caption("Desarrollado en Python + Streamlit.")
