"""Curvas tipo historicas por yacimiento, reutilizando los vectores mensuales DCA."""
from hashlib import sha1
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

QO = "Qo (bpd)"
VOLUMEN = "Aceite (bl)"
VERSION_ESTILO = 3

COLOR_P50 = "#FF6E00"
COLOR_P10 = "#FF1744"
COLOR_P90 = "#FFFF00"
COLOR_MEDIA = "#65D8CA"
COLOR_EXPONENCIAL = "#39FF14"
COLOR_ACTIVOS = "#A0A8AD"
GROSOR_CURVAS = 1.5
ESTILO_CURVAS = "dash"
DIAS_MES_PERFIL = 30.42


@st.cache_data(show_spinner="Preparando historia para Type Curve...")
def cargar_historia_type_curve(version_db, _cargar_dca):
    terminaciones, _ = _cargar_dca(version_db)
    return preparar_historia(terminaciones)


def preparar_historia(datos):
    """Mantiene Qo de DCA, Np desde su vector de volumen y meses calendario desde el primer aceite."""
    columnas = ["YACIMIENTO", "POZO_ID", "POZO", "FECHA", "MES_REL", "QO", "NP_MB"]
    if datos.empty:
        return pd.DataFrame(columns=columnas)
    d = datos.copy()
    d["POZO_ID"] = d["TERMINACION_DCA"].astype(str).str.strip()
    d["POZO"] = d["TERMINACION"].astype(str).str.strip()
    d["YACIMIENTO"] = d["YACIMIENTO"].astype(str).str.strip()
    d["FECHA"] = pd.to_datetime(d["FECHA"], errors="coerce")
    d = d.dropna(subset=["FECHA"])
    d["FECHA"] = d["FECHA"].dt.to_period("M").dt.to_timestamp()
    d["QO"] = pd.to_numeric(d[QO], errors="coerce").replace([np.inf, -np.inf], np.nan)
    d["VOLUMEN"] = pd.to_numeric(d[VOLUMEN], errors="coerce").replace([np.inf, -np.inf], np.nan)
    claves = ["YACIMIENTO", "POZO_ID"]
    d = (d.groupby(claves + ["FECHA"], as_index=False)
         .agg(POZO=("POZO", "first"), QO=("QO", lambda s: s.sum(min_count=1)),
              VOLUMEN=("VOLUMEN", lambda s: s.sum(min_count=1)))
         .sort_values(claves + ["FECHA"]))
    # No desplaza ni comprime los cierres o huecos de la historia.
    inicio = d["FECHA"].where(d["QO"].gt(0)).groupby([d[c] for c in claves]).transform("min")
    d["NP_MB"] = d.groupby(claves)["VOLUMEN"].cumsum() / 1000.0
    d["MES_REL"] = (d["FECHA"].dt.year - inicio.dt.year) * 12 + d["FECHA"].dt.month - inicio.dt.month
    d = d.loc[d["MES_REL"].ge(0)].copy()
    d["MES_REL"] = d["MES_REL"].astype(int)
    return d[columnas].reset_index(drop=True)


def calcular_p50_tiempo(historia, minimo=1):
    if historia.empty:
        return pd.DataFrame(columns=["MES_REL", "P10", "P50", "P90", "MEDIA", "N_POZOS"])
    d = historia.loc[historia["QO"].ge(0)].copy()
    # Un solo voto por pozo y mes, incluyendo los ceros realmente observados.
    d = d.groupby(["POZO_ID", "MES_REL"], as_index=False)["QO"].mean()
    resultado = d.groupby("MES_REL")["QO"].agg(P10=lambda x: x.quantile(0.1), P50="median", P90=lambda x: x.quantile(0.9), MEDIA="mean", N_POZOS="count").reset_index()
    return resultado.loc[resultado["N_POZOS"].ge(minimo)].reset_index(drop=True)


def normalizar_acumulada(historia):
    """Cada pozo parte de Np=0 en el primer registro de la historia considerada."""
    d = historia.sort_values(["POZO_ID", "MES_REL"]).copy()
    d["NP_NORMALIZADA_MB"] = d["NP_MB"] - d.groupby("POZO_ID")["NP_MB"].transform("first")
    return d


def calcular_p50_acumulada(historia, minimo=1, puntos=160, incluir_cero=False):
    """Mediana a Np comunes; incluye el origen normalizado y no extrapola historias."""
    curvas = []
    for _, pozo in historia.groupby("POZO_ID"):
        valida_np = pozo["NP_MB"].ge(0) if incluir_cero else pozo["NP_MB"].gt(0)
        h = pozo.loc[pozo["QO"].gt(0) & valida_np, ["NP_MB", "QO"]]
        h = h.replace([np.inf, -np.inf], np.nan).dropna()
        h = h.groupby("NP_MB", as_index=False)["QO"].median().sort_values("NP_MB")
        if not h.empty:
            curvas.append(h)
    columnas = ["NP_MB", "P10", "P50", "P90", "MEDIA", "N_POZOS"]
    if not curvas:
        return pd.DataFrame(columns=columnas)
    valores = np.concatenate([h["NP_MB"].to_numpy() for h in curvas])
    positivos = valores[valores > 0]
    rejilla = np.geomspace(positivos.min(), positivos.max(), puntos) if len(positivos) else np.array([])
    rejilla = np.unique(np.r_[rejilla, [h["NP_MB"].iloc[0] for h in curvas],
                              [h["NP_MB"].iloc[-1] for h in curvas]])
    matriz = np.full((len(curvas), len(rejilla)), np.nan)
    for i, h in enumerate(curvas):
        x, y = h["NP_MB"].to_numpy(), h["QO"].to_numpy()
        if len(h) == 1:
            matriz[i, rejilla == x[0]] = y[0]
            continue
        pos = x > 0
        if x[0] == 0:
            # El tramo entre cero y el primer Np positivo no admite log(Np).
            primero = x[pos][0]
            mascara = (rejilla >= 0) & (rejilla < primero)
            matriz[i, mascara] = np.exp(np.interp(rejilla[mascara], [0, primero],
                                                   [np.log(y[0]), np.log(y[pos][0])]))
        if pos.any():
            mascara = (rejilla >= x[pos][0]) & (rejilla <= x[pos][-1])
            matriz[i, mascara] = np.exp(np.interp(np.log(rejilla[mascara]),
                                                   np.log(x[pos]), np.log(y[pos])))
    filas = []
    for j, np_mb in enumerate(rejilla):
        muestra = matriz[:, j]
        muestra = muestra[np.isfinite(muestra)]
        suficiente = len(muestra) >= minimo
        filas.append({"NP_MB": np_mb,
                      "P10": np.quantile(muestra, 0.1) if suficiente else np.nan,
                      "P50": np.median(muestra) if suficiente else np.nan,
                      "P90": np.quantile(muestra, 0.9) if suficiente else np.nan,
                      "MEDIA": muestra.mean() if suficiente else np.nan, "N_POZOS": len(muestra)})
    resultado = pd.DataFrame(filas, columns=columnas)
    return resultado if resultado["P50"].notna().any() else resultado.iloc[:0]


def calcular_perfil_exponencial(qi, di, tiempo_di, d2, limite, dias_mes=DIAS_MES_PERFIL):
    """Dos etapas en meses enteros, incluyendo un mes de cierre del limite economico."""
    valores = [qi, di, tiempo_di, d2, limite, dias_mes]
    if not all(np.isfinite(v) for v in valores):
        raise ValueError("Todos los par\u00e1metros deben ser finitos.")
    if qi <= 0 or limite <= 0 or limite >= qi:
        raise ValueError("El gasto inicial debe ser mayor que el l\u00edmite econ\u00f3mico, y ambos deben ser positivos.")
    if di < 0 or d2 < 0 or tiempo_di < 0 or dias_mes <= 0:
        raise ValueError("Las declinaciones y el tiempo deben ser no negativos.")
    if tiempo_di != int(tiempo_di):
        raise ValueError("Tiempo Di debe ser un numero entero de meses.")
    cambio_di = max(int(tiempo_di) - 1, 0)
    log_cociente = np.log(qi) - np.log(limite)
    corte_primero = log_cociente / di if di > 0 else np.inf
    if tiempo_di > 0 and corte_primero <= cambio_di:
        fin = corte_primero
    else:
        if d2 == 0:
            raise ValueError("D2 debe ser mayor que cero para alcanzar el l\u00edmite econ\u00f3mico en la segunda etapa.")
        fin = cambio_di + (log_cociente - di * cambio_di) / d2
    if not np.isfinite(fin):
        raise ValueError("Estos par\u00e1metros generan una duraci\u00f3n no finita. Revisa las declinaciones.")
    if np.isclose(fin, np.rint(fin), atol=1e-10, rtol=0):
        fin = float(np.rint(fin))
    # Incluye el siguiente mes entero al cruce del limite, tambien si cae exacto.
    fin = int(np.floor(fin)) + 1
    if fin > 100000:
        raise ValueError("El perfil supera 100000 meses; revisa las declinaciones ingresadas.")
    t = np.arange(fin + 1, dtype=int)
    t1 = np.minimum(t, cambio_di)
    t2 = np.maximum(t - cambio_di, 0)
    gasto = qi * np.exp(-di * t1 - d2 * t2)
    # El mes cero es el primer periodo y aporta volumen a la reserva.
    volumen_mensual = gasto * dias_mes
    reserva_bbl = np.cumsum(volumen_mensual)
    return pd.DataFrame({"MES_REL": t, "QO": gasto,
                         "NP_MB": reserva_bbl / 1000, "NP_NORMALIZADA_MB": (reserva_bbl - reserva_bbl[0]) / 1000,
                         "RESERVA_BBL": reserva_bbl, "DIAS_MES": dias_mes, "PERIODO": t + 1,
                         "MESES_INTERVALO": np.ones(len(t), dtype=int),
                         "VOLUMEN_INTERVALO_BBL": volumen_mensual,
                         "ETAPA": np.where(t < tiempo_di, 1, 2),
                         "ETAPA_NOMBRE": np.where(t < tiempo_di, "Di", "D2")})


def _agregar_halo(fig, x, y, color, grupo, nombre):
    rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    if grupo == "tc_p90":
        fig.add_trace(go.Scattergl(x=x, y=y, mode="lines", name="Contraste de P90",
            legendgroup=grupo, showlegend=False, hoverinfo="skip", connectgaps=False,
            line=dict(color="rgba(140,120,0,0.55)", width=2.5, dash=ESTILO_CURVAS)))
    capas = [(8, 0.09), (4, 0.24)] if grupo == "tc_p10" else [(7, 0.045), (4, 0.12)]
    for ancho, opacidad in capas:
        fig.add_trace(go.Scattergl(x=x, y=y, mode="lines", name=nombre,
            legendgroup=grupo, showlegend=False, hoverinfo="skip", connectgaps=False,
            line=dict(color=f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{opacidad})",
                      width=ancho, dash=ESTILO_CURVAS)))


def agregar_perfil_exponencial(fig, perfil, modo="tiempo", np_desde_cero=False):
    x = perfil["MES_REL"] if modo == "tiempo" else perfil["NP_NORMALIZADA_MB"]
    if modo != "tiempo" and not np_desde_cero:
        x = x.where(x.gt(0))
    _agregar_halo(fig, x, perfil["QO"], COLOR_EXPONENCIAL, "tc_exponencial", "Brillo del perfil exponencial")
    fig.add_trace(go.Scattergl(
        x=x, y=perfil["QO"], mode="lines", name="Perfil Propuesto",
        legendgroup="tc_exponencial",
        line=dict(color=COLOR_EXPONENCIAL, width=GROSOR_CURVAS, dash=ESTILO_CURVAS),
        customdata=perfil[["MES_REL", "NP_MB", "ETAPA_NOMBRE", "NP_NORMALIZADA_MB"]].to_numpy(),
        hovertemplate="<b>Perfil Propuesto</b><br>Mes: %{customdata[0]:,.0f}"
                      "<br>Qo: %{y:,.2f} bpd<br>Np: %{customdata[1]:,.2f} mb"
                      "<br>Np normalizada: %{customdata[3]:,.2f} mb<br>Etapa: %{customdata[2]}<extra></extra>"))
    return fig


def agregar_resultados_perfil_propuesto(fig, perfil, qi, di, tiempo_di, d2, limite):
    fin = int(perfil.MES_REL.iloc[-1])
    reserva = float(perfil.RESERVA_BBL.iloc[-1])
    anios, meses_restantes = divmod(len(perfil), 12)
    texto = (
        "<b>Perfil Propuesto</b><br>Modelo exponencial de dos etapas \u00b7 b = 0"
        f"<br>Gasto inicial (bpd): <b>{qi:,.2f}</b>"
        f"<br>Di (frac/mes): <b>{di:.4f}</b>"
        f"<br>Duraci\u00f3n Di (meses): <b>{int(tiempo_di):,d}</b>"
        f"<br>Periodos con Di: <b>{int(perfil.ETAPA.eq(1).sum())}</b>"
        f"<br>D2 (frac/mes): <b>{d2:.4f}</b>"
        f"<br>L\u00edmite econ\u00f3mico (bpd): <b>{limite:,.2f}</b>"
        f"<br>Reserva (bbl): <b>{reserva:,.2f}</b>"
        f"<br>Reserva / Np al corte (mb): <b>{reserva / 1000:,.2f}</b>"
        f"<br>Qo al corte (bpd): <b>{perfil.QO.iloc[-1]:,.2f}</b>"
        f"<br>Corte (meses): <b>{fin:,d}</b>"
        f"<br>Corte: <b>{anios} a\u00f1os y {meses_restantes} meses</b>"
        f"<br>Periodos mensuales (incluye mes 0): <b>{len(perfil):,d}</b>"
        f"<br>Factor de volumen: <b>{perfil.DIAS_MES.iloc[0]:.2f} d\u00edas/mes</b>")
    fig.add_annotation(xref="paper", yref="paper", x=0.98, y=0.98,
        xanchor="right", yanchor="top", text=texto, showarrow=False,
        align="left", captureevents=True, bgcolor="rgba(255,255,255,0.96)",
        bordercolor="#CBD5E1", borderwidth=1, borderpad=8,
        font=dict(family="Segoe UI, Arial", size=10, color="#334155"))
    return fig


def calcular_pozos_activos(historia, modo="tiempo"):
    """Cuenta gasto positivo observado por mes, o cobertura positiva a Np comunes."""
    xcol = "MES_REL" if modo == "tiempo" else "NP_MB"
    if historia.empty:
        return pd.DataFrame(columns=[xcol, "N_ACTIVOS"])
    if modo == "tiempo":
        positivos = historia.loc[historia.QO.gt(0) & np.isfinite(historia.QO)]
        conteo = positivos.groupby("MES_REL")["POZO_ID"].nunique()
        meses = range(int(historia.MES_REL.min()), int(historia.MES_REL.max()) + 1)
        return conteo.reindex(meses, fill_value=0).rename("N_ACTIVOS").rename_axis("MES_REL").reset_index()
    d = historia.copy()
    if "NP_NORMALIZADA_MB" in d:
        d["NP_MB"] = d["NP_NORMALIZADA_MB"]
    soporte = calcular_p50_acumulada(d, minimo=1, incluir_cero=True)
    if soporte.empty:
        valores = np.sort(d.loc[d.NP_MB.ge(0) & np.isfinite(d.NP_MB), "NP_MB"].unique())
        return pd.DataFrame({"NP_MB": valores, "N_ACTIVOS": np.zeros(len(valores), dtype=int)})
    return soporte[["NP_MB", "N_POZOS"]].rename(columns={"N_POZOS": "N_ACTIVOS"})


def agregar_banda_percentiles(fig, percentiles, modo="tiempo", np_desde_cero=False, *, semilog=True):
    if percentiles.empty or not {"P10", "P90"}.issubset(percentiles.columns):
        return fig
    eje = "MES_REL" if modo == "tiempo" else "NP_MB"
    curva = percentiles.sort_values(eje).copy()
    if modo == "tiempo":
        curva = curva.set_index(eje).reindex(range(int(curva[eje].min()), int(curva[eje].max()) + 1)).rename_axis(eje).reset_index()
    valida = np.isfinite(curva.P10) & np.isfinite(curva.P90)
    valida &= (curva.P10.gt(0) & curva.P90.gt(0) if semilog
               else curva.P10.ge(0) & curva.P90.ge(0))
    if modo != "tiempo" and not np_desde_cero:
        valida &= curva[eje].gt(0)
    indices = np.flatnonzero(valida.to_numpy())
    grupos = np.split(indices, np.where(np.diff(indices) > 1)[0] + 1)
    leyenda = True
    for grupo in grupos:
        if len(grupo) < 2:
            continue
        h = curva.iloc[grupo]
        fig.add_trace(go.Scatter(x=h[eje], y=h.P10, mode="lines", line=dict(width=0),
            name="Limite P10", legendgroup="tc_banda_percentiles", showlegend=False,
            hoverinfo="skip", connectgaps=False))
        fig.add_trace(go.Scatter(x=h[eje], y=h.P90, mode="lines", line=dict(width=0),
            fill="tonexty", fillcolor="rgba(70,110,150,0.16)", name="P10–P90",
            legendgroup="tc_banda_percentiles", showlegend=leyenda, hoverinfo="skip", connectgaps=False))
        leyenda = False
    return fig


def crear_grafico(historia, p50, modo="tiempo", mostrar_media=True, destacado=None, np_desde_cero=False, mostrar_activos=True, activos=None, *, semilog=True):
    fig = go.Figure()
    xcol = "MES_REL" if modo == "tiempo" else "NP_MB"
    for pozo, h in historia.groupby("POZO_ID", sort=False):
        h = h.sort_values("MES_REL")
        # Reindexa solo para dibujar huecos; no agrega observaciones al P50.
        if modo == "tiempo":
            h = h.set_index("MES_REL").reindex(range(h["MES_REL"].min(), h["MES_REL"].max() + 1)).rename_axis("MES_REL").reset_index()
        q = h["QO"].where(h["QO"].gt(0) if semilog else h["QO"].ge(0))
        valores_np = h["NP_NORMALIZADA_MB"] if "NP_NORMALIZADA_MB" in h else h["NP_MB"]
        eje_x = h[xcol] if modo == "tiempo" else valores_np.where(valores_np.ge(0) if np_desde_cero else valores_np.gt(0))
        resaltado = pozo == destacado
        fig.add_trace(go.Scattergl(
            x=eje_x, y=q, mode="lines", name=str(pozo),
            line=dict(color="#567C8C" if resaltado else "rgba(100,116,139,0.32)",
                      width=2.3 if resaltado else 1),
            connectgaps=False, showlegend=False,
            customdata=np.column_stack([h["MES_REL"], h["NP_MB"], valores_np]),
            hovertemplate=(f"<b>{pozo}</b><br>Mes: %{{customdata[0]:.0f}}"
                           "<br>Qo: %{y:,.2f} bpd<br>Np original: %{customdata[1]:,.2f} mb"
                           "<br>Np normalizada: %{customdata[2]:,.2f} mb<extra></extra>")))
    agregar_banda_percentiles(fig, p50, modo, np_desde_cero, semilog=semilog)
    conteo_activos = activos if activos is not None else calcular_pozos_activos(historia, modo)
    if mostrar_activos and not conteo_activos.empty:
        puntos_activos = conteo_activos[xcol]
        if modo != "tiempo" and not np_desde_cero:
            puntos_activos = puntos_activos.where(puntos_activos.gt(0))
        # Halos suaves bajo la linea blanca; comparten el control de leyenda.
        for ancho_halo, opacidad in [(7, 0.045), (4, 0.12)]:
            fig.add_trace(go.Scattergl(x=puntos_activos, y=conteo_activos["N_ACTIVOS"],
                mode="lines", yaxis="y2", name="Brillo de pozos activos",
                legendgroup="tc_activos", showlegend=False, hoverinfo="skip",
                line=dict(color=f"rgba(100,116,139,{opacidad})", width=ancho_halo, dash=ESTILO_CURVAS)))
        fig.add_trace(go.Scattergl(x=puntos_activos, y=conteo_activos["N_ACTIVOS"],
            name="Pozos activos", mode="lines", yaxis="y2", legendgroup="tc_activos",
            line=dict(color=COLOR_ACTIVOS, width=GROSOR_CURVAS, dash=ESTILO_CURVAS),
            hovertemplate=("<b>Pozos activos: %{y:.0f}</b><br>" +
                           ("Mes" if modo == "tiempo" else "Np normalizada (mb)") +
                           ": %{x:,.2f}<extra></extra>")))
    if not p50.empty:
        # Conserva huecos mensuales donde no se cumple el minimo de muestra.
        curva = p50.copy()
        if modo == "tiempo":
            curva = curva.set_index("MES_REL").reindex(range(curva["MES_REL"].min(), curva["MES_REL"].max() + 1)).rename_axis("MES_REL").reset_index()
        for columna, nombre, color, ancho in [
                ("MEDIA", "Media de la muestra", COLOR_MEDIA, 2),
                ("P90", "P90", COLOR_P90, GROSOR_CURVAS),
                ("P10", "P10", COLOR_P10, GROSOR_CURVAS),
                ("P50", "P50 \u00b7 Mediana", COLOR_P50, GROSOR_CURVAS)]:
            if columna not in curva or (columna == "MEDIA" and not mostrar_media):
                continue
            puntos_x = curva[xcol]
            if modo != "tiempo" and not np_desde_cero:
                puntos_x = puntos_x.where(puntos_x.gt(0))
            gasto = curva[columna].where(curva[columna].gt(0) if semilog else curva[columna].ge(0))
            es_percentil = columna in ("P10", "P50", "P90")
            grupo_percentil = f"tc_{columna.lower()}" if es_percentil else ""
            if es_percentil:
                _agregar_halo(fig, puntos_x, gasto,
                              color, grupo_percentil, f"Brillo del {columna}")
            # Mismo motor WebGL: la ultima traza P50 queda sobre los pozos.
            fig.add_trace(go.Scattergl(x=puntos_x, y=gasto,
                name=nombre, mode="lines", legendgroup=grupo_percentil,
                line=dict(color=color, width=ancho, dash=ESTILO_CURVAS if es_percentil else "solid"), marker=dict(size=7, color=color, line=dict(color="#FFE6AD", width=1)) if columna == "P50" else dict(size=4), connectgaps=False,
                customdata=curva[["N_POZOS"]].to_numpy(),
                hovertemplate=nombre + "<br>" + ("Mes" if modo == "tiempo" else "Np (mb)") +
                    ": %{x:,.2f}<br>Qo: %{y:,.2f} bpd<br>Pozos con dato: %{customdata[0]:.0f}<extra></extra>"))
    fig.update_layout(height=620, template="plotly_white", editrevision="tc_resumen_perfil", paper_bgcolor="white", plot_bgcolor="#F8F8FF",
        font=dict(family="Arial", size=13, color="#111827"),
        margin=dict(l=65, r=75 if mostrar_activos else 22, t=35, b=75), hovermode="closest", dragmode="zoom",
        legend=dict(orientation="h", x=0, y=1.04, font=dict(size=11, color="#475569")),
        uirevision=f"tc:v{VERSION_ESTILO}:{modo}:{np_desde_cero}:{semilog}:{','.join(sorted(historia.POZO_ID.unique()))}")
    eje = dict(showline=True, linewidth=1.2, linecolor="#111827", mirror=True,
               showgrid=True, gridcolor="#E5E7EB", gridwidth=0.7, zeroline=False,
               ticks="outside", tickfont=dict(size=18, color="#111827", family="Arial"),
               title_font=dict(size=18, color="#374151", family="Arial"),
               automargin=True, minor=dict(showgrid=False))
    fig.update_xaxes(title="<b>Meses desde el primer aceite (tiempo 0)</b>" if modo == "tiempo" else "<b>Np normalizada desde el inicio de la historia (mb)</b>",
        type="linear" if modo == "tiempo" or np_desde_cero else "log", **eje)
    if modo != "tiempo" and np_desde_cero:
        fig.update_xaxes(rangemode="tozero")
    escala_qo = dict(type="log", tickvals=[0.1, 1, 10, 100, 1000, 10000, 100000],
                     ticktext=["0.1", "1", "10", "100", "1,000", "10,000", "100,000"]) if semilog else dict(
                         type="linear", rangemode="tozero", tickformat=",.0f")
    fig.update_yaxes(title="<b>Gasto de aceite, Qo (bpd)</b>", **escala_qo, **eje)
    if mostrar_activos:
        max_activos = int(conteo_activos.N_ACTIVOS.max()) if not conteo_activos.empty else 0
        fig.update_layout(yaxis2=dict(
            title=dict(text="<b>Pozos activos</b>", font=dict(size=18, color="#374151", family="Arial")),
            overlaying="y", side="right", type="linear", rangemode="tozero",
            range=[0, max(1, max_activos) * 1.1], dtick=max(1, int(np.ceil(max_activos / 8))),
            tickformat=".0f", tickfont=dict(size=18, color="#111827", family="Arial"), ticks="outside", automargin=True, showgrid=False,
            showline=True, linewidth=1.2, linecolor="#111827", zeroline=False))
    return fig


CSS = """
<style>
.st-key-tc_root {background:#FFFFFF; border:1px solid #DCE3E9; border-radius:14px; padding:20px;}
.st-key-tc_root h2, .st-key-tc_root h3 {color:#263238; font-family:'Segoe UI',Arial,sans-serif;}
.st-key-tc_root label, .st-key-tc_root p, .st-key-tc_root [data-testid='stMetricValue'],
.st-key-tc_root [data-testid='stWidgetLabel'] {color:#334155 !important;}
.st-key-tc_root [data-testid='stCaptionContainer'],
.st-key-tc_root [data-testid='stCaptionContainer'] * {color:#64748B !important;font-size:12px;}
.st-key-tc_root h2 {font-size:28px;}
.st-key-tc_root h3 {font-size:18px;font-weight:650;}
.st-key-tc_root input::placeholder {color:#7B8794 !important;opacity:1;}
.st-key-tc_wells, .st-key-tc_chart {background:#FFFFFF;border:1px solid #DCE3E9;border-radius:11px;padding:18px;}
.st-key-tc_root [data-baseweb='select'] > div,
.st-key-tc_root input:not([type='checkbox']), .st-key-tc_root [data-baseweb='input'] {
 background:#F7F9FC !important;color:#334155 !important;border-color:#D2DAE2 !important;}
.st-key-tc_root [data-baseweb='select'] span {color:#334155 !important;}
.st-key-tc_root button[kind='secondary'] {background:#F7F9FC;color:#475569;border:1px solid #D2DAE2;}
.st-key-tc_root button[kind='secondary']:hover {color:#E8A634;border-color:#E8A634;}
.st-key-tc_root button[kind='primary'] {background:#E8A634;color:#161B1E;border-color:#E8A634;}
.st-key-tc_root [data-testid='stRadio'] label:has(input:checked) {background:#FFF2DB;border-radius:18px;outline:1px solid #B68029;}
.st-key-tc_root [data-testid='stCheckbox'] {margin-bottom:0;}
.st-key-tc_root [data-testid='stNumberInput'] button {background:#F7F9FC !important;color:#334155 !important;}
.st-key-tc_root [data-testid='stExpander'] {background:#FFFFFF;border-color:#D2DAE2;}
.tc-eyebrow {color:#B87400;font-size:11px;font-weight:750;letter-spacing:1.6px;}
</style>
"""


def _widget_pozo(yacimiento, pozo):
    return "tc_check_" + sha1(f"{yacimiento}:{pozo}".encode()).hexdigest()[:16]


def _cambio_pozo(clave, pozo, widget):
    elegidos = set(st.session_state.get(clave, []))
    if st.session_state[widget]:
        elegidos.add(pozo)
    else:
        elegidos.discard(pozo)
    st.session_state[clave] = sorted(elegidos)


def _cambio_busqueda_pozos(clave, widget):
    st.session_state[clave] = list(st.session_state[widget])


def _marcar_pozos(clave, yacimiento, opciones, marcar):
    st.session_state[clave] = list(opciones) if marcar else []
    for pozo in opciones:
        st.session_state[_widget_pozo(yacimiento, pozo)] = marcar


def mostrar_type_curve(historia):
    st.markdown(CSS, unsafe_allow_html=True)
    with st.container(key="tc_root"):
        st.markdown('<div class="tc-eyebrow">PRON\u00d3STICO / TYPE CURVE</div>', unsafe_allow_html=True)
        st.markdown("## Type Curve")
        st.caption("Curvas tipo de aceite por yacimiento \u00b7 Historia normalizada a tiempo cero")
        if historia.empty:
            st.info("No hay historia de aceite disponible para construir curvas tipo.")
            return
        izquierda, derecha = st.columns([1, 2.5], gap="medium")
        with izquierda, st.container(key="tc_wells"):
            yacimientos = sorted(historia.YACIMIENTO.unique())
            yacimiento = st.selectbox("Yacimiento", yacimientos, key="tc_yacimiento")
            base = historia.loc[historia.YACIMIENTO.eq(yacimiento)].copy()
            opciones = sorted(base.POZO_ID.unique())
            clave = f"tc_seleccion_{yacimiento}"
            st.session_state.setdefault(clave, list(opciones))
            st.session_state[clave] = sorted(set(st.session_state[clave]).intersection(opciones))
            st.markdown("### Pozos de la curva tipo")
            todos, ninguno = st.columns(2)
            todos.button("Todos", key="tc_todos", on_click=_marcar_pozos,
                args=(clave, yacimiento, opciones, True), width="stretch")
            ninguno.button("Ninguno", key="tc_ninguno", on_click=_marcar_pozos,
                args=(clave, yacimiento, opciones, False), width="stretch")
            nombres = base.drop_duplicates("POZO_ID").set_index("POZO_ID")["POZO"].to_dict()
            widget_busqueda = f"tc_buscar_multiple_{yacimiento}"
            st.session_state[widget_busqueda] = list(st.session_state[clave])
            elegidos = set(st.multiselect(
                "Buscar pozo", opciones, key=widget_busqueda,
                on_change=_cambio_busqueda_pozos, args=(clave, widget_busqueda),
                format_func=lambda pozo: f"{nombres[pozo]} \u00b7 {pozo}" if nombres[pozo] != pozo else pozo,
                placeholder="Escribe y selecciona los pozos...",
            ))
            st.caption(f"{len(elegidos)} de {len(opciones)} pozos / terminaciones seleccionados")
            st.markdown("### Historia considerada")
            corte = st.date_input("Fecha de corte", value=base.FECHA.max().date(),
                min_value=base.FECHA.min().date(), max_value=base.FECHA.max().date(),
                key=f"tc_corte_{yacimiento}")
            base = base.loc[base.FECHA.le(pd.Timestamp(corte))]
            max_mes = int(base.MES_REL.max()) if not base.empty else 0
            if max_mes > 0:
                meses = st.slider("Meses desde tiempo 0", 0, max_mes, (0, max_mes),
                                  key=f"tc_meses_{yacimiento}_{max_mes}")
            else:
                meses = (0, 0)
            seleccion = base.loc[base.POZO_ID.isin(elegidos) & base.MES_REL.between(*meses)].copy()
            seleccion = normalizar_acumulada(seleccion)
            participantes = int(seleccion.loc[seleccion.QO.ge(0), "POZO_ID"].nunique())
            minimo = st.number_input("M\u00ednimo de pozos para P10/P50/P90", min_value=1,
                max_value=max(1, participantes), value=1, step=1,
                key=f"tc_minimo_v2_{yacimiento}_{participantes}")
            st.caption(f"{participantes} pozos con datos en el intervalo considerado.")
            st.markdown("### Perfil exponencial de dos etapas")
            qi = st.number_input("Gasto inicial (bpd)", min_value=0.0, value=None,
                step=10.0, format="%.2f", key=f"tc_exp_qi_{yacimiento}")
            di = st.number_input("Di (frac)", min_value=0.0, value=None,
                step=0.005, format="%.4f", key=f"tc_exp_di_{yacimiento}")
            tiempo_di = st.number_input("Tiempo Di (Meses)", min_value=0, value=None,
                step=1, key=f"tc_exp_tiempo_{yacimiento}")
            d2 = st.number_input("D2 (frac)", min_value=0.0, value=None,
                step=0.005, format="%.4f", key=f"tc_exp_d2_{yacimiento}")
            limite = st.number_input("L\u00edmite econ\u00f3mico (bpd)", min_value=0.0, value=None,
                step=1.0, format="%.2f", key=f"tc_exp_limite_{yacimiento}")
            st.caption("Di y D2 son tasas nominales mensuales: 0.05 = 5%/mes. "
                       "q = qi \u00d7 exp(-D \u00d7 meses).")
            perfil_exponencial = None
            if all(v is not None for v in [qi, di, tiempo_di, d2, limite]):
                try:
                    perfil_exponencial = calcular_perfil_exponencial(qi, di, tiempo_di, d2, limite)
                except ValueError as error:
                    st.warning(str(error))
            else:
                st.caption("Completa los cinco par\u00e1metros para dibujar el perfil.")

        with derecha, st.container(key="tc_chart"):
            nombre = st.text_input("Nombre de la curva tipo", value="Curva tipo de aceite", key="tc_nombre")
            st.markdown("### Curva tipo de producci\u00f3n de aceite")
            vista = st.radio("Relaci\u00f3n de an\u00e1lisis", ["Gasto vs. tiempo", "Gasto vs. acumulada"],
                horizontal=True, key="tc_modo", label_visibility="collapsed")
            escala_qo = st.radio("Escala del gasto de aceite (bpd)", ["Lineal", "Logar\u00edtmica"],
                                 index=1, horizontal=True, key="tc_escala_qo")
            semilog = escala_qo != "Lineal"
            media = st.checkbox("Mostrar media de la muestra", value=True, key="tc_media")
            mostrar_activos = st.checkbox("Mostrar pozos activos", value=True, key="tc_activos")
            if not elegidos:
                st.info("Selecciona pozos del listado izquierdo para construir la curva tipo.")
                return
            if seleccion.empty:
                st.info("Los pozos seleccionados no tienen historia en el intervalo considerado.")
                return
            modo = "tiempo" if vista == "Gasto vs. tiempo" else "acumulada"
            np_desde_cero = False
            if modo == "acumulada":
                escala_np = st.radio("Escala de Np normalizada",
                    ["Desde Np = 0", "Logar\u00edtmica (Np > 0)"], horizontal=True, key="tc_escala_np")
                np_desde_cero = escala_np == "Desde Np = 0"
            destacar = st.selectbox("Resaltar pozo", ["Ninguno"] + sorted(seleccion.POZO_ID.unique()),
                                    key=f"tc_destacar_{yacimiento}")
            p50 = (calcular_p50_tiempo(seleccion, int(minimo)) if modo == "tiempo"
                   else calcular_p50_acumulada(seleccion.assign(NP_MB=seleccion.NP_NORMALIZADA_MB),
                                               int(minimo), incluir_cero=True))
            activos = calcular_pozos_activos(seleccion, modo)
            fig = crear_grafico(seleccion, p50, modo, media, destacar, np_desde_cero,
                                mostrar_activos, activos, semilog=semilog)
            if perfil_exponencial is not None:
                agregar_perfil_exponencial(fig, perfil_exponencial, modo, np_desde_cero)
                agregar_resultados_perfil_propuesto(fig, perfil_exponencial, qi, di, tiempo_di, d2, limite)
            st.plotly_chart(fig, width="stretch", key=f"tc_grafico_estilo_{VERSION_ESTILO}", theme=None,
                config={"scrollZoom": True, "displaylogo": False, "editable": False,
                        "edits": {"annotationPosition": True},
                        "toImageButtonOptions": {"format": "png", "filename": "type_curve", "scale": 2}})
            if p50.empty:
                st.info("No hay valores comunes con el m\u00ednimo de pozos requerido para P50. Reduce el m\u00ednimo o ampl\u00eda la historia.")
            elif semilog and not p50.P50.gt(0).any():
                st.info("P50 calculado: 0 bpd en el intervalo. El valor cero no se representa en el eje logar\u00edtmico de gasto.")
            elif modo == "acumulada" and not np_desde_cero and not (p50.NP_MB.gt(0) & (p50.P50.gt(0) if semilog else p50.P50.ge(0))).any():
                st.info("P50 disponible en Np = 0. Selecciona 'Desde Np = 0' para verlo.")
            k1, k2, k3 = st.columns(3)
            k1.metric("Pozos con historia", seleccion.POZO_ID.nunique())
            k2.metric("Intervalo (meses)", f"{meses[0]} \u2013 {meses[1]}")
            k3.metric("P50 inicial (bpd)", f"{p50.P50.dropna().iloc[0]:,.1f}" if not p50.empty else "\u2014")
            with st.expander("Ver datos de la curva tipo"):
                eje_tabla = "MES_REL" if modo == "tiempo" else "NP_MB"
                tabla = p50.merge(activos, on=eje_tabla, how="outer").sort_values(eje_tabla)
                if modo == "acumulada":
                    tabla = tabla.rename(columns={"NP_MB": "NP_NORMALIZADA_MB"})
                tabla.insert(0, "Yacimiento", yacimiento)
                tabla.insert(0, "Curva tipo", nombre)
                st.dataframe(tabla, hide_index=True, width="stretch")
                st.download_button("Descargar P10/P50/P90 CSV", tabla.to_csv(index=False).encode("utf-8-sig"),
                    "type_curve_percentiles.csv", "text/csv", key="tc_exportar_p50")
                st.download_button("Descargar historias seleccionadas CSV", seleccion.to_csv(index=False).encode("utf-8-sig"),
                    "type_curve_historias.csv", "text/csv", key="tc_exportar_historia")
                if perfil_exponencial is not None:
                    st.markdown("#### Perfil Propuesto")
                    tabla_perfil = perfil_exponencial[
                        ["MES_REL", "PERIODO", "QO", "NP_MB", "NP_NORMALIZADA_MB", "RESERVA_BBL", "VOLUMEN_INTERVALO_BBL", "ETAPA"]
                    ].rename(columns={
                        "MES_REL": "Mes", "PERIODO": "Periodo", "QO": "Qo (bpd)", "NP_MB": "Np (mb)",
                        "NP_NORMALIZADA_MB": "Np normalizada (mb)",
                        "RESERVA_BBL": "Reserva acumulada (bbl)",
                        "VOLUMEN_INTERVALO_BBL": "Volumen mensual (bbl)", "ETAPA": "Etapa"})
                    tabla_perfil["Etapa"] = tabla_perfil["Etapa"].map({0: "Inicial", 1: "Di", 2: "D2"})
                    st.caption("El mes 0 es el primer periodo de Di y aporta volumen. "
                               "Con Tiempo Di = 18, Di abarca los meses 0 a 17 y D2 comienza en el mes 18.")
                    st.dataframe(tabla_perfil, hide_index=True, width="stretch",
                        column_config={
                            "Mes": st.column_config.NumberColumn(format="%d"),
                            "Periodo": st.column_config.NumberColumn(format="%d"),
                            "Etapa": st.column_config.TextColumn(),
                            "Qo (bpd)": st.column_config.NumberColumn(format="%.2f"),
                            "Np (mb)": st.column_config.NumberColumn(format="%.3f"),
                            "Reserva acumulada (bbl)": st.column_config.NumberColumn(format="%.2f"),
                            "Volumen mensual (bbl)": st.column_config.NumberColumn(format="%.2f")})
                    exportar_perfil = perfil_exponencial.assign(QI_BPD=qi, DI_FRAC_MES=di,
                        TIEMPO_DI_MESES=tiempo_di, D2_FRAC_MES=d2, LIMITE_BPD=limite, DIAS_MES=DIAS_MES_PERFIL)
                    st.download_button("Descargar Perfil Propuesto CSV",
                        exportar_perfil.to_csv(index=False).encode("utf-8-sig"),
                        "type_curve_perfil_exponencial.csv", "text/csv", key="tc_exportar_exponencial")

        from type_curve_estadistica import mostrar_estadistica_type_curve
        with derecha:
            mostrar_estadistica_type_curve(historia, yacimiento, seleccion.POZO_ID.unique())
