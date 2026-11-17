"""Tema visual exclusivo de DCA; no modifica datos, ajustes ni controles."""
CSS = """
<style>
.st-key-dca_root {background:#FFFFFF;border:1px solid #DCE3E9;border-radius:14px;padding:20px;
 font-family:'Segoe UI',Arial,sans-serif;}
.st-key-dca_root h2,.st-key-dca_root h3,.st-key-dca_root h4 {color:#263238 !important;font-family:'Segoe UI',Arial,sans-serif !important;}
.st-key-dca_root label,.st-key-dca_root p,.st-key-dca_root [data-testid='stWidgetLabel'],
.st-key-dca_root [data-testid='stMarkdownContainer'] {color:#334155 !important;font-family:'Segoe UI',Arial,sans-serif;}
.st-key-dca_root [data-testid='stCaptionContainer'],.st-key-dca_root [data-testid='stCaptionContainer'] * {
 color:#64748B !important;font-size:12px;}
.st-key-dca_root .dca-hero {background:#FFFFFF !important;box-shadow:none !important;
 padding:0 0 18px !important;border-radius:0 !important;}
.st-key-dca_root .dca-hero > div:first-child {font-family:'Segoe UI',Arial,sans-serif;font-size:28px !important;
 font-weight:650 !important;color:#263238 !important;}
.st-key-dca_root .dca-hero > div:last-child {color:#64748B !important;font-size:12px !important;}
.st-key-dca_root [data-testid='stColumn']:has(.dca-filter-panel-marker),
.st-key-dca_root [data-testid='column']:has(.dca-filter-panel-marker),
.st-key-dca_root [data-testid='stColumn']:has(.dca-content-panel-marker),
.st-key-dca_root [data-testid='column']:has(.dca-content-panel-marker) {
 background:#FFFFFF !important;border:1px solid #DCE3E9 !important;border-radius:11px !important;
 padding:18px !important;box-shadow:none !important;}
.st-key-dca_root .dca-panel-title {background:transparent !important;border:0 !important;padding:0 0 8px !important;
 color:#263238 !important;font-size:18px !important;font-weight:650 !important;}
.st-key-dca_root .dca-panel-section {color:#B87400 !important;font-size:11px !important;font-weight:650 !important;}
.st-key-dca_root [data-testid='stColumn']:has(.dca-filter-panel-marker) label,
.st-key-dca_root [data-testid='stColumn']:has(.dca-filter-panel-marker) p,
.st-key-dca_root [data-testid='stColumn']:has(.dca-filter-panel-marker) span {
 color:#334155 !important;font-size:13px !important;font-weight:400 !important;}
.st-key-dca_root .dca-kpi-card,.st-key-dca_root .dca-section-card {
 background:#F7F9FC !important;border:1px solid #D2DAE2 !important;border-radius:10px !important;box-shadow:none !important;}
.st-key-dca_root .dca-kpi-label {color:#64748B !important;font-weight:600 !important;font-size:10px !important;}
.st-key-dca_root .dca-kpi-value {color:#263238 !important;font-size:20px !important;font-weight:650 !important;}
.st-key-dca_root .dca-section-title {color:#263238 !important;font-size:18px !important;font-weight:650 !important;}
.st-key-dca_root .dca-section-subtitle {color:#64748B !important;font-size:12px !important;}
.st-key-dca_root [data-baseweb='select'] > div,.st-key-dca_root [data-baseweb='input'],
.st-key-dca_root [data-baseweb='base-input'],.st-key-dca_root input,.st-key-dca_root textarea {
 background:#F7F9FC !important;color:#334155 !important;border-color:#D2DAE2 !important;}
.st-key-dca_root [data-baseweb='select'] span {color:#334155 !important;}
.st-key-dca_root [data-testid='stNumberInput'] button {background:#F7F9FC !important;color:#334155 !important;border-color:#D2DAE2 !important;}
.st-key-dca_root [data-testid='stNumberInput'] button svg {color:#334155 !important;}
.st-key-dca_root input::placeholder,.st-key-dca_root textarea::placeholder {color:#7B8794 !important;opacity:1;}
.st-key-dca_root button[kind='secondary'],.st-key-dca_root button[kind='secondaryFormSubmit'] {
 background:#F7F9FC !important;color:#334155 !important;border:1px solid #D2DAE2 !important;}
.st-key-dca_root button[kind='secondary']:hover {border-color:#E8A634 !important;color:#E8A634 !important;}
.st-key-dca_root button[kind='primary'] {background:#E8A634 !important;color:#161B1E !important;border-color:#E8A634 !important;}
.st-key-dca_root [data-testid='stRadio'] label:has(input:checked) {background:#FFF2DB;border-radius:16px;outline:1px solid #B68029;}
.st-key-dca_root [data-testid='stExpander'] {background:#FFFFFF;border-color:#D2DAE2;border-radius:10px;}
.st-key-dca_root [data-testid='stDataFrame'] {border:1px solid #D2DAE2;border-radius:8px;}
</style>
"""


def aplicar_estilo_grafico_dca(fig):
    """Cambia solo propiedades visuales; conserva trazas, ejes, escalas y vectores."""
    fig.update_layout(template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        editrevision="dca_posicion_resultados",
        font=dict(family="Segoe UI, Arial", size=12, color="#475569"),
        title_font=dict(family="Segoe UI, Arial", size=18, color="#263238"),
        title=dict(y=0.98, yanchor="top", x=0, xanchor="left"),
        margin=dict(t=115),
        legend=dict(orientation="h", x=0, xanchor="left", y=1.02, yanchor="bottom",
                    font=dict(family="Segoe UI, Arial", size=11, color="#475569")),
        hoverlabel=dict(bgcolor="#F7F9FC", bordercolor="#D2DAE2",
                        font=dict(family="Segoe UI, Arial", color="#334155")))
    ejes = dict(gridcolor="#DCE3E9", linecolor="#94A3B8", linewidth=1,
        title_font=dict(family="Segoe UI, Arial", size=12, color="#475569"),
        tickfont=dict(family="Segoe UI, Arial", size=11, color="#475569"),
        minor=dict(gridcolor="#F0F3F7"))
    fig.update_xaxes(**ejes)
    fig.update_yaxes(**ejes)
    for traza in fig.data:
        nombre = (traza.name or "").casefold()
        if "hist" in nombre:
            traza.mode = "markers"
            traza.marker.update(size=4, color="#94A3AD", line=dict(color="#94A3AD", width=0.5))
            continue
        if "markers" in (traza.mode or ""):
            color = "#FF6E00" if "ajuste" in nombre else "#94A3AD"
            traza.marker.update(color=color, line=dict(color=color))
            if "ajuste" in nombre:
                traza.marker.update(size=5, line=dict(width=1))
        if "lines" in (traza.mode or ""):
            color = "#39FF14" if "pron" in nombre or "regresi" in nombre else "#00BFFF"
            traza.line.update(color=color, width=1.5, dash="dash")
    return fig


def estilizar_tabla_dca(datos):
    """Conserva los datos originales y cambia exclusivamente el color de las celdas."""
    return datos.style.set_properties(**{
        "background-color": "#F7F9FC", "color": "#334155", "border-color": "#D2DAE2"})



def agregar_resultados_ajuste_dca(fig, info, np_real, np_total, reserva, limite, fecha_fin=None):
    """Presenta resultados y fechas existentes del ajuste, sin recalcular el modelo."""
    import pandas as pd

    def fecha_texto(valor):
        return pd.Timestamp(valor).strftime("%d/%m/%Y") if valor is not None and pd.notna(valor) else "Sin pron\u00f3stico"

    qo_actual = info.get("Qo \u00faltima producci\u00f3n (bpd)")
    qo_texto = f"{qo_actual:,.2f}" if qo_actual is not None and pd.notna(qo_actual) else "\u2014"
    fecha_actual = fecha_texto(info.get("Fecha \u00faltima producci\u00f3n"))
    texto = (
        "<b>Resultados del ajuste</b>"
        "<br><b>Modelo Exponencial</b>"
        "<br>b = <b>0</b>"
        f"<br>Di mensual nominal: <b>{info['Di mensual nominal (%)']:.3f} %</b>"
        f"<br>Np (mb): <b>{np_real:,.2f}</b>"
        f"<br>EUR (mb): <b>{np_total:,.2f}</b>"
        f"<br>Reserva (mb): <b>{reserva:,.2f}</b>"
        f"<br>Qof (bpd): <b>{limite:,.1f}</b>"
        f"<br>Qo actual (bpd): <b>{qo_texto}</b>"
        f"<br>Fecha Qo actual: <b>{fecha_actual}</b>"
        f"<br>Fin del pron\u00f3stico: <b>{fecha_texto(fecha_fin)}</b>"
        f"<br>Puntos de ajuste: <b>{info['Puntos ajuste']:,.0f}</b>")
    fig.add_annotation(xref="paper", yref="paper", x=0.02, y=0.02,
        xanchor="left", yanchor="bottom", text=texto, showarrow=False, align="left", captureevents=True,
        bgcolor="rgba(255,255,255,0.96)", bordercolor="#CBD5E1", borderwidth=1, borderpad=8,
        font=dict(family="Segoe UI, Arial", size=10, color="#334155"))
    return fig



def mostrar_tabla_resultado_dca(datos):
    """Tabla de resumen con cabecera clara y datos originales, seleccionables y desplazables."""
    import streamlit as st
    tabla = datos.to_html(index=False, border=0, escape=True, classes="dca-selected-result")
    st.html("""
        <style>
        .dca-result-scroll {width:100%;max-height:160px;overflow:auto;
          border:1px solid #D2DAE2;border-radius:8px;background:#F7F9FC;}
        .dca-selected-result {border-collapse:separate;border-spacing:0;min-width:100%;
          font:12px 'Segoe UI',Arial,sans-serif;color:#334155;}
        .dca-selected-result thead th {position:sticky;top:0;z-index:1;
          background:#E8EEF5;color:#334155;font-weight:600;text-align:left;
          white-space:nowrap;padding:10px 12px;border-bottom:1px solid #CBD5E1;}
        .dca-selected-result tbody td {background:#F7F9FC;color:#334155;
          white-space:nowrap;text-align:left;padding:9px 12px;border-bottom:1px solid #D2DAE2;}
        .dca-selected-result th + th,.dca-selected-result td + td {border-left:1px solid #D2DAE2;}
        .dca-selected-result tbody tr:hover td {background:#EDF3F8;}
        .dca-selected-result ::selection {background:#D5E8FF;color:#263238;}
        </style>
        <div class="dca-result-scroll" tabindex="0" role="region"
             aria-label="Resultado del pozo seleccionado">""" + tabla + "</div>")
