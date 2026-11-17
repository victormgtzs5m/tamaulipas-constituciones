"""Dashboard de historia observada; utiliza lectores y gráficos de la aplicación."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

VARIABLES = {
    'Inyección': ('Qiny (bpd)', 'bpd'), 'Aceite': ('Qo (bpd)', 'bpd'),
    'Agua': ('Qw (bpd)', 'bpd'), 'Líquidos': ('QL', 'bpd'),
    'Gas': ('Qg (mpcd)', 'mpcd'), 'Corte de agua': ('%Agua', '%'),
    'WOR': ('WOR', 'bl/bl'), 'RGA': ('RGA (pc/bl)', 'pc/bl'),
    'Inyección acumulada': ('Winj (mbl)', 'mbl'),
    'Aceite acumulado': ('Np (mbl)', 'mbl'), 'Agua acumulada': ('Wp (mbl)', 'mbl'),
    'Gas acumulado': ('Gp (mmpc)', 'mmpc'),
    'Presión': ('PRESION', 'kg/cm²'), 'Salinidad': ('SALINIDAD_PPM', 'ppm'),
    'Densidad del agua': ('DENSIDAD', 'g/cm³'), 'API del aceite': ('API', '°API'),
    'Agua laboratorio': ('% AGUA LAB', '%'),
}
SAMPLES = {'Presión', 'Salinidad', 'Densidad del agua', 'API del aceite', 'Agua laboratorio'}


def prepare(raw, calculate):
    """Reutiliza conversiones existentes, conservando ausencia y ceros observados."""
    d=raw.copy().sort_values(['TERMINACION','FECHA']).reset_index(drop=True)
    for col in ['ACEITE','AGUA','GAS','INJ','DIAS']:
        d[col]=pd.to_numeric(d[col],errors='coerce').replace([np.inf,-np.inf],np.nan)
        d.loc[d[col].lt(0),col]=np.nan
    calculated=calculate(d).sort_values(['TERMINACION','FECHA']).reset_index(drop=True)
    if len(calculated)!=len(d):raise ValueError('El cálculo compartido cambió la cantidad de registros.')
    for rawcol,rate,volume,accum in [
        ('ACEITE','Qo (bpd)','Aceite (bl)','Np (mbl)'),
        ('AGUA','Qw (bpd)','Agua (bl)','Wp (mbl)'),
        ('GAS','Qg (mpcd)','Gas (pc)','Gp (mmpc)'),
        ('INJ','Qiny (bpd)','Agua inyectada (bl)','Winj (mbl)')]:
        missing=d[rawcol].isna()
        calculated.loc[missing|~d.DIAS.gt(0),rate]=np.nan
        calculated.loc[missing,[volume,accum]]=np.nan
    calculated['QL']=calculated['Qo (bpd)']+calculated['Qw (bpd)']
    calculated['%Agua']=100*calculated['Qw (bpd)']/calculated.QL.where(calculated.QL.gt(0))
    calculated['WOR']=calculated['Qw (bpd)']/calculated['Qo (bpd)'].where(calculated['Qo (bpd)'].gt(0))
    calculated['RGA (pc/bl)']=calculated['Qg (mpcd)']*1000/calculated['Qo (bpd)'].where(calculated['Qo (bpd)'].gt(0))
    return calculated


def roles(raw):
    rows=[]
    for well,g in raw.groupby('TERMINACION'):
        prod=g[['ACEITE','AGUA','GAS']].apply(pd.to_numeric,errors='coerce').gt(0).any(axis=1)
        inj=pd.to_numeric(g.INJ,errors='coerce').gt(0)
        role='Sin actividad positiva'
        if prod.any() and inj.any():
            role='Productor → inyector' if g.loc[prod,'FECHA'].min()<g.loc[inj,'FECHA'].max() else 'Inyector → productor'
        elif inj.any():role='Inyector'
        elif prod.any():role='Productor'
        rows.append({'TERMINACION':well,'Rol histórico':role,'DOBLE':bool(prod.any() and inj.any())})
    return pd.DataFrame(rows,columns=['TERMINACION','Rol histórico','DOBLE'])


def locations(coord,wells,yac):
    c=coord.copy()
    if 'YACIMIENTO' in c:c=c[c.YACIMIENTO.astype(str).str.strip().eq(yac)]
    c=c[c.TERMINACION.astype(str).str.strip().isin(wells)].copy()
    c['TERMINACION']=c.TERMINACION.astype(str).str.strip()
    for name in ['FONDO X UTM','FONDO Y UTM','CIMA X UTM','CIMA Y UTM']:
        c[name]=pd.to_numeric(c[name],errors='coerce') if name in c else np.nan
        c[name]=c[name].replace([np.inf,-np.inf],np.nan)
    bottom=c[['FONDO X UTM','FONDO Y UTM']].notna().all(axis=1)
    c['X']=c['FONDO X UTM'].where(bottom,c['CIMA X UTM'])
    c['Y']=c['FONDO Y UTM'].where(bottom,c['CIMA Y UTM'])
    return c.dropna(subset=['X','Y']).drop_duplicates('TERMINACION')


def map_figure(c,classification,labels=True):
    data=c.merge(classification,on='TERMINACION',how='left');fig=go.Figure()
    groups=[('Productores',data['Rol histórico'].eq('Productor'),'circle','#16A566',16),
            ('Inyectores',data['Rol histórico'].eq('Inyector'),'triangle-up','#1769FF',20),
            ('Producción e inyección',data.DOBLE.eq(True),'triangle-up','#1769FF',25),
            ('Sin actividad positiva',data['Rol histórico'].eq('Sin actividad positiva'),'circle','#94A3B8',13)]
    for name,mask,symbol,color,size in groups:
        g=data[mask]
        if g.empty:continue
        fig.add_trace(go.Scatter(x=g.X,y=g.Y,name=name,mode='markers+text' if labels else 'markers',
            text=g.TERMINACION,textposition='top center',customdata=g[['TERMINACION','Rol histórico']],
            marker=dict(symbol=symbol,color=color,size=size,line=dict(color='#12334A',width=1)),
            hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br>X %{x:,.0f} · Y %{y:,.0f}<extra></extra>'))
        if name=='Producción e inyección':
            fig.add_trace(go.Scatter(x=g.X,y=g.Y,mode='markers',showlegend=False,hoverinfo='skip',
                marker=dict(symbol='circle',color='#16A566',size=10,line=dict(color='white',width=1))))
    fig.update_layout(title=dict(text='<b>Arreglo de pozos seleccionado</b>',x=.02),template='plotly_white',
        height=540,paper_bgcolor='white',plot_bgcolor='#F8F8FF',font=dict(family='Arial',color='#111827'),
        legend=dict(orientation='h',y=1.02),margin=dict(l=65,r=25,t=90,b=55),hovermode='closest')
    fig.update_xaxes(title='UTM X (m)',tickformat=',.0f',gridcolor='#E5E7EB')
    fig.update_yaxes(title='UTM Y (m)',tickformat=',.0f',gridcolor='#E5E7EB',scaleanchor='x',scaleratio=1)
    return fig


def history_plot(data,column,title,unit,wells,plot,colors,semilog=False,monthly=True,bounds=None):
    parts=[]
    for well in wells:
        g=data[data.TERMINACION.eq(well)].sort_values('FECHA').copy()
        if g.empty:continue
        if monthly:
            g['FECHA']=g.FECHA.dt.to_period('M').dt.to_timestamp()
            if g.FECHA.duplicated().any():raise ValueError(f'{well}: registros duplicados en un mes.')
            calendar=pd.date_range(g.FECHA.min(),g.FECHA.max(),freq='MS')
            g=g.set_index('FECHA').reindex(calendar).rename_axis('FECHA').reset_index()
            g['TERMINACION']=well
        parts.append(g)
    d=pd.concat(parts,ignore_index=True) if parts else pd.DataFrame(columns=['TERMINACION','FECHA',column])
    fig=plot(d,column,title,unit,wells,semilog=semilog,normalizar_tiempo=False,rango_fechas=bounds)
    for trace in fig.data:
        g=d[d.TERMINACION.eq(trace.name)].sort_values('FECHA')
        if g.empty:continue
        values=pd.to_numeric(g[column],errors='coerce').replace([np.inf,-np.inf],np.nan)
        if semilog:values=values.where(values.gt(0))
        trace.update(y=values.to_numpy(),connectgaps=False,line=dict(color=colors[trace.name],width=2.8))
        if not monthly:trace.update(mode='markers',marker=dict(color=colors[trace.name],size=8))
    fig.update_layout(height=420)
    return fig


def oil_injection_plot(fig,data,wells,semilog=False):
    """Curvas individuales; dos ejes y familias visuales por variable."""
    oil_colors=['#137547','#27965F','#52AE78','#086440','#79BC8E']
    injection_colors=['#1769FF','#0047AB','#468DE0','#087EBD','#699FE8']
    oil_wells=[p for p in wells if data.loc[data.TERMINACION.eq(p),'Qo (bpd)'].gt(0).any()]
    fig.data=tuple(t for t in fig.data if t.name in oil_wells)
    for index,trace in enumerate(fig.data):
        well=trace.name
        trace.update(name=well+' · Aceite',legendgroup='oil_'+well,
            line=dict(color=oil_colors[index%len(oil_colors)],dash='solid',width=2.8))
    injectors=[p for p in wells if data.loc[data.TERMINACION.eq(p),'Qiny (bpd)'].gt(0).any()]
    for index,well in enumerate(injectors):
        g=data[data.TERMINACION.eq(well)].sort_values('FECHA').copy()
        g['FECHA']=g.FECHA.dt.to_period('M').dt.to_timestamp()
        if g.FECHA.duplicated().any():raise ValueError(f'{well}: registros duplicados en un mes.')
        calendar=pd.date_range(g.FECHA.min(),g.FECHA.max(),freq='MS')
        values=g.set_index('FECHA')['Qiny (bpd)'].reindex(calendar)
        if semilog:values=values.where(values.gt(0))
        fig.add_trace(go.Scatter(x=calendar,y=values.to_numpy(),mode='lines',connectgaps=False,
            name=well+' · Inyección',legendgroup='injection_'+well,yaxis='y2',
            line=dict(color=injection_colors[index%len(injection_colors)],width=2.2,
                      dash=['dash','dot','dashdot','longdash','longdashdot'][index%5]),
            hovertemplate='<b>'+well+'</b><br>Fecha: %{x|%d/%m/%Y}<br>Inyección: %{y:,.2f} bpd<extra></extra>'))
    fig.update_layout(title=dict(text='<b>Aceite e inyección por pozo</b>'),height=470,
        margin=dict(r=80,t=100),yaxis2=dict(title=dict(text='<b>Inyección (bpd)</b>',font=dict(color='#1769FF')),
        overlaying='y',side='right',showgrid=False,zeroline=False,type='log' if semilog else 'linear',
        tickfont=dict(color='#1769FF'),showline=True,linecolor='#1769FF'))
    fig.update_yaxes(title_text='<b>Aceite (bpd)</b>',title_font_color='#137547',selector=dict(anchor='x'))
    # Aplicar al eje izquierdo sin cambiar el titulo del eje secundario.
    fig.layout.yaxis.title.text='<b>Aceite (bpd)</b>'
    fig.layout.yaxis.title.font.color='#137547'
    fig.layout.yaxis2.title.text='<b>Inyección (bpd)</b>'
    return fig



def monthly_series(data,well,column,calendar):
    if data.empty or column not in data:return pd.Series(np.nan,index=calendar)
    g=data[data.TERMINACION.eq(well)].copy()
    g['MES']=pd.to_datetime(g.FECHA).dt.to_period('M').dt.to_timestamp()
    g[column]=pd.to_numeric(g[column],errors='coerce').replace([np.inf,-np.inf],np.nan)
    return g.groupby('MES')[column].median().reindex(calendar)


def _correlations_rows(x,y,min_pairs=12):
    """Correlacion por fila en meses coincidentes; nunca sustituye ausencias por cero."""
    mask=np.isfinite(x)&np.isfinite(y)[None,:]
    n=mask.sum(axis=1);safe=np.maximum(n,1)
    a=np.where(mask,x,0.);b=np.where(mask,y,0.)
    sx=a.sum(axis=1);sy=b.sum(axis=1)
    numerator=(a*b).sum(axis=1)-sx*sy/safe
    denominator=np.sqrt(np.maximum(0,(a*a).sum(axis=1)-sx*sx/safe)*np.maximum(0,(b*b).sum(axis=1)-sy*sy/safe))
    out=np.full(len(x),np.nan)
    valid=(n>=min_pairs)&(denominator>1e-12)
    out[valid]=numerator[valid]/denominator[valid]
    return np.clip(out,-1,1),n


@st.cache_data(show_spinner=False,max_entries=12)
def temporal_associations(data,extra,producer,injectors,start,end,max_lag=6,permutations=399):
    """Exploracion de cambios mensuales con null por bloques y correccion de rezagos."""
    calendar=pd.date_range(pd.Timestamp(start).to_period('M').to_timestamp(),pd.Timestamp(end).to_period('M').to_timestamp(),freq='MS')
    if len(calendar)<14:return pd.DataFrame()
    data=data[data.FECHA.ge(pd.Timestamp(start))&data.FECHA.le(pd.Timestamp(end))].copy()
    extra={k:v[v.FECHA.ge(pd.Timestamp(start))&v.FECHA.le(pd.Timestamp(end))].copy() if not v.empty else v for k,v in extra.items()}
    liquid=monthly_series(data,producer,'QL',calendar)
    own_injection=monthly_series(data,producer,'Qiny (bpd)',calendar)
    active=liquid.gt(0)&~own_injection.gt(0)
    # Ambos meses deben ser productivos: evita puntuar reaperturas y conversiones.
    consecutive=active&active.shift(1,fill_value=False)
    variables={name:(data,col) for name,(col,unit) in VARIABLES.items() if name not in SAMPLES and 'acumulad' not in name.lower() and name!='Inyección'}
    for name in SAMPLES:
        group='Presión' if name=='Presión' else 'Agua laboratorio' if name=='Agua laboratorio' else 'Química'
        frame=extra.get(group,pd.DataFrame()).copy()
        if not frame.empty and group=='Química' and 'FUENTE' in frame:
            if name=='Densidad del agua':frame=frame[frame.FUENTE.astype(str).str.upper().eq('STIFF')]
            if name=='API del aceite':frame=frame[frame.FUENTE.astype(str).str.upper().eq('ACEITE')]
        if name=='Salinidad' and not frame.empty and 'FUENTE' in frame:
            groups=list(frame[frame.TERMINACION.eq(producer)].groupby('FUENTE',dropna=False))
            if groups:frame=max(groups,key=lambda item:len(item[1]))[1]
        # No mezclar presiones de diferentes tipos/profundidades en una sola respuesta.
        if name=='Presión' and not frame.empty:
            keys=[k for k in ['TIPO','TIPO PRESION','PROFUNDIDAD','PROFUNDIDAD PLANO REFERENCIA'] if k in frame]
            if keys:
                selected=frame[frame.TERMINACION.eq(producer)]
                groups=list(selected.groupby(keys,dropna=False))
                if groups:frame=max(groups,key=lambda item:len(item[1]))[1]
        variables[name]=(frame,VARIABLES[name][0])
    rows=[];rng=np.random.default_rng(185)
    for injector in injectors:
        if injector==producer:continue
        injection=monthly_series(data,injector,'Qiny (bpd)',calendar)
        dx=injection.diff().to_numpy(float)
        blocks=[np.arange(i,min(i+3,len(calendar))) for i in range(0,len(calendar),3)]
        null=np.array([dx[np.concatenate([blocks[k] for k in rng.permutation(len(blocks))])] for _ in range(permutations)])
        for variable,(frame,column) in variables.items():
            dy=monthly_series(frame,producer,column,calendar).diff().where(consecutive).to_numpy(float)
            candidates=[];null_max=np.full(permutations,np.nan)
            for lag in range(max_lag+1):
                x=dx.copy();shuffled=null.copy()
                if lag:
                    x[lag:]=dx[:-lag];x[:lag]=np.nan
                    shuffled[:,lag:]=null[:,:-lag];shuffled[:,:lag]=np.nan
                rho,n=_correlations_rows(x[None,:],dy)
                if not np.isfinite(rho[0]):continue
                boot,_=_correlations_rows(shuffled,dy)
                null_max=np.fmax(null_max,np.abs(boot))
                candidates.append((abs(rho[0]),float(rho[0]),lag,int(n[0]),x))
            if not candidates:continue
            _,rho,lag,n,x=max(candidates,key=lambda v:v[0])
            valid=np.isfinite(null_max)
            pvalue=(1+np.sum(null_max[valid]>=abs(rho)))/(1+valid.sum()) if valid.sum()>=permutations*.8 else 1.
            mask=np.isfinite(x)&np.isfinite(dy)
            months=calendar[mask]
            mid=len(calendar)//2
            left,_=_correlations_rows(x[:mid][None,:],dy[:mid],6)
            right,_=_correlations_rows(x[mid:][None,:],dy[mid:],6)
            stable=np.isfinite(left[0]) and np.isfinite(right[0]) and left[0]>0 and right[0]>0
            positive_months=calendar[mask&(x>0)&(dy>0)]
            metadata=[k for k in ['FUENTE','TIPO','TIPO PRESION','PROFUNDIDAD','PROFUNDIDAD PLANO REFERENCIA'] if k in frame]
            series_description='; '.join(k+': '+str(frame[k].iloc[0]) for k in metadata) if not frame.empty else ''
            rows.append({'Inyector':injector,'Productor':producer,'Variable':variable,'Serie respuesta':series_description,'r cambios':rho,
                'Rezago meses':lag,'Meses comparados':n,'p rezagos':pvalue,'Consistente en ambas mitades':bool(stable),
                'Primer mes comparado':months.min(),'Ultimo mes comparado':months.max(),'MESES_RESPUESTA':list(positive_months)})
    table=pd.DataFrame(rows)
    if table.empty:return table
    # Benjamini-Hochberg sobre todos los inyectores y variables evaluados.
    order=np.argsort(table['p rezagos'].to_numpy());pvalues=table['p rezagos'].to_numpy()[order]
    adjusted=np.minimum.accumulate((pvalues*len(table)/np.arange(1,len(table)+1))[::-1])[::-1]
    q=np.empty(len(table));q[order]=np.minimum(1,adjusted);table['q comparaciones']=q
    table['Resaltable']=(table['r cambios'].ge(.35)&table['q comparaciones'].le(.05)&table['Consistente en ambas mitades'])
    return table.sort_values(['Variable','r cambios'],ascending=[True,False]).reset_index(drop=True)


def choose_association(table,variable,data,start,end):
    if table.empty:return None,'No hay al menos 12 cambios mensuales coincidentes para evaluar.'
    candidates=table[table.Variable.eq(variable)&table.Resaltable]
    if candidates.empty:return None,'No hay una asociacion positiva suficientemente consistente para resaltar en esta variable.'
    best=candidates.sort_values('r cambios',ascending=False).iloc[0]
    # Inyectores con historias casi iguales no se pueden distinguir por esta comparacion.
    calendar=pd.date_range(pd.Timestamp(start).to_period('M').to_timestamp(),pd.Timestamp(end).to_period('M').to_timestamp(),freq='MS')
    base=monthly_series(data,best.Inyector,'Qiny (bpd)',calendar).diff()
    others=table[table.Variable.eq(variable)]
    for injector in others.Inyector.unique():
        if injector==best.Inyector:continue
        other=monthly_series(data,injector,'Qiny (bpd)',calendar).diff()
        common=pd.concat([base,other],axis=1).dropna()
        if len(common)>=12 and abs(common.iloc[:,0].corr(common.iloc[:,1]))>=.85:
            return None,'Los cambios de '+best.Inyector+' y '+injector+' son muy similares; no se puede distinguir su influencia.'
    return best,''


def highlight_association(fig,best,producer,variable,reference,start,end):
    # Fechas y ticks identicos en todos los paneles, incluidos los de muestreos.
    days=(pd.Timestamp(end)-pd.Timestamp(start)).days
    tick='M1' if days<=730 else 'M3' if days<=2190 else 'M12'
    fig.update_xaxes(type='date',range=[start,end],autorange=False,dtick=tick,tick0=pd.Timestamp(start).to_period('M').to_timestamp(),tickformat='%m/%Y')
    fig.update_layout(margin=dict(l=70,r=80))
    if best is None:return fig
    for trace in fig.data:
        name=trace.name or ''
        well=name.split(' · ')[0]
        if well==best.Inyector:
            trace.line.color='#E49500';trace.line.width=4
            if trace.mode and 'markers' in trace.mode:trace.marker.color='#E49500'
        elif well==producer:
            trace.line.width=3.5
    # Bandas = meses de aumento de inyeccion seguidos de aumento en variable de referencia.
    months=sorted(best.MESES_RESPUESTA)
    spans=[]
    for month in months:
        finish=month+pd.offsets.MonthBegin(1)
        if spans and month==spans[-1][1]:spans[-1]=(spans[-1][0],finish)
        else:spans.append((month,finish))
    for begin,finish in spans:
        fig.add_vrect(x0=max(begin,pd.Timestamp(start)),x1=min(finish,pd.Timestamp(end)),
            fillcolor='#E49500',opacity=.09,line_width=0,layer='below')
    return fig


def samples_frame(raw,wells,yac,date_col):
    if raw.empty or not {'TERMINACION',date_col}.issubset(raw.columns):return pd.DataFrame()
    d=raw.copy();d['TERMINACION']=d.TERMINACION.astype(str).str.strip()
    d=d[d.TERMINACION.isin(wells)]
    if 'YACIMIENTO' in d:
        declared=d.YACIMIENTO.fillna('').astype(str).str.strip()
        d=d[declared.eq(yac)|declared.str.upper().isin(['','NAN','NONE'])]
    d['FECHA']=pd.to_datetime(d[date_col],errors='coerce')
    return d.dropna(subset=['FECHA'])


def show(raw,coord,calculate,plot,load_pressure,load_salinity,load_labs):
    st.markdown("<div class='section-title'>Waterflood · Historia de producción e inyección</div>",unsafe_allow_html=True)
    st.caption('Selección de pozos · Variables observadas · Comparación histórica')
    if raw.empty:st.info('No hay historia disponible.');return
    raw=raw.copy();raw['TERMINACION']=raw.TERMINACION.astype(str).str.strip()
    raw['YACIMIENTO']=raw.YACIMIENTO.astype(str).str.strip();raw['FECHA']=pd.to_datetime(raw.FECHA,errors='coerce')
    raw=raw.dropna(subset=['FECHA'])
    with st.container(border=True):
        a,b=st.columns([1,3])
        yac=a.selectbox('Yacimiento',sorted(raw.YACIMIENTO.unique()),key='waterflood_yac')
        field=raw[raw.YACIMIENTO.eq(yac)]
        available=sorted(field.TERMINACION.unique())
        wells=b.multiselect('Pozos a analizar',available,default=available[:1],key='waterflood_wells_'+yac)
        chosen=st.multiselect('Variables del dashboard',list(VARIABLES),default=['Inyección','Aceite','Agua','Corte de agua','Presión','Agua laboratorio'],key='waterflood_vars')
    if not wells:st.info('Selecciona uno o más pozos para ver su mapa e historia.');return
    history=field[field.TERMINACION.isin(wells)].copy()
    duplicate=history.assign(MES=history.FECHA.dt.to_period('M')).duplicated(['TERMINACION','MES'],keep=False)
    if duplicate.any():
        st.warning(f'{int(duplicate.sum())} registros pertenecen a meses duplicados; se excluyen para evitar sumar o elegir datos ambiguos.')
        history=history.loc[~duplicate]
    if history.empty:st.info('No quedan registros mensuales únicos para esta selección.');return
    data=prepare(history,calculate);classifications=roles(field[field.TERMINACION.isin(wells)])
    extra={};warnings=[]
    loaders=[]
    if 'Presión' in chosen:loaders.append(('Presión',load_pressure,'FECHA'))
    if any(v in chosen for v in ['Salinidad','Densidad del agua','API del aceite']):loaders.append(('Química',load_salinity,'FECHA MUESTREO'))
    if 'Agua laboratorio' in chosen:loaders.append(('Agua laboratorio',load_labs,'FECHA MUESTREO'))
    for name,loader,datecol in loaders:
        try:
            with st.spinner('Cargando '+name.lower()+'…'):extra[name]=samples_frame(loader(),wells,yac,datecol)
        except Exception as exc:warnings.append(f'{name}: no se pudo cargar la fuente ({exc}).')
    all_dates=pd.concat([data.FECHA]+[d.FECHA for d in extra.values() if not d.empty],ignore_index=True)
    lo,hi=all_dates.min().date(),all_dates.max().date()
    with st.container(border=True):
        a,b,c=st.columns([2,1,1])
        dates=a.date_input('Periodo de análisis',value=(lo,hi),min_value=lo,max_value=hi,key='waterflood_dates_'+yac+'_'+'_'.join(wells))
        semilog=b.toggle('Escala semilogarítmica',key='waterflood_log')
        labels=c.toggle('Nombres en el mapa',value=True,key='waterflood_labels')
    overlay_oil=False
    if 'Aceite' in chosen:
        overlay_oil=st.toggle('Ver inyecci\u00f3n por pozo junto al aceite',value=True,key='waterflood_oil_injection')
    if len(dates)!=2:st.info('Elige la fecha inicial y final.');return
    start,end=map(pd.Timestamp,dates);end_exclusive=end+pd.Timedelta(days=1)
    filtered=data[data.FECHA.ge(start)&data.FECHA.lt(end_exclusive)]
    best=None;producer=None;reference='Aceite'
    producers=[p for p in wells if data.loc[data.TERMINACION.eq(p),'QL'].gt(0).any()]
    injectors=[p for p in wells if data.loc[data.TERMINACION.eq(p),'Qiny (bpd)'].gt(0).any()]
    with st.expander('Comparar inyección con respuesta del productor',expanded=True):
        enabled=st.toggle('Resaltar asociaciones temporales',value=True,key='waterflood_association')
        if enabled and producers and injectors:
            a,b,c=st.columns([2,2,1])
            producer=a.selectbox('Productor de referencia',producers,key='waterflood_reference_'+yac+'_'+'_'.join(wells))
            reference=b.selectbox('Variable para priorizar',['Aceite','Presión','Líquidos','Agua','Corte de agua','WOR','Salinidad','Agua laboratorio'],key='waterflood_reference_variable')
            lag=int(c.number_input('Rezago máximo (meses)',min_value=0,max_value=12,value=6,key='waterflood_maxlag'))
            if reference in SAMPLES:
                group='Presi\u00f3n' if reference=='Presi\u00f3n' else 'Agua laboratorio' if reference=='Agua laboratorio' else 'Qu\u00edmica'
                if group not in extra:
                    loader=load_pressure if group=='Presi\u00f3n' else load_labs if group=='Agua laboratorio' else load_salinity
                    datecol='FECHA' if group=='Presi\u00f3n' else 'FECHA MUESTREO'
                    try:
                        with st.spinner('Cargando datos de referencia...'):extra[group]=samples_frame(loader(),wells,yac,datecol)
                    except Exception as exc:st.warning(f'No se pudo cargar {group}: {exc}')
            with st.spinner('Cotejando cambios mensuales observados...'):
                table=temporal_associations(data,extra,producer,injectors,start,end,lag)
                best,message=choose_association(table,reference,data,start,end)
            if best is not None:
                st.success(f"Asociación positiva más fuerte: {best.Inyector} con {producer} | {reference} | r={best['r cambios']:.2f} | rezago {int(best['Rezago meses'])} meses | {int(best['Meses comparados'])} cambios coincidentes.")
                st.caption('Dorado: inyector resaltado. Bandas: meses con aumento de la variable de referencia después de un aumento de inyección. Asociación temporal exploratoria; no es un porcentaje de influencia ni demuestra causalidad.')
            else:st.info(message)
            if not table.empty:
                st.dataframe(table.drop(columns='MESES_RESPUESTA'),hide_index=True,use_container_width=True)
            st.caption('Se comparan cambios entre meses consecutivos, en etapas activas del productor, con 12 pares como mínimo. Sin rellenar meses faltantes. Se corrige la búsqueda entre rezagos, inyectores y variables; se exige consistencia en ambas mitades del periodo.')
        elif enabled:st.info('Selecciona al menos un productor y un inyector con historia positiva para comparar.')
    kpis=st.columns(4)
    kpis[0].metric('Pozos seleccionados',len(wells))
    for area,label,col in [(kpis[1],'Aceite observado · mbl','Aceite (bl)'),(kpis[2],'Agua observada · mbl','Agua (bl)'),(kpis[3],'Inyección observada · mbl','Agua inyectada (bl)')]:
        value=filtered[col].sum(min_count=1)/1000
        area.metric(label,f'{value:,.1f}' if pd.notna(value) else 'Sin dato')
    c=locations(coord,wells,yac)
    mapcol,summary=st.columns([2,1])
    mapcol.plotly_chart(map_figure(c,classifications,labels),use_container_width=True,key='waterflood_map')
    with summary:
        st.markdown('**Pozos del análisis**')
        st.dataframe(classifications.drop(columns='DOBLE'),hide_index=True,use_container_width=True)
        st.caption('El símbolo representa la historia completa del pozo en el yacimiento. Las curvas y volúmenes utilizan el periodo seleccionado. Coordenadas de fondo; cima como respaldo.')
        absent=sorted(set(wells)-set(c.TERMINACION))
        if absent:st.warning('Sin coordenadas: '+', '.join(absent))
    for warning in warnings:st.warning(warning)
    colors={p:px.colors.qualitative.Plotly[i%len(px.colors.qualitative.Plotly)] for i,p in enumerate(wells)}
    st.caption('Gastos según días registrados, igual que Comparativa por pozo. Acumuladas desde el inicio de la historia disponible. Sin dato = hueco; cero observado se conserva en escala lineal. Muestreos: puntos en su fecha real.')
    columns=st.columns(2)
    for index,variable in enumerate(chosen):
        col,unit=VARIABLES[variable];d=data;monthly=variable not in SAMPLES
        if not monthly:
            group='Presión' if variable=='Presión' else 'Agua laboratorio' if variable=='Agua laboratorio' else 'Química'
            d=extra.get(group,pd.DataFrame()).copy()
            if not d.empty and group=='Química':
                if variable=='Densidad del agua':d=d[d.FUENTE.astype(str).str.upper().eq('STIFF')]
                elif variable=='API del aceite':d=d[d.FUENTE.astype(str).str.upper().eq('ACEITE')]
        with columns[index%2]:
            with st.container(border=True):
                if d.empty or col not in d:st.info(variable+': sin datos disponibles.');continue
                d=d[d.FECHA.ge(start)&d.FECHA.lt(end_exclusive)].copy()
                d[col]=pd.to_numeric(d[col],errors='coerce').replace([np.inf,-np.inf],np.nan)
                if not monthly:d=d.dropna(subset=[col])
                if d.empty or not d[col].notna().any():st.info(variable+': sin datos en este periodo.');continue
                if variable=='Salinidad' and 'FUENTE' in d:
                    fig=go.Figure()
                    for source,g in d.groupby('FUENTE'):
                        partial=history_plot(g,col,variable,unit,wells,plot,colors,semilog,False,(start,end))
                        fig.update_layout(partial.layout)
                        for trace in partial.data:
                            trace.name=trace.name+' · '+str(source)
                            trace.marker.symbol='diamond' if str(source).upper()=='STIFF' else 'circle'
                            fig.add_trace(trace)
                else:fig=history_plot(d,col,variable,unit,wells,plot,colors,semilog,monthly,(start,end))
                if variable=='Aceite' and overlay_oil:
                    fig=oil_injection_plot(fig,d,wells,semilog)
                    st.caption('Aceite: verde continuo, eje izquierdo. Inyecci\u00f3n: azul discontinuo, eje derecho. Cada curva corresponde a un pozo; pulsa su nombre en la leyenda para ocultarla.')
                fig=highlight_association(fig,best,producer,variable,reference,start,end)
                st.plotly_chart(fig,use_container_width=True,key='waterflood_chart_'+variable)
    with st.expander('Datos observados y exportación'):
        st.dataframe(filtered,hide_index=True,use_container_width=True)
        st.download_button('Descargar historia seleccionada · CSV',filtered.to_csv(index=False).encode('utf-8-sig'),'waterflood_historia.csv','text/csv')
        for name,d in extra.items():
            if not d.empty:
                subset=d[d.FECHA.ge(start)&d.FECHA.lt(end_exclusive)]
                st.download_button('Descargar '+name+' · CSV',subset.to_csv(index=False).encode('utf-8-sig'),'waterflood_'+name+'.csv','text/csv',key='waterflood_export_'+name)
