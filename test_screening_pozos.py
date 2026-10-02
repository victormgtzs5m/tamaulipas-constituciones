import unittest
import numpy as np
import pandas as pd
from screening_pozos import (preparar_base_screening,actualizar_muestras_screening,
                            crear_figura_screening,crear_mapa_screening)

class ScreeningTests(unittest.TestCase):
    def setUp(self):
        self.p=pd.DataFrame({"POZO_FISICO":["A","A","B","B"],"TERMINACION":["A1","A1","B1","B1"],
            "YACIMIENTO":["JSA"]*4,"FECHA":pd.to_datetime(["2024-01-01","2024-02-01"]*2),
            "ACEITE":[10,20,30,0],"AGUA":[20,30,40,0],"GAS":[10,20,30,0],
            "Qo (bpd)":[100,200,300,0],"Qw (bpd)":[200,300,400,0],
            "Qg (pcd)":[1000,2000,3000,0],"RGA (pc/bl)":[10,12,10,0]})
        self.a=pd.DataFrame({"TERMINACION":["A1","B1"],"NP_BLS":[500000,100000],"WP_BLS":[1000000,2000000]})
        self.e=pd.DataFrame({"POZO":["A","B"],"ESTADO":["PRODUCTOR","CERRADO"]})
        self.co=pd.DataFrame({"TERMINACION":["A1","B1"],"YACIMIENTO":["JSA"]*2,
                              "CIMA X UTM":[100.,200.],"CIMA Y UTM":[200.,300.]})
    def base(self,p=None,a=None,co=None):
        return preparar_base_screening(self.p if p is None else p,self.a if a is None else a,
                                        self.e,self.co if co is None else co)
    def test_acumuladas_son_las_de_mapas_no_integracion(self):
        r=self.base().set_index("POZO")
        self.assertEqual(r.loc["A","NP_MB"],500)
        self.assertEqual(r.loc["A","WP_MB"],1000)
        self.assertEqual(r.loc["A","RWA"],2)
        otro=self.p.assign(ACEITE=1e12,AGUA=1e12)
        pd.testing.assert_series_equal(self.base(otro).NP_MB,self.base().NP_MB)
    def test_ultimo_dato_y_ceros_sin_promedio(self):
        r=self.base().set_index("POZO")
        self.assertEqual(r.loc["A","QO_ACTUAL"],200)
        self.assertEqual(r.loc["A","RGA_ACTUAL"],12)
        self.assertEqual(r.loc["A","WC_ACTUAL"],60)
        self.assertEqual(r.loc["B","QO_ACTUAL"],0)
        self.assertTrue(pd.isna(r.loc["B","WOR_ACTUAL"]))
        self.assertTrue(pd.isna(r.loc["B","WC_ACTUAL"]))
        self.assertNotIn("FECHA_CORTE",r)
    def test_terminaciones_se_suman_sin_duplicar_historia(self):
        p=pd.concat([self.p,self.p[self.p.TERMINACION.eq("A1")].assign(TERMINACION="A2")])
        a=pd.concat([self.a,self.a.iloc[:1].assign(TERMINACION="A2")])
        r=self.base(p,a).set_index("POZO")
        self.assertEqual(len(r),2)
        self.assertEqual(r.loc["A","NP_MB"],1000)
        self.assertEqual(r.loc["A","QO_ACTUAL"],400)
        self.assertEqual(r.loc["A","RGA_ACTUAL"],10)
    def test_no_suma_tasa_de_terminacion_antigua(self):
        p=pd.concat([self.p,self.p.iloc[:1].assign(TERMINACION="A2")])
        a=pd.concat([self.a,self.a.iloc[:1].assign(TERMINACION="A2")])
        self.assertEqual(self.base(p,a).set_index("POZO").loc["A","QO_ACTUAL"],200)
    def test_muestra_posterior_a_produccion_y_cero_valido(self):
        m=pd.DataFrame({"TERMINACION":["A1","A1","OTRA"],"POZO":["A"]*3,
                       "FECHA MUESTREO":pd.to_datetime(["2025-01-01","2026-01-01","2026-02-01"]),
                       "% AGUA LAB":[90,0,100]})
        r=actualizar_muestras_screening(self.base(),m).set_index("POZO")
        self.assertEqual(r.loc["A","WC_ACTUAL"],0)
        self.assertEqual(r.loc["A","FUENTE_AGUA"],"Laboratorio")
        self.assertEqual(r.loc["A","FECHA_AGUA"],pd.Timestamp("2026-01-01"))
    def test_coordenadas_y_yacimiento_sin_mezclar(self):
        otra=self.co.assign(YACIMIENTO="OTRO",**{"CIMA X UTM":999.})
        r=self.base(co=pd.concat([self.co,otra])).set_index("POZO")
        self.assertEqual(r.loc["A","X"],100)
    def test_ceros_y_faltantes_conservados_en_tabla(self):
        a=self.a.copy()
        a.loc[0,"NP_BLS"]=0
        a.loc[1,"WP_BLS"]=np.nan
        r=self.base(a=a)
        self.assertEqual(len(r),2)
        self.assertFalse(r.EN_GRAFICO.any())
        self.assertTrue(r.MOTIVO.ne("").all())
    def test_figura_log_colores_lineas_tamanos(self):
        r=self.base()
        fig=crear_figura_screening(r,True)
        self.assertEqual(fig.layout.xaxis.type,"log")
        self.assertEqual(fig.layout.yaxis.type,"log")
        for tr,k in zip(fig.data[:3],[1,10,.1]):
            np.testing.assert_allclose(np.array(tr.y),np.array(tr.x)*k)
        color=fig.data[3].marker.colorscale
        self.assertEqual(color[0],(0,"#2ca02c"))
        self.assertEqual(color[-1],(1,"#0066ff"))
        for tr in fig.data[3:]:
            self.assertTrue(all(10<=v<=32 for v in tr.marker.size))
    def test_bandas_mapa(self):
        r=pd.concat([self.base().iloc[:1]]*5,ignore_index=True)
        r["RWA"]=[.5,1,10,11,np.nan]
        fig=crear_mapa_screening(r,None,"JSA")
        self.assertEqual([len(t.x) for t in fig.data],[1,2,1,1])
    def test_fallback_tasas_si_no_hay_vector(self):
        p=self.p.drop(columns=["Qo (bpd)","Qw (bpd)","Qg (pcd)","RGA (pc/bl)"])
        r=self.base(p).set_index("POZO")
        self.assertAlmostEqual(r.loc["A","QO_ACTUAL"],20*6.289810770/29)

    def test_recupera_etapa_productora_antes_de_inyeccion(self):
        p=self.p.assign(INJ=0.)
        iny=p.iloc[[1]].assign(FECHA=pd.Timestamp("2026-08-01"),INJ=1000.,ACEITE=0,AGUA=0,GAS=0,
            **{"Qo (bpd)":0.,"Qw (bpd)":0.,"Qg (pcd)":0.})
        r=self.base(pd.concat([p,iny])).set_index("POZO")
        self.assertEqual(r.loc["A","QO_ACTUAL"],200)
        self.assertEqual(r.loc["A","FECHA_ULTIMO_DATO"],pd.Timestamp("2024-02-01"))
        self.assertFalse(r.loc["A","OPERANDO_AGOSTO_2026"])
        self.assertEqual(r.loc["A","REGISTROS_INYECCION_EXCLUIDOS"],1)
        self.assertEqual(r.loc["A","NP_MB"],500)

    def test_operando_agosto_usa_volumenes_no_estado_ni_dias(self):
        p=self.p.assign(INJ=0.)
        agosto=p.iloc[[1,3]].assign(FECHA=pd.Timestamp("2026-08-01"))
        agosto.loc[agosto.TERMINACION.eq("B1"),"AGUA"]=50.
        r=self.base(pd.concat([p,agosto])).set_index("POZO")
        self.assertTrue(r.OPERANDO_AGOSTO_2026.all())
        agosto.loc[agosto.TERMINACION.eq("A1"),"INJ"]=1
        r=self.base(pd.concat([p,agosto])).set_index("POZO")
        self.assertFalse(r.loc["A","OPERANDO_AGOSTO_2026"])
        self.assertTrue(r.loc["B","OPERANDO_AGOSTO_2026"])

    def test_inyector_puro_conservado_sin_tasas_productoras(self):
        r=self.base(self.p.assign(INJ=100)).set_index("POZO")
        self.assertEqual(len(r),2)
        self.assertTrue(r.QO_ACTUAL.isna().all())
        self.assertTrue(r.FECHA_ULTIMO_DATO.isna().all())
        self.assertFalse(r.OPERANDO_AGOSTO_2026.any())

class ChanTests(unittest.TestCase):
    def historia(self,n=8):
        fechas=pd.date_range("2024-01-01",periods=n,freq="MS")
        dias=np.cumsum(fechas.days_in_month.to_numpy())
        return pd.DataFrame({"FECHA":fechas,"POZO":"A","YACIMIENTO":"JSA",
                             "QO":10.,"QW":10*(2+.01*dias)})
    def test_dias_calendario_bisiesto_y_derivada(self):
        from screening_pozos import preparar_datos_chan
        h=preparar_datos_chan(self.historia())
        self.assertEqual(h.DIAS_ACUMULADOS.iloc[:3].tolist(),[31,60,91])
        np.testing.assert_allclose(h.DERIVADA_WOR,.01,atol=1e-12)
    def test_huecos_no_se_derivan_y_no_reinician_tiempo(self):
        from screening_pozos import preparar_datos_chan
        h=preparar_datos_chan(self.historia().drop(index=3))
        self.assertEqual(h.DIAS_ACUMULADOS.iloc[3],121)
        self.assertTrue(pd.isna(h.DERIVADA_WOR.iloc[3]))
        np.testing.assert_allclose(h.DERIVADA_WOR.dropna(),.01,atol=1e-12)
    def test_cero_aceite_y_derivada_negativa(self):
        from screening_pozos import preparar_datos_chan,crear_figura_chan
        p=self.historia(); p["QW"]=100-p.QW; p.loc[3,"QO"]=0
        h=preparar_datos_chan(p)
        self.assertTrue(pd.isna(h.WOR.iloc[3]))
        self.assertTrue((h.DERIVADA_WOR.dropna()<0).all())
        fig,avisos=crear_figura_chan(h,"A")
        self.assertEqual(fig.layout.xaxis.type,"log")
        self.assertEqual(fig.layout.yaxis.type,"log")
        self.assertNotIn("WOR′ = dWOR/dt",[t.name for t in fig.data])
        self.assertTrue(any("negativos" in a for a in avisos))
    def test_polinomio_grado_cuatro_unidades_originales(self):
        from screening_pozos import ajustar_polinomio_chan
        t=np.linspace(30,6000,12)
        f=lambda x: 1+2e-3*x+3e-6*x**2-4e-10*x**3+5e-14*x**4
        x,y=ajustar_polinomio_chan(t,f(t))
        np.testing.assert_allclose(y,f(x),rtol=1e-10)
        self.assertEqual((x.min(),x.max()),(t.min(),t.max()))
        self.assertIsNone(ajustar_polinomio_chan(t[:4],f(t[:4])))
    def test_no_mezclar_pozos(self):
        from screening_pozos import preparar_datos_chan
        h=self.historia(); h.loc[0,"POZO"]="B"
        with self.assertRaises(ValueError):
            preparar_datos_chan(h)

class ActualScatterTests(unittest.TestCase):
    def base(self):
        t=ScreeningTests(); t.setUp()
        return t.base()
    def test_wor_actual_color_y_tamano_qo(self):
        from screening_pozos import crear_scatter_actual
        r=self.base()
        fig,n=crear_scatter_actual(r)
        self.assertEqual(n,1)
        self.assertEqual(fig.data[0].y[0],1.5)
        self.assertEqual(fig.data[0].x[0],500)
        self.assertEqual(fig.data[0].marker.size[0],32)
        self.assertEqual(fig.data[0].marker.color[0],200)
        self.assertEqual(fig.data[0].marker.cmin,0)
        self.assertEqual(fig.data[0].marker.cmax,200)
        self.assertEqual(fig.layout.xaxis.type,"linear")
    def test_agua_color_fuente_y_sin_muestra(self):
        from screening_pozos import crear_scatter_actual
        r=self.base(); r.loc[0,"WC_ACTUAL"]=100; r.loc[0,"FUENTE_AGUA"]="Laboratorio"
        fig,n=crear_scatter_actual(r,"WP_MB",True)
        self.assertEqual(n,2)
        self.assertEqual(fig.data[0].marker.color[0],100)
        self.assertIn("Laboratorio",fig.data[0].customdata[0])
        self.assertEqual(fig.data[0].marker.colorscale[-1],(1,"#0066ff"))
        self.assertEqual(fig.data[1].marker.color,"#909090")
    def test_filtros_ceros_y_vacio(self):
        from screening_pozos import crear_scatter_actual
        r=self.base().iloc[:1].copy(); r["WOR_ACTUAL"]=0
        self.assertEqual(crear_scatter_actual(r)[1],1)
        self.assertEqual(crear_scatter_actual(r,logaritmico=True)[1],0)
        self.assertEqual(crear_scatter_actual(r.iloc[:0],"WP_MB")[1],0)

if __name__=="__main__":
    unittest.main()
