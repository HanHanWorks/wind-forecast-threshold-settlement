import os
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','DejaVu Serif'],
    'font.size':8,'axes.linewidth':0.7,'pdf.fonttype':42,'ps.fonttype':42,
    'xtick.direction':'out','ytick.direction':'out','legend.frameon':False})

OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'outputs', 'figures')
A='acc_S02_src2'; B='acc_S06_scale'
D=pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'daily_acc_panel.csv'),parse_dates=['date'])
P7=['acc_S01_src1','acc_S02_src2','acc_S04_vendorF','acc_S06_scale','acc_S09_scale','acc_S11_floor05','acc_S13_blendY']
g=D.groupby('date')[P7].mean()
wins=pd.date_range('2024-01-01','2025-03-26',freq='15D')
rows=[]
for s in wins:
    bt=g.loc[s-pd.Timedelta(days=365): s-pd.Timedelta(days=1)]
    dp=g.loc[s:s+pd.Timedelta(days=89)]
    if len(bt)<300 or len(dp)<85: continue
    bm=bt.mean(); dm=dp.mean(); pick=bm.idxmax(); best=dm.idxmax()
    d=(dp[A]-dp[B]).dropna()
    rows.append(dict(window=s,pick=pick,best=best,hit=int(pick==best),
        bt_gap=bm.nlargest(2).iloc[0]-bm.nlargest(2).iloc[1],
        se90=d.std(ddof=1)/np.sqrt(len(d)),
        regret_oracle=float((dp.max(1)-dp[pick]).mean()),
        regret_fixed=float(dm.max()-dm[pick])))
R=pd.DataFrame(rows); K=1.98
BLUE='#2b6cb0'; ORNG='#e07b39'; RED='#c0392b'

# ================= FIG 2 =================
fig,ax=plt.subplots(figsize=(7.0,2.05))
n=len(R); x=np.arange(n)
ax.set_xlim(-0.7,n-0.3); ax.set_ylim(-0.55,2.45)
for sp in ['left','right','top','bottom']: ax.spines[sp].set_visible(False)
ax.set_yticks([])
col={A:BLUE,B:ORNG}
for field,y0,lab in [('best',1.72,'Deployment truth'),('pick',0.92,'Backtest choice')]:
    for i,r in R.iterrows():
        ax.add_patch(plt.Rectangle((i-0.44,y0-0.30),0.88,0.60,color=col[r[field]],lw=0.6,ec='white'))
    ax.text(-1.0,y0,lab,ha='right',va='center',fontsize=8)
for i,r in R.iterrows():
    if not r.hit: ax.plot(i,0.28,marker='v',ms=3.6,color=RED,lw=0)
ax.text(-1.0,0.28,'Ordering error',ha='right',va='center',fontsize=8,color=RED)
ax.hlines(0.02,-0.7,n-0.3,color='0.55',lw=0.6)
tick=[i for i in range(n) if R.window.iloc[i].month in (1,7) and R.window.iloc[i].day<=15]
ax.set_xticks(tick); ax.set_xticklabels([R.window.iloc[i].strftime('%Y-%m') for i in tick],fontsize=6.5)
ax.tick_params(axis='x',length=2.5,pad=2)
ax.set_xlabel('Rolling 90-day decision cycle (window start)',fontsize=8)
ax.legend(handles=[Patch(color=BLUE,label='src2 (incumbent)'),Patch(color=ORNG,label='S06 (scaled variant of src1)')],
          loc='lower center',bbox_to_anchor=(0.5,1.0),ncol=2,fontsize=7.5,handlelength=1.1,columnspacing=1.4)
fig.tight_layout()
for e in ['pdf','png']: fig.savefig(OUT+f'fig2_shortlist.{e}',dpi=400,bbox_inches='tight')
plt.close(fig)

# ================= FIG 3 =================
fig,ax=plt.subplots(figsize=(3.5,3.0))
hit=R.hit==1; lim=1.12
ax.fill_between([0,lim],[0,lim],[lim,lim],color='0.90',lw=0,zorder=0)
ax.plot([0,lim],[0,lim],'k--',lw=0.8,zorder=1)
ax.scatter(R.bt_gap[hit],R.se90[hit],s=28,facecolor=BLUE,edgecolor='white',lw=0.5,
           label=f'ordered correctly (n={hit.sum()})',zorder=3)
ax.scatter(R.bt_gap[~hit],R.se90[~hit],s=28,facecolor=RED,edgecolor='white',lw=0.5,
           label=f'ordered wrongly (n={(~hit).sum()})',zorder=3)
ax.text(0.05,0.60,'margin below resolution\n→ ordering not identifiable',fontsize=6.4,color='0.30',va='top')
ax.text(0.94,0.30,'margin above resolution\n→ identifiable',fontsize=6.4,color='0.30',ha='right',va='bottom')
ax.set_xlim(0,lim); ax.set_ylim(0,lim)
ax.set_xlabel('Backtest margin between #1 and #2\n(ACC points)',fontsize=7.5)
ax.set_ylabel('Resolution of the 90-day evaluation\n(paired standard error, ACC points)',fontsize=7.5)
ax.legend(loc='lower right',fontsize=6.4,handletextpad=0.3,borderaxespad=0.2)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
for e in ['pdf','png']: fig.savefig(OUT+f'fig3_resolution.{e}',dpi=400,bbox_inches='tight')
plt.close(fig)

# ================= FIG 4 =================
lad=pd.DataFrame({'k':[3,4,5,6,7],'hit':[93.5,83.1,72.6,62.1,51.6],
                  'lo':[93.5,51.6,51.6,51.6,51.6],'hi':[93.5,93.5,93.5,93.5,51.6],
                  'gap':[3.36,2.67,1.99,1.30,0.62]})
fig,ax=plt.subplots(figsize=(3.6,2.95))
ax.errorbar(lad.k,lad.hit,yerr=[lad.hit-lad.lo,lad.hi-lad.hit],fmt='o-',color=BLUE,ms=5,lw=1.2,
            capsize=2.5,elinewidth=0.7,label='Top-1 hit rate (range across subsets)',zorder=3)
ax.axhline(50,ls=':',color='0.45',lw=0.8)
ax.set_ylim(40,100); ax.set_xlim(2.7,7.3)
ax.set_xticks([3,4,5,6,7])
ax.set_xlabel('Candidates in the pool, k',fontsize=7.5)
ax.set_ylabel('Top-1 hit rate (%)',color=BLUE,fontsize=7.5)
ax.tick_params(axis='y',colors=BLUE)
ax2=ax.twinx()
ax2.plot(lad.k,lad.gap,'s--',color=ORNG,ms=4.5,lw=1.0,label='median #1−#2 margin',zorder=2)
ax2.set_ylabel('Median #1−#2 margin (ACC points)',color=ORNG,fontsize=7.5)
ax2.tick_params(axis='y',colors=ORNG); ax2.set_ylim(0,4.0)
ax.annotate('93.5%',(3,93.5),textcoords='offset points',xytext=(7,-7),fontsize=7,color=BLUE)
ax.annotate('51.6%',(7,51.6),textcoords='offset points',xytext=(-6,10),fontsize=7,color=BLUE)
ax.plot([4],[51.6],marker='v',ms=4.5,color=RED,lw=0,zorder=5)
ax.annotate('this bound is a single\nadded variant (S06)',(4,51.6),textcoords='offset points',
            xytext=(9,-13),fontsize=6.2,color=RED)
ax.text(2.82,46.6,'coin flip (50%)',fontsize=6.4,color='0.42')
ax.spines['top'].set_visible(False); ax2.spines['top'].set_visible(False)
fig.tight_layout()
for e in ['pdf','png']: fig.savefig(OUT+f'fig4_ladder.{e}',dpi=400,bbox_inches='tight')
plt.close(fig)

# ================= FIG 5 =================
fig,ax=plt.subplots(figsize=(3.7,2.8))
bins=np.linspace(0,5.0,11)
ax.hist(R.regret_oracle,bins=bins,color='0.78',edgecolor='white',lw=0.5,
        label='daily-oracle regret (as reported: 5.2 GWh)')
ax.hist(R.regret_fixed,bins=bins,color=BLUE,alpha=0.9,edgecolor='white',lw=0.5,
        label='decision-consistent regret (1.0 GWh)')
ax.axvline(R.regret_oracle.median(),color='0.45',ls='--',lw=0.8)
ax.axvline(R.regret_fixed.median(),color=BLUE,ls='--',lw=0.9)
ax.set_xlim(-0.08,5.0); ax.set_ylim(0,25)
ax.annotate('',xy=(R.regret_oracle.median(),19.0),xytext=(R.regret_fixed.median()+0.06,19.0),
            arrowprops=dict(arrowstyle='->',color='0.25',lw=0.8))
ax.text(1.35,19.6,'5.8× overstatement',fontsize=6.8,color='0.25')
ax.set_xlabel('Regret over a 90-day decision cycle (ACC points)',fontsize=7.5)
ax.set_ylabel('Number of cycles',fontsize=7.5)
ax2x=ax.twiny(); ax2x.set_xlim(np.array(ax.get_xlim())*K)
ax2x.set_xlabel('Equivalent assessed energy (GWh)',fontsize=7.5)
ax2x.spines['right'].set_visible(False); ax2x.spines['bottom'].set_visible(False)
ax.legend(loc='upper right',fontsize=6.1,handlelength=1.1,borderaxespad=0.2)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
for e in ['pdf','png']: fig.savefig(OUT+f'fig5_economics.{e}',dpi=400,bbox_inches='tight')
plt.close(fig)

R.to_csv(os.path.join(os.path.dirname(OUT), 'stats', 'table2_windows.csv'),index=False)
print("ok")
