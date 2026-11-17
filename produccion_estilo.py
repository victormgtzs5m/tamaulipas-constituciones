"""Estilo exclusivo de Produccion por pozo; conserva controles, vectores y calculos."""
import colorsys
from html import escape
import streamlit as st
import streamlit.components.v1 as components

SCOPE = ".block-container:has(.prod-style-marker)"
CSS = """
<style>
$SCOPE {background:#FFFFFF;color:#17324D;font-family:Arial,sans-serif;}
/* Oculta los bloques vacios que separaban el menu de los filtros. */
$SCOPE [data-testid='stElementContainer']:has(.prod-style-marker),
$SCOPE [data-testid='stElementContainer']:has(.filter-box),
$SCOPE [data-testid='stElementContainer']:has([data-testid='stMarkdownContainer'] > style:only-child) {display:none;}
$SCOPE .muestreo-agua-valor {color:#2563EB !important;font-weight:700;}
html:has(.prod-style-marker),body:has(.prod-style-marker),
[data-testid='stApp']:has(.prod-style-marker),[data-testid='stAppViewContainer']:has(.prod-style-marker),
[data-testid='stMain']:has(.prod-style-marker) {background:#FFFFFF !important;}
body:has(.prod-style-marker) [data-testid='stHeader'] {background:#FFFFFF !important;}
body:has(.prod-style-marker) [data-testid='stHeader'] * {color:#334155 !important;}
$SCOPE .prod-table-heading {background:#F8FAFC !important;border-color:#CBD5E1 !important;}
$SCOPE .filter-box {background:#FFFFFF !important;border-color:#FFFFFF !important;box-shadow:none !important;}
$SCOPE [data-testid='stMarkdownContainer'] div[style*='#F8F9F9'],
$SCOPE [data-testid='stMarkdownContainer'] div[style*='#f8f9f9'] {
 background:#F8FAFC !important;border-color:#CBD5E1 !important;}
/* Tabla clara sin invertir el canvas nativo. */
$SCOPE .st-key-prod_tabla_historica_contenedor canvas {filter:none;}
$SCOPE .st-key-prod_tabla_historica_contenedor {background:#FFFFFF;border-radius:8px;}
$SCOPE .st-key-prod_tabla_historica_contenedor * {scrollbar-color:#94A3B8 #FFFFFF;}
$SCOPE .st-key-prod_tabla_historica_contenedor [data-testid='stElementToolbar'] {background:#FFFFFF;color:#334155;}

$SCOPE h1,$SCOPE h2,$SCOPE h3,$SCOPE h4 {color:#17324D !important;font-family:Arial,sans-serif !important;font-weight:600 !important;}
$SCOPE p,$SCOPE label,$SCOPE .small-note,$SCOPE [data-testid='stWidgetLabel'] {
 color:#17324D !important;font-family:Arial,sans-serif;}
$SCOPE [data-testid='stCaptionContainer'],$SCOPE [data-testid='stCaptionContainer'] * {color:#64748B !important;font-size:12px;}
$SCOPE .section-title {color:#17324D !important;font-size:18px;font-weight:650;}
$SCOPE [data-testid='stHorizontalBlock']:has(.st-key-prod_pozo_sel) {
 background:#F8FAFC;border:1px solid #E2E8F0;border-radius:11px;padding:18px;}
$SCOPE [data-baseweb='select'] > div,$SCOPE [data-baseweb='input'],$SCOPE [data-baseweb='base-input'],
$SCOPE input,$SCOPE textarea {background:#FFFFFF !important;color:#1E293B !important;border-color:#CBD5E1 !important;}
$SCOPE [data-baseweb='select'] span {color:#1E293B !important;}
$SCOPE input::placeholder {color:#64748B !important;opacity:1;}
$SCOPE button[kind='secondary'],$SCOPE [data-testid='stNumberInput'] button {
 background:#FFFFFF !important;color:#334155 !important;border-color:#CBD5E1 !important;}
$SCOPE button[kind='secondary']:hover {border-color:#B7791F !important;color:#B7791F !important;}
$SCOPE button[kind='primary'] {background:#1F4E79 !important;color:#FFFFFF !important;border-color:#1F4E79 !important;}
$SCOPE [data-testid='stRadio'] label:has(input:checked) {background:#E8F0F7;border-radius:16px;outline:1px solid #1F4E79;}
$SCOPE [data-testid='stExpander'] {background:#F8FAFC;border-color:#CBD5E1;border-radius:10px;}
$SCOPE [data-testid='stDataFrame'] {border:1px solid #CBD5E1;border-radius:8px;}
$SCOPE [data-testid='stMarkdownContainer'] div[style*='background-color:#F8F9F9'] {
 background:#F8FAFC !important;border-color:#CBD5E1 !important;}
$SCOPE [data-testid='stMarkdownContainer'] h4 {color:#17324D !important;}
</style>
""".replace("$SCOPE", SCOPE)


def _color_presentacion(color):
    nombres = {"black": "#1E293B", "white": "#1E293B", "cyan": "#0E7490",
               "red": "#DC2626", "blue": "#4338CA", "green": "#15803D"}
    if color is None:
        return "#64748B"
    valor = str(color).lower()
    if valor in nombres:
        return nombres[valor]
    if valor.startswith("#") and len(valor) == 7:
        rgb = [int(valor[i:i+2], 16) / 255 for i in (1, 3, 5)]
        h, saturacion, brillo = colorsys.rgb_to_hsv(*rgb)
        if saturacion < 0.25 or brillo < 0.1:
            return "#1E293B"
        r, g, b = colorsys.hsv_to_rgb(h, max(saturacion, 0.65), min(brillo, 0.68))
        return "#%02X%02X%02X" % (round(r*255), round(g*255), round(b*255))
    return color


def _color_curva(traza):
    nombre = (traza.name or "").casefold()
    if nombre.startswith("qo "):
        return "#15803D"
    if nombre.startswith("np "):
        return "#047857"
    if nombre.startswith("qw "):
        return "#2563EB"
    if nombre.startswith("wp "):
        return "#0284C7"
    if "agua lab" in nombre:
        return "#2563EB"
    if "agua" in nombre:
        return "#4338CA"
    if nombre.startswith("qg ") or nombre.startswith("rga "):
        return "#DC2626"
    if nombre.startswith("gp "):
        return "#B91C1C"
    if nombre.startswith("qb "):
        return "#475569"
    if nombre.startswith("qiny total"):
        return "#0E7490"
    if nombre.startswith("winj total"):
        return "#0369A1"
    if nombre == "seguimiento":
        return "#B7791F"
    return _color_presentacion(traza.line.color)


def aplicar_grafico(fig, mapa=False):
    """Cambia colores y tipografia, sin tocar los vectores ni las escalas."""
    fig.update_layout(template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family="Arial", size=13, color="#17324D"),
        title_font=dict(family="Arial", size=18, color="#17324D", weight=600),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#CBD5E1", font=dict(color="#1E293B")),
        legend=dict(font=dict(family="Arial", size=12, color="#17324D")))
    if not mapa:
        fig.update_layout(title=dict(y=0.98, yanchor="top", x=0, xanchor="left"),
            margin=dict(t=max(fig.layout.margin.t or 0, 95)))
    ejes = dict(gridcolor="#E2E8F0", linecolor="#94A3B8", zerolinecolor="#CBD5E1",
        title_font=dict(family="Arial", size=14, color="#17324D", weight=600),
        tickfont=dict(family="Arial", size=12, color="#17324D"))
    fig.update_xaxes(**ejes)
    fig.update_yaxes(**ejes)
    for traza in fig.data:
        if mapa:
            if traza.name == "Contorno":
                traza.line.update(color="#0284C7")
            elif traza.name == "Asignaci\u00f3n":
                traza.line.update(color="#64748B")
            if getattr(traza, "textfont", None):
                traza.textfont.update(color="#1E293B", family="Arial")
            continue
        color = _color_curva(traza)
        if "lines" in (traza.mode or ""):
            traza.line.update(color=color)
        if "markers" in (traza.mode or ""):
            traza.marker.update(color=color)
            if traza.marker.line.color is not None:
                traza.marker.line.update(color=_color_presentacion(traza.marker.line.color))
        if traza.fill is not None and traza.fill != "none" and str(color).startswith("#"):
            rgb = [int(str(color)[i:i+2], 16) for i in (1, 3, 5)]
            traza.fillcolor = f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.12)"
        if getattr(traza, "textfont", None):
            traza.textfont.update(color="#1E293B", family="Arial")
    for anotacion in fig.layout.annotations or []:
        anotacion.font.update(color=_color_presentacion(anotacion.font.color), family="Arial")
        anotacion.bgcolor = "rgba(255,255,255,0.96)"
        if anotacion.bordercolor is not None:
            anotacion.bordercolor = _color_presentacion(anotacion.bordercolor)
    for forma in fig.layout.shapes or []:
        if forma.line.color is not None:
            forma.line.update(color=_color_presentacion(forma.line.color))
    return fig


def kpi_card(titulo, valor, subtitulo="", color="#1F4E79"):
    acento = _color_presentacion(color)
    components.html(f"""
        <style>html,body {{margin:0;padding:0;background:#FFFFFF;}}</style>
        <div style="box-sizing:border-box;background:#FFFFFF;border:1px solid #CBD5E1;
             border-top:3px solid {acento};border-radius:9px;height:70px;padding:8px;
             font-family:Arial,sans-serif;overflow:hidden;">
          <div style="color:#64748B;font-size:10px;font-weight:600;text-transform:uppercase;
               letter-spacing:.3px;line-height:1.2;min-height:24px;">{escape(str(titulo))}</div>
          <div style="color:#17324D;font-size:15px;font-weight:650;margin-top:4px;white-space:nowrap;">
            {escape(str(valor))} <span style="color:#64748B;font-size:10px;">{escape(str(subtitulo))}</span>
          </div>
        </div>""", height=80)


def estilizar_tabla(datos):
    # Recibe el Styler existente para conservar todos sus formatos numericos.
    # Fondo claro y texto contrastado, conservando los formatos y los datos.
    return datos.set_properties(**{"background-color":"#FFFFFF", "color":"#1E293B", "border-color":"#E2E8F0"})


def mostrar_estado_pozo(yacimiento, estado):
    """Estado actualizado de la zona seleccionada, junto al selector del pozo."""
    etiquetas = {
        "OP": "Operando", "CCP": "Cerrado con posibilidades (CCP)",
        "CSP": "Cerrado sin posibilidades (CSP)", "NOP": "No operando",
        "IA": "Inyector de agua", "INY": "Inyector de agua",
        "IA OPERANDO": "Inyector de agua operando",
    }
    texto = etiquetas.get(str(estado).strip().upper(), str(estado))
    st.markdown(
        '<div style="font-family:Arial,sans-serif;font-size:13px;color:#475569;'
        'margin-top:4px;line-height:1.6;">'
        f'Yacimiento: <b style="color:#17324D;">{escape(str(yacimiento))}</b>'
        ' &nbsp;|&nbsp; Estado: '
        f'<b style="color:#17324D;">{escape(texto)}</b></div>',
        unsafe_allow_html=True,
    )
