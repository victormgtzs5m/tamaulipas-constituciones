"""Identidad y contadores del resumen de Mapas."""
import pandas as pd
from estados_pozos import clave


def preparar_identidad_mapa(datos):
    """Conserva sufijos de la terminacion y separa etiquetas de pozos vecinos."""
    r = datos.copy()
    if "TERMINACION" in r:
        partes = r.TERMINACION.fillna("").astype(str).str.strip().str.upper().str.extract(
            r"^(CONST|TMLP|CHAMPAYAN|PEDRERA)_([0-9]+[A-Z0-9]*)_[A-Z0-9]+$")
        prefijo = partes[0].map({"CONST":"C", "TMLP":"T", "CHAMPAYAN":"CH", "PEDRERA":"P"})
        correcto = prefijo + "-" + partes[1]
        if "POZO" not in r:
            r["POZO"] = correcto
        else:
            r["POZO"] = correcto.combine_first(r.POZO)
    nombres = clave(r.POZO)
    raiz = nombres.str.replace(r"[A-Z]+$", "", regex=True)
    con_sufijo = raiz.ne(nombres) & raiz.isin(nombres)
    raices_vecinas = set(raiz[con_sufijo])
    r["POSICION_NOMBRE"] = "top center"
    r.loc[nombres.isin(raices_vecinas), "POSICION_NOMBRE"] = "top left"
    r.loc[con_sufijo, "POSICION_NOMBRE"] = "bottom right"
    return r


def contadores_estados(mapa, colores, estados_activos=None):
    """Cuenta pozos fisicos unicos dentro del yacimiento y filtros actuales."""
    grupos = [
        ("Operando", ("OP",)),
        ("CCP", ("CCP",)),
        ("CSP", ("CSP",)),
        ("Inyector de Agua", ("IA", "INY")),
        ("Prog. Taponamiento", ("PROG TAPONAMIENTO",)),
        ("Taponados", ("TAPONADO",)),
    ]
    for etiqueta, estado in [("Inyector de Agua Operando", "IA OPERANDO"),
                              ("Improductivos", "IMPRODUCTIVO"), ("No operando", "NOP")]:
        if mapa.ESTADO_MAPA.eq(estado).any():
            grupos.append((etiqueta, (estado,)))
    visibles = mapa if estados_activos is None else mapa.loc[mapa.ESTADO_MAPA.isin(estados_activos)]
    resultado = []
    for etiqueta, estados in grupos:
        pozos = visibles.loc[visibles.ESTADO_MAPA.isin(estados), "POZO"]
        numero = clave(pozos).replace("", pd.NA).nunique()
        resultado.append((etiqueta, numero, colores[estados[0]]))
    return resultado
