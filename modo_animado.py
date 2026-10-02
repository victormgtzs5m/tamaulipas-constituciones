"""Gráficos históricos y reproductor compartido del módulo Modo Animado."""
import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative
from plotly.offline import get_plotlyjs
from plotly.utils import PlotlyJSONEncoder

VERSION_GRAFICOS = 18

# Paleta original: reemplazar solamente el azul por cafe.
PALETA_POZOS = tuple("#8C564B" if color == "#636EFA" else color
                    for color in qualitative.Plotly)


def colores_por_pozo(pozos):
    return {pozo: PALETA_POZOS[i % len(PALETA_POZOS)]
            for i, pozo in enumerate(pozos)}


def colorear_burbujas(mapa, colores):
    """Colorea JSON de Np sin reconstruir ni validar objetos Plotly por mes."""
    indices = {i for i, traza in enumerate(mapa["data"])
               if traza.get("name") == "Np acumulado"}

    def aplicar(traza):
        filas = traza.get("customdata")
        if filas is None:
            return
        marker = traza["marker"]
        originales = list(marker.get("color", []))
        rellenos, bordes, anchos = [], [], []
        for i, fila in enumerate(filas):
            color = colores.get(str(fila[0]), "#64748B")
            anterior = str(originales[i]) if i < len(originales) else ""
            alfa = float(anterior.rsplit(",", 1)[1].rstrip(")")) if anterior.startswith("rgba(") else 0.45
            r, g, b = (int(color[j:j + 2], 16) for j in (1, 3, 5))
            rellenos.append(f"rgba({r},{g},{b},{alfa})")
            produciendo = len(fila) > 5 and float(fila[5]) > 0
            bordes.append("#000000" if produciendo else "rgba(0,0,0,0)")
            anchos.append(2.5 if produciendo else 0)
        marker["color"] = rellenos
        marker.setdefault("line", {})["color"] = bordes
        marker["line"]["width"] = anchos

    for i in indices:
        aplicar(mapa["data"][i])
    for frame in mapa.get("frames", []):
        for i, traza in zip(frame.get("traces", range(len(frame["data"]))), frame["data"]):
            if i in indices:
                aplicar(traza)


def etiquetar_acumuladas(mapa):
    """Valores mensuales en miles de barriles junto a sus burbujas."""
    tipos = {i: t.get("name") for i, t in enumerate(mapa["data"])
             if t.get("name") in ("Np acumulado", "Winj acumulado")}

    def aplicar(traza, tipo):
        filas = traza.get("customdata")
        if filas is None:
            return
        aceite = tipo == "Np acumulado"
        textos_previos = traza.get("text")
        textos_previos = list(textos_previos) if textos_previos is not None else []
        textos = []
        for i, fila in enumerate(filas):
            nombre = (str(fila[0]) + "<br>") if aceite and i < len(textos_previos) and str(textos_previos[i]) == str(fila[0]) else ""
            valor = float(fila[2 if aceite else 3]) / 1000
            textos.append(f"{nombre}{'Np' if aceite else 'Iny'}: {valor:,.1f} mb")
        traza["mode"] = "markers+text"
        traza["text"] = textos
        traza["textposition"] = "bottom center" if aceite else "top center"
        traza["textfont"] = dict(color="#15803D" if aceite else "#001BFF", size=12)
        traza["cliponaxis"] = False

    for i, tipo in tipos.items():
        aplicar(mapa["data"][i], tipo)
    for frame in mapa.get("frames", []):
        for i, traza in zip(frame.get("traces", range(len(frame["data"]))), frame["data"]):
            if i in tipos:
                aplicar(traza, tipos[i])


def aplicar_formato_comparativa(fig, titulo, unidad, fechas):
    """Formato visual de Comparativa por pozo, con el mismo reloj mensual."""
    fig.update_layout(
        title=dict(text=f"<b>{titulo}</b>", x=0.02, xanchor="left",
                   font=dict(size=20, family="Arial Black", color="#111827")),
        template="plotly_white", hovermode="x unified", height=450,
        plot_bgcolor="#F8F8FF", paper_bgcolor="white", uirevision="historial",
        font=dict(family="Arial", size=13, color="#111827"),
        margin=dict(l=70, r=40, t=90, b=70),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                    font=dict(size=14, family="Arial", color="#111827"),
                    bgcolor="rgba(255,255,255,0.8)", bordercolor="#D1D5DB", borderwidth=1)
    )
    ejes = dict(showgrid=True, gridcolor="#E5E7EB", gridwidth=0.7, zeroline=False,
                showline=True, linewidth=1.2, linecolor="#111827", mirror=True,
                ticks="outside", tickfont=dict(size=18, color="#111827"))
    fig.update_xaxes(**ejes, title=dict(text="<b>Fecha</b>", font=dict(size=18, color="#374151")),
                     range=[fechas[0], fechas[-1] + pd.offsets.MonthEnd(0)],
                     tickformat="%d/%m/%Y", rangeslider=dict(visible=False))
    fig.update_yaxes(**ejes, title=dict(text=f"<b>{unidad}</b>", font=dict(size=18, color="#374151")),
                     separatethousands=True)
    fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Fecha: %{x|%d/%m/%Y}<br>"
                      + unidad + ": %{y:,.2f}<extra></extra>")


def crear_graficos(historiales, fechas):
    """Alinea meses sin reiniciar acumuladas ni sumar razones entre pozos."""
    fechas = pd.DatetimeIndex(fechas)
    colores = colores_por_pozo(historiales)
    metricas = [
        ("Qo (bpd)", "Producción de aceite por pozo", "Qo (bpd)"),
        ("WOR", "Relación agua / aceite", "WOR (bbl/bbl)"),
        ("%Agua", "Porcentaje de agua", "% de agua"),
        ("RGA (pc/bl)", "Relación gas / aceite", "RGA (pc/bl)"),
        ("Np (mbl)", "Acumulada de aceite", "Np (mbl)"),
        ("Wp (mbl)", "Acumulada de agua", "Wp (mbl)"),
        ("Gp (mmpc)", "Acumulada de gas", "Gp (mmpc)"),
        ("Winj (mbl)", "Acumulada de inyección", "Winj (mbl)"),
    ]
    series = {}
    for pozo, (produccion, presion) in historiales.items():
        if produccion.empty:
            continue
        datos = produccion.copy()
        datos["FECHA"] = pd.to_datetime(datos["FECHA"]).dt.to_period("M").dt.to_timestamp()
        datos = datos.sort_values("FECHA").groupby("FECHA").last().reindex(fechas)
        for columna, _, _ in metricas[4:]:
            datos[columna] = datos[columna].ffill().fillna(0)
        for columna in ["Qo (bpd)", "Qw (bpd)", "%Agua", "RGA (pc/bl)"]:
            datos[columna] = datos[columna].fillna(0)
        datos["WOR"] = datos["Qw (bpd)"] / datos["Qo (bpd)"].replace(0, np.nan)
        series[pozo] = datos
    graficos = []
    for indice, (columna, titulo, unidad) in enumerate(metricas):
        fig = go.Figure()
        for j, (pozo, datos) in enumerate(series.items()):
            color = colores[pozo]
            traza = go.Scatter(x=fechas.tolist(), y=datos[columna].tolist(), name=pozo,
                              legendgroup=pozo, mode="lines", line=dict(color=color, width=2.8), connectgaps=False)
            fig.add_trace(traza)
        if indice == 0 or indice >= 4:
            total = sum((datos[columna] for datos in series.values()), pd.Series(0., index=fechas))
            traza = go.Scatter(x=fechas.tolist(), y=total.tolist(), name="Total seleccionados",
                              mode="lines", line=dict(color="#111827", width=3))
            fig.add_trace(traza)
        aplicar_formato_comparativa(fig, titulo, unidad, fechas)
        graficos.append(fig)
    presiones = go.Figure()
    for j, (pozo, (_, presion)) in enumerate(historiales.items()):
        if presion.empty:
            continue
        mediciones = presion[["FECHA", "PRESION"]].copy()
        mediciones["FECHA"] = pd.to_datetime(mediciones["FECHA"], errors="coerce")
        mediciones["PRESION"] = pd.to_numeric(mediciones["PRESION"], errors="coerce")
        mediciones = mediciones.replace([np.inf, -np.inf], np.nan).dropna()
        if mediciones.empty:
            continue
        mediciones = mediciones.sort_values("FECHA", kind="stable")
        mediciones["MES"] = mediciones["FECHA"].dt.to_period("M").dt.to_timestamp()
        # Promedio de mediciones validas del mes; conservarlo hasta el siguiente mes con datos.
        mensual = mediciones.groupby("MES")["PRESION"].mean()
        ultimo_mes_medido = mensual.index.max()
        mensual = mensual.reindex(mensual.index.union(fechas)).sort_index().ffill().reindex(fechas)
        # Rellenar huecos internos, sin prolongar la curva tras la ultima medicion.
        mensual = mensual.loc[mensual.index <= ultimo_mes_medido].dropna()
        presiones.add_trace(go.Scatter(
            x=mensual.index.tolist(),
            y=mensual.tolist(), name=pozo, legendgroup=pozo,
            mode="lines", line=dict(color=colores[pozo], width=2.8,
                                    dash="dot", shape="hv"),
            connectgaps=False
        ))
    aplicar_formato_comparativa(presiones, "Presión por pozo", "Presión (kg/cm²)", fechas)
    if not presiones.data:
        presiones.add_annotation(text="Sin mediciones de presión para los pozos seleccionados",
                                 x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
    graficos.append(presiones)
    return graficos


def crear_html_sincronizado(mapa, graficos, fechas, duracion_ms, colores_mapa=None, frames_mapa=None, presion_animada=None, tipo_presion="Grid"):
    """Un solo reloj espera mapa y gráficos antes de avanzar; series se envían una vez."""
    mapa = go.Figure(mapa)
    mapa.update_layout(updatemenus=[], sliders=[], height=900, margin=dict(t=120, b=45), dragmode="pan")
    if len(graficos) == 3:
        graficos = [go.Figure(g) for g in graficos]
        for grafico in graficos:
            grafico.update_layout(height=290, margin=dict(l=65, r=25, t=75, b=50))
            grafico.update_xaxes(tickfont=dict(size=13), title_font=dict(size=14))
            grafico.update_yaxes(tickfont=dict(size=13), title_font=dict(size=14))
            grafico.update_layout(title_font_size=17, legend_font_size=11)
    titulos = [g.layout.title.text.replace("<b>", "").replace("</b>", "") for g in graficos]
    graficos = [go.Figure(g) for g in graficos]
    for grafico in graficos:
        alto = (grafico.layout.height or 450) - 34
        grafico.layout.title = None
        grafico.update_layout(height=alto, margin=dict(l=65, r=145, t=12, b=50),
                              legend=dict(orientation="v", x=1.02, xanchor="left", y=1,
                                          yanchor="top", font=dict(size=11)))
        if "maxheight" in go.layout.Legend()._valid_props:
            grafico.update_layout(legend_maxheight=1.0)
    mapa_json = mapa.to_plotly_json()
    # update_layout fusiona arreglos: retirarlos explicitamente del JSON.
    mapa_json["layout"].pop("updatemenus", None)
    mapa_json["layout"].pop("sliders", None)
    if frames_mapa is not None:
        mapa_json["frames"] = frames_mapa
    for frame in mapa_json.get("frames", []):
        frame.get("layout", {}).pop("sliders", None)
        frame.get("layout", {}).pop("updatemenus", None)
    def extraer_resumen(layout):
        anotaciones = layout.get("annotations", [])
        resumen = ""
        otras = []
        for anotacion in anotaciones:
            texto = anotacion.get("text", "")
            if "Np:" in texto and "Agua inyectada:" in texto:
                resumen = texto.replace("<b>", "").replace("</b>", "")
            else:
                otras.append(anotacion)
        layout["annotations"] = otras
        return resumen

    resumen_inicial = extraer_resumen(mapa_json["layout"])
    resumenes = [extraer_resumen(frame.setdefault("layout", {})) or resumen_inicial
                for frame in mapa_json.get("frames", [])]
    if colores_mapa is not None:
        colorear_burbujas(mapa_json, colores_mapa)
    etiquetar_acumuladas(mapa_json)
    if presion_animada is not None:
        import presion_animada as _presion_animada
        if getattr(_presion_animada, "VERSION_CAPA", 0) != 5:
            import importlib
            _presion_animada = importlib.reload(_presion_animada)
        _presion_animada.agregar_presion_animada(mapa_json, presion_animada, tipo=tipo_presion)
        resumenes = [f"{resumen} | {estado}" for resumen, estado in zip(resumenes, presion_animada["estados"])]
        mapa_json["layout"]["margin"]["r"] = 95

    payload = dict(mapa=mapa_json, resumenes=resumenes, titulos=titulos, graficos=[g.to_plotly_json() for g in graficos],
                   fechas=[pd.Timestamp(f).isoformat() for f in fechas], duracion=duracion_ms)
    encoded = json.dumps(payload, cls=PlotlyJSONEncoder).replace("</", "<\\/")
    return """<!doctype html><html><head><meta charset="utf-8"><style>
    body {margin:0;font-family:Arial;color:#111827;background:white}
    #cabecera {position:sticky;top:0;z-index:10;background:white}
    #controles {background:#f1f5f9;padding:10px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
    #resumen-mapa {padding:10px 12px;margin:0 0 8px;border-bottom:1px solid #cbd5e1;
                   font-weight:bold;color:#111827;line-height:1.4;overflow-wrap:anywhere}
    button {padding:8px 14px;cursor:pointer} #fecha {white-space:nowrap} input {flex:1;min-width:60px}
    #panel {display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr);gap:16px}
    #graficos {display:grid;gap:16px;align-content:start;min-width:0}
    #mapa {position:sticky;top:var(--alto-cabecera,110px);height:900px} .grafico {height:450px;min-width:0}
    .grafico {overflow:hidden;display:flex;flex-direction:column}
    .titulo-grafico {flex:0 0 34px;box-sizing:border-box;margin:0;padding:6px 8px;
                     font:bold 16px Arial;color:#111827;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .lienzo-grafico {flex:1;min-height:0;width:100%}
    #panel:has(.grafico:nth-child(3)) #graficos {gap:12px}
    #panel:has(.grafico:nth-child(3)) .grafico {height:290px}
    @media(max-width:850px){#panel{display:block}#mapa{position:relative;top:0;height:900px}}
    </style></head><body>
    <div id="cabecera"><div id="controles"><button id="play" disabled>Reproducir</button><button id="stop">Pausa</button>
    <button id="inicio">Inicio</button><input id="rango" aria-label="Mes de la animación" type="range" min="0" value="0" step="1"><b id="fecha"></b></div>
    <div id="resumen-mapa" role="status"></div></div>
    <div id="panel"><div id="mapa"></div><div id="graficos"></div></div><p id="error" role="alert"></p>
    <script>""" + get_plotlyjs() + "</script><script>const datos=" + encoded + r""";
    const mapa=document.getElementById('mapa'), rango=document.getElementById('rango');
    const cabecera=document.getElementById('cabecera');
    new ResizeObserver(()=>document.documentElement.style.setProperty(
      '--alto-cabecera',cabecera.offsetHeight+'px')).observe(cabecera);
    document.getElementById('resumen-mapa').textContent=datos.resumenes[0] || '';
    let actual=0, reproduciendo=false, version=0, cola=Promise.resolve();
    const paneles=[], originales=datos.graficos.map(g=>g.data);
    rango.max=datos.fechas.length-1;
    const config={responsive:true,displaylogo:false,scrollZoom:true};
    function detener(){reproduciendo=false;version++;}
    function fallo(e){detener();document.getElementById('error').textContent='No se pudo actualizar la animación: '+e.message;}
    async function dibujar(i){
      const mes=new Date(datos.fechas[i]);
      const limite=new Date(mes.getFullYear(),mes.getMonth()+1,1).getTime();
      const tareas=paneles.map((div,j)=>{
        const xs=[],ys=[];
        originales[j].forEach(t=>{
          const x=[],y=[];
          t.x.forEach((fecha,k)=>{if(new Date(fecha).getTime()<limite){x.push(fecha);y.push(t.y[k]);}});
          xs.push(x);ys.push(y);
        });
        return Plotly.restyle(div,{x:xs,y:ys});
      });
      // Actualizar las trazas existentes en una sola operacion, sin el ciclo
      // animate/redraw que retira y reconstruye la imagen de presion.
      const frame=datos.mapa.frames[i];
      const cambios={};
      const campos=['x','y','z','text','customdata','marker.size','marker.color',
                    'marker.line.color','marker.line.width'];
      for(const campo of campos){
        const valores=frame.data.map(traza=>campo.split('.').reduce(
          (valor,clave)=>valor == null ? undefined : valor[clave],traza));
        // undefined conserva el atributo de las trazas a las que no aplica.
        if(valores.some(valor=>valor !== undefined))cambios[campo]=valores;
      }
      tareas.push(Plotly.restyle(mapa,cambios,frame.traces));
      await Promise.all(tareas);
      actual=i;rango.value=i;
      document.getElementById('resumen-mapa').textContent=datos.resumenes[i] || '';
      document.getElementById('fecha').textContent=mes.toLocaleDateString('es-MX',{month:'short',year:'numeric'});
    }
    function solicitar(i){cola=cola.then(()=>dibujar(i));return cola;}
    document.getElementById('stop').onclick=detener;
    document.getElementById('inicio').onclick=()=>{detener();solicitar(0).catch(fallo);};
    rango.oninput=()=>{detener();solicitar(Number(rango.value)).catch(fallo);};
    document.getElementById('play').onclick=async()=>{
      if(reproduciendo)return;
      reproduciendo=true;const turno=++version;
      try {
        await cola;
        if(actual===datos.fechas.length-1)await solicitar(0);
        while(reproduciendo && turno===version && actual<datos.fechas.length-1){
          await solicitar(actual+1);
          await new Promise(resolve=>setTimeout(resolve,datos.duracion));
        }
        if(turno===version)reproduciendo=false;
      }catch(e){fallo(e);}
    };
    (async()=>{
      await Plotly.newPlot(mapa,datos.mapa.data,datos.mapa.layout,config);
      for(let j=0;j<datos.graficos.length;j++){
        const bloque=document.createElement('section');bloque.className='grafico';
        const titulo=document.createElement('h3');titulo.className='titulo-grafico';
        titulo.textContent=datos.titulos[j];titulo.title=datos.titulos[j];
        const div=document.createElement('div');div.className='lienzo-grafico';
        bloque.append(titulo,div);
        document.getElementById('graficos').appendChild(bloque);paneles.push(div);
        const g=datos.graficos[j];
        await Plotly.newPlot(div,g.data.map(t=>({...t,x:[],y:[]})),g.layout,config);
      }
      await solicitar(0);document.getElementById('play').disabled=false;
    })().catch(fallo);
    </script></body></html>"""
