"""Calculo compartido por el mapa de Presiones y el indicador IDPI."""
import numpy as np
import pandas as pd


def _clave(s):
    return s.astype(str).str.strip().str.upper().str.replace(r"\s+", " ", regex=True)


def unir_presiones_coordenadas(presiones, coordenadas):
    """Misma asociacion por terminacion/yacimiento para ambas vistas."""
    pr = presiones.copy()
    co = coordenadas.copy()
    pr.columns = pr.columns.str.strip().str.upper()
    co.columns = co.columns.str.strip().str.upper()
    for col in ["TERMINACION", "YACIMIENTO"]:
        pr[col] = _clave(pr[col])
        co[col] = _clave(co[col])
    for col in ["CIMA X UTM", "CIMA Y UTM"]:
        co[col] = pd.to_numeric(co[col], errors="coerce")
    co = co.dropna(subset=["CIMA X UTM", "CIMA Y UTM"])
    co = co.drop_duplicates(["TERMINACION", "YACIMIENTO"])
    pr = pr.merge(
        co[["TERMINACION", "YACIMIENTO", "CIMA X UTM", "CIMA Y UTM"]],
        on=["TERMINACION", "YACIMIENTO"], how="left", validate="many_to_one"
    )
    return pr.dropna(subset=["CIMA X UTM", "CIMA Y UTM", "PRESION_MAPA"])


def datos_kriging_presion(pres_mapa):
    d = pres_mapa[["CIMA X UTM", "CIMA Y UTM", "PRESION_MAPA"]].copy()
    d = d.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    d = d.dropna()
    d = d[d["PRESION_MAPA"] > 0]
    # Una coordenada no puede aportar observaciones espaciales contradictorias.
    return d.groupby(["CIMA X UTM", "CIMA Y UTM"], as_index=False)["PRESION_MAPA"].mean()


def evaluar_kriging_presion(pres_mapa, x, y, modo="points"):
    """Configuracion unica: esferico, dos lags y ponderacion, en kg/cm2."""
    from pykrige.ok import OrdinaryKriging
    d = datos_kriging_presion(pres_mapa)
    if len(d) < 3:
        raise ValueError("Se requieren al menos tres coordenadas con presion del yacimiento.")
    xy = d[["CIMA X UTM", "CIMA Y UTM"]].to_numpy(dtype=float)
    if np.linalg.matrix_rank(xy - xy.mean(axis=0)) < 2:
        raise ValueError("Las coordenadas de presion estan alineadas.")
    valores = d["PRESION_MAPA"].to_numpy(dtype=float)
    shape = (len(y), len(x)) if modo == "grid" else (len(x),)
    if np.ptp(valores) == 0:
        return np.full(shape, valores[0]), np.zeros(shape)
    modelo = OrdinaryKriging(
        xy[:, 0], xy[:, 1], valores,
        variogram_model="spherical", nlags=2, weight=True,
        verbose=False, enable_plotting=False, pseudo_inv=True
    )
    z, varianza = modelo.execute(modo, np.asarray(x, dtype=float), np.asarray(y, dtype=float))
    return np.asarray(z, dtype=float), np.maximum(np.asarray(varianza, dtype=float), 0)


def estimar_presiones_para_pozos(presiones, pres_mapa, coordenadas, contorno, yacimiento, solo_mapa=False):
    """Conserva la ultima medicion; estima solo donde no existe una medicion.

    El soporte y el contorno son exactamente los del mapa de Presiones.
    Una estimacion no recibe una fecha de medicion inventada: se guarda
    por separado la fecha de referencia de la superficie.
    """
    from matplotlib.path import Path
    from scipy.spatial import cKDTree

    yac = str(yacimiento).strip().upper()
    co = coordenadas.copy()
    co.columns = co.columns.str.strip().str.upper()
    co["TERMINACION"] = _clave(co["TERMINACION"])
    co["YACIMIENTO"] = _clave(co["YACIMIENTO"])
    co = co[co["YACIMIENTO"] == yac].copy()
    for eje in ["X", "Y"]:
        cima = pd.to_numeric(co["CIMA " + eje + " UTM"], errors="coerce")
        fondo = pd.to_numeric(co.get("FONDO " + eje + " UTM", pd.Series(index=co.index, dtype=float)), errors="coerce")
        co[eje] = cima.fillna(fondo)
    co["_COORD_VALIDA"] = co[["X", "Y"]].notna().all(axis=1)
    co = co.sort_values("_COORD_VALIDA", ascending=False).drop_duplicates("TERMINACION")

    pr = presiones.copy()
    pr.columns = pr.columns.str.strip().str.upper()
    pr["TERMINACION"] = _clave(pr["TERMINACION"])
    pr["YACIMIENTO"] = _clave(pr["YACIMIENTO"])
    pr["FECHA"] = pd.to_datetime(pr["FECHA"], errors="coerce")
    pr["PRESION"] = pd.to_numeric(pr["PRESION"], errors="coerce")
    pr = pr[(pr["YACIMIENTO"] == yac) & pr["FECHA"].notna() & pr["PRESION"].gt(0) & np.isfinite(pr["PRESION"])]
    fecha_mapa = pr["FECHA"].max()
    pr = pr.groupby(["TERMINACION", "FECHA"], as_index=False)["PRESION"].mean()
    pr = pr.sort_values("FECHA").drop_duplicates("TERMINACION", keep="last").set_index("TERMINACION")

    terms = pd.Index(co["TERMINACION"]).union(pr.index, sort=False)
    r = pd.DataFrame({"TERMINACION": terms})
    r["PRESION_IDPI"] = r["TERMINACION"].map(pr["PRESION"]) if not pr.empty else np.nan
    r["FECHA_PRESION_IDPI"] = r["TERMINACION"].map(pr["FECHA"]) if not pr.empty else pd.NaT
    r["FUENTE_PRESION"] = np.where(r["PRESION_IDPI"].notna(), "Medida", "Sin dato")
    r["FECHA_MAPA_PRESION"] = fecha_mapa
    r["ERROR_KRIGING"] = np.nan
    r["DISTANCIA_PRESION_M"] = np.nan
    r["NOTA_PRESION"] = ""
    if solo_mapa:
        # Para el IDPI todos los pozos se evaluan en la misma superficie.
        r["PRESION_IDPI"] = np.nan
        r["FECHA_PRESION_IDPI"] = pd.NaT
        r["FUENTE_PRESION"] = "Sin dato"
    co = co.set_index("TERMINACION")
    xy = pd.DataFrame({"X": r["TERMINACION"].map(co["X"]), "Y": r["TERMINACION"].map(co["Y"])})
    falta = r["PRESION_IDPI"].isna()
    validos = xy.notna().all(axis=1) & np.isfinite(xy).all(axis=1)
    r.loc[falta & ~validos, "NOTA_PRESION"] = "Sin coordenadas para estimar"
    if not (falta & validos).any():
        return r
    borde = contorno.copy()
    borde.columns = borde.columns.str.strip().str.upper()
    if "ORDEN" in borde:
        borde = borde.sort_values("ORDEN")
    borde[["X", "Y"]] = borde[["X", "Y"]].apply(pd.to_numeric, errors="coerce")
    borde = borde.dropna(subset=["X", "Y"])
    if len(borde) < 3:
        r.loc[falta, "NOTA_PRESION"] = "Sin contorno valido para estimar"
        return r
    dentro = pd.Series(False, index=r.index)
    dentro.loc[validos] = Path(borde[["X", "Y"]].to_numpy()).contains_points(
        xy.loc[validos].to_numpy(), radius=1e-7
    )
    r.loc[falta & validos & ~dentro, "NOTA_PRESION"] = "Fuera del contorno del mapa de presiones"
    evaluar = falta & validos & dentro
    if not evaluar.any():
        return r
    if pres_mapa.empty:
        r.loc[evaluar, "NOTA_PRESION"] = "Sin mediciones del yacimiento para interpolar"
        return r
    fuente = pres_mapa.copy()
    if "YACIMIENTO" in fuente:
        fuente = fuente[_clave(fuente["YACIMIENTO"]) == yac]
    try:
        z, varianza = evaluar_kriging_presion(fuente, xy.loc[evaluar, "X"], xy.loc[evaluar, "Y"])
        indices = r.index[evaluar]
        aceptado = np.isfinite(z) & (z > 0)
        indices_ok = indices[aceptado]
        r.loc[indices_ok, "PRESION_IDPI"] = z[aceptado]
        r.loc[indices_ok, "FUENTE_PRESION"] = "Estimada por kriging"
        r.loc[indices_ok, "ERROR_KRIGING"] = np.sqrt(varianza[aceptado])
        soporte = datos_kriging_presion(fuente)[["CIMA X UTM", "CIMA Y UTM"]].to_numpy()
        dist, _ = cKDTree(soporte).query(xy.loc[indices_ok].to_numpy())
        r.loc[indices_ok, "DISTANCIA_PRESION_M"] = dist
        r.loc[indices[~aceptado], "NOTA_PRESION"] = "La interpolacion no produjo una presion positiva valida"
    except (ValueError, np.linalg.LinAlgError) as exc:
        r.loc[evaluar, "NOTA_PRESION"] = str(exc)
    return r
