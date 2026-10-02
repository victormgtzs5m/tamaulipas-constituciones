import unittest
import numpy as np
import pandas as pd
from presion_interpolada import (
    evaluar_kriging_presion, estimar_presiones_para_pozos,
    unir_presiones_coordenadas
)


class PresionInterpoladaTests(unittest.TestCase):
    def setUp(self):
        self.co = pd.DataFrame({
            "TERMINACION": list("ABCDEF"),
            "YACIMIENTO": ["JSA"] * 6,
            "POZO": list("ABCDEF"),
            "CIMA X UTM": [0., 1000., 0., 1000., 500., 3000.],
            "CIMA Y UTM": [0., 0., 1000., 1000., 500., 3000.]
        })
        self.pr = pd.DataFrame({
            "TERMINACION": list("ABCD"), "YACIMIENTO": ["JSA"] * 4,
            "FECHA": pd.to_datetime(["2026-01-01"] * 4),
            "PRESION": [100., 200., 300., 400.]
        })
        self.base = self.co.iloc[:4].copy()
        self.base["PRESION_MAPA"] = self.pr["PRESION"]
        self.borde = pd.DataFrame({"X": [-100,1100,1100,-100], "Y": [-100,-100,1100,1100]})

    def test_grid_y_evaluacion_coinciden(self):
        z, _ = evaluar_kriging_presion(self.base, [0.,500.,1000.], [0.,500.,1000.], "grid")
        punto, _ = evaluar_kriging_presion(self.base, [500.], [500.])
        self.assertAlmostEqual(z[1,1], punto[0], places=8)
        self.assertAlmostEqual(punto[0], 250., places=6)

    def test_preserva_medidas_y_estima_sin_fecha_ficticia(self):
        r=estimar_presiones_para_pozos(self.pr,self.base,self.co,self.borde,"JSA").set_index("TERMINACION")
        self.assertEqual(r.loc["A","PRESION_IDPI"],100.)
        self.assertEqual(r.loc["A","FUENTE_PRESION"],"Medida")
        self.assertAlmostEqual(r.loc["E","PRESION_IDPI"],250.,places=6)
        self.assertEqual(r.loc["E","FUENTE_PRESION"],"Estimada por kriging")
        self.assertTrue(pd.isna(r.loc["E","FECHA_PRESION_IDPI"]))
        self.assertEqual(r.loc["E","FECHA_MAPA_PRESION"],pd.Timestamp("2026-01-01"))
        self.assertGreaterEqual(r.loc["E","ERROR_KRIGING"],0)
        self.assertGreater(r.loc["E","DISTANCIA_PRESION_M"],0)
        self.assertTrue(pd.isna(r.loc["F","PRESION_IDPI"]))
        self.assertIn("Fuera del contorno",r.loc["F","NOTA_PRESION"])

    def test_pocas_mediciones_no_inventa_presion(self):
        r=estimar_presiones_para_pozos(self.pr.iloc[:2],self.base.iloc[:2],self.co,self.borde,"JSA").set_index("TERMINACION")
        self.assertTrue(pd.isna(r.loc["E","PRESION_IDPI"]))
        self.assertIn("tres",r.loc["E","NOTA_PRESION"])
        self.assertEqual(r.loc["A","PRESION_IDPI"],100.)

    def test_constante_y_coordenadas_repetidas(self):
        base=self.base.assign(PRESION_MAPA=150.)
        base=pd.concat([base,base.iloc[:1]],ignore_index=True)
        z,var=evaluar_kriging_presion(base,[500.],[500.])
        self.assertEqual(z[0],150.)
        self.assertEqual(var[0],0.)

    def test_no_mezcla_yacimientos(self):
        otra=self.base.assign(YACIMIENTO="KTIA",PRESION_MAPA=9999.)
        pr_otra=self.pr.assign(YACIMIENTO="KTIA",PRESION=9999.)
        r=estimar_presiones_para_pozos(
            pd.concat([self.pr,pr_otra]),pd.concat([self.base,otra]),
            self.co,self.borde,"JSA"
        ).set_index("TERMINACION")
        self.assertAlmostEqual(r.loc["E","PRESION_IDPI"],250.,places=6)
        sin=estimar_presiones_para_pozos(
            self.pr.iloc[:0],self.base.iloc[:0],self.co,self.borde,"JSA"
        )
        self.assertTrue(sin.PRESION_IDPI.isna().all())

    def test_asocia_por_terminacion_y_yacimiento(self):
        seleccion=self.base.drop(columns=["CIMA X UTM","CIMA Y UTM"]).copy()
        seleccion.loc[0,"POZO"]="Nombre diferente"
        r=unir_presiones_coordenadas(seleccion,self.co)
        self.assertEqual(len(r),4)
        self.assertEqual(r.loc[r.TERMINACION.eq("A"),"CIMA X UTM"].iloc[0],0.)


    def test_solo_mapa_evalua_tambien_pozos_con_medicion(self):
        medidas=self.pr.assign(PRESION=9999.)
        r=estimar_presiones_para_pozos(
            medidas,self.base,self.co,self.borde,"JSA",solo_mapa=True
        ).set_index("TERMINACION")
        z,_=evaluar_kriging_presion(self.base,[0.,500.],[0.,500.])
        self.assertAlmostEqual(r.loc["A","PRESION_IDPI"],z[0])
        self.assertAlmostEqual(r.loc["E","PRESION_IDPI"],z[1])
        self.assertEqual(r.loc["A","FUENTE_PRESION"],"Estimada por kriging")
        self.assertTrue(pd.isna(r.loc["A","FECHA_PRESION_IDPI"]))
        sin=estimar_presiones_para_pozos(
            medidas,self.base.iloc[:0],self.co,self.borde,"JSA",solo_mapa=True)
        self.assertTrue(sin.PRESION_IDPI.isna().all())


if __name__=="__main__":
    unittest.main()
