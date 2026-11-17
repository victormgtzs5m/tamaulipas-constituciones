import unittest
import pandas as pd
from mapas_resumen import preparar_identidad_mapa, contadores_estados


class ResumenMapasTests(unittest.TestCase):
    def test_525a_conserva_sufijo_y_coordenadas(self):
        datos = pd.DataFrame({"TERMINACION":["CONST_525A_KTIA","CONST_525_KTS"],
            "POZO":["C-525","C-525"], "X":[609820.3,609815.0], "Y":[2482912.,2482907.]})
        r = preparar_identidad_mapa(datos)
        self.assertEqual(r.POZO.tolist(), ["C-525A","C-525"])
        self.assertEqual(r.POSICION_NOMBRE.tolist(), ["bottom right","top left"])
        pd.testing.assert_frame_equal(r[["X","Y"]], datos[["X","Y"]])

    def test_nombres_no_estandar_no_se_reescriben(self):
        r = preparar_identidad_mapa(pd.DataFrame({"TERMINACION":["OTRO_1"],"POZO":["Pozo especial"]}))
        self.assertEqual(r.POZO.iloc[0], "Pozo especial")

    def test_contadores_unicos_colores_y_filtros(self):
        m = pd.DataFrame({"POZO":["C-525A","CONST-525A","C-525","C-3","C-4","C-5","C-6"],
            "ESTADO_MAPA":["OP","OP","CCP","CSP","IA","PROG TAPONAMIENTO","TAPONADO"]})
        colores = {"OP":"#00A65A","CCP":"#FFD700","CSP":"#DC143C","IA":"#0000FF",
            "PROG TAPONAMIENTO":"#BA55D3","TAPONADO":"#808080"}
        r = {titulo:(n,color) for titulo,n,color in contadores_estados(m,colores)}
        self.assertEqual(r["Operando"], (1,colores["OP"]))
        self.assertEqual(r["Taponados"], (1,colores["TAPONADO"]))
        r = {titulo:n for titulo,n,_ in contadores_estados(m,colores,{"OP"})}
        self.assertEqual(r["Operando"], 1)
        self.assertEqual(r["CCP"], 0)
        self.assertEqual(r["CSP"], 0)

    def test_sin_pozos_mantiene_seis_contadores_en_cero(self):
        colores={k:"#000000" for k in ["OP","CCP","CSP","IA","PROG TAPONAMIENTO","TAPONADO"]}
        r=contadores_estados(pd.DataFrame(columns=["POZO","ESTADO_MAPA"]),colores)
        self.assertEqual(len(r),6)
        self.assertTrue(all(n==0 for _,n,_ in r))

if __name__ == "__main__":
    unittest.main()
