import unittest
import pandas as pd
from estados_pozos import construir_estados, adjuntar_estados


class EstadosTests(unittest.TestCase):
    def setUp(self):
        self.e = pd.DataFrame({"Pozo":["T-1","C-2","C-3","C-4","CH-5"],
            "Estado":["Taponado"]*5,
            "Estado Final":["Operando","Operando","Taponado","CCP","IA"], "SAP":["A"]*5})
        self.p = pd.DataFrame({"POZO":["TMLP-1","TMLP-1","CONST-2","CONST-3","CONST-4","CHAMPAYAN-5"],
            "TERMINACION":["TMLP_1_JSA","TMLP_1_KTIA","CONST_2_JSA","CONST_3_JSA","CONST_4_JSA","CHAMPAYAN_5_JSA"],
            "YACIMIENTO":["JSA","KTIA","JSA","JSA","JSA","JSA"],
            "FECHA":["2026-08-01","2026-07-01","2026-08-01","2026-08-01","2026-08-01","2026-08-01"],
            "ACEITE":[5,10,0,3,0,0],"AGUA":[0]*6,"GAS":[0,0,0,0,2,0],"INJ":[0,0,0,0,0,100]})
        self.co = self.p[["TERMINACION","POZO","YACIMIENTO"]].copy()

    def catalogo(self, prod=None):
        return construir_estados(self.e, self.p if prod is None else prod, self.co)

    def test_final_no_columna_anterior_y_demueve_operando(self):
        c=self.catalogo(); r=c[c.YACIMIENTO.eq("")].set_index("POZO")
        self.assertEqual(r.loc["T1","ESTADO"],"Operando")
        self.assertEqual(r.loc["C2","ESTADO"],"CCP")
        self.assertEqual(r.loc["C3","ESTADO"],"Operando")
        self.assertEqual(r.loc["C4","ESTADO"],"Operando")
        self.assertEqual(r.loc["CH5","ESTADO"],"IA")

    def test_no_propaga_produccion_a_otra_zona(self):
        d=pd.DataFrame({"POZO":["T-1","T-1","T-1"],"YACIMIENTO":["JSA","KTIA","OTRA"]})
        r=adjuntar_estados(d,self.catalogo())
        self.assertEqual(r.ESTADO.tolist(),["Operando","CCP","CCP"])
        self.assertEqual(len(r),len(d))
        self.assertEqual(adjuntar_estados(d.drop(columns="YACIMIENTO"),self.catalogo()).ESTADO.tolist(),["Operando"]*3)

    def test_corte_avanza_y_no_usa_ultimo_mes_de_cada_pozo(self):
        p=pd.concat([self.p,self.p.iloc[[2]].assign(FECHA="2026-09-01",ACEITE=5)])
        r=self.catalogo(p); fis=r[r.YACIMIENTO.eq("")].set_index("POZO")
        self.assertEqual(fis.loc["T1","ESTADO"],"CCP")
        self.assertEqual(fis.loc["C2","ESTADO"],"Operando")
        self.assertEqual(r.FECHA_ESTADO.max(),pd.Timestamp("2026-09-01"))

    def test_terminacion_respaldo_coord_y_duplicados_no_multiplican(self):
        p=self.p.copy(); p["POZO"]=None
        c=construir_estados(self.e,p,pd.concat([self.co,self.co]))
        d=pd.DataFrame({"POZO":["T-1","T-1"],"YACIMIENTO":["JSA","JSA"]},index=[4,4])
        r=adjuntar_estados(d,c)
        self.assertEqual(len(r),2)
        self.assertEqual(r.ESTADO.tolist(),["Operando"]*2)

    def test_no_fecha_valida_no_cierra_pozos(self):
        r=self.catalogo(self.p.assign(FECHA=None))
        self.assertEqual(r.loc[r.POZO.eq("T1") & r.YACIMIENTO.eq(""),"ESTADO"].iloc[0],"Operando")

    def test_exige_columna_final_y_conflictos_explicitos(self):
        with self.assertRaisesRegex(ValueError,"Estado Final"):
            construir_estados(self.e.drop(columns="Estado Final"),self.p,self.co)
        with self.assertRaisesRegex(ValueError,"contradictorio"):
            construir_estados(pd.concat([self.e,self.e.iloc[[0]].assign(**{"Estado Final":"CSP"})]),self.p,self.co)

if __name__ == "__main__":
    unittest.main()
