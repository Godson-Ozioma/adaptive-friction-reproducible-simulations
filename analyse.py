"""Reproducible illustrative simulation; no observed human data."""
from pathlib import Path
import json,sys,platform
import numpy as np
import pandas as pd
from scipy.stats import t
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
OUT=Path(__file__).resolve().parent
SEED=20261103
rng=np.random.default_rng(SEED)
N=165
arm=np.repeat(np.arange(3),55)
a=rng.normal(size=N)
X=np.column_stack([np.ones(N),arm==1,arm==2,a,(arm==1)*a,(arm==2)*a])
B=np.array([65,6,7.5,10,-3.5,-2.5])
A=np.array([np.log(45),.22,.03,-.15,0,0])
z=rng.normal(size=(N,2))
y=X@B+6.5*z[:,0]
logtime=X@A+.12*(.3*z[:,0]+np.sqrt(1-.3**2)*z[:,1])
delayed=y+np.choose(arm,[-14,-6,-5])+rng.normal(0,4,N)
df=pd.DataFrame({'synthetic_id':np.arange(1,N+1),'arm':np.array(['Ordinary','Static','Adaptive'])[arm],'ability_z':a,'immediate_transfer':y,'delayed_transfer':delayed,'assisted_time_min':np.exp(logtime),'log_time':logtime})
df.to_csv(OUT/'synthetic_data.csv',index=False)
def fit(v):
 inv=np.linalg.inv(X.T@X); beta=inv@X.T@v; e=v-X@beta
 cov=inv*(e@e/(N-6))
 return beta,cov
fy=fit(y);ft=fit(logtime);fd=fit(delayed)
def contrast(f,c,level=.95,exp=False):
 b,v=f;est=float(c@b);se=float(np.sqrt(c@v@c));q=t.ppf((1+level)/2,N-6);lo=est-q*se;hi=est+q*se
 return {'estimate':float(np.exp(est) if exp else est),'lo':float(np.exp(lo) if exp else lo),'hi':float(np.exp(hi) if exp else hi),'se':se}
contr={}
for label,c in [('Adaptive vs ordinary',[0,0,1,0,0,0]),('Static vs ordinary',[0,1,0,0,0,0]),('Adaptive vs static',[0,-1,1,0,0,0])]:
 c=np.array(c);contr[label]={'transfer95':contrast(fy,c),'delayed95':contrast(fd,c),'time90':contrast(ft,c,.90,True)}
for val in [-1,1]:
 contr['Adaptive at '+str(val)]={'transfer95':contrast(fy,np.array([0,0,1,0,0,val]))}
# Replicated simulations use independent PCG64 streams per scenario and sample size.
scenarios=[('Source-like',7.5,-2.5,.03),('No benefit',0.,0.,0.),('Weak benefit',2.,-1.,.03),('Excess delay',7.5,-2.5,.15),('Gain boundary',5.,-2.5,.03),('Time boundary',7.5,-2.5,np.log(1.10))]
R=5000
rows=[]
for ni,n in enumerate([165,330,660]):
 for si,(name,effect,interaction,delay) in enumerate(scenarios):
  rr=np.random.default_rng(SEED+1000*(ni+1)+si)
  ar=np.repeat(np.arange(3),n//3);stat=ar==1;ad=ar==2
  totals=np.zeros(5); estimates=[]; ses=[]
  for start in range(0,R,250):
   b=min(250,R-start);ab=rr.normal(size=(b,n));ones=np.ones_like(ab)
   xx=np.stack([ones,np.broadcast_to(stat,ab.shape),np.broadcast_to(ad,ab.shape),ab,ab*stat,ab*ad],axis=-1)
   inv=np.linalg.inv(np.einsum('bni,bnj->bij',xx,xx))
   beta=np.array([65,6,effect,10,-3.5,interaction]);alpha=np.array([np.log(45),.22,delay,-.15,0,0])
   noise=rr.normal(size=(b,n,2)); yy=xx@beta+6.5*noise[:,:,0];tt=xx@alpha+.12*(.3*noise[:,:,0]+np.sqrt(.91)*noise[:,:,1])
   def calc(out):
    bh=np.einsum('bij,bj->bi',inv,np.einsum('bni,bn->bi',xx,out));err=out-np.einsum('bni,bi->bn',xx,bh)
    variance=np.sum(err**2,axis=1)/(n-6);se=np.sqrt(inv[:,2,2]*variance);seint=np.sqrt(inv[:,5,5]*variance)
    return bh,se,seint
   by,sy,si_y=calc(yy);bt,st,_=calc(tt);q=t.ppf(.95,n-6);q2=t.ppf(.975,n-6)
   lower=by[:,2]-q*sy;upper=bt[:,2]+q*st
   superiority=lower>0;ni_ok=upper<np.log(1.10);gate=(lower>5)&ni_ok
   inter=np.abs(by[:,5]/si_y)>q2
   coverage=np.abs(by[:,2]-effect)<=q2*sy
   totals+=np.array([superiority.sum(),ni_ok.sum(),gate.sum(),inter.sum(),coverage.sum()])
   estimates.extend(by[:,2]);ses.extend(sy)
  rates=totals/R
  row={'n':n,'scenario':name,'true_gain':effect,'true_log_time':delay,'replications':R,'bias':float(np.mean(estimates)-effect),'empirical_sd':float(np.std(estimates,ddof=1))}
  for key,val in zip(['superiority','time_noninferiority','joint_gate','interaction','coverage95'],rates):row[key]=float(val);row[key+'_mcse']=float(np.sqrt(val*(1-val)/R))
  rows.append(row)
mc=pd.DataFrame(rows);mc.to_csv(OUT/'monte_carlo.csv',index=False)
# Analytical telemetry sensitivity, not an empirically fitted classifier.
p=.4;benefit=24.;harm=2.;minutes_per_prompt=9.;baseline=45.
sens=np.linspace(.1,1,181);spec=np.linspace(.1,1,181);se,sp=np.meshgrid(sens,spec)
prompt_rate=p*se+(1-p)*(1-sp)
gain=benefit*p*se-harm*(1-p)*(1-sp)
time_ratio=1+minutes_per_prompt*prompt_rate/baseline
feasible=(gain>=5)&(time_ratio<=1.10)
summary={'seed':SEED,'n':N,'R':R,'contrasts':contr,'synthetic_ranges':{'min_transfer':float(y.min()),'max_transfer':float(y.max())},'versions':{'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__},'gate':bool(contr['Adaptive vs ordinary']['transfer95']['estimate']-t.ppf(.95,N-6)*contr['Adaptive vs ordinary']['transfer95']['se']>5 and contr['Adaptive vs ordinary']['time90']['hi']<1.10),'telemetry':{'prevalence':p,'benefit':benefit,'false_prompt_harm':harm,'all_prompt_minutes':minutes_per_prompt,'baseline_minutes':baseline}}
(OUT/'results.json').write_text(json.dumps(summary,indent=2))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':220})
colors=['#566473','#287C8E','#B55B32']
# Figure 1: decision flow
fig,ax=plt.subplots(figsize=(7.3,3.8));ax.set_xlim(0,10);ax.set_ylim(0,5);ax.axis('off')
def box(x,y,w,h,text):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.05',fc='#F3F5F6',ec='#5C6871',lw=1));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=9)
def arrow(a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=12,color='#5C6871'))
box(.2,3.7,2.55,.85,'Ordinary assistance\nNo reasoning prompts');box(3.7,3.7,2.55,.85,'Static friction\nFixed prompt schedule');box(7.2,3.7,2.55,.85,'Adaptive friction\nTelemetry triggered prompts')
box(2.3,2.1,5.4,.85,'Assess assisted time and subsequent unaided transfer\nPreserve ability as a continuous moderator')
for x in [1.475,4.975,8.475]:arrow((x,3.7),(5,2.95))
box(.9,.45,3.65,1.0,'Learning requirement\nOne sided 95% lower bound > 5 points');box(5.45,.45,3.65,1.0,'Efficiency requirement\nOne sided 95% upper time ratio < 1.10')
arrow((4.25,2.1),(2.725,1.45));arrow((5.75,2.1),(7.275,1.45));ax.text(5,.13,'Both conditions must hold for the same candidate policy',ha='center',fontsize=9,fontweight='bold')
fig.tight_layout();fig.savefig(OUT/'fig1.png');plt.close(fig)
# Figure 2
fig,axs=plt.subplots(1,2,figsize=(7.3,3.5));grid=np.linspace(-2,2,100)
for j,name in enumerate(['Ordinary','Static','Adaptive']):
 xx=np.column_stack([np.ones(100),np.full(100,j==1),np.full(100,j==2),grid,grid*(j==1),grid*(j==2)])
 pred=xx@fy[0];sepred=np.sqrt(np.einsum('ij,jk,ik->i',xx,fy[1],xx))
 axs[0].plot(grid,pred,color=colors[j],label=name);axs[0].fill_between(grid,pred-1.975*sepred,pred+1.975*sepred,color=colors[j],alpha=.12)
axs[0].set(xlabel='Baseline ability (standard deviations)',ylabel='Immediate transfer index',title='A  Synthetic conditional means');axs[0].legend(frameon=False,fontsize=8)
for j,key in enumerate(['Static vs ordinary','Adaptive vs ordinary']):
 q=contr[key]['time90'];axs[1].errorbar(q['estimate'],j,xerr=[[q['estimate']-q['lo']],[q['hi']-q['estimate']]],fmt='o',color=colors[j+1],capsize=4)
axs[1].axvspan(.9,1.1,color='#E2EFE9');axs[1].axvline(1.1,ls='--',c='#555');axs[1].set(yticks=[0,1],yticklabels=['Static','Adaptive'],xlabel='Geometric time ratio vs ordinary',title='B  Synthetic time estimates',ylim=(-.6,1.6));axs[1].text(.91,1.3,'Equivalence region',fontsize=8)
fig.tight_layout();fig.savefig(OUT/'fig2.png');plt.close(fig)
# Figure3 operating characteristics
fig,axs=plt.subplots(1,2,figsize=(7.3,3.8))
for ax,key,title in zip(axs,['joint_gate','interaction'],['A  Joint decision\npass rate','B  Ability interaction\nrejection rate']):
 data=mc.pivot(index='scenario',columns='n',values=key).loc[[s[0] for s in scenarios]].values
 im=ax.imshow(data,vmin=0,vmax=1,cmap='Blues',aspect='auto')
 for i in range(6):
  for j in range(3):ax.text(j,i,f'{100*data[i,j]:.1f}%',ha='center',va='center',color='white' if data[i,j]>.55 else '#202020',fontsize=9)
 ax.set(xticks=range(3),xticklabels=[165,330,660],yticks=range(6),yticklabels=[s[0] for s in scenarios],xlabel='Total synthetic sample size',title=title)
fig.tight_layout();fig.savefig(OUT/'fig3.png');plt.close(fig)
# Figure4 classifier surface
fig,ax=plt.subplots(figsize=(7.3,3.7));im=ax.pcolormesh(se,sp,gain,cmap='viridis',shading='auto',vmin=-1.2,vmax=9.6)
c1=ax.contour(se,sp,gain,levels=[5],colors='white',linewidths=1.8);ax.clabel(c1,fmt={5:'5 point gain'},fontsize=9,manual=[(.55,.77)])
c2=ax.contour(se,sp,time_ratio,levels=[1.1],colors='#EDC849',linewidths=1.8);ax.clabel(c2,fmt={1.1:'1.10 time ratio'},fontsize=9)
ax.contourf(se,sp,feasible,levels=[.5,1.5],colors='none',hatches=['///']);ax.plot(.8,.85,'o',mec='black',mfc='white',ms=6);ax.text(.81,.87,'Illustrative detector',color='white',fontsize=8)
ax.set(xlabel='Trigger sensitivity',ylabel='Trigger specificity',title='Expected feasibility under assumed detector performance');cbar=fig.colorbar(im,ax=ax,pad=.02);cbar.set_label('Expected transfer gain (points)');ax.text(.12,.96,'Hatching: both expected thresholds satisfied',fontsize=8,color='white')
fig.tight_layout();fig.savefig(OUT/'fig4.png');plt.close(fig)
print(json.dumps(summary,indent=2));print(mc[['n','scenario','superiority','time_noninferiority','joint_gate','interaction','coverage95','bias']].to_string(index=False))
