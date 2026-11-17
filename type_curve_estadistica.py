"""Estadistica de los pozos de Type Curve, con los graficos del modulo Estadistica."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

COL_POZO = "Pozo / Terminaci\u00f3n"
COL_NP = "Np acumulada (mb)"


def preparar_muestra(historia, yacimiento, pozos):
    columnas = ["Yacimiento", COL_POZO, "Primer gasto (bpd)", "Segundo gasto (bpd)",
                "Registro utilizado", "Qoi", COL_NP]
    base = historia.loc[historia.YACIMIENTO.eq(yacimiento) & historia.POZO_ID.isin(pozos)]
    filas = []
    for pozo, h in base.groupby("POZO_ID", sort=True):
        h = h.sort_values("MES_REL")
        # Los dos primeros meses del vector normalizado; un mes ausente equivale
        # al cero completado en Produccion por pozo y Estadistica.
        gastos = h.groupby("MES_REL")["QO"].first()
        primero = float(gastos.iloc[0])
        segundo = float(gastos.get(int(gastos.index[0]) + 1, 0.0))
        registro = 2 if segundo > primero else 1
        filas.append({"Yacimiento": yacimiento, COL_POZO: pozo,
            "Primer gasto (bpd)": primero, "Segundo gasto (bpd)": segundo,
            "Registro utilizado": registro, "Qoi": segundo if registro == 2 else primero,
            COL_NP: pd.to_numeric(h["NP_MB"], errors="coerce").iloc[-1]})
    return pd.DataFrame(filas, columns=columnas)


def analizar_muestra(datos, variable):
    numerica = pd.to_numeric(datos[variable], errors="coerce")
    x = numerica.loc[numerica.notna() & np.isfinite(numerica)]
    if x.empty:
        return x, pd.Series(dtype=float, name=variable), datos.iloc[:0].copy()
    q1, q3 = x.quantile([.25, .75])
    ric = q3 - q1
    li, ls = q1 - 1.5 * ric, q3 + 1.5 * ric
    atipicos = datos.loc[x.index[(x < li) | (x > ls)]].copy()
    w, valor_p = (stats.shapiro(x) if 3 <= len(x) <= 5000 and x.nunique() > 1 else (np.nan, np.nan))
    resumen = pd.Series({
        "Muestras": len(x), "M\u00ednimo": x.min(), "Primer cuartil": q1,
        "Mediana": x.median(), "Media": x.mean(), "Tercer cuartil": q3,
        "M\u00e1ximo": x.max(), "Rango": x.max() - x.min(), "Rango intercuartil": ric,
        "Varianza muestral": x.var(ddof=1), "Desviaci\u00f3n est\u00e1ndar muestral": x.std(ddof=1),
        "Coeficiente de variaci\u00f3n (%)": 100 * x.std(ddof=1) / x.mean() if x.mean() != 0 else np.nan,
        "Asimetr\u00eda": x.skew(), "Exceso de curtosis": x.kurt(),
        "L\u00edmite inferior RIC": li, "L\u00edmite superior RIC": ls,
        "At\u00edpicos RIC": len(atipicos), "Shapiro-Wilk W": w, "Shapiro-Wilk p": valor_p,
    }, name=variable)
    return x, resumen, atipicos


def crear_distribuciones(datos, variable, yacimiento, etiquetas_hist=True, etiquetas_box=True):
    x, resumen, atipicos = analizar_muestra(datos, variable)
    if x.empty:
        return None, None, resumen, atipicos
    simbolo, unidad = ("Qoi", "bpd") if variable == "Qoi" else ("Np", "mb")
    media, mediana = x.mean(), x.median()
    q1, q3 = x.quantile([.25, .75])
    li, ls = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    interiores = x.loc[x.between(li, ls)]
    conteos, bordes = np.histogram(x.to_numpy(dtype=float), bins="sturges")
    fig_hist = go.Figure(go.Bar(x=(bordes[:-1] + bordes[1:]) / 2, y=conteos, width=np.diff(bordes),
        marker=dict(color="#00A65A", line=dict(color="black", width=1.5)), opacity=.8,
        text=conteos, textposition="outside", textfont=dict(size=12, color="black", family="Tahoma"),
        customdata=np.column_stack([bordes[:-1], bordes[1:]]),
        hovertemplate=simbolo + ": %{customdata[0]:,.2f} a %{customdata[1]:,.2f} " + unidad +
            "<br>Pozos: %{y}<extra></extra>", name="Pozos", showlegend=False))
    fig_hist.update_layout(title=f"<b>Distribuci\u00f3n de {simbolo} | {yacimiento}</b>",
        xaxis_title=f"{simbolo} ({unidad})", yaxis_title="N\u00famero de pozos", bargap=0)
    fig_box = go.Figure(go.Box(q1=[q1], median=[mediana], q3=[q3],
        lowerfence=[interiores.min()], upperfence=[interiores.max()], y=[simbolo],
        orientation="h", boxpoints=False, fillcolor="rgba(242,165,65,0.55)",
        line=dict(color="#B86E12", width=2), name=simbolo, showlegend=False))
    detalle = datos.loc[x.index]
    colores = np.where((x < li) | (x > ls), "#C00000", "#1F4E79")
    clases = np.clip(np.searchsorted(bordes, x.to_numpy(), side="right") - 1, 0, len(conteos) - 1)
    niveles = pd.Series(clases).groupby(pd.Series(clases), sort=False).cumcount().to_numpy() + .5
    hover = ("<b>%{customdata[0]}</b><br>Qoi: %{customdata[1]:,.2f} bpd"
             "<br>Np acumulada: %{customdata[2]:,.2f} mb<extra></extra>")
    custom = detalle[[COL_POZO, "Qoi", COL_NP]].to_numpy()
    for figura, eje_y in [(fig_hist, niveles), (fig_box, [simbolo] * len(x))]:
        figura.add_trace(go.Scatter(x=x, y=eje_y, mode="markers",
            marker=dict(size=9, color=colores, line=dict(color="white", width=1)),
            customdata=custom, hovertemplate=hover, name="Pozos", showlegend=False))
    for es_hist, figura, mostrar in [(True, fig_hist, etiquetas_hist), (False, fig_box, etiquetas_box)]:
        if not mostrar:
            continue
        orden = detalle if es_hist else detalle.sort_values(variable, kind="stable")
        for i, (_, fila) in enumerate(orden.iterrows()):
            texto = (f"<b>{fila[COL_POZO]}</b><br>Qoi: {fila['Qoi']:,.2f} bpd"
                     f"<br>Np: {fila[COL_NP]:,.2f} mb")
            figura.add_annotation(x=float(fila[variable]), y=float(niveles[i]) if es_hist else simbolo,
                text=texto, showarrow=True, arrowhead=0, arrowwidth=1, arrowcolor="#7F8C8D",
                ax=[-45,45,-70,70][i % 4] if es_hist else 0,
                ay=[-45,-75,45,75][i % 4] if es_hist else [-60,65,-125,130][i % 4],
                bgcolor="rgba(255,255,255,0.9)", borderpad=3,
                font=dict(size=10, color="black", family="Tahoma"))
    fig_box.update_layout(title=f"<b>Boxplot de {simbolo} | {yacimiento}</b>",
        xaxis_title=f"{simbolo} ({unidad})", yaxis_title="", yaxis=dict(showticklabels=False))
    for figura in (fig_hist, fig_box):
        figura.add_vline(x=media, line_color="#C00000", line_dash="dash", line_width=2,
            annotation_text=f"Media: {media:,.2f}", annotation_position="top left")
        figura.add_vline(x=mediana, line_color="#1F4E79", line_dash="dot", line_width=2,
            annotation_text=f"Mediana: {mediana:,.2f}", annotation_position="bottom right")
        figura.update_layout(height=560, template="plotly_white",
            font=dict(size=14, color="black", family="Arial Black"),
            plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=90, b=70))
        figura.update_xaxes(showline=True, linewidth=1, linecolor="black",
            tickfont=dict(size=11, color="black", family="Tahoma"), tickformat=",.0f", gridcolor="#EAECEE")
        figura.update_yaxes(showline=True, linewidth=1, linecolor="black",
            tickfont=dict(size=11, color="black", family="Tahoma"), gridcolor="#EAECEE")
    fig_hist.update_yaxes(dtick=1, range=[0, max(conteos) * 1.25])
    return fig_hist, fig_box, resumen, atipicos


def mostrar_estadistica_type_curve(historia, yacimiento, pozos):
    datos = preparar_muestra(historia, yacimiento, pozos)
    st.markdown("### An\u00e1lisis estad\u00edstico de los pozos seleccionados")
    if datos.empty:
        st.info("No hay datos disponibles para estos pozos.")
        return
    tabs = st.tabs(["Gasto inicial de aceite (Qoi)", "Producci\u00f3n acumulada de aceite (Np)"])
    for tab, variable, sufijo in zip(tabs, ["Qoi", COL_NP], ["qoi", "np"]):
        with tab:
            a, b = st.columns(2)
            etiquetas_hist = a.checkbox("Mostrar etiquetas en histograma", value=True, key=f"tc_stats_hist_{sufijo}")
            etiquetas_box = b.checkbox("Mostrar etiquetas en boxplot", value=True, key=f"tc_stats_box_{sufijo}")
            hist, box, resumen, atipicos = crear_distribuciones(datos, variable, yacimiento, etiquetas_hist, etiquetas_box)
            if hist is None:
                st.info("No hay valores num\u00e9ricos v\u00e1lidos para esta variable.")
                continue
            n, media, mediana = st.columns(3)
            n.metric("Pozos analizados", int(resumen["Muestras"]))
            media.metric("Media", f"{resumen['Media']:,.2f}")
            mediana.metric("Mediana", f"{resumen['Mediana']:,.2f}")
            col_hist, col_box = st.columns(2)
            config = {"displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 3}}
            col_hist.plotly_chart(hist, width="stretch", theme=None, config=config, key=f"tc_stats_histograma_{sufijo}")
            col_box.plotly_chart(box, width="stretch", theme=None, config=config, key=f"tc_stats_boxplot_{sufijo}")
            with st.expander("Ver estad\u00edsticas, datos por pozo y at\u00edpicos"):
                st.dataframe(resumen.rename_axis("Estad\u00edstico").reset_index(), hide_index=True, width="stretch")
                st.dataframe(datos, hide_index=True, width="stretch")
                st.dataframe(atipicos, hide_index=True, width="stretch")
                if pd.notna(resumen["Shapiro-Wilk p"]):
                    st.write("Shapiro-Wilk (\u03b1 = 0.05): " +
                        ("se rechaza normalidad." if resumen["Shapiro-Wilk p"] < .05 else "no se rechaza normalidad."))
                st.write("Qoi compara los dos primeros gastos mensuales y toma el segundo si es mayor. "
                         "Np es la \u00faltima acumulada observada del pozo en el yacimiento en toda su historia disponible, "
                         "sin restar la acumulada inicial. Los at\u00edpicos se conservan en el an\u00e1lisis.")
                st.download_button("Descargar estad\u00edsticas CSV", resumen.to_csv().encode("utf-8-sig"),
                    f"type_curve_estadisticas_{sufijo}.csv", "text/csv", key=f"tc_stats_csv_{sufijo}")
    with st.expander("Descargar muestra de pozos analizados"):
        st.dataframe(datos, hide_index=True, width="stretch")
        st.download_button("Descargar muestra CSV", datos.to_csv(index=False).encode("utf-8-sig"),
            "type_curve_muestra_estadistica.csv", "text/csv", key="tc_stats_muestra_csv")
