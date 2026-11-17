"""Vista compacta del mapa de burbujas para Produccion por pozo."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

VERSION_VISTA = 3


def _clave(serie):
    return serie.fillna("").astype(str).str.strip().str.upper()


def preparar_mapa_pozo(coordenadas, produccion, seleccion, yacimiento, factor_bbl):
    """Usa las cimas y el respaldo de fondo de Mapas; cruza terminacion y yacimiento."""
    co = coordenadas.copy()
    co.columns = co.columns.astype(str).str.strip().str.upper()
    columnas = {"TERMINACION", "YACIMIENTO", "CIMA X UTM", "CIMA Y UTM"}
    if not columnas.issubset(co.columns):
        return pd.DataFrame()
    co = co.loc[_clave(co["YACIMIENTO"]).eq(str(yacimiento).strip().upper())].copy()
    for col in ["TERMINACION", "YACIMIENTO"]:
        co[col] = _clave(co[col])
    if "POZO" not in co:
        co["POZO"] = co["TERMINACION"]
    for eje in ["X", "Y"]:
        cima = pd.to_numeric(co[f"CIMA {eje} UTM"], errors="coerce")
        fondo = pd.to_numeric(co.get(f"FONDO {eje} UTM", pd.Series(index=co.index, dtype=float)), errors="coerce")
        co[eje] = cima.fillna(fondo).replace([np.inf, -np.inf], np.nan)
    co = co.dropna(subset=["X", "Y"]).drop_duplicates(["TERMINACION", "YACIMIENTO"])
    prod = produccion.copy()
    prod["TERMINACION"] = _clave(prod["TERMINACION"])
    prod["YACIMIENTO"] = _clave(prod["YACIMIENTO"])
    prod = prod.loc[prod["YACIMIENTO"].eq(str(yacimiento).strip().upper())].copy()
    prod["NP_MB"] = pd.to_numeric(prod["ACEITE"], errors="coerce").fillna(0) * factor_bbl / 1000
    acumuladas = prod.groupby(["TERMINACION", "YACIMIENTO"], as_index=False)["NP_MB"].sum()
    co = co.merge(acumuladas, on=["TERMINACION", "YACIMIENTO"], how="left", validate="one_to_one")
    co["NP_MB"] = co["NP_MB"].fillna(0)
    seleccion = seleccion.loc[_clave(seleccion["YACIMIENTO"]).eq(str(yacimiento).strip().upper())]
    co["SELECCIONADO"] = co["TERMINACION"].isin(set(_clave(seleccion["TERMINACION"])))
    return co


def crear_mapa_pozo(mapa, contorno, asignacion, yacimiento, seleccion_id):
    if mapa.empty or not mapa["SELECCIONADO"].any():
        return None
    fig = go.Figure()
    limites_x = list(mapa["X"])
    limites_y = list(mapa["Y"])
    for datos, nombre, color in [(asignacion, "Asignaci\u00f3n", "#7F8C8D"),
                                  (contorno, "Contorno", "#1F4E79")]:
        borde = datos.copy()
        borde.columns = borde.columns.astype(str).str.strip().str.upper()
        if not {"X", "Y"}.issubset(borde.columns):
            continue
        if "ORDEN" in borde:
            borde = borde.sort_values("ORDEN")
        borde["X"] = pd.to_numeric(borde["X"], errors="coerce")
        borde["Y"] = pd.to_numeric(borde["Y"], errors="coerce")
        borde = borde.dropna(subset=["X", "Y"])
        limites_x.extend(borde["X"].tolist())
        limites_y.extend(borde["Y"].tolist())
        fig.add_trace(go.Scatter(x=borde["X"], y=borde["Y"], mode="lines",
            line=dict(color=color, width=1.5), name=nombre, hoverinfo="skip", showlegend=False))
    vecinos = mapa.loc[~mapa["SELECCIONADO"]]
    elegidos = mapa.loc[mapa["SELECCIONADO"]]
    for puntos, nombre, color, seleccionado in [
            (vecinos, "Pozos del yacimiento", "#8DA2B5", False),
            (elegidos, "Pozo seleccionado", "#F2A541", True)]:
        if puntos.empty:
            continue
        magnitudes = np.sqrt(puntos["NP_MB"].clip(lower=0))
        referencia = max(float(np.sqrt(mapa["NP_MB"].clip(lower=0)).max()), 1)
        tamanos = 8 + 20 * magnitudes / referencia
        if seleccionado:
            tamanos = np.maximum(tamanos, 18)
        fig.add_trace(go.Scatter(x=puntos["X"], y=puntos["Y"],
            mode="markers+text" if seleccionado else "markers",
            text=puntos["POZO"] if seleccionado else None, textposition="top center",
            textfont=dict(size=12, color="black", family="Tahoma"),
            marker=dict(size=tamanos, color=color, opacity=1 if seleccionado else 0.5,
                        line=dict(color="#B86E12" if seleccionado else "white", width=2 if seleccionado else 1)),
            name=nombre, customdata=puntos[["POZO", "TERMINACION", "YACIMIENTO", "NP_MB"]].to_numpy(),
            hovertemplate="<b>%{customdata[0]}</b><br>Terminaci\u00f3n: %{customdata[1]}"
                          "<br>Yacimiento: %{customdata[2]}<br>Np: %{customdata[3]:,.2f} mb<extra></extra>"))
    # Ajusta el encuadre a todo el campo, incluidos contorno y asignacion.
    x_min, x_max = min(limites_x), max(limites_x)
    y_min, y_max = min(limites_y), max(limites_y)
    x, y = (x_min + x_max) / 2, (y_min + y_max) / 2
    margen_x = max(500, (x_max - x_min) * 0.56)
    margen_y = max(500, (y_max - y_min) * 0.56)
    fig.update_layout(title=dict(text=f"<b>Campo completo | {yacimiento}</b>", font=dict(size=13)),
        height=1000, template="plotly_white", paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=8, r=8, t=35, b=50),
        font=dict(size=10, color="black", family="Tahoma"), dragmode="zoom",
        legend=dict(orientation="h", y=-0.13, x=0, font=dict(size=10)),
        uirevision=f"produccion_proporciones_originales_1000:{seleccion_id}:{yacimiento}")
    fig.update_xaxes(range=[x - margen_x, x + margen_x], title="UTM X (m)",
                     tickformat=",.0f", showgrid=False, zeroline=False, fixedrange=False,
                     scaleanchor=False, constrain="range", domain=[0, 1], autorange=False)
    fig.update_yaxes(range=[y - margen_y, y + margen_y], title="UTM Y (m)",
                     tickformat=",.0f", showgrid=False, zeroline=False, fixedrange=False,
                     scaleanchor="x", scaleratio=1, constrain="range", domain=[0, 1], autorange=False)
    return fig
