import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
st.set_page_config(
    page_title="Visualizador de Producción",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="collapsed"
)
#

# =========================================================
# RUTA DE LA BASE DE DATOS
# Cambia esta ruta si tu archivo .db está en otra carpeta.
# =========================================================

# Ruta de la base SQLite
ruta_db = "prod.db"

# Nombre de la tabla
TABLA_PROD = "PROD"


conn = sqlite3.connect(ruta_db)
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


try:
    df = load_data()
except Exception as e:
    st.error(f"No fue posible cargar la base: {e}")
    st.stop()

# =========================================================
# ENCABEZADO
# =========================================================
st.markdown(
    "<div class='main-title'>Campo Tamaulipas-Constituciones Producción</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='subtitle'>Producción diaria promedio mensual</div>",
    unsafe_allow_html=True
)

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
    yac_sel = st.multiselect("Yacimiento", yacs, default=yacs)

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
        ["Producción por pozo", "Comparativa por pozo"],
        horizontal=True
    )

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
        f"Yacimiento: <b>{first_row.get(COL_YAC, '')}</b> | "
        f"Conta: <b>{first_row.get(COL_CONTA, '')}</b> | "
        f"Registros reales cargados: <b>{len(dfp)}</b></span>",
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
    k8.metric("Wp / Gp", f"{dfp[COL_WP].iloc[-1]:,.2f} mbl/ {dfp[COL_GP].iloc[-1]:,.2f} mmpc")

# =========================================================
# FUNCIÓN PARA GRÁFICAS COMPARATIVAS
# =========================================================
def comparative_plot(data, y_col, title, y_title, pozos_sel_comp, semilog=False):

    fig = go.Figure()

    for pozo in pozos_sel_comp:
        dfi = data[data[COL_POZO].astype(str) == str(pozo)].copy()
        dfi = dfi.sort_values(COL_FECHA).reset_index(drop=True)

        if dfi.empty:
            continue

        y_values = dfi[y_col].copy()
        if semilog:
            y_values = y_values.replace(0, np.nan)

        fig.add_trace(
            go.Scatter(
                x=dfi[COL_FECHA],
                y=y_values,
                mode="lines+markers",
                name=str(pozo),
                line=dict(width=2.5),
                marker=dict(size=3),
                connectgaps=False,
                hovertemplate=
                    "<b>Pozo: %{fullData.name}</b><br>" +
                    "Fecha: %{x|%d/%m/%Y}<br>" +
                    f"{y_title}: " + "%{y:,.2f}<extra></extra>"
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
    ),
    )

    fig.update_xaxes(
        title_text="Fecha",
        tickformat="%d/%m/%Y",
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
        separatethousands=True,
        tickfont=dict(size=16)
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

    fig1.update_xaxes(title_text="Fecha", tickformat="%d/%m/%Y")
    fig1.update_yaxes(title_text="Qo (bpd) / % Agua", secondary_y=False)
    fig1.update_yaxes(title_text="Np (mbl) / Qg (mpcd)", secondary_y=True)

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

    fig2.update_xaxes(title_text="Fecha", tickformat="%d/%m/%Y")
    fig2.update_yaxes(title_text="Qw (bpd)", secondary_y=False)
    fig2.update_yaxes(title_text="Wp (mbl)", secondary_y=True)

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

    fig3.update_xaxes(title_text="Fecha", tickformat="%d/%m/%Y")
    fig3.update_yaxes(title_text="RGA (pc/bl)", secondary_y=False)
    fig3.update_yaxes(title_text="Gp (mmpc)", secondary_y=True)

    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("<div class='section-title'>Datos filtrados del pozo</div>", unsafe_allow_html=True)

    show_cols = [
        COL_POZO, COL_FECHA, COL_YAC, COL_CONTA, COL_DIAS,
        COL_ACEITE, COL_AGUA, COL_GAS,
        COL_ACEITE_BBL, COL_AGUA_BBL, COL_GAS_PC,
        COL_QO, COL_QW, COL_QG,
        COL_NP, COL_WP, COL_GP,
        COL_WC, COL_RGA
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
                    semilog=True
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
