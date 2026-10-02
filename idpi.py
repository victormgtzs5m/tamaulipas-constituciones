"""Indicador de seis variables, relativo dentro de cada yacimiento."""
import numpy as np
import pandas as pd

VERSION_MODELO = 7
PESOS_IDPI = {"S_NP12": .25, "S_PRESION": .25, "S_AGUA": .15, "S_RGA": .10, "S_QO3": .10, "S_RELACION": .15}
M3_A_BBL = 6.289810770
M3_A_PC = 35.3147

def clave(s):
    return s.astype(str).str.strip().str.upper().str.replace(r"\s+", " ", regex=True)

def percentil(s):
    validos = s.replace([np.inf, -np.inf], np.nan).round(10)
    n = validos.notna().sum()
    return 100 * (validos.rank(method="average") - .5) / n if n else validos

def calcular_idpi(produccion, presiones, muestras, yacimiento, fecha_corte=None,
                  acumuladas_historicas=None, presiones_mapa=None, vectores_produccion=None):
    """Seis componentes. Presion exclusivamente de la superficie compartida.
    
    Se conservan argumentos antiguos por compatibilidad; presiones medidas y
    acumuladas historicas no participan directamente en este modelo.
    RGA: media aritmetica mensual, ventana de 12 meses al ultimo mes con aceite del pozo.
    """
    p = produccion.copy()
    p.columns = p.columns.str.strip().str.upper()
    yac = str(yacimiento).strip().upper()
    usar_ultimos = fecha_corte is None
    corte = pd.Timestamp(fecha_corte).to_period("M").end_time if not usar_ultimos else None
    for col in ["TERMINACION", "YACIMIENTO"]:
        p[col] = clave(p[col])
    p["FECHA"] = pd.to_datetime(p["FECHA"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    p = p.loc[p.YACIMIENTO.eq(yac) & p.FECHA.notna()].copy()
    if corte is not None:
        p = p.loc[p.FECHA.le(corte)]
    for col in ["ACEITE", "AGUA", "GAS"]:
        p[col] = pd.to_numeric(p[col], errors="coerce").replace([np.inf,-np.inf],np.nan)
    vectores = None
    if vectores_produccion is not None:
        vectores = vectores_produccion.copy()
        for col in ["TERMINACION", "YACIMIENTO"]:
            vectores[col] = clave(vectores[col])
        vectores["FECHA"] = pd.to_datetime(vectores["FECHA"], errors="coerce").dt.to_period("M").dt.to_timestamp()
        vectores = vectores.loc[vectores.YACIMIENTO.eq(yac)].copy()
        if corte is not None:
            vectores = vectores.loc[vectores.FECHA.le(corte)]
    referencia = p.FECHA.max()
    filas = []
    for term,g in p.sort_values("FECHA").groupby("TERMINACION",sort=False):
        activos = g[["ACEITE","AGUA","GAS"]].gt(0).any(axis=1)
        if not g.ACEITE.gt(0).any():
            continue
        inicio = g.loc[activos,"FECHA"].min()
        edad = (referencia.year-inicio.year)*12 + referencia.month-inicio.month + 1
        g12 = g[g.FECHA.between(inicio,inicio+pd.DateOffset(months=11))]
        g3 = g[g.FECHA.between(inicio,inicio+pd.DateOffset(months=2))]
        dias = ((inicio+pd.DateOffset(months=3))-inicio).days
        np12 = g12.ACEITE.sum()*M3_A_BBL/1000 if edad>=12 and g12.ACEITE.ge(0).all() else np.nan
        qo3 = g3.ACEITE.sum()*M3_A_BBL/dias if edad>=3 and g3.ACEITE.ge(0).all() else np.nan
        fin_rga = g.loc[g.ACEITE.gt(0), "FECHA"].max()
        desde_rga = fin_rga-pd.DateOffset(months=11)
        gr = g[g.FECHA.between(desde_rga,fin_rga)]
        validos = gr.ACEITE.gt(0) & gr.GAS.ge(0)
        rga = (gr.loc[validos,"GAS"]*M3_A_PC/(gr.loc[validos,"ACEITE"]*M3_A_BBL)).mean()
        if vectores is not None:
            v = vectores.loc[vectores.TERMINACION.eq(term)].sort_values("FECHA")
            v3 = v.loc[v.FECHA.between(inicio, inicio + pd.DateOffset(months=2))]
            # Los vectores usan dias calendario: promedio ponderado por dias.
            dias_v3 = v3.FECHA.dt.days_in_month
            qo3 = (v3["Qo (bpd)"] * dias_v3).sum() / dias if (
                edad >= 3 and not v3.empty and v3["Qo (bpd)"].ge(0).all()
                and g3.ACEITE.ge(0).all()
            ) else np.nan
            vr = v.loc[v.FECHA.between(desde_rga, fin_rga)]
            # El cero de RGA en meses sin aceite es un relleno del grafico.
            validos = vr["Aceite (bl)"].gt(0) & vr["RGA (pc/bl)"].ge(0)
            validos &= np.isfinite(vr["RGA (pc/bl)"])
            # No convertir gas ausente en un cero favorable del indicador.
            fechas_gas = gr.loc[gr.ACEITE.gt(0) & gr.GAS.ge(0), "FECHA"]
            validos &= vr.FECHA.isin(fechas_gas)
            rga = vr.loc[validos, "RGA (pc/bl)"].mean()
        # Ultimos seis meses con aceite; pueden pertenecer a etapas separadas.
        g6 = g.loc[g.ACEITE.gt(0)].drop_duplicates("FECHA",keep="last").tail(6)
        inicio_q6 = g6.FECHA.min()
        dias_q6 = int(g6.FECHA.dt.days_in_month.sum())
        completos6 = len(g6)==6
        qo6 = g6.ACEITE.sum()*M3_A_BBL/dias_q6 if completos6 else np.nan
        if vectores is not None and completos6:
            v6 = v.loc[v.FECHA.isin(g6.FECHA)]
            completos_v6 = len(v6)==6 and v6.FECHA.nunique()==6 and v6["Qo (bpd)"].ge(0).all()
            qo6 = (v6["Qo (bpd)"]*v6.FECHA.dt.days_in_month).sum()/dias_q6 if completos_v6 else np.nan
        relacion = qo6/qo3 if pd.notna(qo6) and pd.notna(qo3) and qo3>0 else np.nan
        nota_relacion = "Meses usados: " + ", ".join(g6.FECHA.dt.strftime("%m/%Y"))
        if pd.isna(qo6):
            nota_relacion = "Sin seis meses registrados con aceite valido"
        if pd.isna(qo3) or qo3<=0:
            nota_relacion += "; Qo inicial no positivo o sin dato"
        nota_relacion = nota_relacion.strip("; ")
        liq = g[g[["ACEITE","AGUA"]].ge(0).all(axis=1) & (g.ACEITE+g.AGUA).gt(0)]
        ult = liq.iloc[-1] if not liq.empty else None
        agua = 100*ult.AGUA/(ult.ACEITE+ult.AGUA) if ult is not None else np.nan
        filas.append(dict(
            TERMINACION=term,YACIMIENTO=yac,INICIO=inicio,NP12_MB=np12,QO_3M_INICIAL=qo3,
            QO_6M=qo6,RELACION_QO=relacion,INICIO_QO_6M=inicio_q6,FIN_QO_6M=fin_rga,
            DIAS_QO_6M=dias_q6,MESES_QO_6M=g6.FECHA.nunique(),NOTA_RELACION=nota_relacion,
            RGA_12M=rga,MESES_RGA=int(validos.sum()),INICIO_RGA=desde_rga,FIN_RGA=fin_rga,
            AGUA_RECIENTE=agua,FUENTE_AGUA="Ultima produccion liquida" if ult is not None else "Sin dato",
            FECHA_AGUA=ult.FECHA if ult is not None else pd.NaT,
            MESES_REG_12=g12.FECHA.nunique(),MESES_REG_3=g3.FECHA.nunique(),DIAS_CAL_3M=dias,
            ULTIMO_REGISTRO=g.FECHA.max(),DUPLICADOS=bool(g.FECHA.duplicated().any())))
    columnas = ["TERMINACION","YACIMIENTO","INICIO","NP12_MB","QO_3M_INICIAL","RGA_12M",
                "MESES_RGA","INICIO_RGA","FIN_RGA","AGUA_RECIENTE","FUENTE_AGUA","FECHA_AGUA",
                "MESES_REG_12","MESES_REG_3","DIAS_CAL_3M","ULTIMO_REGISTRO","DUPLICADOS","QO_6M","RELACION_QO","INICIO_QO_6M",
                "FIN_QO_6M","DIAS_QO_6M","MESES_QO_6M","NOTA_RELACION"]
    r = pd.DataFrame(filas,columns=columnas)
    defaults = dict(PRESION_IDPI=np.nan,FECHA_PRESION_IDPI=pd.NaT,FUENTE_PRESION="Sin dato",
                    FECHA_MAPA_PRESION=pd.NaT,ERROR_KRIGING=np.nan,DISTANCIA_PRESION_M=np.nan,NOTA_PRESION="")
    for col,val in defaults.items():
        r[col]=val
    if presiones_mapa is not None and not presiones_mapa.empty:
        pr=presiones_mapa.copy()
        if "YACIMIENTO" in pr:
            pr=pr[clave(pr.YACIMIENTO).eq(yac)].copy()
        pr["TERMINACION"]=clave(pr.TERMINACION)
        if pr.TERMINACION.duplicated().any():
            raise ValueError("Las presiones del mapa deben ser unicas por terminacion.")
        pr=pr.set_index("TERMINACION")
        for col in defaults:
            if col in pr:
                r[col]=r.TERMINACION.map(pr[col])
        r["PRESION_IDPI"]=pd.to_numeric(r.PRESION_IDPI,errors="coerce")
        r.loc[~(r.PRESION_IDPI.gt(0)&np.isfinite(r.PRESION_IDPI)),"PRESION_IDPI"]=np.nan
        r["FUENTE_PRESION"]=r.FUENTE_PRESION.fillna("Sin dato")
        r["NOTA_PRESION"]=r.NOTA_PRESION.fillna("")
    if not r.empty and not muestras.empty:
        m = muestras.copy()
        m.columns = m.columns.str.strip().str.upper()
        m["TERMINACION"] = clave(m["TERMINACION"])
        m["FECHA MUESTREO"] = pd.to_datetime(m["FECHA MUESTREO"], errors="coerce")
        m["% AGUA LAB"] = pd.to_numeric(m["% AGUA LAB"], errors="coerce")
        m = m.loc[
            m["FECHA MUESTREO"].notna()
            & (True if usar_ultimos else m["FECHA MUESTREO"].le(corte))
            & m["% AGUA LAB"].between(0, 100)
        ]
        m = m.groupby(["TERMINACION", "FECHA MUESTREO"], as_index=False)["% AGUA LAB"].mean()
        m = m.sort_values("FECHA MUESTREO").drop_duplicates("TERMINACION", keep="last").set_index("TERMINACION")
        lab = r["TERMINACION"].map(m["% AGUA LAB"])
        tiene_lab = lab.notna()
        if tiene_lab.any():
            r.loc[tiene_lab, "AGUA_RECIENTE"] = lab[tiene_lab]
            r.loc[tiene_lab, "FUENTE_AGUA"] = "Laboratorio"
            r.loc[tiene_lab, "FECHA_AGUA"] = r.loc[tiene_lab, "TERMINACION"].map(m["FECHA MUESTREO"])


    motivos = {"RELACION_QO":"Sin relacion Qo6/Qo3 valida", "NP12_MB":"Np del primer ano incompleta o invalida",
               "QO_3M_INICIAL":"Qo inicial incompleto o invalido",
               "RGA_12M":"Sin meses validos de RGA",
               "AGUA_RECIENTE":"Sin agua disponible","PRESION_IDPI":"Sin presion del mapa"}
    valido = r[list(motivos)].notna().all(axis=1) & ~r.DUPLICADOS.astype(bool)
    r["MOTIVO_IDPI"]=""
    for col,motivo in motivos.items():
        r.loc[r[col].isna(),"MOTIVO_IDPI"]+=motivo+"; "
    r.loc[r.DUPLICADOS.astype(bool),"MOTIVO_IDPI"]+="Meses duplicados; "
    r["MOTIVO_IDPI"]=r.MOTIVO_IDPI.str.rstrip("; ")
    for score,col in [("S_NP12","NP12_MB"),("S_PRESION","PRESION_IDPI"),
                      ("S_RGA","RGA_12M"),("S_QO3","QO_3M_INICIAL"),("S_RELACION","RELACION_QO")]:
        r[score]=np.nan
        puntos=percentil(r.loc[valido,col])
        r.loc[valido,score]=100-puntos if score=="S_RGA" else puntos
    r["S_AGUA"]=(100-r.AGUA_RECIENTE).clip(0,100)
    r["IDPI"]=sum(r[col]*peso for col,peso in PESOS_IDPI.items())
    r.loc[~valido,"IDPI"]=np.nan
    r["IDPI"]=r.IDPI.clip(0,100)
    return r

def interpolar_idpi(mapa, contorno, x_col, y_col, grid_n=180, radio=1500):
    """IDW local: 3-6 coordenadas, dentro de su envolvente y radio maximo."""
    from scipy.spatial import cKDTree, Delaunay, QhullError
    from matplotlib.path import Path
    datos = mapa.copy()
    for col in [x_col, y_col, "IDPI"]:
        datos[col] = pd.to_numeric(datos[col], errors="coerce")
    datos = datos.replace({x_col: {np.inf: np.nan, -np.inf: np.nan},
                           y_col: {np.inf: np.nan, -np.inf: np.nan}})
    datos = datos.loc[datos["IDPI"].between(0, 100)].dropna(subset=[x_col, y_col]).copy()
    datos["VALOR_KRIGING"] = datos["IDPI"]
    puntos = datos.groupby([x_col, y_col], as_index=False)["IDPI"].mean()
    if len(puntos) < 3:
        return None
    xy = puntos[[x_col, y_col]].to_numpy(dtype=float)
    try:
        hull = Delaunay(xy)
    except QhullError:
        return None
    borde = contorno.copy()
    borde.columns = borde.columns.str.strip().str.upper()
    if "ORDEN" in borde:
        borde = borde.sort_values("ORDEN")
    borde[["X", "Y"]] = borde[["X", "Y"]].apply(pd.to_numeric, errors="coerce")
    borde = borde.dropna(subset=["X", "Y"])
    if len(borde) < 3:
        return None
    xi = np.linspace(borde.X.min(), borde.X.max(), grid_n)
    yi = np.linspace(borde.Y.min(), borde.Y.max(), grid_n)
    xx, yy = np.meshgrid(xi, yi)
    grid = np.column_stack([xx.ravel(), yy.ravel()])
    distancia, indice = cKDTree(xy).query(grid, k=min(6, len(xy)))
    vecinos = distancia <= radio
    pesos = np.where(vecinos, 1 / np.maximum(distancia, 1e-6) ** 2, 0)
    total = pesos.sum(axis=1)
    valores = puntos["IDPI"].to_numpy()[indice]
    z = np.divide((pesos * valores).sum(axis=1), total,
                  out=np.full(len(grid), np.nan), where=total > 0)
    mask = (vecinos.sum(axis=1) >= 3) & (hull.find_simplex(grid) >= 0)
    mask &= Path(borde[["X", "Y"]].to_numpy()).contains_points(grid)
    z = np.where(mask, z, np.nan).reshape(xx.shape)
    if not np.isfinite(z).any():
        return None
    return xi, yi, z, datos, 0.0, 100.0, "puntos"
