import json, pandas as pd
ts=pd.read_csv("powerbi/timeseries.csv"); m=pd.read_csv("powerbi/metrics.csv").set_index("metric")
c=pd.read_csv("powerbi/contribution.csv"); cr=pd.read_csv("powerbi/correlation.csv").set_index("ticker")
mr=pd.read_csv("powerbi/model_runs.csv").sort_values("run_ts"); run=mr.iloc[-1]
pr=pd.read_csv("powerbi/predictions.csv"); pr=pr[pr.run_id==run.run_id].sort_values("pred_return",ascending=False)
t=ts.iloc[::max(1,len(ts)//400)]
L=lambda s:[None if pd.isna(x) else round(float(x),4) for x in s]
D=dict(dates=t.date.tolist(),port=L(t.Portfolio),bench=L(t.Benchmark),ddp=L(t.Portfolio_DD),ddb=L(t.Benchmark_DD),vol=L(t.RollVol30),
  kpi={k:[None if pd.isna(v) else float(v) for v in r] for k,r in m[["Portfolio","Benchmark"]].iterrows()},
  contrib=dict(t=c.ticker.tolist(),v=L(c.return_contribution)),
  corr=dict(t=cr.index.tolist(),v=[L(r) for r in cr.values]),
  pred=dict(t=pr.ticker.tolist(),v=L(pr.pred_return),d=str(pr.as_of_date.iloc[0])),
  run=dict(id=run.run_id,model=run.model,r2=round(float(run.r2),3),acc=round(float(run.dir_acc),3),tr=int(run.train_rows),te=int(run.test_rows)))
html=r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Portfolio Performance & Risk Analytics</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>:root{--bg:#f4f6fa;--card:#fff;--tx:#1b2430;--mu:#6b7686;--bd:#e2e6ee;--p:#1f6feb;--b:#8b95a5;--g:#1a9e5c;--r:#d64545}
@media(prefers-color-scheme:dark){:root{--bg:#0f141b;--card:#18202b;--tx:#e6ebf2;--mu:#93a0b2;--bd:#263243}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:14px system-ui,sans-serif;padding:20px;max-width:1300px;margin:auto}
h1{font-size:20px;margin:0 0 4px}.sub{color:var(--mu);margin-bottom:16px}
.k{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:14px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px}
.k .n{font-size:20px;font-weight:600}.k .l{color:var(--mu);font-size:12px}.k .s{font-size:11px;color:var(--mu)}
.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:12px}.card h3{margin:0 0 8px;font-size:13px;color:var(--mu);font-weight:600}
.c{position:relative;height:240px}table{border-collapse:collapse;width:100%;font-size:11px}td,th{padding:4px;text-align:center}.w{overflow-x:auto}
</style></head><body><h1>Portfolio Performance & Risk Analytics</h1><div class="sub" id="sub"></div>
<div class="k" id="k"></div>
<div class="g"><div class="card"><h3>Cumulative growth (1 = start)</h3><div class="c"><canvas id="a"></canvas></div></div>
<div class="card"><h3>Drawdown</h3><div class="c"><canvas id="b"></canvas></div></div>
<div class="card"><h3>30-day rolling volatility (annualised)</h3><div class="c"><canvas id="c"></canvas></div></div>
<div class="card"><h3>Return contribution by stock</h3><div class="c"><canvas id="d"></canvas></div></div>
<div class="card"><h3 id="pt"></h3><div class="c"><canvas id="e"></canvas></div></div>
<div class="card"><h3>Correlation</h3><div class="w" id="cr"></div></div></div>
<script>const D=__DATA__;const css=getComputedStyle(document.documentElement),C=n=>css.getPropertyValue(n).trim();
const pct=new Set(["CAGR","Volatility","Max Drawdown","Alpha","Tracking Error","VaR 95%","CVaR 95%"]);
const f=(k,v)=>v==null?"–":pct.has(k)?(v*100).toFixed(1)+"%":v.toFixed(2);
document.getElementById("sub").textContent=`Model ${D.run.model} · R² ${D.run.r2} · direction acc. ${(D.run.acc*100).toFixed(1)}% · train ${D.run.tr} / test ${D.run.te} · run ${D.run.id}`;
document.getElementById("k").innerHTML=["CAGR","Volatility","Sharpe","Sortino","Max Drawdown","Beta","Alpha","VaR 95%","CVaR 95%","Info Ratio"].map(k=>`<div class="card"><div class="l">${k}</div><div class="n">${f(k,D.kpi[k][0])}</div><div class="s">Benchmark ${f(k,D.kpi[k][1])}</div></div>`).join("");
Chart.defaults.color=C("--mu");Chart.defaults.borderColor=C("--bd");
const o={responsive:true,maintainAspectRatio:false,animation:false,plugins:{legend:{labels:{boxWidth:10}}}};
const line=(id,ds)=>new Chart(id,{type:"line",data:{labels:D.dates,datasets:ds},options:{...o,elements:{point:{radius:0},line:{borderWidth:1.5}},scales:{x:{ticks:{maxTicksLimit:6}}}}});
line("a",[{label:"Portfolio",data:D.port,borderColor:C("--p")},{label:"Benchmark",data:D.bench,borderColor:C("--b")}]);
line("b",[{label:"Portfolio",data:D.ddp,borderColor:C("--r"),fill:true,backgroundColor:"rgba(214,69,69,.15)"},{label:"Benchmark",data:D.ddb,borderColor:C("--b")}]);
line("c",[{label:"Portfolio vol",data:D.vol,borderColor:C("--p")}]);
new Chart("d",{type:"bar",data:{labels:D.contrib.t,datasets:[{label:"Annualised contribution",data:D.contrib.v,backgroundColor:D.contrib.v.map(v=>v>=0?C("--g"):C("--r"))}]},options:{...o,plugins:{legend:{display:false}}}});
document.getElementById("pt").textContent="Predicted 5-day return (as of "+D.pred.d+") · top & bottom 8";
const n=D.pred.t.length,ix=[...Array(n).keys()].filter(i=>i<8||i>=n-8);
new Chart("e",{type:"bar",data:{labels:ix.map(i=>D.pred.t[i]),datasets:[{data:ix.map(i=>D.pred.v[i]),backgroundColor:ix.map(i=>D.pred.v[i]>=0?C("--g"):C("--r"))}]},options:{...o,indexAxis:"y",plugins:{legend:{display:false}}}});
let h="<table><tr><th></th>"+D.corr.t.map(x=>`<th>${x.slice(0,6)}</th>`).join("")+"</tr>";
D.corr.v.forEach((r,i)=>{h+=`<tr><th>${D.corr.t[i].slice(0,6)}</th>`+r.map(v=>`<td style="background:rgba(31,111,235,${Math.abs(v)*.7});color:${Math.abs(v)>.5?"#fff":"inherit"}">${v.toFixed(2)}</td>`).join("")+"</tr>"});
document.getElementById("cr").innerHTML=h+"</table>";</script></body></html>'''
open("dashboard.html","w").write(html.replace("__DATA__",json.dumps(D)))
print("dashboard.html written")

# ---------- Markdown dashboard ----------
P={"CAGR","Volatility","Max Drawdown","Alpha","Tracking Error","VaR 95%","CVaR 95%"}
F=lambda k,v:"–" if pd.isna(v) else (f"{v*100:.1f}%" if k in P else f"{v:.2f}")
tb=lambda h,rows:"| "+" | ".join(h)+" |\n|"+"|".join(["---"]*len(h))+"|\n"+"\n".join("| "+" | ".join(map(str,r))+" |" for r in rows)
s=ts.iloc[::max(1,len(ts)//24)].dropna(subset=["Portfolio","Benchmark"]); lab=",".join(f'"{x[:7]}"' for x in s.date)
mm=lambda t,a,b,y:f'```mermaid\nxychart-beta\n    title "{t}"\n    x-axis [{lab}]\n    y-axis "{y}"\n    line [{",".join(f"{v:.3f}" for v in a)}]\n    line [{",".join(f"{v:.3f}" for v in b)}]\n```'
top=pr.head(8); bot=pr.tail(8).iloc[::-1]; cs=c.sort_values("return_contribution",ascending=False)
cm=cr.round(2); n=len(cm)
md=f"""# Portfolio Performance & Risk Dashboard
_Period {ts.date.iloc[0]} → {ts.date.iloc[-1]} · Model {run.model} · run `{run.run_id}`_

## KPIs
{tb(["Metric","Portfolio","Benchmark"],[[k,F(k,r.Portfolio),F(k,r.Benchmark)] for k,r in m.iterrows()])}

## Cumulative Growth (blue = portfolio, orange = benchmark)
{mm("Cumulative growth",s.Portfolio,s.Benchmark,"Growth of 1")}

## Drawdown (blue = portfolio, orange = benchmark)
{mm("Drawdown",s.Portfolio_DD,s.Benchmark_DD,"Drawdown")}

![Dashboard](output/dashboard.png)

## Return Contribution (annualised)
{tb(["Ticker","Sector","Weight","Contribution"],[[r.ticker,r.sector,f"{r.weight*100:.0f}%",f"{r.return_contribution*100:.2f}%"] for r in cs.itertuples()])}

## ML Predictions: 5-day return (as of {pr.as_of_date.iloc[0]})
**Top 8**
{tb(["Ticker","Pred. return"],[[r.ticker,f"{r.pred_return*100:.2f}%"] for r in top.itertuples()])}

**Bottom 8**
{tb(["Ticker","Pred. return"],[[r.ticker,f"{r.pred_return*100:.2f}%"] for r in bot.itertuples()])}

**Model:** R² {run.r2:.3f} · direction accuracy {run.dir_acc*100:.1f}% · train {int(run.train_rows)} / test {int(run.test_rows)} rows

## Correlation
{tb([""]+[x[:6] for x in cm.index],[[cm.index[i][:6]]+[f"{v:.2f}" for v in cm.iloc[i]] for i in range(n)])}
"""
open("dashboard.md","w").write(md); print("dashboard.md written")
