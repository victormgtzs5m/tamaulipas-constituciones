import unittest
import numpy as np
import pandas as pd
from idpi import calcular_idpi, interpolar_idpi, M3_A_BBL, M3_A_PC

class IndicadorTests(unittest.TestCase):
    def setUp(self):
        self.p=pd.DataFrame([
            dict(TERMINACION=t,YACIMIENTO="JSA",FECHA=d,ACEITE=100*f,AGUA=50,GAS=100*f*f)
            for t,f in [("A",1),("B",2),("C",3)]
            for d in pd.date_range("2024-01-01","2025-12-01",freq="MS")])
        self.pm=pd.DataFrame(dict(TERMINACION=list("ABC"),PRESION_IDPI=[100,200,300],
                                 FECHA_MAPA_PRESION=pd.to_datetime(["2026-02-01"]*3)))
        self.m=pd.DataFrame({"TERMINACION":list("ABC"),
            "FECHA MUESTREO":pd.to_datetime(["2026-01-01"]*3),"% AGUA LAB":[0,20,40]})
    def calc(self,p=None,m=None,pm=None,**kwargs):
        return calcular_idpi(self.p if p is None else p,pd.DataFrame(),
            self.m if m is None else m,"JSA",
            presiones_mapa=self.pm if pm is None else pm,**kwargs).set_index("TERMINACION")
    def test_formula_unidades_y_pesos(self):
        r=self.calc()
        a=r.loc["A"]
        self.assertAlmostEqual(a.NP12_MB,1200*M3_A_BBL/1000)
        self.assertAlmostEqual(a.QO_3M_INICIAL,300*M3_A_BBL/91)
        self.assertAlmostEqual(a.RGA_12M,M3_A_PC/M3_A_BBL)
        self.assertAlmostEqual(a.IDPI,.25*(100/6)+.25*(100/6)+.15*100+.1*(500/6)+.1*(100/6)+.15*50)
        self.assertEqual(a.MESES_RGA,12)
        self.assertFalse("NP12_NORM" in r)
    def test_rga_promedio_mensual_no_cociente_acumulados(self):
        p=self.p.copy()
        a=p.TERMINACION.eq("A") & p.FECHA.ge("2025-01-01")
        p.loc[a,"ACEITE"]=100
        p.loc[a,"GAS"]=100
        idx=p.index[a][-1]
        p.loc[idx,["ACEITE","GAS"]]=[1000,2000]
        self.assertAlmostEqual(self.calc(p=p).loc["A","RGA_12M"],(11+2)/12*M3_A_PC/M3_A_BBL)
    def test_rga_ventana_individual(self):
        p=self.p[~(self.p.TERMINACION.eq("A")&self.p.FECHA.gt("2024-12-01"))]
        a=self.calc(p=p).loc["A"]
        self.assertEqual(a.FIN_RGA,pd.Timestamp("2024-12-01"))
        self.assertEqual(a.MESES_RGA,12)
        self.assertTrue(pd.notna(a.IDPI))
    def test_rga_cero_gas_valido_aceite_cero_y_nulo_excluidos(self):
        p=self.p.copy()
        a=p.TERMINACION.eq("A")&p.FECHA.ge("2025-01-01")
        ids=p.index[a]
        p.loc[ids[0],"ACEITE"]=0
        p.loc[ids[1],"GAS"]=np.nan
        p.loc[ids[2],"GAS"]=0
        r=self.calc(p=p).loc["A"]
        self.assertEqual(r.MESES_RGA,10)
        self.assertAlmostEqual(r.RGA_12M,.9*M3_A_PC/M3_A_BBL)
        p.loc[ids,"ACEITE"]=0
        r=self.calc(p=p).loc["A"]
        self.assertTrue(pd.notna(r.IDPI))
        self.assertEqual(r.FIN_RGA,pd.Timestamp("2024-12-01"))
    def test_agua_lab_y_fallback(self):
        self.assertEqual(self.calc().loc["A","AGUA_RECIENTE"],0)
        r=self.calc(m=pd.DataFrame())
        self.assertAlmostEqual(r.loc["A","AGUA_RECIENTE"],100/3)
        self.assertEqual(r.loc["A","FUENTE_AGUA"],"Ultima produccion liquida")
    def test_presion_solo_mapa(self):
        medidas=pd.DataFrame(dict(TERMINACION=list("ABC"),YACIMIENTO=["JSA"]*3,
                                 FECHA=pd.to_datetime(["2026-03-01"]*3),PRESION=[9999]*3))
        r=calcular_idpi(self.p,medidas,self.m,"JSA",presiones_mapa=self.pm).set_index("TERMINACION")
        self.assertEqual(r.loc["A","PRESION_IDPI"],100)
        r=calcular_idpi(self.p,medidas,self.m,"JSA")
        self.assertTrue(r.IDPI.isna().all())
    def test_duplicados_e_historia_joven(self):
        r=self.calc(p=pd.concat([self.p,self.p.iloc[:1]]))
        self.assertTrue(pd.isna(r.loc["A","IDPI"]))
        r=self.calc(p=self.p[self.p.FECHA.le("2024-06-01")])
        self.assertTrue(r.NP12_MB.isna().all())
    def test_dias_calendario_y_huecos(self):
        pd.testing.assert_frame_equal(self.calc(),self.calc(p=self.p.assign(DIAS=0)))
        p=self.p[~(self.p.TERMINACION.eq("A")&self.p.FECHA.eq("2024-02-01"))]
        a=self.calc(p=p).loc["A"]
        self.assertAlmostEqual(a.NP12_MB,1100*M3_A_BBL/1000)
        self.assertAlmostEqual(a.QO_3M_INICIAL,200*M3_A_BBL/91)
    def test_sin_mezcla_yacimiento_y_vacio(self):
        extra=self.p.assign(YACIMIENTO="OTRO",ACEITE=1e9)
        pd.testing.assert_frame_equal(self.calc(),self.calc(p=pd.concat([self.p,extra])))
        self.assertTrue(self.calc(p=self.p.iloc[:0]).empty)

    def test_vectores_compartidos_y_conversion_a_inyector(self):
        import ast
        from pathlib import Path
        tree=ast.parse(Path("app.py").read_text(encoding="utf-8"))
        ns={"pd":pd,"np":np}
        for node in tree.body:
            if isinstance(node,ast.Assign):
                for target in node.targets:
                    if isinstance(target,ast.Name) and target.id.startswith(("COL_","M3_")):
                        try:
                            ns[target.id]=ast.literal_eval(node.value)
                        except (ValueError,TypeError):
                            pass
        for name in ["calcular_columnas_produccion","preparar_vectores_produccion_idpi"]:
            node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
            exec(compile(ast.Module(body=[node],type_ignores=[]),"app.py","exec"),ns)
        p=self.p.assign(INJ=0.,DIAS=0.)
        iny=p[p.TERMINACION.eq("A")].copy()
        iny["FECHA"]=iny.FECHA+pd.DateOffset(years=2)
        iny[["ACEITE","AGUA","GAS"]]=0.
        iny["INJ"]=1000.
        p=pd.concat([p,iny],ignore_index=True)
        v=ns["preparar_vectores_produccion_idpi"](p)
        r=self.calc(p=p,vectores_produccion=v).loc["A"]
        self.assertEqual(r.FIN_RGA,pd.Timestamp("2025-12-01"))
        self.assertEqual(r.ULTIMO_REGISTRO,pd.Timestamp("2027-12-01"))
        self.assertEqual(r.MESES_RGA,12)
        esperado=v[v.TERMINACION.eq("A")&v.FECHA.between("2025-01-01","2025-12-01")]
        self.assertAlmostEqual(r.RGA_12M,esperado["RGA (pc/bl)"].mean())
        self.assertAlmostEqual(r.QO_3M_INICIAL,300*M3_A_BBL/91)
        self.assertTrue(pd.notna(r.IDPI))
        # Confirmar que el indicador consume la curva recibida.
        v.loc[v.TERMINACION.eq("A"),"RGA (pc/bl)"]=123.
        self.assertAlmostEqual(self.calc(p=p,vectores_produccion=v).loc["A","RGA_12M"],123.)



    def test_relacion_calendario_y_pesos(self):
        from idpi import PESOS_IDPI
        r=self.calc()
        a=r.loc["A"]
        self.assertAlmostEqual(a.QO_6M,600*M3_A_BBL/184)
        self.assertAlmostEqual(a.RELACION_QO,(600/184)/(300/91))
        self.assertEqual(a.INICIO_QO_6M,pd.Timestamp("2025-07-01"))
        self.assertEqual(a.FIN_QO_6M,pd.Timestamp("2025-12-01"))
        self.assertEqual(PESOS_IDPI,dict(S_NP12=.25,S_PRESION=.25,S_AGUA=.15,
            S_RGA=.10,S_QO3=.10,S_RELACION=.15))
        self.assertAlmostEqual(sum(PESOS_IDPI.values()),1.)
        p=self.p.copy()
        p.loc[p.TERMINACION.eq("C")&p.FECHA.ge("2025-07-01"),"ACEITE"]*=2
        r=self.calc(p=p)
        self.assertGreater(r.loc["C","S_RELACION"],r.loc["A","S_RELACION"])

    def test_relacion_no_divide_cero_ni_rellena_huecos(self):
        p=self.p.copy()
        p.loc[p.TERMINACION.eq("A")&p.FECHA.le("2024-03-01"),"ACEITE"]=0.
        r=self.calc(p=p).loc["A"]
        self.assertTrue(pd.isna(r.RELACION_QO))
        self.assertTrue(pd.isna(r.IDPI))
        p=self.p[~(self.p.TERMINACION.eq("A")&self.p.FECHA.eq("2025-08-01"))]
        r=self.calc(p=p).loc["A"]
        self.assertAlmostEqual(r.QO_6M,600*M3_A_BBL/183)
        self.assertEqual(r.INICIO_QO_6M,pd.Timestamp("2025-06-01"))
        self.assertIn("06/2025",r.NOTA_RELACION)

    def test_relacion_ignora_inyeccion_posterior(self):
        iny=self.p[self.p.TERMINACION.eq("A")].copy()
        iny["FECHA"]+=pd.DateOffset(years=2)
        iny[["ACEITE","AGUA","GAS"]]=0
        r=self.calc(p=pd.concat([self.p,iny])).loc["A"]
        self.assertAlmostEqual(r.RELACION_QO,self.calc().loc["A","RELACION_QO"])
        self.assertEqual(r.FIN_QO_6M,pd.Timestamp("2025-12-01"))

    def test_grid_acotado(self):
        mapa=pd.DataFrame(dict(X=[0,1000,0],Y=[0,0,1000],IDPI=[0,50,100]))
        borde=pd.DataFrame(dict(X=[-500,1500,1500,-500],Y=[-500,-500,1500,1500]))
        r=interpolar_idpi(mapa,borde,"X","Y",grid_n=31,radio=1500)
        self.assertIsNotNone(r)
        self.assertTrue(np.isnan(r[2][-1,-1]))
        self.assertGreaterEqual(np.nanmin(r[2]),0)
        self.assertLessEqual(np.nanmax(r[2]),100)
        self.assertIsNone(interpolar_idpi(mapa,borde,"X","Y",radio=10))

if __name__=="__main__":
    unittest.main()
