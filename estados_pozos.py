"""Estados de catalogo conciliados con el ultimo mes real de Produccion."""
import unicodedata
import pandas as pd


def clave(serie):
    return (serie.fillna("").astype(str).str.normalize("NFKD")
            .str.encode("ascii", errors="ignore").str.decode("ascii")
            .str.upper()
            .str.replace(r"^CONST(?=[ _-]|[0-9])", "C", regex=True)
            .str.replace(r"^TMLP(?=[ _-]|[0-9])", "T", regex=True)
            .str.replace(r"^CHAMPAYAN(?=[ _-]|[0-9])", "CH", regex=True)
            .str.replace(r"^PEDRERA(?=[ _-]|[0-9])", "P", regex=True)
            .str.replace(r"[^A-Z0-9]", "", regex=True))


def _columnas(datos):
    datos = datos.copy()
    datos.columns = [str(c).strip().upper() for c in datos.columns]
    return datos


def construir_estados(estados, produccion, coordenadas):
    """Una fila agregada por pozo y una por zona; nunca modifica la base SQLite.

    Produccion positiva = aceite, agua o gas > 0. INJ por si solo no es produccion.
    La fecha de corte es el mes maximo de registros reales, no el ultimo de cada pozo.
    """
    e, p, co = map(_columnas, (estados, produccion, coordenadas))
    if "ESTADO FINAL" not in e:
        raise ValueError("Falta la columna Estado Final en la tabla Estado.")
    if "POZO" not in e:
        raise ValueError("Falta la columna Pozo en la tabla Estado.")
    e["POZO"] = clave(e.POZO)
    e = e.loc[e.POZO.ne("")].copy()
    e["ESTADO_BASE"] = e["ESTADO FINAL"].fillna("Sin estado").astype(str).str.strip().replace("", "Sin estado")
    e["SAP"] = e.get("SAP", pd.Series("Sin SAP", index=e.index)).fillna("Sin SAP")
    conflictos = e.groupby("POZO").ESTADO_BASE.nunique()
    if conflictos.gt(1).any():
        raise ValueError("Estado Final contradictorio para el mismo pozo: " + ", ".join(conflictos[conflictos.gt(1)].index))
    e = e[["POZO", "ESTADO_BASE", "SAP"]].drop_duplicates("POZO")
    p["TERMINACION"] = clave(p.TERMINACION)
    p["YACIMIENTO"] = clave(p.YACIMIENTO)
    p["POZO"] = clave(p.get("POZO", pd.Series("", index=p.index)))
    if {"TERMINACION", "POZO"}.issubset(co.columns):
        co["TERMINACION"], co["POZO"] = clave(co.TERMINACION), clave(co.POZO)
        relacion = co.loc[co.POZO.ne("") & co.TERMINACION.ne(""), ["TERMINACION", "POZO"]].drop_duplicates()
        ambiguas = relacion.groupby("TERMINACION").POZO.nunique().gt(1)
        relacion = relacion.loc[~relacion.TERMINACION.isin(ambiguas[ambiguas].index)]
        p["POZO"] = p.POZO.mask(p.POZO.eq(""), p.TERMINACION.map(relacion.set_index("TERMINACION").POZO))
    # Match exacto de terminacion solo cuando coincide con el identificador fisico.
    p["POZO"] = p.POZO.fillna("")
    exacto = p.TERMINACION.isin(e.POZO)
    p.loc[p.POZO.eq("") & exacto, "POZO"] = p.loc[p.POZO.eq("") & exacto, "TERMINACION"]
    p["FECHA"] = pd.to_datetime(p.FECHA, errors="coerce")
    p = p.loc[p.FECHA.notna() & p.TERMINACION.ne("")].copy()
    corte = p.FECHA.max()
    positivos = pd.DataFrame({c: pd.to_numeric(p.get(c, pd.Series(0, index=p.index)), errors="coerce") for c in ["ACEITE", "AGUA", "GAS"]}).gt(0).any(axis=1)
    actual = p.FECHA.dt.to_period("M").eq(corte.to_period("M")) if pd.notna(corte) else pd.Series(False, index=p.index)
    activos = p.loc[actual & positivos & p.POZO.ne(""), ["POZO", "YACIMIENTO"]].drop_duplicates()
    # El catalogo define la base; solo Operando sin produccion se convierte a CCP.
    base_op = clave(e.ESTADO_BASE).isin(["OP", "OPERANDO"])
    e["ESTADO_BASE"] = e.ESTADO_BASE.mask(base_op & pd.notna(corte), "CCP")
    e["ESTADO"] = e.ESTADO_BASE.mask(e.POZO.isin(activos.POZO), "Operando")
    e["YACIMIENTO"] = ""
    zonas = p.loc[p.POZO.ne("") & p.YACIMIENTO.ne(""), ["POZO", "YACIMIENTO"]]
    if {"POZO", "YACIMIENTO"}.issubset(co.columns):
        zonas = pd.concat([zonas, pd.DataFrame({"POZO": clave(co.POZO), "YACIMIENTO": clave(co.YACIMIENTO)})])
    zonas = zonas.loc[zonas.POZO.ne("") & zonas.YACIMIENTO.ne("")].drop_duplicates()
    zonas = zonas.merge(e.drop(columns=["YACIMIENTO", "ESTADO"]), on="POZO", how="inner", validate="many_to_one")
    activos_idx = pd.MultiIndex.from_frame(activos[["POZO", "YACIMIENTO"]])
    zonas["ESTADO"] = zonas.ESTADO_BASE.mask(pd.MultiIndex.from_frame(zonas[["POZO", "YACIMIENTO"]]).isin(activos_idx), "Operando")
    resultado = pd.concat([e, zonas], ignore_index=True)
    resultado["FECHA_ESTADO"] = corte.to_period("M").to_timestamp() if pd.notna(corte) else pd.NaT
    return resultado


def adjuntar_estados(datos, catalogo):
    """Cruza por pozo y zona sin multiplicar filas ni propagar actividad entre zonas."""
    r = datos.copy()
    e = catalogo.copy()
    e["_POZO_ESTADO"] = clave(e.POZO)
    if "YACIMIENTO" not in e:
        e["YACIMIENTO"] = ""
    e["_YAC_ESTADO"] = clave(e.YACIMIENTO)
    if "ESTADO_BASE" not in e:
        e["ESTADO_BASE"] = e.ESTADO
    fisicos = e.loc[e._YAC_ESTADO.eq("")].drop_duplicates("_POZO_ESTADO").set_index("_POZO_ESTADO")
    llave = clave(r.POZO)
    tiene_zona = "YACIMIENTO" in r
    r["ESTADO"] = llave.map(fisicos.ESTADO_BASE if tiene_zona else fisicos.ESTADO)
    r["SAP"] = llave.map(fisicos.SAP) if "SAP" in fisicos else "Sin SAP"
    if tiene_zona:
        zonas = e.loc[e._YAC_ESTADO.ne("")].drop_duplicates(["_POZO_ESTADO", "_YAC_ESTADO"]).set_index(["_POZO_ESTADO", "_YAC_ESTADO"])
        idx = pd.MultiIndex.from_arrays([llave, clave(r.YACIMIENTO)])
        especifico = pd.Series(zonas.ESTADO.reindex(idx).to_numpy(), index=r.index)
        r["ESTADO"] = especifico.combine_first(r.ESTADO)
        sin_zona = clave(r.YACIMIENTO).eq("")
        r.loc[sin_zona, "ESTADO"] = llave[sin_zona].map(fisicos.ESTADO)
    r["ESTADO"] = r.ESTADO.fillna("Sin estado")
    r["SAP"] = r.SAP.fillna("Sin SAP")
    return r
