"""Developer Salary Intelligence | Streamlit client-facing dashboard.
Only aggregate survey statistics and bootstrap summaries are bundled.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='Developer Salary Intelligence',page_icon='📊',layout='wide',initial_sidebar_state='expanded')
D=json.loads((Path(__file__).parent/'dashboard_data.json').read_text())
Q1,Q2,Q3=D['q1'],D['q2'],D['q3']
NAVY='#15253F';INDIGO='#6258E8';TEAL='#0E9E9A';ORANGE='#F29A5B';INK='#26334D';MUTED='#73819A'
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"],.stApp {font-family:'DM Sans',sans-serif!important}
.stApp{background:#F7F9FD;color:#26334D}
.block-container{padding-top:2.2rem;padding-bottom:4rem;max-width:1420px}
h1,h2,h3{font-family:'Manrope',sans-serif!important;letter-spacing:-.035em!important;color:#17263D!important}
[data-testid="stSidebar"]{background:#15253F!important}
[data-testid="stSidebar"] *{color:#E9EFFE!important}
[data-testid="stSidebar"] [data-baseweb="radio"] label{padding:9px 8px;border-radius:9px}
[data-testid="stMetric"]{background:white;border:1px solid #E6EAF3;border-radius:15px;padding:19px 20px;box-shadow:0 5px 18px rgba(29,48,81,.035)}
[data-testid="stMetricLabel"]{font-weight:600;color:#78849A}
[data-testid="stMetricValue"]{color:#17263D;font-weight:800;font-size:1.85rem}
div[data-testid="stVerticalBlockBorderWrapper"]>div{border-radius:16px!important;border-color:#E6EAF3!important;background:#fff}
.stTabs [data-baseweb="tab-list"]{gap:12px}.stTabs [data-baseweb="tab"]{border-radius:9px;background:#EEF1F8;padding:9px 15px}
.stTabs [aria-selected="true"]{background:#E6E5FF;color:#4B43CA}
.hero{background:linear-gradient(118deg,#172842 0%,#263C67 60%,#4A4B9D 100%);color:white;padding:35px 38px;border-radius:21px;margin-bottom:23px;box-shadow:0 15px 35px rgba(26,44,82,.14)}
.hero .eyebrow{font-size:.73rem;letter-spacing:.17em;color:#B9C7FF;font-weight:700;margin-bottom:10px}
.hero h1{color:#fff!important;font-size:2.1rem;margin:0 0 10px}
.hero p{color:#DFE6FF;max-width:740px;font-size:1.03rem;margin:0}
.pill{display:inline-block;background:#EAE9FF;color:#5046C8;font-size:.76rem;font-weight:700;padding:7px 11px;border-radius:40px;margin-bottom:12px}
.insight{border-left:4px solid #6258E8;background:#F0F1FD;border-radius:0 12px 12px 0;padding:15px 19px;color:#33435E;margin:12px 0 22px}
.note{color:#76829A;font-size:.82rem}
.section-intro{font-size:1.04rem;color:#6B7891;margin-top:-5px;margin-bottom:19px}
hr{border-color:#E8ECF3}
</style>''',unsafe_allow_html=True)

def money(v,short=False):return f'${v/1000:,.1f}K' if short else f'${v:,.0f}'
def pval(v):return f'{v:.2e}' if v<.0001 else f'{v:.4f}'
def heading(title,subtitle=None):
 st.markdown(f'## {title}')
 if subtitle:st.markdown(f'<p class="section-intro">{subtitle}</p>',unsafe_allow_html=True)
def insight(text):st.markdown(f'<div class="insight">{text}</div>',unsafe_allow_html=True)
def histfig(hist,title,xlabel,color=INDIGO,markers=None,unit=None):
 f=go.Figure(go.Bar(x=hist['x'],y=hist['y'],marker_color=color,opacity=.78,hovertemplate='%{x:,.2f}<br>Replications: %{y:,}<extra></extra>'))
 if markers:
  for m in markers:f.add_vline(x=m[0],line_color=m[1],line_dash=m[2] if len(m)>2 else 'dash',line_width=2,annotation_text=m[3] if len(m)>3 else None,annotation_position='top left')
 f.update_layout(title=dict(text=title,font_size=16),height=340,margin=dict(l=15,r=15,t=52,b=28),xaxis_title=xlabel,yaxis_title='Bootstrap replications',showlegend=False,bargap=.045,plot_bgcolor='white',paper_bgcolor='white',font=dict(color=INK,family='DM Sans'),xaxis=dict(showgrid=True,gridcolor='#EFF2F8'),yaxis=dict(showgrid=True,gridcolor='#EFF2F8'))
 return f

def horizontal(names,values,title,xlabel,color=INDIGO,extra=None):
 f=go.Figure(go.Bar(x=values,y=names,orientation='h',marker_color=color,hovertemplate='%{y}<br>%{x:,.2f}<extra></extra>'))
 if extra is not None:f.add_trace(go.Scatter(x=extra,y=names,mode='markers',marker=dict(color=ORANGE,size=9,symbol='diamond'),name='Median'))
 f.update_layout(title=title,height=max(400,len(names)*32+85),margin=dict(l=10,r=20,t=50,b=25),yaxis=dict(autorange='reversed'),xaxis_title=xlabel,plot_bgcolor='white',paper_bgcolor='white',font=dict(color=INK),xaxis=dict(gridcolor='#EDF0F6'),legend=dict(orientation='h',y=1.06))
 return f

def stats_table(stats):
 rows=[]
 for k,v in stats.items():rows.append({'Group':k,'N':f"{v['n']:,}",'Mean':money(v['mean']),'Median':money(v['median']),'Std. dev.':money(v['std']),'Min':money(v['min']),'Max':money(v['max'])})
 st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)

def metricrow(items):
 cols=st.columns(len(items))
 for c,(label,value,delta) in zip(cols,items):
  with c:st.metric(label,value,delta=delta)

with st.sidebar:
 st.markdown('### ◈ Developer Insights')
 st.caption('SALARY INTELLIGENCE · SURVEY ANALYSIS')
 st.divider()
 page=st.radio('Explore the analysis',['Overview','Q1 · Exploratory Analysis','Q2 · Work Arrangement','Q3 · Education & ANOVA','Methods & Limitations'],label_visibility='collapsed')
 st.divider()
 st.markdown('**Analysis scope**')
 st.caption(f"{D['meta']['rows']:,} survey records · {D['meta']['columns']} columns")
 st.caption('10,000 bootstrap replications')
 st.caption('Salaries shown in USD')
 st.caption('Public app uses aggregate data only')

if page=='Overview':
 st.markdown('<div class="hero"><div class="eyebrow">WORKFORCE ANALYTICS / EXECUTIVE BRIEF</div><h1>Developer Salary Intelligence</h1><p>Explore how work arrangement, education, age, and developer roles relate to compensation. A client-ready statistical analysis with transparent methods and uncertainty estimates.</p></div>',unsafe_allow_html=True)
 metricrow([('Remote mean salary',money(Q2['trimmed']['Remote']['mean'],True),'After trimming'),('Hybrid mean salary',money(Q2['trimmed']['Hybrid']['mean'],True),'After trimming'),('Remote salary premium',money(Q2['observed_diff'],True),'Mean difference'),('Education ANOVA',f"F = {Q3['anova']['f']:.2f}",'p < 0.001')])
 st.markdown('### Key findings')
 c1,c2=st.columns(2)
 with c1:
  with st.container(border=True):
   st.markdown('**01 / Work arrangement**')
   f=go.Figure(go.Bar(x=['Remote','Hybrid'],y=[Q2['trimmed'][x]['mean'] for x in ['Remote','Hybrid']],marker_color=[INDIGO,TEAL],text=[money(Q2['trimmed'][x]['mean'],True) for x in ['Remote','Hybrid']],textposition='outside'))
   f.update_layout(height=310,margin=dict(l=5,r=5,t=25,b=20),yaxis_title='Mean salary (USD)',plot_bgcolor='white',paper_bgcolor='white',showlegend=False)
   st.plotly_chart(f,use_container_width=True)
   st.caption('Remote respondents earned more on average after removing the top 1% of salaries within each group.')
 with c2:
  with st.container(border=True):
   st.markdown('**02 / Education**')
   keys=["Bachelor's","Master's","Professional"]
   f=go.Figure(go.Bar(x=keys,y=[Q3['trimmed'][x]['mean'] for x in keys],marker_color=[INDIGO,TEAL,ORANGE],text=[money(Q3['trimmed'][x]['mean'],True) for x in keys],textposition='outside'))
   f.update_layout(height=310,margin=dict(l=5,r=5,t=25,b=20),yaxis_title='Mean salary (USD)',plot_bgcolor='white',paper_bgcolor='white',showlegend=False)
   st.plotly_chart(f,use_container_width=True)
   st.caption('North American respondents with higher degree categories had higher observed group mean salaries.')
 insight('<b>Executive takeaway.</b> Both work arrangement and education are associated with meaningful salary differences in this sample. These are observational comparisons, not causal estimates. Confidence intervals and bootstrap tests are available in the detailed sections.')
 st.markdown('### Explore the full evidence')
 st.write('Use the sidebar to inspect Q1 visualizations, Q2 manual and built-in t-tests, bootstrap distributions, Mood’s median test, and Q3 ANOVA with pairwise uncertainty intervals.')

elif page=='Q1 · Exploratory Analysis':
 heading('Q1 · Exploratory Data Analysis','Job satisfaction, role-based compensation, and age patterns across developer respondents.')
 st.markdown('<span class="pill">FIGURE 1 · JOB SATISFACTION</span>',unsafe_allow_html=True)
 js=Q1['job_satisfaction'];st.plotly_chart(horizontal([x['DevType'] for x in js],[x['mean'] for x in js],'Average job satisfaction by developer role','Mean satisfaction (0–10)'),use_container_width=True)
 insight('Only roles with at least 30 valid satisfaction responses are included. Values outside the 0–10 satisfaction scale were excluded from this analysis.')
 st.markdown('<span class="pill">FIGURE 2 · ROLE COMPENSATION</span>',unsafe_allow_html=True)
 sal=Q1['salary_by_role'];st.plotly_chart(horizontal([x['DevType'] for x in sal],[x['mean'] for x in sal],'Mean and median salary by developer role','Annual salary (USD)',extra=[x['median'] for x in sal]),use_container_width=True)
 insight('The gap between mean salary (bars) and median salary (orange diamonds) highlights right-skew and the influence of extreme compensation values.')
 st.markdown('<span class="pill">FIGURE 3 · SALARY VS AGE</span>',unsafe_allow_html=True)
 ages=Q1['age_summary'];f=go.Figure()
 f.add_trace(go.Scatter(x=[x['Age'] for x in ages],y=[x['median'] for x in ages],mode='lines+markers',name='Median salary',line_color=INDIGO))
 f.add_trace(go.Scatter(x=[x['Age'] for x in ages],y=[x['mean'] for x in ages],mode='lines+markers',name='Mean salary',line_color=ORANGE,opacity=.8))
 f.update_layout(title='Salary by age (aggregated to protect individual records)',height=420,xaxis_title='Age (years)',yaxis_title='Annual salary (USD, log scale)',yaxis_type='log',plot_bgcolor='white',paper_bgcolor='white',margin=dict(l=15,r=15,t=50,b=30))
 st.plotly_chart(f,use_container_width=True)
 st.caption('Privacy-preserving aggregated alternative to the individual-level scatterplot in the notebook; age-by-age means and medians, not respondent records. Exact notebook scatter is not reproduced because the underlying individual records are intentionally excluded from the public dashboard.')
 with st.expander('Data cleaning & figure notes'):
  st.write('Ages outside 18–100 and job-satisfaction scores outside 0–10 were treated as missing for Q1. At least 30 observations were required per role for Figures 1 and 2. Salary was plotted on a logarithmic scale in the notebook for Figure 3.')

elif page=='Q2 · Work Arrangement':
 heading('Q2 · Remote vs Hybrid','Comparing compensation with parametric tests, bootstrap uncertainty, and a median-based robustness check.')
 metricrow([('Remote · mean',money(Q2['trimmed']['Remote']['mean'],True),None),('Hybrid · mean',money(Q2['trimmed']['Hybrid']['mean'],True),None),('Mean difference',money(Q2['observed_diff'],True),None),('Welch p-value',pval(Q2['welch']['p']),None)])
 tabs=st.tabs(['Descriptives','t-Tests','Bootstrap & CIs','Median Test','Sensitivity'])
 with tabs[0]:
  st.markdown('#### Original salary data');stats_table(Q2['original'])
  st.markdown('#### After trimming salaries above each group’s 99th percentile');stats_table(Q2['trimmed'])
  c1,c2=st.columns(2)
  for col,name,color in zip([c1,c2],['Remote','Hybrid'],[INDIGO,TEAL]):
   with col:st.plotly_chart(histfig(Q2['hist_trimmed'][name],f'{name} · trimmed salary distribution','Annual salary (USD)',color),use_container_width=True)
  insight('Salary distributions are strongly right-skewed. To reduce the influence of extreme values, salaries above each group-specific 99th percentile were excluded before inferential analysis.')
 with tabs[1]:
  st.markdown('#### Manual calculations vs built-in SciPy tests')
  tdf=pd.DataFrame([{'Method':'Student (pooled variance)','t-statistic':Q2['student']['t'],'Degrees of freedom':Q2['student']['df'],'Two-sided p-value':pval(Q2['student']['p'])},{'Method':'Welch (unequal variance)','t-statistic':Q2['welch']['t'],'Degrees of freedom':Q2['welch']['df'],'Two-sided p-value':pval(Q2['welch']['p'])}])
  st.dataframe(tdf,hide_index=True,use_container_width=True)
  c1,c2=st.columns(2)
  with c1:st.metric('Pooled standard deviation',money(Q2['student']['pooled_sd']))
  with c2:st.metric('Welch standard error',money(Q2['welch']['se']))
  insight('<b>Interpretation.</b> Manual and SciPy implementations agree. Both tests reject equal mean salaries at α = 0.05. Welch is the primary analysis because it does not assume equal population variances.')
 with tabs[2]:
  st.markdown('#### Figure 1 · Group bootstrap mean distributions')
  c1,c2=st.columns(2)
  with c1:st.plotly_chart(histfig(Q2['bootstrap']['remote'],'Remote · mean salary','USD',INDIGO),use_container_width=True)
  with c2:st.plotly_chart(histfig(Q2['bootstrap']['hybrid'],'Hybrid · mean salary','USD',TEAL),use_container_width=True)
  st.markdown('#### Figure 2 · Bootstrap mean differences')
  st.plotly_chart(histfig(Q2['bootstrap']['diff'],'Remote − Hybrid mean salary','USD',INDIGO,[(Q2['observed_diff'],ORANGE,'dash','Observed'),(0,'#D24B5A','dot','Zero')]),use_container_width=True)
  st.markdown('#### Figure 3 · Standardized bootstrap mean differences')
  st.plotly_chart(histfig(Q2['bootstrap']['standardized'],'Centered and standardized mean differences','Standardized units',TEAL,[(0,ORANGE,'dash','Center')]),use_container_width=True)
  c1,c2,c3=st.columns(3)
  with c1:st.metric('Bootstrap standard error',money(Q2['bootstrap']['se']))
  with c2:st.metric('Bootstrap t-test p-value',pval(Q2['bootstrap']['p_t']))
  with c3:st.metric('Bootstrap replications','10,000')
  st.markdown('#### 95% confidence intervals')
  cis=[('Welch t-based',Q2['welch']['ci']),('Bootstrap percentile',Q2['bootstrap']['ci'])]
  f=go.Figure()
  for i,(name,(lo,hi)) in enumerate(cis):f.add_trace(go.Scatter(x=[lo,hi],y=[name,name],mode='lines+markers',line=dict(color=[INDIGO,TEAL][i],width=6),marker=dict(size=10),name=name,hovertemplate='%{x:$,.0f}<extra></extra>'))
  f.add_vline(x=0,line_dash='dot',line_color='#D24B5A');f.update_layout(height=255,margin=dict(l=20,r=20,t=25,b=35),xaxis_title='Remote − Hybrid salary difference (USD)',showlegend=False,plot_bgcolor='white',paper_bgcolor='white')
  st.plotly_chart(f,use_container_width=True)
  st.dataframe(pd.DataFrame([{'Method':name,'Lower bound':money(ci[0]),'Upper bound':money(ci[1])} for name,ci in cis]),hide_index=True,use_container_width=True)
  st.plotly_chart(histfig(Q2['bootstrap']['null_t'],'Bootstrap Welch t-statistics under H₀','t-statistic',TEAL,[(Q2['welch']['t'],ORANGE,'dash','Observed t')]),use_container_width=True)
  insight('Both 95% intervals exclude zero. The null-centered bootstrap t-test also rejects equal means (p ≈ 0.0001). The zero-centered standardized distribution above is not itself a null-hypothesis test.')
 with tabs[3]:
  m=Q2['median'];metricrow([('Remote median',money(m['Remote']),None),('Hybrid median',money(m['Hybrid']),None),('Median gap',money(m['difference']),None)])
  st.dataframe(pd.DataFrame([{'Test':'Mood’s median','Statistic':f"χ² = {m['chi2']:.4f}",'p-value':pval(m['mood_p'])},{'Test':'Null-centered bootstrap median','Statistic':'10,000 replications','p-value':pval(m['bootstrap_p'])}]),hide_index=True,use_container_width=True)
  st.plotly_chart(histfig(m['null_hist'],'Bootstrap median differences under H₀','Median difference (USD)',TEAL,[(m['difference'],ORANGE,'dash','Observed median gap'),(0,NAVY,'dot','Null center')]),use_container_width=True)
  insight('Both approaches reject equal population medians at the 5% level. The p-values differ because the methods use different null distributions and the simulation has finite p-value resolution.')
 with tabs[4]:
  s=Q2['sensitivity'];st.dataframe(pd.DataFrame([{'Dataset':'Original','Mean difference':money(s['original_diff']),'Welch t':f"{s['original_t']:.4f}",'p-value':pval(s['original_p'])},{'Dataset':'Trimmed','Mean difference':money(Q2['observed_diff']),'Welch t':f"{Q2['welch']['t']:.4f}",'p-value':pval(Q2['welch']['p'])}]),hide_index=True,use_container_width=True)
  insight('The salary difference remains positive and statistically significant with and without trimming, but the t-statistic changes substantially because extreme salaries increase variability.')

elif page=='Q3 · Education & ANOVA':
 heading('Q3 · Education & ANOVA','Bachelor’s, Master’s, and Professional degree holders in Canada and the United States.')
 keys=["Bachelor's","Master's","Professional"]
 metricrow([('Bachelor’s mean',money(Q3['trimmed']["Bachelor's"]['mean'],True),None),('Master’s mean',money(Q3['trimmed']["Master's"]['mean'],True),None),('Professional mean',money(Q3['trimmed']['Professional']['mean'],True),None),('ANOVA F',f"{Q3['anova']['f']:.2f}",None)])
 tabs=st.tabs(['Descriptives','ANOVA','Bootstrap means','Pairwise differences','Bootstrap ANOVA'])
 with tabs[0]:
  st.markdown('#### Original sample');stats_table(Q3['original'])
  st.markdown('#### Trimmed sample (top 1% per education group removed)');stats_table(Q3['trimmed'])
  c=st.columns(3)
  for col,name,color in zip(c,keys,[INDIGO,TEAL,ORANGE]):
   with col:st.plotly_chart(histfig(Q3['hist_trimmed'][name],name,'Annual salary (USD)',color),use_container_width=True)
  insight('Salary distributions are right-skewed in all three groups. Removing the top 1% within each degree category reduces the influence of extreme compensation observations.')
 with tabs[1]:
  a=Q3['anova'];metricrow([('F-statistic',f"{a['f']:.4f}",None),('p-value',pval(a['p']),None),('Degrees of freedom',f"{a['df_between']}, {a['df_within']}",None)])
  st.markdown('#### Group summary');stats_table(Q3['trimmed'])
  insight('One-way ANOVA rejects the null hypothesis that all three population mean salaries are equal (p < 0.05). ANOVA alone does not establish which specific pairs differ.')
 with tabs[2]:
  st.markdown('#### Figure 1 · Bootstrap distributions of group mean salaries')
  c=st.columns(3)
  for col,name,color in zip(c,keys,[INDIGO,TEAL,ORANGE]):
   with col:
    b=Q3['bootstrap_means'][name];st.plotly_chart(histfig(b['hist'],name,'Mean salary (USD)',color),use_container_width=True)
  st.dataframe(pd.DataFrame([{'Education':k,'Bootstrap mean':money(Q3['bootstrap_means'][k]['mean']),'Bootstrap SE':money(Q3['bootstrap_means'][k]['se']),'95% CI':f"{money(Q3['bootstrap_means'][k]['ci'][0])} – {money(Q3['bootstrap_means'][k]['ci'][1])}"} for k in keys]),hide_index=True,use_container_width=True)
  insight('The Professional group has the highest bootstrap mean but also a relatively wide uncertainty interval, reflecting its smaller sample size and higher salary variability.')
 with tabs[3]:
  st.markdown('#### Figure 2 · Pairwise bootstrap mean differences')
  pairs=Q3['pairwise'];c=st.columns(3)
  for col,(name,v),color in zip(c,pairs.items(),[INDIGO,TEAL,ORANGE]):
   with col:st.plotly_chart(histfig(v['hist'],name,'Salary difference (USD)',color,[(0,NAVY,'dot','Zero')]),use_container_width=True)
  st.markdown('#### Figure 3 · Standardized pairwise bootstrap distributions')
  c=st.columns(3)
  for col,(name,v),color in zip(c,pairs.items(),[INDIGO,TEAL,ORANGE]):
   with col:st.plotly_chart(histfig(v['standardized'],name,'Standardized units',color,[(0,NAVY,'dot','Center')]),use_container_width=True)
  st.dataframe(pd.DataFrame([{'Comparison':name,'Mean difference':money(v['mean']),'95% CI':f"{money(v['ci'][0])} – {money(v['ci'][1])}",'CI excludes zero':'Yes' if v['ci'][0]>0 or v['ci'][1]<0 else 'No'} for name,v in pairs.items()]),hide_index=True,use_container_width=True)
  insight('The Master’s–Bachelor’s and Professional–Bachelor’s intervals exclude zero. The Professional–Master’s interval includes zero, so this pair is not clearly separated by its unadjusted bootstrap percentile interval. These pairwise intervals are exploratory and are not multiplicity-adjusted.')
 with tabs[4]:
  a=Q3['anova'];b=Q3['bootstrap_anova'];metricrow([('Observed F',f"{a['f']:.4f}",None),('Parametric p',pval(a['p']),None),('Bootstrap p',pval(b['p']),None)])
  st.plotly_chart(histfig(b['null_hist'],'Bootstrap F-statistics under equal-means H₀','F-statistic',INDIGO,[(a['f'],ORANGE,'dash','Observed F')]),use_container_width=True)
  insight('Both the standard one-way ANOVA and the null-centered bootstrap ANOVA reject equal population means at α = 0.05. The bootstrap p-value is limited by the 10,000-replication simulation resolution.')

else:
 heading('Methods & Limitations','How to interpret the results and what the dashboard does—and does not—show.')
 st.markdown('''### Study design
- **Data:** Stack Overflow developer survey, 20,407 rows and 168 columns in the supplied cleaned CSV.
- **Q1:** Invalid ages (outside 18–100) and satisfaction values (outside 0–10) are excluded for relevant plots. Roles require at least 30 valid responses.
- **Q2:** Remote vs Hybrid, top 1% of annual salary excluded **within each group** for the primary analysis. Manual Student and Welch tests, 10,000-replication bootstrap, confidence intervals, and Mood’s median test.
- **Q3:** Canada and United States only, three degree categories, top 1% salary trimmed **within each group**. One-way ANOVA and 10,000-replication bootstrap comparisons.

### Statistical cautions
- Observational associations are **not causal**; occupation, geography, experience, and other confounders are not controlled here.
- Group-specific outlier trimming changes the target population and may affect estimates and p-values. Original-data sensitivity results are shown in Q2.
- ANOVA assumptions and group variance differences should be considered; pairwise bootstrap intervals are not multiplicity-adjusted.
- A bootstrap p-value of **0.0001** means no more extreme statistic was observed in 10,000 draws under the null, not that the exact theoretical p-value equals 0.0001.
- Salary and survey responses may be subject to self-selection, reporting error, and category limitations.

### Privacy and reproducibility
This deployed application contains **only aggregated statistics and binned bootstrap summaries**. It does not include the 67 MB respondent-level CSV. The Q1 salary-by-age scatter from the notebook is replaced by an age-aggregated line plot to avoid releasing individual records. All inferential statistics were recomputed from the same dataset, filters, seeds, and 10,000-replication methods used in the uploaded notebook.
''')

st.divider()
st.markdown('<div class="note">Developer Salary Intelligence · MIE Assignment 1 · Analytical dashboard · Values in USD · Aggregated survey results</div>',unsafe_allow_html=True)
