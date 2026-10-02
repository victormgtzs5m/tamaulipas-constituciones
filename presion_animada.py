"""Superficies mensuales de presion para el reproductor Np / Winj."""
import numpy as np
import pandas as pd
import streamlit as st
from plotly.colors import get_colorscale
from matplotlib.path import Path
from presion_interpolada import evaluar_kriging_presion, unir_presiones_coordenadas

VERSION_CAPA = 5


@st.cache_data(show_spinner=False, max_entries=2048)
def _superficie(datos, x, y):
    soporte = pd.DataFrame(datos, columns=["CIMA X UTM", "CIMA Y UTM", "PRESION_MAPA"])
    try:
        z, _ = evaluar_kriging_presion(soporte, x, y, modo="grid")
        return z, ""
    except (ValueError, np.linalg.LinAlgError, RuntimeError) as exc:
        return None, str(exc)


@st.cache_data(show_spinner=False, max_entries=8)
def preparar_presion_animada(presiones, coordenadas, contorno, yacimiento, fechas, resolucion=120):
    """Promedio mensual y LOCF interior; nunca usa una medicion futura como valor."""
    fechas = pd.DatetimeIndex(fechas)
    pr = presiones.copy()
    pr.columns = pr.columns.str.strip().str.upper()
    pr = pr[pr["YACIMIENTO"].astype(str).str.strip().str.upper() == str(yacimiento).strip().upper()].copy()
    pr["FECHA"] = pd.to_datetime(pr["FECHA"], errors="coerce")
    pr["PRESION"] = pd.to_numeric(pr["PRESION"], errors="coerce")
    pr = pr[pr["FECHA"].notna() & pr["PRESION"].gt(0) & np.isfinite(pr["PRESION"])].copy()
    if pr.empty:
        raise ValueError("No hay presiones validas del yacimiento para animar.")
    pr["MES"] = pr["FECHA"].dt.to_period("M").dt.to_timestamp()
    mensual = pr.groupby(["TERMINACION", "YACIMIENTO", "MES"], as_index=False)["PRESION"].mean()
    mensual = mensual.rename(columns={"PRESION": "PRESION_MAPA"})
    unidos = unir_presiones_coordenadas(mensual, coordenadas)
    if unidos.empty:
        raise ValueError("Las presiones no tienen coordenadas validas para interpolar.")
    borde = contorno.copy()
    borde.columns = borde.columns.str.strip().str.upper()
    if "ORDEN" in borde:
        borde = borde.sort_values("ORDEN")
    xy_borde = borde[["X", "Y"]].apply(pd.to_numeric, errors="coerce").dropna().to_numpy()
    if len(xy_borde) < 3:
        raise ValueError("No hay un contorno valido para el mapa de presion.")
    x = np.linspace(xy_borde[:, 0].min(), xy_borde[:, 0].max(), resolucion)
    y = np.linspace(xy_borde[:, 1].min(), xy_borde[:, 1].max(), resolucion)
    xx, yy = np.meshgrid(x, y)
    mascara = Path(xy_borde).contains_points(np.column_stack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
    series = []
    for pozo, grupo in unidos.groupby("TERMINACION", sort=True):
        mensual_pozo = grupo.set_index("MES")["PRESION_MAPA"].sort_index()
        ultimo = mensual_pozo.index.max()
        valores = mensual_pozo.reindex(mensual_pozo.index.union(fechas)).sort_index().ffill().reindex(fechas)
        valores = valores.where(fechas <= ultimo)
        serie = pd.DataFrame({"FECHA": fechas, "PRESION_MAPA": valores.to_numpy(),
                              "CIMA X UTM": grupo["CIMA X UTM"].iloc[0],
                              "CIMA Y UTM": grupo["CIMA Y UTM"].iloc[0]})
        series.append(serie.dropna())
    soporte = pd.concat(series, ignore_index=True)
    grupos = {fecha: g for fecha, g in soporte.groupby("FECHA")}
    superficies, indices, estados = [], [], []
    vistos = {}
    for fecha in fechas:
        g = grupos.get(fecha)
        if g is None:
            datos = np.empty((0, 3))
        else:
            g = g.groupby(["CIMA X UTM", "CIMA Y UTM"], as_index=False)["PRESION_MAPA"].mean()
            datos = g[["CIMA X UTM", "CIMA Y UTM", "PRESION_MAPA"]].to_numpy(dtype=float)
        clave = datos.tobytes()
        if clave not in vistos:
            z, error = _superficie(datos, x, y)
            if z is None:
                superficie = [[None] * len(x) for _ in y]
            else:
                z = np.where(mascara & np.isfinite(z) & (z > 0), np.round(z, 1), np.nan)
                superficie = [[float(v) if np.isfinite(v) else None for v in fila] for fila in z]
                if not np.isfinite(z).any():
                    error = "Sin celdas validas dentro del contorno."
            vistos[clave] = (len(superficies), error)
            superficies.append(superficie)
        indice, error = vistos[clave]
        indices.append(indice)
        estados.append(f"Presion: {len(datos)} ubicaciones de soporte" if not error else f"Presion sin superficie: {error}")
    valores_validos = [v for superficie in superficies for fila in superficie for v in fila if v is not None]
    minimo = min(valores_validos) if valores_validos else 0
    maximo = max(valores_validos) if valores_validos else 1
    if maximo <= minimo:
        maximo = minimo + 1
    return dict(x=x.tolist(), y=y.tolist(), superficies=superficies, indices=indices,
                estados=estados, zmin=minimo, zmax=maximo)


def agregar_presion_animada(mapa, presion, tipo="Grid"):
    """Anteponer el grid a las burbujas y desplazar sus indices de actualizacion."""
    escala = dict(colorscale=get_colorscale("Turbo"), autocolorscale=False,
                  reversescale=False, zauto=False,
                  zmin=presion["zmin"], zmax=presion["zmax"])
    if tipo == "Contour":
        estilo = dict(type="contour", autocontour=False, connectgaps=False,
                      contours=dict(coloring="heatmap", showlines=True,
                                    start=presion["zmin"], end=presion["zmax"],
                                    size=(presion["zmax"] - presion["zmin"]) / 20),
                      line=dict(width=0.8, color="rgba(30,41,59,0.55)"))
    else:
        estilo = dict(type="heatmap", zsmooth=False)
    traza = dict(**estilo, x=presion["x"], y=presion["y"],
                 z=presion["superficies"][presion["indices"][0]],
                 **escala,
                 opacity=0.75, hoverongaps=False,
                 colorbar=dict(title=dict(text="Presión<br>(kg/cm²)"), thickness=12, len=0.6),
                 name="Presion kriging", hovertemplate="Presion estimada: %{z:,.1f} kg/cm2<extra></extra>")
    mapa["data"].insert(0, traza)
    for i, frame in enumerate(mapa["frames"]):
        previos = frame.get("traces", list(range(len(frame["data"]))))
        frame["traces"] = [0] + [indice + 1 for indice in previos]
        frame["data"] = [dict(**estilo, **escala, opacity=0.75,
                              hoverongaps=False,
                              colorbar=traza["colorbar"],
                              z=presion["superficies"][presion["indices"][i]])] + frame["data"]
