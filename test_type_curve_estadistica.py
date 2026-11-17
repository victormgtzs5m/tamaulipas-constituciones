import unittest
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from type_curve import agregar_banda_percentiles
from type_curve_estadistica import preparar_muestra, analizar_muestra, crear_distribuciones, COL_POZO, COL_NP


class TypeCurveEstadisticaTests(unittest.TestCase):
    def test_muestra_solo_pozos_yacimiento_y_vectores_observados(self):
        h = pd.DataFrame({"YACIMIENTO": ["KTIA"] * 6 + ["JSA"],
            "POZO_ID": ["A", "A", "A", "B", "B", "C", "A"],
            "MES_REL": [0, 1, 2, 0, 2, 0, 0], "QO": [10, 20, 500, 30, 100, 1, 900],
            "NP_MB": [3, 9, 8, 2, 10, 1, 99]})
        d = preparar_muestra(h, "KTIA", ["A", "B"]).set_index(COL_POZO)
        self.assertEqual(set(d.index), {"A", "B"})
        self.assertEqual(d.loc["A", "Qoi"], 20)
        self.assertEqual(d.loc["A", COL_NP], 8)
        self.assertEqual(d.loc["B", "Qoi"], 30)
        self.assertEqual(d.loc["B", COL_NP], 10)
        self.assertEqual(d.loc["A", "Registro utilizado"], 2)

    def test_estadisticos_atipicos_y_diseno_de_ambas_variables(self):
        d = pd.DataFrame({COL_POZO:list("ABCDE"), "Qoi":[1,2,3,4,100], COL_NP:[10,20,30,40,1000]})
        for variable in ["Qoi", COL_NP]:
            x, resumen, atipicos = analizar_muestra(d, variable)
            self.assertEqual(len(x), 5)
            self.assertEqual(list(atipicos[COL_POZO]), ["E"])
            self.assertAlmostEqual(resumen["Media"], d[variable].mean())
            hist, box, _, _ = crear_distribuciones(d, variable, "KTIA", False, False)
            self.assertEqual(sum(hist.data[0].y), len(d))
            self.assertEqual(hist.data[0].marker.color, "#00A65A")
            self.assertEqual(box.data[0].fillcolor, "rgba(242,165,65,0.55)")
            self.assertAlmostEqual(box.data[0].median[0], d[variable].median())
            self.assertEqual(hist.layout.height, 560)
            hist.to_json(); box.to_json()

    def test_un_pozo_sin_falsa_prueba_normalidad(self):
        d = pd.DataFrame({COL_POZO:["A"], "Qoi":[100], COL_NP:[10]})
        hist, box, resumen, _ = crear_distribuciones(d, "Qoi", "KTIA")
        self.assertEqual(resumen["Muestras"], 1)
        self.assertTrue(pd.isna(resumen["Shapiro-Wilk p"]))
        self.assertEqual(sum(hist.data[0].y), 1)
        box.to_json()

    def test_banda_no_conecta_huecos_temporales(self):
        p = pd.DataFrame({"MES_REL":[0,1,4,5], "P10":[10,9,7,6], "P90":[100,90,70,60]})
        f = agregar_banda_percentiles(go.Figure(), p)
        zonas = [t for t in f.data if t.fill == "tonexty"]
        self.assertEqual(len(zonas), 2)
        self.assertEqual(list(zonas[0].x), [0,1])
        self.assertEqual(list(zonas[1].x), [4,5])
        self.assertEqual(sum(bool(t.showlegend) for t in zonas), 1)

    def test_banda_loglog_no_incluye_cero_ni_valores_no_positivos(self):
        p = pd.DataFrame({"NP_MB":[0,1,2,3,4], "P10":[10,9,8,0,6], "P90":[100,90,80,70,60]})
        f = agregar_banda_percentiles(go.Figure(), p, "acumulada", False)
        zonas = [t for t in f.data if t.fill == "tonexty"]
        self.assertEqual(len(zonas), 1)
        self.assertEqual(list(zonas[0].x), [1,2])
        self.assertEqual(list(zonas[0].y), [90,80])
        self.assertEqual(list(f.data[0].y), [9,8])


if __name__ == "__main__":
    unittest.main()
