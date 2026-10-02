"""Screening sobre resumen compartido de Mapas y ultima produccion."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

VERSION_SCREENING = 10
M3_A_BBL = 6.289810770
M3_A_PC = 35.3147

def _clave(s):
    return s.fillna("").astype(str).str.strip().str.upper()

def preparar_base_screening(produccion, acumuladas, estados, coordenadas):
    """Se ejecuta una vez en cache. No integra volumenes de la historia."""
    p=produccion.copy()
    p.columns=p.columns.str.upper().str.strip()
    for c in ["TERMINACION","YACIMIENTO","POZO_FISICO"]:
        p[c]=_clave(p[c])
    p["FECHA"]=pd.to_datetime(p.FECHA,errors="coerce")
    p=p.dropna(subset=["FECHA"]).sort_values("FECHA")
    keys=["POZO_FISICO","YACIMIENTO"]
    # Asociacion compacta: una fila por terminacion, igual que las acumuladas de Mapas.
    terms=p.drop_duplicates("TERMINACION",keep="last")
    a=acumuladas[["TERMINACION","NP_BLS","WP_BLS"]].copy()
    a["TERMINACION"]=_clave(a.TERMINACION)
    if a.TERMINACION.duplicated().any():
        raise ValueError("Acumuladas de Mapas duplicadas por terminacion")
    term_acum=terms[["TERMINACION"]+keys].merge(a,on="TERMINACION",how="left",validate="one_to_one")
    tot=term_acum.groupby(keys)[["NP_BLS","WP_BLS"]].sum(min_count=1)
    # No aceptar acumuladas parciales si falta una terminacion del pozo.
    faltan=term_acum[["NP_BLS","WP_BLS"]].isna().assign(
        POZO_FISICO=term_acum.POZO_FISICO,YACIMIENTO=term_acum.YACIMIENTO).groupby(keys).any()
    tot=tot.mask(faltan)
    r=tot.rename(columns={"NP_BLS":"NP_MB","WP_BLS":"WP_MB"}).div(1000).reset_index()
    # INJ positivo identifica registros de inyeccion, no produccion actual.
    inj=pd.to_numeric(p["INJ"],errors="coerce").fillna(0) if "INJ" in p else pd.Series(0.,index=p.index)
    no_inyeccion=~inj.gt(0)
    agosto=p.FECHA.dt.to_period("M").eq(pd.Period("2026-08",freq="M"))
    con_produccion=p[["ACEITE","AGUA","GAS"]].apply(pd.to_numeric,errors="coerce").gt(0).any(axis=1)
    operando=p.loc[no_inyeccion & agosto & con_produccion,keys].drop_duplicates()
    operando["OPERANDO_AGOSTO_2026"]=True
    r=r.merge(operando,on=keys,how="left",validate="one_to_one")
    r["OPERANDO_AGOSTO_2026"]=r.OPERANDO_AGOSTO_2026.eq(True)
    registros_iny=p.loc[~no_inyeccion].groupby(keys).size().rename("REGISTROS_INYECCION_EXCLUIDOS")
    r=r.merge(registros_iny,on=keys,how="left")
    r["REGISTROS_INYECCION_EXCLUIDOS"]=r.REGISTROS_INYECCION_EXCLUIDOS.fillna(0).astype(int)
    # Solo el ultimo registro no inyector; no sumar tasas de fechas distintas.
    prod=p.loc[no_inyeccion].copy()
    fecha=prod.groupby(keys).FECHA.transform("max")
    ult=prod.loc[prod.FECHA.eq(fecha)].copy()
    dias=ult.FECHA.dt.days_in_month
    for tasa,vol,factor in [("QO (BPD)","ACEITE",M3_A_BBL),
                            ("QW (BPD)","AGUA",M3_A_BBL),("QG (PCD)","GAS",M3_A_PC)]:
        fallback=pd.to_numeric(ult[vol],errors="coerce")*factor/dias
        ult[tasa]=pd.to_numeric(ult[tasa],errors="coerce").fillna(fallback) if tasa in ult else fallback
        ult.loc[~np.isfinite(ult[tasa])|ult[tasa].lt(0),tasa]=np.nan
    tasas=ult.groupby(keys)[["QO (BPD)","QW (BPD)","QG (PCD)"]].sum(min_count=1)
    tasas=tasas.rename(columns={"QO (BPD)":"QO_ACTUAL","QW (BPD)":"QW_ACTUAL","QG (PCD)":"QG_ACTUAL"})
    r=r.merge(tasas,on=keys,how="left").merge(ult.groupby(keys).FECHA.max().rename("FECHA_ULTIMO_DATO"),on=keys,how="left")
    r["RGA_ACTUAL"]=r.QG_ACTUAL/r.QO_ACTUAL.where(r.QO_ACTUAL.gt(0))
    # Reutilizar directamente RGA calculada cuando hay una sola terminacion en el ultimo dato.
    if "RGA (PC/BL)" in ult:
        unicos=ult.loc[~ult.duplicated(keys,keep=False)].set_index(keys)["RGA (PC/BL)"]
        idx=pd.MultiIndex.from_frame(r[keys])
        directa=pd.Series(pd.to_numeric(unicos,errors="coerce").reindex(idx).to_numpy(),index=r.index)
        r["RGA_ACTUAL"]=directa.where(directa.ge(0)&np.isfinite(directa)&r.QO_ACTUAL.gt(0),r.RGA_ACTUAL)
    r["WOR_ACTUAL"]=r.QW_ACTUAL/r.QO_ACTUAL.where(r.QO_ACTUAL.gt(0))
    liq=r.QO_ACTUAL+r.QW_ACTUAL
    r["WC_ACTUAL"]=100*r.QW_ACTUAL/liq.where(liq.gt(0))
    r["FUENTE_AGUA"]=np.where(r.WC_ACTUAL.notna(),"Produccion","Sin dato")
    r["FECHA_AGUA"]=r.FECHA_ULTIMO_DATO.where(r.WC_ACTUAL.notna())
    r["RWA"]=r.WP_MB/r.NP_MB.where(r.NP_MB.gt(0))
    r["EN_GRAFICO"]=r.NP_MB.gt(0)&r.WP_MB.gt(0)&np.isfinite(r.NP_MB)&np.isfinite(r.WP_MB)
    r["MOTIVO"]=""
    for col,nombre in [("NP_MB","Np"),("WP_MB","Wp")]:
        r.loc[~np.isfinite(r[col]),"MOTIVO"]+=nombre+": sin acumulada valida de Mapas; "
        r.loc[r[col].le(0),"MOTIVO"]+=nombre+" <= 0: fuera de escala logaritmica; "
    r["MOTIVO"]=r.MOTIVO.str.rstrip("; ")
    r["DIAGNOSTICO"]=np.select([r.RWA.lt(1),r.RWA.between(1,10),r.RWA.gt(10)],
        ["Wp/Np < 1","1 <= Wp/Np <= 10","Wp/Np > 10"],default="Sin relacion calculable")
    es=estados.copy()
    es["POZO"]=_clave(es.POZO)
    es["ESTADO"]=es.ESTADO.fillna("Sin estado")
    estado=es.groupby("POZO").ESTADO.agg(lambda x:" / ".join(sorted(set(x))))
    r["ESTADO"]=r.POZO_FISICO.map(estado).fillna("Sin estado")
    r["TERMINACIONES"]=term_acum.groupby(keys).TERMINACION.agg(tuple).reindex(pd.MultiIndex.from_frame(r[keys])).to_numpy()
    co=coordenadas.copy()
    co.columns=co.columns.str.upper().str.strip()
    for col in ["TERMINACION","YACIMIENTO"]:
        co[col]=_clave(co[col])
    for col in ["CIMA X UTM","CIMA Y UTM","FONDO X UTM","FONDO Y UTM"]:
        co[col]=pd.to_numeric(co[col],errors="coerce").replace([np.inf,-np.inf],np.nan) if col in co else np.nan
    cima=co[["CIMA X UTM","CIMA Y UTM"]].notna().all(axis=1)
    co["X"]=co["CIMA X UTM"].where(cima,co["FONDO X UTM"])
    co["Y"]=co["CIMA Y UTM"].where(cima,co["FONDO Y UTM"])
    co=co.dropna(subset=["X","Y"])
    co=terms[["TERMINACION","YACIMIENTO","POZO_FISICO","FECHA"]].merge(
        co[["TERMINACION","YACIMIENTO","X","Y"]],on=["TERMINACION","YACIMIENTO"],how="inner")
    co=co.sort_values(["FECHA","TERMINACION"]).drop_duplicates(keys,keep="last")
    r=r.merge(co[keys+["X","Y"]],on=keys,how="left",validate="one_to_one")
    return r.rename(columns={"POZO_FISICO":"POZO"})

def actualizar_muestras_screening(base,muestras):
    """Une el ultimo muestreo por pozo/yacimiento, sin recorrer historia."""
    r=base.copy()
    if muestras is None or muestras.empty or r.empty:
        return r
    lab=muestras.copy()
    lab.columns=lab.columns.str.upper().str.strip()
    for c in ["TERMINACION","POZO"]:
        lab[c]=_clave(lab[c]) if c in lab else ""
    lab["FECHA MUESTREO"]=pd.to_datetime(lab["FECHA MUESTREO"],errors="coerce")
    lab["% AGUA LAB"]=pd.to_numeric(lab["% AGUA LAB"],errors="coerce")
    lab=lab.loc[lab["FECHA MUESTREO"].notna()&lab["% AGUA LAB"].between(0,100)]
    mapping=r[["POZO","YACIMIENTO","TERMINACIONES"]].explode("TERMINACIONES").rename(columns={"TERMINACIONES":"TERMINACION"})
    keys=["TERMINACION"]
    if "YACIMIENTO" in lab:
        lab["YACIMIENTO"]=_clave(lab.YACIMIENTO)
        keys.append("YACIMIENTO")
    unidos=lab.drop(columns="POZO").merge(mapping,on=keys,how="inner")
    sin_term=lab.loc[lab.TERMINACION.eq("")]
    if not sin_term.empty:
        # Un nombre sin terminacion solo es seguro si tiene un unico yacimiento.
        seguros=r.loc[~r.POZO.duplicated(keep=False),["POZO","YACIMIENTO"]]
        fallback=sin_term.merge(seguros,on=["POZO","YACIMIENTO"] if "YACIMIENTO" in sin_term else ["POZO"],how="inner")
        unidos=pd.concat([unidos,fallback],ignore_index=True)
    if unidos.empty:
        return r
    keys=["POZO","YACIMIENTO"]
    fecha=unidos.groupby(keys)["FECHA MUESTREO"].transform("max")
    ultimo=unidos.loc[unidos["FECHA MUESTREO"].eq(fecha)].groupby(keys).agg(
        AGUA_LAB=("% AGUA LAB","mean"),FECHA_LAB=("FECHA MUESTREO","max"))
    r=r.merge(ultimo,on=keys,how="left",validate="one_to_one")
    tiene=r.AGUA_LAB.notna()
    r.loc[tiene,"WC_ACTUAL"]=r.loc[tiene,"AGUA_LAB"]
    r.loc[tiene,"FECHA_AGUA"]=r.loc[tiene,"FECHA_LAB"]
    r.loc[tiene,"FUENTE_AGUA"]="Laboratorio"
    return r.drop(columns=["AGUA_LAB","FECHA_LAB"])

def crear_figura_screening(resultados, linea_01=False, mostrar_nombres=True):
    d=resultados.loc[resultados.EN_GRAFICO.eq(True)].copy()
    fig=go.Figure()
    if not d.empty:
        lo,hi=np.log10(d.NP_MB.min()),np.log10(d.NP_MB.max())
        margen=max(.15,(hi-lo)*.06)
        x=np.logspace(lo-margen,hi+margen,100)
        for k,color in [(1,"#555555"),(10,"#c0392b")]+([(0.1,"#2980b9")] if linea_01 else []):
            fig.add_trace(go.Scatter(x=x,y=k*x,mode="lines",name=f"Wp/Np = {k:g}",
                line=dict(color=color,dash="dash",width=1.5),
                hovertemplate=f"Wp/Np = {k:g}<extra></extra>"))
        maxqo=d.QO_ACTUAL.max()
        d["TAMANO"]=10+22*np.sqrt(d.QO_ACTUAL.fillna(0).clip(lower=0)/maxqo) if pd.notna(maxqo) and maxqo>0 else 10.
        campos=["POZO","YACIMIENTO","NP_MB","WP_MB","RWA","QO_ACTUAL","QW_ACTUAL",
                "WC_ACTUAL","WOR_ACTUAL","RGA_ACTUAL","FECHA_ULTIMO_DATO","FUENTE_AGUA","FECHA_AGUA"]
        cd=d[campos].copy()
        for c in campos[2:10]:
            cd[c]=cd[c].map(lambda v:"N/D" if pd.isna(v) else f"{v:,.2f}")
        for c in ["FECHA_ULTIMO_DATO","FECHA_AGUA"]:
            cd[c]=pd.to_datetime(cd[c]).dt.strftime("%m/%Y").fillna("N/D")
        labels=["Pozo","Yacimiento","Np [Mb]","Wp [Mb]","Wp/Np","Qo actual [bpd]","Qw actual [bpd]",
                "Corte de agua [%]","WOR actual","RGA actual [pc/bl]","Fecha último dato",
                "Fuente agua","Fecha agua"]
        hover="<br>".join(label+": %{customdata["+str(i)+"]}" for i,label in enumerate(labels))+"<extra></extra>"
        for con_wc in [True,False]:
            mask=d.WC_ACTUAL.notna().eq(con_wc)
            z=d.loc[mask]
            if z.empty: continue
            marker=dict(size=z.TAMANO,sizemode="diameter",opacity=.8,line=dict(width=.6,color="#333333"))
            marker.update(dict(color=z.WC_ACTUAL,colorscale=[[0,"#2ca02c"],[1,"#0066ff"]],cmin=0,cmax=100,
                colorbar=dict(title="Agua [%]")) if con_wc else dict(color="#909090"))
            fig.add_trace(go.Scatter(x=z.NP_MB,y=z.WP_MB,
                mode="markers+text" if mostrar_nombres else "markers",
                text=z.POZO if mostrar_nombres else None,textposition="top center",
                textfont=dict(size=10,color="#374151",family="Arial"),cliponaxis=False,
                name="Pozos" if con_wc else "Sin corte de agua",marker=marker,
                customdata=cd.loc[mask].to_numpy(),hovertemplate=hover))
        fig.update_xaxes(range=[lo-margen,hi+margen])
    fig.update_layout(title="Diagnóstico Np vs Wp — Screening de producción de agua",
        xaxis=dict(title="Np acumulada [Mb]",type="log"),
        yaxis=dict(title="Wp acumulada [Mb]",type="log"),
        template="plotly_white",height=670,legend=dict(orientation="h",y=1.08),
        margin=dict(t=110),hovermode="closest")
    aplicar_formato_screening(fig,"Diagnóstico Np vs Wp")
    return fig

def preparar_historia_wor(vectores):
    """Reutiliza Np en Mb y gastos calculados; no integra volumenes."""
    p=vectores.copy()
    p.columns=p.columns.str.upper().str.strip()
    for c in ["POZO_FISICO","YACIMIENTO","TERMINACION"]:
        p[c]=_clave(p[c])
    p["FECHA"]=pd.to_datetime(p.FECHA,errors="coerce").dt.to_period("M").dt.to_timestamp()
    p=p.dropna(subset=["FECHA"]).sort_values("FECHA")
    for c in ["NP (MBL)","QO (BPD)","QW (BPD)","INJ"]:
        p[c]=pd.to_numeric(p[c],errors="coerce").replace([np.inf,-np.inf],np.nan)
    salida=[]
    for (pozo,yac),g in p.groupby(["POZO_FISICO","YACIMIENTO"],sort=False):
        fechas=pd.date_range(g.FECHA.min(),g.FECHA.max(),freq="MS")
        # Conservar la acumulada de terminaciones antiguas al sumar el pozo.
        np_term=g.pivot_table(index="FECHA",columns="TERMINACION",values="NP (MBL)",aggfunc="last")
        np_total=np_term.reindex(fechas).ffill().sum(axis=1,min_count=1)
        productor=g.loc[~g.INJ.fillna(0).gt(0)].copy()
        for c in ["QO (BPD)","QW (BPD)"]:
            productor.loc[productor[c].lt(0),c]=np.nan
        tasas=productor.groupby("FECHA")[["QO (BPD)","QW (BPD)"]].sum(min_count=1).reindex(fechas)
        h=tasas.rename(columns={"QO (BPD)":"QO","QW (BPD)":"QW"})
        h["NP_MB"]=np_total
        h["WOR"]=h.QW/h.QO.where(h.QO.gt(0))
        h["POZO"]=pozo
        h["YACIMIENTO"]=yac
        h.index.name="FECHA"
        salida.append(h.reset_index())
    return pd.concat(salida,ignore_index=True) if salida else pd.DataFrame(
        columns=["FECHA","QO","QW","NP_MB","WOR","POZO","YACIMIENTO"])


def crear_figura_historia_wor(historia, logaritmico=True):
    fig=go.Figure()
    for pozo,g in historia.groupby("POZO",sort=True):
        g=g.sort_values("FECHA")
        valido=g.NP_MB.ge(0)&np.isfinite(g.NP_MB)&np.isfinite(g.WOR)
        valido &= g.WOR.gt(0) if logaritmico else g.WOR.ge(0)
        if not valido.any():
            continue
        datos=g[["FECHA","QO","QW","YACIMIENTO"]].copy()
        datos["FECHA"]=datos.FECHA.dt.strftime("%m/%Y")
        fig.add_trace(go.Scattergl(x=g.NP_MB,y=g.WOR.where(valido),
            mode="lines+markers",name=pozo,connectgaps=False,
            line=dict(width=1.8),marker=dict(size=4),
            customdata=datos.to_numpy(),
            hovertemplate="<b>"+pozo+"</b><br>Yacimiento: %{customdata[3]}<br>"
                "Fecha: %{customdata[0]}<br>Np: %{x:,.2f} Mb<br>WOR: %{y:,.3f}<br>"
                "Qo: %{customdata[1]:,.2f} bpd<br>Qw: %{customdata[2]:,.2f} bpd<extra></extra>"))
    aplicar_formato_screening(fig,"Trayectoria histórica — WOR vs Np")
    fig.update_xaxes(title="Np acumulada [Mb]",type="linear")
    fig.update_yaxes(title="WOR = Qw/Qo [bbl/bbl]",type="log" if logaritmico else "linear")
    return fig


def preparar_datos_chan(historia):
    """Dias calendario acumulados y dWOR/dt por tramos mensuales validos."""
    h=historia.copy().sort_values("FECHA")
    if h.empty:
        return h.assign(DIAS_MES=pd.Series(dtype=float),
                        DIAS_ACUMULADOS=pd.Series(dtype=float),
                        DERIVADA_WOR=pd.Series(dtype=float))
    if h[["POZO","YACIMIENTO"]].drop_duplicates().shape[0] != 1:
        raise ValueError("Chan requiere un solo pozo y yacimiento")
    h["FECHA"]=pd.to_datetime(h.FECHA).dt.to_period("M").dt.to_timestamp()
    if h.FECHA.duplicated().any():
        raise ValueError("La historia debe tener un registro por mes")
    inicio=h.loc[h.QO.gt(0)|h.QW.gt(0),"FECHA"].min()
    if pd.isna(inicio):
        return h.iloc[:0].assign(DIAS_MES=pd.Series(dtype=float),
            DIAS_ACUMULADOS=pd.Series(dtype=float),DERIVADA_WOR=pd.Series(dtype=float))
    h=h.set_index("FECHA").reindex(pd.date_range(inicio,h.FECHA.max(),freq="MS"))
    h.index.name="FECHA"
    h=h.reset_index()
    h["DIAS_MES"]=h.FECHA.dt.days_in_month
    h["DIAS_ACUMULADOS"]=h.DIAS_MES.cumsum()
    h["WOR"]=h.QW.where(h.QW.ge(0))/h.QO.where(h.QO.gt(0))
    h["WOR"]=h.WOR.replace([np.inf,-np.inf],np.nan)
    h["DERIVADA_WOR"]=np.nan
    valido=h.WOR.notna()
    bloques=(~valido).cumsum()
    # No derivar a traves de cierres, inyeccion o huecos en la historia.
    for _,g in h.loc[valido].groupby(bloques[valido]):
        if len(g)>=2:
            h.loc[g.index,"DERIVADA_WOR"]=np.gradient(
                g.WOR.to_numpy(dtype=float),g.DIAS_ACUMULADOS.to_numpy(dtype=float),
                edge_order=2 if len(g)>=3 else 1)
    return h


def ajustar_polinomio_chan(t,y):
    """Minimos cuadrados de grado 4 en unidades originales, con dominio escalado."""
    t=np.asarray(t,dtype=float); y=np.asarray(y,dtype=float)
    valido=np.isfinite(t)&np.isfinite(y)&(t>0)
    t,y=t[valido],y[valido]
    if len(np.unique(t))<5:
        return None
    modelo=np.polynomial.Polynomial.fit(t,y,deg=3)
    x=np.geomspace(t.min(),t.max(),400)
    return x,modelo(x)


def crear_figura_chan(datos,pozo):
    fig=go.Figure()
    avisos=[]
    for columna,nombre,color,unidad in [
        ("WOR","WOR","#2878b5","bbl/bbl"),
        ("DERIVADA_WOR","WOR′ = dWOR/dt","#e34a4a","1/día")]:
        g=datos
        visibles=g[columna].gt(0)&np.isfinite(g[columna])
        if visibles.any():
            z=g.loc[visibles]
            fig.add_trace(go.Scatter(x=z.DIAS_ACUMULADOS,y=z[columna],
                mode="markers",name=nombre,marker=dict(color=color,size=6,symbol="circle-open"),
                customdata=z.FECHA.dt.strftime("%m/%Y").to_numpy(),
                hovertemplate="Fecha: %{customdata}<br>Días acumulados: %{x:,.0f}<br>"
                    +nombre+": %{y:.5g} "+unidad+"<extra></extra>"))
        ajuste=ajustar_polinomio_chan(g.DIAS_ACUMULADOS,g[columna])
        if ajuste is None:
            avisos.append(nombre+": se requieren al menos 5 meses con valores válidos para el ajuste de grado 4.")
        else:
            x,y=ajuste
            fig.add_trace(go.Scatter(x=x,y=np.where(np.isfinite(y)&(y>0),y,np.nan),
                mode="lines",connectgaps=False,name=nombre+" · ajuste grado 4",
                line=dict(color=color,width=3),
                hovertemplate="Días acumulados: %{x:,.0f}<br>Ajuste: %{y:.5g} "+unidad+"<extra></extra>"))
        cantidad=int((g[columna].notna()&g[columna].le(0)).sum())
        if cantidad:
            avisos.append(f"{nombre}: {cantidad} valores cero o negativos no visibles en escala logarítmica.")
    aplicar_formato_screening(fig,"Diagnóstico de Chan — "+str(pozo))
    fig.update_xaxes(title="Tiempo acumulado [días calendario]",type="log")
    fig.update_yaxes(title="WOR [bbl/bbl] · dWOR/dt [1/día]",type="log")
    return fig,avisos


def crear_scatter_actual(resultados, variable="WOR_ACTUAL", logaritmico=False, mostrar_nombres=True):
    """Scatter del resumen filtrado; no carga ni recalcula historia."""
    if variable not in ("WOR_ACTUAL","WP_MB"):
        raise ValueError("Variable no soportada")
    d=resultados.copy()
    valido=np.isfinite(d.NP_MB)&np.isfinite(d[variable])
    valido &= (d.NP_MB.gt(0)&d[variable].gt(0) if logaritmico
               else d.NP_MB.ge(0)&d[variable].ge(0))
    d=d.loc[valido].copy()
    fig=go.Figure()
    es_wor=variable=="WOR_ACTUAL"
    qo=d.QO_ACTUAL.where(np.isfinite(d.QO_ACTUAL)&d.QO_ACTUAL.ge(0))
    maxqo=qo.max()
    limite_qo=float(maxqo) if pd.notna(maxqo) and maxqo>0 else 1.
    tamanos=10+22*np.sqrt(qo.fillna(0)/limite_qo)
    campos=["POZO","YACIMIENTO","NP_MB","WP_MB","WOR_ACTUAL","QO_ACTUAL","QW_ACTUAL",
            "WC_ACTUAL","FUENTE_AGUA","FECHA_AGUA","FECHA_ULTIMO_DATO"]
    cd=d[campos].copy()
    for c in campos[2:8]:
        cd[c]=cd[c].map(lambda v:"N/D" if pd.isna(v) or not np.isfinite(v) else f"{v:,.3f}")
    for c in ["FECHA_AGUA","FECHA_ULTIMO_DATO"]:
        cd[c]=pd.to_datetime(cd[c]).dt.strftime("%m/%Y").fillna("N/D")
    etiquetas=["Pozo","Yacimiento","Np [Mb]","Wp [Mb]","WOR actual","Qo actual [bpd]",
               "Qw actual [bpd]","Agua actual [%]","Fuente agua","Fecha agua","Fecha producción"]
    hover="<br>".join(label+": %{customdata["+str(i)+"]}" for i,label in enumerate(etiquetas))+"<extra></extra>"
    grupos=[("Con Qo",qo.notna()),
        ("Sin Qo",qo.isna())] if es_wor else [
        ("Con dato de agua",d.WC_ACTUAL.between(0,100)),
        ("Sin dato de agua",~d.WC_ACTUAL.between(0,100))]
    for nombre,mask in grupos:
        z=d.loc[mask]
        if z.empty:
            continue
        marker=dict(size=tamanos.loc[mask] if es_wor else 12,opacity=.8,
                    line=dict(color="#333333",width=.6),sizemode="diameter")
        if es_wor and nombre=="Con Qo":
            marker.update(color=qo.loc[mask],
                colorscale=[[0,"#2ca02c"],[1,"#0066ff"]],cmin=0,cmax=limite_qo,
                colorbar=dict(title="Qo actual [bpd]"))
        elif nombre=="Con dato de agua":
            marker.update(color=z.WC_ACTUAL,colorscale=[[0,"#2ca02c"],[1,"#0066ff"]],
                          cmin=0,cmax=100,colorbar=dict(title="Agua [%]"))
        else:
            marker["color"]="#909090"
        fig.add_trace(go.Scatter(x=z.NP_MB,y=z[variable],
            mode="markers+text" if mostrar_nombres else "markers",name=nombre,
            text=z.POZO if mostrar_nombres else None,textposition="top center",
            textfont=dict(size=10,color="#374151",family="Arial"),cliponaxis=False,
            marker=marker,customdata=cd.loc[mask].to_numpy(),hovertemplate=hover))
    titulo="Np vs WOR actual · color y tamaño: Qo actual" if es_wor else "Np vs Wp · color: agua actual"
    aplicar_formato_screening(fig,titulo)
    fig.update_xaxes(title="Np acumulada [Mb]",type="log" if logaritmico else "linear")
    fig.update_yaxes(title="WOR actual = Qw/Qo [bbl/bbl]" if es_wor else "Wp acumulada [Mb]",
                     type="log" if logaritmico else "linear")
    return fig,len(d)


def mostrar_screening(resumen,contorno=None,cargar_historia=None):
    import streamlit as st
    st.subheader("Screening Pozos")
    st.caption("Modelo 1 — Np vs Wp log–log")
    if resumen.empty:
        st.info("No hay datos de producción disponibles.")
        return
    yacs=sorted(resumen.YACIMIENTO.dropna().unique())
    c1,_=st.columns([1,1])
    yac=c1.selectbox("Yacimiento",yacs,key="screen_yac")
    r=resumen.loc[resumen.YACIMIENTO.eq(yac)].copy()
    opciones=sorted(r.ESTADO.unique())
    seleccion=st.multiselect("Estado del pozo",opciones,default=opciones,key="screen_estado_"+yac)
    r=r.loc[r.ESTADO.isin(seleccion)].copy()
    solo_operando=st.checkbox("Solo pozos operando en agosto de 2026",key="screen_solo_operando")
    if solo_operando:
        r=r.loc[r.OPERANDO_AGOSTO_2026].copy()
    st.caption("Operando en agosto de 2026: registro en ese mes con aceite, agua o gas positivo, "
               "sin inyección positiva en INJ. Se combina con el filtro de estado.")
    linea=st.checkbox("Mostrar relación Wp/Np = 0.1",key="screen_linea01")
    mostrar_nombres=st.checkbox("Mostrar nombres de pozos en los scatter",value=True,key="screen_scatter_nombres")

    st.caption("Última información disponible por pozo. Np y Wp se toman de las acumuladas "
        "de Mapas; Qo, Qw y RGA del último registro sin inyección positiva en INJ. "
        "Agua: último muestreo disponible; sin muestreo, corte de agua de ese registro. "
        "Las fechas de producción y muestreo pueden ser distintas. Un punto por pozo físico "
        "y yacimiento; estado del catálogo actual.")
    c1,c2,c3=st.columns(3)
    c1.metric("Pozos en tabla",len(r))
    c2.metric("Pozos en gráfico",int(r.EN_GRAFICO.sum()))
    c3.metric("Wp/Np > 10",int(r.RWA.gt(10).sum()))
    izquierda,derecha=st.columns([1.2,1])
    with izquierda:
        if r.EN_GRAFICO.any():
            st.plotly_chart(crear_figura_screening(r,linea,mostrar_nombres),width="stretch",key="screen_plot")
        else:
            st.info("No hay pozos representables en log–log. Consulta los motivos en la tabla.")
    with derecha:
        mapa=r
        st.plotly_chart(crear_mapa_screening(mapa,contorno,yac),width="stretch",key="screen_map")
        st.caption(f"{mapa.X.notna().sum()} de {len(mapa)} pozos con coordenadas. "
                   "Verde: <1 · Naranja: 1 a 10 · Rojo: >10 · Gris: sin relación. "
                   "Los pozos sin coordenadas permanecen en la tabla.")
    st.markdown("**Lectura:** debajo de 1:1 hay más aceite acumulado que agua; entre 1:1 y 10:1 "
        "aumenta la contribución acumulada de agua; por encima de 10:1 se activa una bandera diagnóstica. "
        "Investigar Np alta y Wp/Np alto junto con aceite reciente significativo y corte de agua alto. "
        "**El gráfico no determina candidatos a microgel.**")
    st.markdown("**Trayectorias históricas — WOR vs Np**")
    opciones_hist=sorted(r.POZO.unique())
    preferidos=r.sort_values(["QO_ACTUAL","RWA"],ascending=False).POZO.head(5).tolist()
    seleccion_key="screen_hist_pozos_"+str(yac)
    if seleccion_key in st.session_state:
        st.session_state[seleccion_key]=[p for p in st.session_state[seleccion_key] if p in opciones_hist]
    candidatos=st.multiselect("Pozos para comparar su historia",opciones_hist,
        default=None if seleccion_key in st.session_state else preferidos,key=seleccion_key)
    log_wor=st.checkbox("Escala logarítmica de WOR",value=True,key="screen_hist_log")
    st.caption("Selección inicial: hasta cinco pozos con mayor Qo actual entre los filtrados. "
        "Cada curva sigue los meses en orden cronológico usando Np, Qo y Qw de Producción por pozo. "
        "WOR se calcula con gastos de producción, no con muestreos de laboratorio. "
        "Se interrumpe la curva en meses sin datos válidos o con inyección positiva; "
        "Qo = 0 no permite calcular WOR. En escala logarítmica también se omite WOR = 0.")
    if candidatos and cargar_historia is not None:
        historia=cargar_historia(yac,tuple(sorted(candidatos)))
        figura_hist=crear_figura_historia_wor(historia,log_wor)
        if figura_hist.data:
            st.plotly_chart(figura_hist,width="stretch",key="screen_hist_plot")
        else:
            st.info("Los pozos seleccionados no tienen puntos válidos para esta escala.")
        sin_curva=sorted(set(candidatos)-{t.name for t in figura_hist.data})
        if sin_curva:
            st.caption("Sin trayectoria representable: "+", ".join(sin_curva))
    else:
        st.info("Selecciona pozos para visualizar sus trayectorias.")
    st.caption("Un incremento rápido del WOR puede ser consistente con canalización, comunicación "
        "preferencial o irrupción de agua; por sí solo no demuestra el mecanismo.")
    st.markdown("**Gráfico de Chan — WOR y derivada vs tiempo**")
    if opciones_hist and cargar_historia is not None:
        chan_key="screen_chan_pozo_"+str(yac)
        if chan_key in st.session_state and st.session_state[chan_key] not in opciones_hist:
            del st.session_state[chan_key]
        col_chan,_=st.columns([1,2])
        pozo_chan=col_chan.selectbox("Pozo para diagnóstico de Chan",opciones_hist,key=chan_key)
        # Reutilizar la historia ya cargada cuando el pozo esta en la comparativa.
        hist_chan=(historia.loc[historia.POZO.eq(pozo_chan)] if pozo_chan in candidatos
                   else cargar_historia(yac,(pozo_chan,)))
        datos_chan=preparar_datos_chan(hist_chan)
        st.caption("Tiempo: suma de los días calendario de cada mes desde el primer mes con producción; "
            "incluye meses de cierre y meses sin registros. Cada punto se ubica al final del mes. "
            "WOR = Qw/Qo de los vectores de producción. La derivada dWOR/dt usa diferencias finitas "
            "en tramos mensuales válidos, sin atravesar cierres, inyección ni huecos.")
        if datos_chan.empty or not datos_chan.WOR.gt(0).any():
            st.info("El pozo no tiene WOR positivo representable en escala logarítmica.")
        else:
            figura_chan,avisos_chan=crear_figura_chan(datos_chan,pozo_chan)
            st.plotly_chart(figura_chan,width="stretch",key="screen_chan_plot")
            st.caption("Azul: WOR · Rojo: dWOR/dt. Líneas: ajustes independientes de grado 4 por "
                "mínimos cuadrados sobre toda la historia válida, en unidades originales (no sobre logaritmos). "
                "No se extrapolan. Los valores cero o negativos se conservan en la tabla y en el ajuste, "
                "pero se ocultan en el gráfico logarítmico; no se usa valor absoluto.")
            for aviso in avisos_chan:
                st.caption(aviso)
        if not datos_chan.empty:
            with st.expander("Datos del diagnóstico de Chan"):
                st.dataframe(datos_chan[["FECHA","DIAS_MES","DIAS_ACUMULADOS","QO","QW","WOR","DERIVADA_WOR"]]
                    .rename(columns={"FECHA":"Fecha","DIAS_MES":"Días del mes",
                        "DIAS_ACUMULADOS":"Días acumulados","QO":"Qo [bpd]","QW":"Qw [bpd]",
                        "DERIVADA_WOR":"dWOR/dt [1/día]"}),hide_index=True,width="stretch")
        st.caption("El ajuste describe la tendencia de los datos; por sí solo no identifica el mecanismo de producción de agua.")
    else:
        st.info("No hay pozos disponibles para Chan con los filtros actuales.")
    st.markdown("**Acumuladas y condición actual de los pozos**")
    actual_izq,actual_der=st.columns(2)
    with actual_izq:
        log_actual=st.checkbox("Escala log–log: Np vs WOR actual",key="screen_actual_wor_log")
        fig_actual,n_actual=crear_scatter_actual(r,"WOR_ACTUAL",log_actual,mostrar_nombres)
        st.plotly_chart(fig_actual,width="stretch",key="screen_actual_wor_plot")
        st.caption(f"{n_actual} de {len(r)} pozos representados. Color y tamaño según Qo actual: "
            "verde = menor gasto, azul = mayor gasto. Escala de color lineal de 0 al máximo Qo representado, "
            "en bpd; burbujas de 10 a 32 píxeles. Gris: Qo no disponible. "
            "WOR usa Qw/Qo del último registro sin inyección; con Qo = 0 no se calcula.")
    with actual_der:
        log_acum=st.checkbox("Escala log–log: Np vs Wp y agua",value=True,key="screen_actual_agua_log")
        fig_agua,n_agua=crear_scatter_actual(r,"WP_MB",log_acum,mostrar_nombres)
        st.plotly_chart(fig_agua,width="stretch",key="screen_actual_agua_plot")
        st.caption(f"{n_agua} de {len(r)} pozos representados. Color: verde = 0% agua, azul = 100%; "
            "gris = sin dato. Se usa el último muestreo disponible; sin muestreo, el corte "
            "del último registro de producción sin inyección.")
    st.caption("Ambos gráficos respetan yacimiento, estado y el filtro de operando en agosto de 2026. "
        "Usan el resumen en caché, sin recalcular acumuladas. Se omiten valores faltantes o negativos; "
        "en escala logarítmica también se omiten ceros. Los pozos permanecen en la tabla.")
    nombres=dict(POZO="Pozo",YACIMIENTO="Yacimiento",ESTADO="Estado",NP_MB="Np [Mb]",WP_MB="Wp [Mb]",
        RWA="Wp/Np",QO_ACTUAL="Qo actual [bpd]",QW_ACTUAL="Qw actual [bpd]",WC_ACTUAL="Corte de agua [%]",
        WOR_ACTUAL="WOR actual",RGA_ACTUAL="RGA actual [pc/bl]",FECHA_ULTIMO_DATO="Fecha último dato sin inyección",
        EN_GRAFICO="En gráfico",MOTIVO="Motivo de exclusión",
        DIAGNOSTICO="Diagnóstico",FUENTE_AGUA="Fuente agua",FECHA_AGUA="Fecha agua",X="UTM X",Y="UTM Y",OPERANDO_AGOSTO_2026="Operando agosto 2026",
        REGISTROS_INYECCION_EXCLUIDOS="Registros de inyección excluidos")
    tabla=r.drop(columns=["TERMINACIONES","QG_ACTUAL"],errors="ignore").rename(columns=nombres)
    st.dataframe(tabla,width='stretch',hide_index=True)
    st.download_button("Descargar resultados CSV",tabla.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"screening_{yac}_ultimos_datos.csv",mime="text/csv",key="screen_csv")

def aplicar_formato_screening(fig,titulo):
    """Formato visual de Comparativa; hover puntual para el scatter."""
    fig.update_layout(
        title=dict(text=f"<b>{titulo}</b>",x=.02,xanchor="left",
                   font=dict(size=20,family="Arial Black",color="#111827")),
        template="plotly_white",height=620,plot_bgcolor="#F8F8FF",paper_bgcolor="white",
        font=dict(family="Arial",size=13,color="#111827"),hovermode="closest",
        margin=dict(l=65,r=30,t=100,b=65),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="center",x=.5,
                    font=dict(size=12,family="Arial",color="#111827"),
                    bgcolor="rgba(255,255,255,0.8)",bordercolor="#D1D5DB",borderwidth=1))
    ejes=dict(showgrid=True,gridcolor="#E5E7EB",gridwidth=.7,zeroline=False,
              showline=True,linewidth=1.2,linecolor="#111827",mirror=True,ticks="outside",
              tickfont=dict(size=14,color="#111827"),separatethousands=True)
    fig.update_xaxes(**ejes)
    fig.update_yaxes(**ejes)

def crear_mapa_screening(mapa,contorno,yacimiento):
    fig=go.Figure()
    if contorno is not None and not contorno.empty:
        borde=contorno.copy()
        borde.columns=borde.columns.str.upper().str.strip()
        if "YACIMIENTO" in borde:
            borde=borde.loc[borde.YACIMIENTO.astype(str).str.strip().str.upper().eq(str(yacimiento).strip().upper())]
        if "ORDEN" in borde:
            borde=borde.sort_values("ORDEN")
        borde[["X","Y"]]=borde[["X","Y"]].apply(pd.to_numeric,errors="coerce")
        borde=borde.dropna(subset=["X","Y"])
        if not borde.empty:
            cerrado=pd.concat([borde,borde.iloc[:1]])
            fig.add_trace(go.Scatter(x=cerrado.X,y=cerrado.Y,mode="lines",name="Contorno",
                                    line=dict(color="#333333",width=1.5),hoverinfo="skip"))
    d=mapa.dropna(subset=["X","Y"])
    grupos=[("Wp/Np < 1","#2ca02c",d.RWA.lt(1)),
            ("1 ≤ Wp/Np ≤ 10","#ff9900",d.RWA.between(1,10)),
            ("Wp/Np > 10","#e31a1c",d.RWA.gt(10)),
            ("Sin relación","#909090",d.RWA.isna())]
    for nombre,color,mask in grupos:
        z=d.loc[mask]
        if z.empty: continue
        fig.add_trace(go.Scatter(x=z.X,y=z.Y,mode="markers",name=nombre,
            marker=dict(size=11,color=color,line=dict(color="white",width=.7)),
            customdata=z[["POZO","RWA","QO_ACTUAL","WC_ACTUAL","FUENTE_AGUA"]].to_numpy(),
            hovertemplate="<b>%{customdata[0]}</b><br>Wp/Np: %{customdata[1]:.2f}<br>"
                "Qo: %{customdata[2]:.2f} bpd<br>Agua: %{customdata[3]:.1f}%<br>"
                "Fuente agua: %{customdata[4]}<extra></extra>"))
    aplicar_formato_screening(fig,f"Mapa de pozos — {yacimiento}")
    fig.update_xaxes(title="UTM X [m]")
    fig.update_yaxes(title="UTM Y [m]",scaleanchor="x",scaleratio=1)
    if not d.empty:
        dx=max(d.X.max()-d.X.min(),100)
        dy=max(d.Y.max()-d.Y.min(),100)
        fig.update_xaxes(range=[d.X.min()-.08*dx,d.X.max()+.08*dx])
        fig.update_yaxes(range=[d.Y.min()-.08*dy,d.Y.max()+.08*dy])
    return fig
