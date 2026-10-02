
"""Modelo volumetrico FR para la capa de radios de Mapas."""
import sqlite3
import unicodedata
import numpy as np
import pandas as pd
import plotly.graph_objects as go
VERSION_RADIOS = 7

def normalizar(valor):
    return "".join(c for c in unicodedata.normalize("NFKD", str(valor))
                   if not unicodedata.combining(c)).strip().upper()

def leer_evaluaciones(ruta):
    with sqlite3.connect(f"file:{ruta}?mode=ro", uri=True) as con:
        tablas={normalizar(r[0]):r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        nombre=tablas.get("EVALUACIONES") or tablas.get("EVAL")
        if nombre is None:
            return pd.DataFrame(), "No existe Evaluaciones ni EVAL"
        seguro=nombre.replace('"','""')
        e=pd.read_sql_query(f'SELECT * FROM "{seguro}"',con)
    e.columns=[normalizar(c) for c in e.columns]
    return e,nombre

def columna_bo(e):
    return next((c for c in e.columns if normalizar(c) in
        ("BO","BOI","BO [M3/M3]","BO (M3/M3)","BO [RB/STB]","BO (RB/STB)")),None)

def preparar_radios_evaluacion(evaluaciones, acumuladas, fr=.15, bo_global=1.19):
    return pd.concat([
        _calcular_radio(evaluaciones, acumuladas, fr, bo_global, tipo)
        for tipo in ("Np total", "Np primaria")
    ], ignore_index=True)

def _calcular_radio(evaluaciones, acumuladas, fr, bo_global, tipo):
    e=evaluaciones.copy()
    e.columns=[normalizar(c) for c in e.columns]
    for c in ["TERMINACION","YACIMIENTO"]:
        if c not in e: e[c]=""
        e[c]=e[c].fillna("").map(normalizar)
    if "POZO" not in e: e["POZO"]=e.TERMINACION
    e["TIPO_NP"]=tipo
    if tipo == "Np total":
        a=acumuladas[["TERMINACION","NP_BLS"]].copy()
        a["TERMINACION"]=a.TERMINACION.fillna("").map(normalizar)
        if a.TERMINACION.duplicated().any(): raise ValueError("Np duplicada por terminación")
        e=e.drop(columns=["NP_BLS"],errors="ignore").merge(a,on="TERMINACION",how="left",validate="many_to_one")
    else:
        e["NP_BLS"]=pd.to_numeric(e["NP PRIMARIA (BLS)"],errors="coerce") if "NP PRIMARIA (BLS)" in e else np.nan
    for c in ["ESPESOR","POROSIDAD","SW","NP_BLS"]:
        e[c]=pd.to_numeric(e[c],errors="coerce") if c in e else np.nan
    for c in ["POROSIDAD","SW"]:
        e[c]=e[c].where(~e[c].gt(1),e[c]/100)
    bo_col=columna_bo(e)
    e["BO_USADO"]=pd.to_numeric(e[bo_col],errors="coerce") if bo_col else bo_global
    e["FR_USADO"]=fr
    e["MOTIVO"]=""
    reglas=[
        (e.TERMINACION.eq(""),"Sin terminación"),
        (e.duplicated(["TERMINACION","YACIMIENTO"],keep=False),"Evaluaciones duplicadas"),
        (~(np.isfinite(e.NP_BLS)&e.NP_BLS.ge(0)),"Np ausente o inválida"),
        (~(np.isfinite(e.ESPESOR)&e.ESPESOR.gt(0)),"Espesor ausente o inválido"),
        (~(np.isfinite(e.POROSIDAD)&e.POROSIDAD.gt(0)&e.POROSIDAD.le(1)),"Porosidad ausente o inválida"),
        (~(np.isfinite(e.SW)&e.SW.ge(0)&e.SW.lt(1)),"Sw ausente o inválida"),
        (~(np.isfinite(e.BO_USADO)&e.BO_USADO.gt(0)),"Bo ausente o inválido"),
        (~(np.isfinite(e.FR_USADO)&e.FR_USADO.gt(0)&e.FR_USADO.le(1)),"FR fuera de (0,1]"),
    ]
    for mask,motivo in reglas: e.loc[mask,"MOTIVO"]+=motivo+"; "
    valido=e.MOTIVO.eq("")
    e["N_DRENADO_BBL"]=np.nan
    e["AREA_M2"]=np.nan
    with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
        e.loc[valido,"N_DRENADO_BBL"]=e.loc[valido,"NP_BLS"]/e.loc[valido,"FR_USADO"]
        e.loc[valido,"AREA_M2"]=(e.loc[valido,"NP_BLS"]*e.loc[valido,"BO_USADO"]/
            (6.28981*e.loc[valido,"ESPESOR"]*e.loc[valido,"POROSIDAD"]*
             (1-e.loc[valido,"SW"])*e.loc[valido,"FR_USADO"]))
        e["RADIO_M"]=np.sqrt(e.AREA_M2/np.pi)
    mal=valido&~np.isfinite(e[["N_DRENADO_BBL","AREA_M2","RADIO_M"]]).all(axis=1)
    e.loc[mal,"MOTIVO"]+="Resultado no finito; "
    e.loc[mal,["N_DRENADO_BBL","AREA_M2","RADIO_M"]]=np.nan
    e["MOTIVO"]=e.MOTIVO.str.rstrip("; ")
    e["ESTADO_DATOS"]=np.where(e.MOTIVO.eq(""),"Calculado","Sin datos suficientes")
    return e

def agregar_radios_evaluacion(fig,radios,mapa,x_col,y_col,gis=False):
    resultados=[]
    for _,grupo in radios.groupby("TIPO_NP",sort=False):
        resultados.append(_agregar_radio(fig,grupo,mapa,x_col,y_col,gis))
    return pd.concat(resultados,ignore_index=True) if resultados else radios.iloc[:0]

def _agregar_radio(fig,radios,mapa,x_col,y_col,gis=False):
    coords=mapa[["TERMINACION",x_col,y_col]].copy()
    coords["TERMINACION"]=coords.TERMINACION.fillna("").map(normalizar)
    for c in [x_col,y_col]:
        coords[c]=pd.to_numeric(coords[c],errors="coerce").replace([np.inf,-np.inf],np.nan)
    coords=coords.dropna(subset=[x_col,y_col]).drop_duplicates("TERMINACION")
    r=radios.merge(coords,on="TERMINACION",how="inner",validate="many_to_one")
    r=r.loc[r.MOTIVO.eq("")&r.RADIO_M.ge(0)]
    if r.empty:return r
    tipo=r.TIPO_NP.iloc[0]
    color="#2563eb" if tipo=="Np total" else "#f97316"
    theta=np.linspace(0,2*np.pi,121)
    if gis:
        from pyproj import Transformer,Geod
        trans=Transformer.from_crs("EPSG:26714","EPSG:4326",always_xy=True)
        geod=Geod(ellps="WGS84")
    xs=[];ys=[];custom=[];centros_x=[];centros_y=[];centros_d=[]
    for _,row in r.iterrows():
        if gis:
            cx,cy=trans.transform(row[x_col],row[y_col])
            x,y,_=geod.fwd(np.full(len(theta),cx),np.full(len(theta),cy),
                np.degrees(theta),np.full(len(theta),row.RADIO_M))
        else:
            cx,cy=row[x_col],row[y_col]
            x=cx+row.RADIO_M*np.cos(theta);y=cy+row.RADIO_M*np.sin(theta)
        dato=[row.POZO,row.TERMINACION,row.NP_BLS/1e6,row.ESPESOR,row.POROSIDAD,
              row.SW,row.BO_USADO,row.FR_USADO*100,row.N_DRENADO_BBL/1e6,row.AREA_M2,row.RADIO_M]
        xs.extend(list(x)+[None]);ys.extend(list(y)+[None]);custom.extend([dato]*len(theta)+[[None]*11])
        centros_x.append(cx);centros_y.append(cy);centros_d.append(dato)
    hover=("<b>"+tipo+"</b><br><b>Pozo: %{customdata[0]}</b><br>%{customdata[1]}<br>Np: %{customdata[2]:,.3f} MMbl<br>"
        "h: %{customdata[3]:,.2f} m<br>Porosidad: %{customdata[4]:.4f}<br>Sw: %{customdata[5]:.4f}<br>"
        "Bo: %{customdata[6]:.3f}<br>FR: %{customdata[7]:.0f}%<br>N drenado: %{customdata[8]:,.3f} MMbl<br>"
        "Área drenada: %{customdata[9]:,.1f} m²<br>Radio: %{customdata[10]:,.1f} m<extra></extra>")
    opts=dict(name="Radio Drene Volumétrico" if tipo=="Np total" else "Radio Drene Primaria",legendgroup=f"radios_fr_{tipo}",
        customdata=custom,hovertemplate=hover)
    if gis:
        fig.add_trace(go.Scattermapbox(lon=xs,lat=ys,mode="markers",marker=dict(size=3,color=color),**opts))
    else:
        fig.add_trace(go.Scatter(x=xs,y=ys,mode="lines",line=dict(color=color,width=2,dash="dot"),**opts))
    centro=dict(mode="markers",marker=dict(size=12,color="rgba(0,0,0,0)"),customdata=centros_d,
                hovertemplate=hover,showlegend=False,legendgroup=f"radios_fr_{tipo}",name=f"Datos radio {tipo}")
    fig.add_trace(go.Scattermapbox(lon=centros_x,lat=centros_y,**centro) if gis else
                  go.Scatter(x=centros_x,y=centros_y,**centro))
    return r
