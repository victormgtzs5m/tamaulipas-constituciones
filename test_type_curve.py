import unittest
import numpy as np
import pandas as pd
from type_curve import agregar_resultados_perfil_propuesto, calcular_perfil_exponencial, agregar_perfil_exponencial, calcular_pozos_activos, normalizar_acumulada, preparar_historia, calcular_p50_tiempo, calcular_p50_acumulada, crear_grafico


class TypeCurveTests(unittest.TestCase):
    def test_tiempo_cero_calendario_y_volumen(self):
        datos = pd.DataFrame({
            "TERMINACION_DCA": ["T1"] * 3, "TERMINACION": ["C-1"] * 3,
            "YACIMIENTO": ["KTIA"] * 3, "FECHA": pd.to_datetime(["2020-01-01", "2020-02-01", "2020-04-01"]),
            "Qo (bpd)": [0, 100, 50], "Aceite (bl)": [0, 3000, 1500]})
        h = preparar_historia(datos)
        self.assertEqual(list(h.MES_REL), [0, 2])
        np.testing.assert_allclose(h.NP_MB, [3, 4.5])
        self.assertEqual(list(h.QO), [100, 50])

    def test_no_mezcla_terminaciones_ni_yacimientos(self):
        d = pd.DataFrame({"TERMINACION_DCA": ["T1", "T2", "T1"],
            "TERMINACION": ["C-1"] * 3, "YACIMIENTO": ["KTIA", "KTIA", "JSA"],
            "FECHA": pd.to_datetime(["2020-01-01"] * 3),
            "Qo (bpd)": [100, 200, 400], "Aceite (bl)": [3000, 6000, 12000]})
        h = preparar_historia(d)
        self.assertEqual(len(h), 3)
        self.assertEqual(set(h.NP_MB), {3, 6, 12})
        self.assertTrue(h.MES_REL.eq(0).all())

    def test_p50_tiempo_incluye_ceros_sin_inventar_faltantes(self):
        d = pd.DataFrame({"POZO_ID": ["A", "B", "C", "A"], "MES_REL": [0, 0, 0, 2], "QO": [0, 50, 100, 25]})
        p = calcular_p50_tiempo(d, 2)
        self.assertEqual(list(p.MES_REL), [0])
        self.assertEqual(p.iloc[0].P50, 50)
        self.assertEqual(p.iloc[0].N_POZOS, 3)
        self.assertEqual(calcular_p50_tiempo(d, 1).iloc[-1].N_POZOS, 1)

    def test_p50_acumulada_sin_extrapolacion(self):
        h = pd.DataFrame({"POZO_ID": ["A", "A", "B", "B"],
                          "NP_MB": [1, 10, 10, 100], "QO": [100, 10, 1000, 100]})
        p = calcular_p50_acumulada(h, 1).set_index("NP_MB")
        self.assertAlmostEqual(p.loc[1, "P50"], 100)
        self.assertAlmostEqual(p.loc[10, "P50"], 505)
        self.assertAlmostEqual(p.loc[100, "P50"], 100)
        p = calcular_p50_acumulada(h, 2)
        self.assertTrue(p.loc[p.P50.notna(), "NP_MB"].eq(10).all())
        self.assertTrue(p.loc[p.N_POZOS.lt(2), "P50"].isna().all())

    def test_interpolacion_loglog(self):
        h = pd.DataFrame({"POZO_ID": ["A", "A"], "NP_MB": [1, 100], "QO": [1000, 10]})
        p = calcular_p50_acumulada(h, puntos=3).set_index("NP_MB")
        self.assertAlmostEqual(p.loc[10, "P50"], 100)
        self.assertEqual(p.loc[10, "N_POZOS"], 1)

    def test_hueco_sin_participantes_no_se_conecta(self):
        h = pd.DataFrame({"POZO_ID": ["A", "A", "B", "B"],
                          "NP_MB": [1, 2, 10, 20], "QO": [100, 50, 20, 10]})
        p = calcular_p50_acumulada(h)
        hueco = p.loc[p.NP_MB.between(2.01, 9.99)]
        self.assertFalse(hueco.empty)
        self.assertTrue(hueco.P50.isna().all())

    def test_semilog_loglog_y_huecos_de_historia(self):
        h = pd.DataFrame({"POZO_ID": ["A", "A"], "MES_REL": [0, 2], "NP_MB": [3, 4.5], "QO": [100, 50]})
        p = calcular_p50_tiempo(h)
        f = crear_grafico(h, p)
        self.assertEqual(f.layout.xaxis.type, "linear")
        self.assertEqual(f.layout.yaxis.type, "log")
        self.assertEqual(len(f.data[0].x), 3)
        self.assertTrue(np.isnan(f.data[0].y[1]))
        f = crear_grafico(h, calcular_p50_acumulada(h), "acumulada")
        self.assertEqual(f.layout.xaxis.type, "log")
        self.assertEqual(f.layout.yaxis.type, "log")
        self.assertEqual(f.data[-1].line.color, "#FF6E00")
        f.to_json()

    def test_normalizacion_por_pozo_y_ventana_considerada(self):
        h = pd.DataFrame({"POZO_ID": ["A", "A", "B", "B"],
            "MES_REL": [12, 13, 12, 13], "NP_MB": [100, 120, 300, 350], "QO": [100, 80, 200, 150]})
        d = normalizar_acumulada(h)
        np.testing.assert_allclose(d.NP_NORMALIZADA_MB, [0, 20, 0, 50])
        np.testing.assert_allclose(h.NP_MB, [100, 120, 300, 350])
        p = calcular_p50_acumulada(d.assign(NP_MB=d.NP_NORMALIZADA_MB), incluir_cero=True)
        self.assertEqual(p.iloc[0].NP_MB, 0)
        self.assertAlmostEqual(p.iloc[0].P50, 150)
        self.assertEqual(p.iloc[0].N_POZOS, 2)
        f = crear_grafico(d, p, "acumulada", np_desde_cero=True)
        self.assertEqual(f.layout.xaxis.type, "linear")
        self.assertEqual(f.layout.yaxis.type, "log")
        self.assertEqual(f.data[0].x[0], 0)
        self.assertEqual(f.data[1].x[0], 0)
        self.assertEqual(f.data[-1].x[0], 0)
        self.assertEqual(f.data[-1].type, "scattergl")
        self.assertGreater(f.data[-1].line.width, 0)
        f.to_json()

    def test_cero_normalizado_con_un_registro_por_pozo(self):
        h = pd.DataFrame({"POZO_ID": ["A", "B"], "MES_REL": [0, 0],
                          "NP_MB": [3, 8], "QO": [100, 300]})
        d = normalizar_acumulada(h)
        p = calcular_p50_acumulada(d.assign(NP_MB=d.NP_NORMALIZADA_MB), incluir_cero=True)
        self.assertEqual(len(p), 1)
        self.assertEqual(p.iloc[0].NP_MB, 0)
        self.assertEqual(p.iloc[0].P50, 200)
        self.assertEqual(p.iloc[0].N_POZOS, 2)

    def test_activos_por_mes_ceros_huecos_y_duplicados(self):
        h = pd.DataFrame({"POZO_ID": ["A", "A", "B", "A", "B", "A"],
            "MES_REL": [0, 0, 0, 1, 1, 3], "QO": [100, 100, 0, 0, 50, 20],
            "NP_MB": [3, 3, 0, 3, 2, 4]})
        a = calcular_pozos_activos(h)
        self.assertEqual(list(a.MES_REL), [0, 1, 2, 3])
        self.assertEqual(list(a.N_ACTIVOS), [1, 1, 0, 1])
        # La curva sigue presente incluso si el minimo elimina todo el P50.
        h = h.drop_duplicates(["POZO_ID", "MES_REL"])
        f = crear_grafico(h, calcular_p50_tiempo(h, minimo=3))
        traza = next(t for t in f.data if t.name == "Pozos activos")
        self.assertEqual(traza.yaxis, "y2")
        self.assertEqual(list(traza.y), [1, 1, 0, 1])
        self.assertEqual(f.layout.yaxis2.type, "linear")
        self.assertEqual(f.layout.yaxis.type, "log")

    def test_activos_acumulada_normalizada_sin_extrapolar(self):
        h = pd.DataFrame({"POZO_ID": ["A", "A", "B", "B"],
            "MES_REL": [0, 1, 0, 1], "NP_MB": [100, 110, 200, 220], "QO": [100, 50, 200, 100]})
        h = normalizar_acumulada(h)
        a = calcular_pozos_activos(h, "acumulada").set_index("NP_MB")
        self.assertEqual(a.loc[0, "N_ACTIVOS"], 2)
        self.assertEqual(a.loc[10, "N_ACTIVOS"], 2)
        self.assertEqual(a.loc[20, "N_ACTIVOS"], 1)
        for cero in [True, False]:
            f = crear_grafico(h, calcular_p50_acumulada(h.assign(NP_MB=h.NP_NORMALIZADA_MB), incluir_cero=True),
                              "acumulada", np_desde_cero=cero)
            self.assertEqual(f.layout.yaxis2.side, "right")
            self.assertEqual(f.layout.yaxis2.type, "linear")
            self.assertTrue(any(t.name == "Pozos activos" for t in f.data))
            f.to_json()
        f = crear_grafico(h, pd.DataFrame(), "acumulada", mostrar_activos=False)
        self.assertFalse(any(t.name == "Pozos activos" for t in f.data))

    def test_exponencial_dos_etapas_continuidad_y_suma_mensual(self):
        p = calcular_perfil_exponencial(100, 0.05, 12, 0.02, 5, dias_mes=30)
        q_cambio = 100 * np.exp(-0.05 * 11)
        esperado_fin = 11 + np.log(q_cambio / 5) / 0.02
        self.assertEqual(p.MES_REL.iloc[-1], int(np.floor(esperado_fin)) + 1)
        self.assertEqual(p.QO.iloc[0], 100)
        self.assertEqual(p.NP_NORMALIZADA_MB.iloc[0], 0)
        self.assertLess(p.QO.iloc[-1], 5)
        self.assertAlmostEqual(p.loc[p.MES_REL.eq(11), "QO"].iloc[0], q_cambio)
        meses = np.arange(int(p.MES_REL.iloc[-1]) + 1)
        tasas = 100 * np.exp(-.05 * np.minimum(meses, 11) - .02 * np.maximum(meses - 11, 0))
        esperado_np = tasas.sum() * 30 / 1000
        self.assertAlmostEqual(p.NP_MB.iloc[-1], esperado_np)
        self.assertAlmostEqual(p.VOLUMEN_INTERVALO_BBL.sum(), p.RESERVA_BBL.iloc[-1])
        self.assertTrue(np.all(np.diff(p.QO) <= 1e-10))
        self.assertTrue(np.all(np.diff(p.NP_MB) >= 0))

    def test_exponencial_corte_en_primera_etapa(self):
        p = calcular_perfil_exponencial(100, 0.5, 12, 0, 10)
        self.assertEqual(p.MES_REL.iloc[-1], int(np.floor(np.log(10) / 0.5)) + 1)
        self.assertTrue(p.loc[p.MES_REL.gt(0), "ETAPA"].eq(1).all())
        self.assertLess(p.QO.iloc[-1], 10)
        p = calcular_perfil_exponencial(100, 0, 6, 0.1, 10, dias_mes=30)
        self.assertTrue(p.loc[p.MES_REL.lt(6), "QO"].eq(100).all())
        self.assertAlmostEqual(p.loc[p.MES_REL.eq(5), "NP_MB"].iloc[0], 18)

    def test_exponencial_validaciones_y_duracion_sin_truncar(self):
        for valores in [(0, .1, 12, .1, 5), (100, .1, 12, .1, 100),
                        (100, 0, 12, 0, 5), (100, -.1, 12, .1, 5),
                        (100, .1, -1, .1, 5), (100, .1, 12, .1, 0)]:
            with self.assertRaises(ValueError):
                calcular_perfil_exponencial(*valores)
        p = calcular_perfil_exponencial(100, 0, 12, .0001, 5)
        self.assertGreater(p.MES_REL.iloc[-1], 2400)
        self.assertEqual(len(p), int(p.MES_REL.iloc[-1]) + 1)
        self.assertTrue(np.all(np.diff(p.MES_REL) == 1))
        self.assertLess(p.QO.iloc[-1], 5)

    def test_exponencial_superpuesta_en_tiempo_y_acumulada(self):
        h = pd.DataFrame({"POZO_ID": ["A", "A"], "MES_REL": [0, 1], "NP_MB": [0, 3], "QO": [100, 90]})
        p = calcular_perfil_exponencial(100, .05, 12, .02, 5)
        for modo, cero in [("tiempo", False), ("acumulada", True), ("acumulada", False)]:
            f = crear_grafico(h, pd.DataFrame(), modo, np_desde_cero=cero)
            agregar_perfil_exponencial(f, p, modo, cero)
            traza = f.data[-1]
            self.assertEqual(traza.mode, "lines")
            self.assertEqual(traza.line.color, "#39FF14")
            self.assertEqual(traza.line.dash, "dash")
            if modo == "acumulada" and not cero:
                self.assertTrue(np.isnan(traza.x[0]))
            else:
                self.assertEqual(traza.x[0], 0)
            f.to_json()

    def test_estilo_comun_y_halo_activos(self):
        h = pd.DataFrame({"POZO_ID": ["A", "A"], "MES_REL": [0, 1], "NP_MB": [0, 3], "QO": [100, 90]})
        f = crear_grafico(h, calcular_p50_tiempo(h))
        agregar_perfil_exponencial(f, calcular_perfil_exponencial(100, .05, 12, .02, 5))
        activos = next(t for t in f.data if t.name == "Pozos activos")
        p50 = next(t for t in f.data if t.name.startswith("P50"))
        perfil = f.data[-1]
        for t, color in [(activos, "#A0A8AD"), (p50, "#FF6E00"), (perfil, "#39FF14")]:
            self.assertEqual(t.line.color, color)
            self.assertEqual(t.line.width, 1.5)
            self.assertEqual(t.line.dash, "dash")
            self.assertEqual(t.mode, "lines")
        halos = [t for t in f.data if t.name == "Brillo de pozos activos"]
        self.assertEqual(len(halos), 2)
        self.assertTrue(all(t.legendgroup == activos.legendgroup and not t.showlegend for t in halos))
        for principal, nombre in [(p50, "Brillo del P50"), (perfil, "Brillo del perfil exponencial")]:
            brillo = [t for t in f.data if t.name == nombre]
            self.assertEqual(len(brillo), 2)
            self.assertTrue(all(t.legendgroup == principal.legendgroup and not t.showlegend for t in brillo))
            self.assertTrue(all(t.hoverinfo == "skip" for t in brillo))
        f.to_json()

    def test_percentiles_temporales_misma_muestra(self):
        h = pd.DataFrame({"POZO_ID": ["A", "B", "C", "A"], "MES_REL": [0, 0, 0, 1],
                          "QO": [0, 50, 100, 40], "NP_MB": [0, 1, 2, 3]})
        p = calcular_p50_tiempo(h, 2)
        self.assertEqual(list(p.MES_REL), [0])
        self.assertEqual(p.iloc[0].P10, 10)
        self.assertEqual(p.iloc[0].P50, 50)
        self.assertEqual(p.iloc[0].P90, 90)
        f = crear_grafico(h, p)
        for nombre, color in [("P10", "#FF1744"), ("P90", "#FFFF00")]:
            t = next(t for t in f.data if t.name == nombre)
            self.assertEqual(t.line.color, color)
            self.assertEqual(t.line.width, 1.5)
            self.assertEqual(t.line.dash, "dash")
            self.assertEqual(t.mode, "lines")
            halos = [a for a in f.data if a.name == "Brillo del " + nombre]
            self.assertEqual(len(halos), 2)
            self.assertTrue(all(a.legendgroup == t.legendgroup for a in halos))
        f.to_json()

    def test_percentiles_acumulada_normalizada_minimo_compartido(self):
        h = pd.DataFrame({"POZO_ID": ["A", "A", "B", "B"], "MES_REL": [0, 1, 0, 1],
                          "NP_MB": [100, 110, 200, 220], "QO": [100, 50, 300, 150]})
        d = normalizar_acumulada(h)
        p = calcular_p50_acumulada(d.assign(NP_MB=d.NP_NORMALIZADA_MB), 2, incluir_cero=True)
        origen = p.loc[p.NP_MB.eq(0)].iloc[0]
        self.assertAlmostEqual(origen.P10, 120)
        self.assertAlmostEqual(origen.P50, 200)
        self.assertAlmostEqual(origen.P90, 280)
        self.assertTrue(p.loc[p.N_POZOS.lt(2), ["P10", "P50", "P90"]].isna().all().all())
        for cero in [True, False]:
            f = crear_grafico(d, p, "acumulada", np_desde_cero=cero)
            self.assertTrue(any(t.name == "P10" for t in f.data))
            self.assertTrue(any(t.name == "P90" for t in f.data))
            f.to_json()

    def test_reserva_3042_cierre_mes_siguiente_sin_fracciones(self):
        limite = 100 * np.exp(-.1 * .5)
        p = calcular_perfil_exponencial(100, 0, 1, .1, limite)
        self.assertEqual(p.MES_REL.iloc[-1], 1)
        self.assertEqual(p.NP_NORMALIZADA_MB.iloc[0], 0)
        self.assertEqual(p.RESERVA_BBL.iloc[0], 100 * 30.42)
        self.assertAlmostEqual(p.RESERVA_BBL.iloc[-1], (100 + 100*np.exp(-.1)) * 30.42)
        self.assertTrue(np.all(np.diff(p.MES_REL) == 1))
        self.assertTrue(p.MESES_INTERVALO.iloc[1:].eq(1).all())
        self.assertAlmostEqual(p.NP_MB.iloc[-1] * 1000, p.RESERVA_BBL.iloc[-1])
        self.assertAlmostEqual(p.VOLUMEN_INTERVALO_BBL.sum(), p.RESERVA_BBL.iloc[-1])
        self.assertTrue(p.VOLUMEN_INTERVALO_BBL.ge(0).all())

    def test_reserva_meses_enteros_y_recuadro_superior_derecho(self):
        limite = 100 * np.exp(-.1 - .2 * 2)
        p = calcular_perfil_exponencial(100, .1, 2, .2, limite)
        esperado = (100 + 100*np.exp(-.1) + 100*np.exp(-.3) + limite + 100*np.exp(-.7)) * 30.42
        self.assertEqual(p.MES_REL.iloc[-1], 4)
        self.assertAlmostEqual(p.RESERVA_BBL.iloc[-1], esperado)
        h = pd.DataFrame({"POZO_ID": ["A", "A"], "MES_REL": [0, 1], "NP_MB": [0, 3], "QO": [100, 90]})
        f = crear_grafico(h, calcular_p50_tiempo(h))
        agregar_resultados_perfil_propuesto(f, p, 100, .1, 2, .2, limite)
        self.assertIn(f.layout.paper_bgcolor, ["#FFFFFF", "white"])
        a = f.layout.annotations[-1]
        self.assertEqual(a.xanchor, "right")
        self.assertEqual(a.yanchor, "top")
        for palabra in ["Perfil Propuesto", "Reserva (bbl)", "30.42", "Corte (meses)", "Gasto inicial", "D2"]:
            self.assertIn(palabra, a.text)
        f.to_json()

    def test_di_18_periodos_contando_mes_cero(self):
        p = calcular_perfil_exponencial(100, .05, 18, .02, 1)
        self.assertEqual(p.iloc[0].ETAPA, 1)
        self.assertEqual(p.iloc[0].ETAPA_NOMBRE, "Di")
        self.assertEqual(list(p.loc[p.ETAPA.eq(1), "MES_REL"]), list(range(18)))
        self.assertEqual(p.ETAPA.eq(1).sum(), 18)
        self.assertEqual(p.loc[p.ETAPA.eq(2), "MES_REL"].iloc[0], 18)
        self.assertAlmostEqual(p.loc[p.MES_REL.eq(17), "QO"].iloc[0] / p.loc[p.MES_REL.eq(16), "QO"].iloc[0], np.exp(-.05))
        self.assertAlmostEqual(p.loc[p.MES_REL.eq(18), "QO"].iloc[0] / p.loc[p.MES_REL.eq(17), "QO"].iloc[0], np.exp(-.02))
        self.assertAlmostEqual(p.RESERVA_BBL.iloc[-1], p.QO.sum() * 30.42)
        self.assertAlmostEqual(p.RESERVA_BBL.iloc[0], 100 * 30.42)
        self.assertEqual(p.NP_NORMALIZADA_MB.iloc[0], 0)
        self.assertTrue(p.MESES_INTERVALO.eq(1).all())
        self.assertEqual(p.PERIODO.iloc[0], 1)
        self.assertEqual(p.PERIODO.iloc[-1], len(p))
        p0 = calcular_perfil_exponencial(100, .05, 0, .02, 1)
        self.assertFalse(p0.ETAPA.eq(1).any())
        self.assertEqual(p0.iloc[0].ETAPA_NOMBRE, "D2")

    def test_un_dato_y_muestra_vacia(self):
        h = pd.DataFrame({"POZO_ID": ["A"], "NP_MB": [3], "QO": [100]})
        p = calcular_p50_acumulada(h)
        self.assertEqual(len(p), 1)
        self.assertEqual(p.iloc[0].P50, 100)
        self.assertTrue(calcular_p50_acumulada(h, 2).empty)
        self.assertTrue(calcular_p50_acumulada(h.assign(QO=0)).empty)
        self.assertTrue(preparar_historia(pd.DataFrame()).empty)


if __name__ == "__main__":
    unittest.main()
