import unittest
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from waterflood_dashboard import temporal_associations,choose_association,highlight_association


def fixture(months=160):
    rng=np.random.default_rng(18)
    dates=pd.date_range('2000-01-01',periods=months,freq='MS')
    i1=rng.uniform(100,300,months);i2=rng.uniform(100,300,months)
    oil=100+.6*np.r_[i1[:2],i1[:-2]]+rng.normal(0,2,months)
    rows=[]
    for p,qi,qo in [('I1',i1,np.zeros(months)),('I2',i2,np.zeros(months)),('P',np.zeros(months),oil)]:
        rows.extend(dict(TERMINACION=p,FECHA=d,**{'Qiny (bpd)':a,'Qo (bpd)':b,'QL':b*1.4}) for d,a,b in zip(dates,qi,qo))
    return pd.DataFrame(rows),dates


class AssociationTests(unittest.TestCase):
    def test_recovers_known_injector_and_lag(self):
        d,dates=fixture()
        t=temporal_associations(d,{},'P',['I1','I2'],dates[0],dates[-1])
        best,message=choose_association(t,'Aceite',d,dates[0],dates[-1])
        self.assertIsNotNone(best,message)
        self.assertEqual(best.Inyector,'I1');self.assertEqual(best['Rezago meses'],2)
        self.assertGreater(best['r cambios'],.95)

    def test_missing_months_are_not_imputed(self):
        d,dates=fixture();d=d[~(d.TERMINACION.eq('I1')&d.FECHA.isin(dates[::5]))]
        t=temporal_associations(d,{},'P',['I1'],dates[0],dates[-1])
        row=t[t.Variable.eq('Aceite')].iloc[0]
        self.assertLess(row['Meses comparados'],120)
        self.assertGreater(row['r cambios'],.9)

    def test_closed_producer_cannot_be_ranked(self):
        d,dates=fixture();d.loc[d.TERMINACION.eq('P'),'QL']=0
        self.assertTrue(temporal_associations(d,{},'P',['I1'],dates[0],dates[-1]).empty)

    def test_indistinguishable_injectors_have_no_winner(self):
        d,dates=fixture();a=d[d.TERMINACION.eq('I1')]['Qiny (bpd)'].to_numpy()
        d.loc[d.TERMINACION.eq('I2'),'Qiny (bpd)']=a
        t=temporal_associations(d,{},'P',['I1','I2'],dates[0],dates[-1])
        best,message=choose_association(t,'Aceite',d,dates[0],dates[-1])
        self.assertIsNone(best);self.assertIn('similares',message)

    def test_unrelated_and_inverse_changes_not_highlighted(self):
        d,dates=fixture()
        original=d[d.TERMINACION.eq('P')]['Qo (bpd)'].to_numpy().copy()
        for mode in ['unrelated','inverse']:
            a=np.random.default_rng(66).uniform(100,300,len(dates)) if mode=='unrelated' else 500-original
            d.loc[d.TERMINACION.eq('P'),'Qo (bpd)']=a
            t=temporal_associations(d,{},'P',['I1','I2'],dates[0],dates[-1])
            best,message=choose_association(t,'Aceite',d,dates[0],dates[-1])
            self.assertIsNone(best)

    def test_sparse_samples_do_not_create_monthly_evidence(self):
        d,dates=fixture();sample=pd.DataFrame({'TERMINACION':'P','FECHA':dates[::6],'PRESION':np.arange(len(dates[::6]))})
        t=temporal_associations(d,{'Presi\u00f3n':sample},'P',['I1'],dates[0],dates[-1])
        self.assertFalse(t.Variable.eq('Presi\u00f3n').any())

    def test_all_panels_share_range_ticks_and_highlight(self):
        d,dates=fixture();t=temporal_associations(d,{},'P',['I1'],dates[0],dates[-1])
        best,_=choose_association(t,'Aceite',d,dates[0],dates[-1])
        panels=[]
        for variable in ['Aceite','Presion','Salinidad']:
            fig=go.Figure(go.Scatter(x=dates,y=np.arange(len(dates)),name='I1'))
            fig=highlight_association(fig,best,'P',variable,'Aceite',dates[0],dates[-1])
            self.assertEqual(fig.data[0].line.color,'#E49500');self.assertTrue(fig.to_json())
            panels.append(fig)
        self.assertTrue(all(f.layout.xaxis.range==panels[0].layout.xaxis.range for f in panels))
        self.assertTrue(all(f.layout.xaxis.dtick==panels[0].layout.xaxis.dtick for f in panels))
        self.assertTrue(all(f.layout.xaxis.tick0==panels[0].layout.xaxis.tick0 for f in panels))

if __name__=='__main__':unittest.main()
