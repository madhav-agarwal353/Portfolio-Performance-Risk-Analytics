import sqlite3, datetime as dt, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.ensemble import HistGradientBoostingRegressor
RF, AF, CONF, H = 0.065, 248, 0.95, 5          # India rf ~6.5%, ~248 trading days, 5-day horizon
CSV = "data/NIFTY50_all.csv"                   # cols: Date, Symbol, Close (NSE); add BSE rows same format
PORT = {"RELIANCE":"Energy","TCS":"IT","HDFCBANK":"Fin","INFY":"IT","ICICIBANK":"Fin",
        "HINDUNILVR":"FMCG","ITC":"FMCG","SBIN":"Fin","BHARTIARTL":"Telecom","LT":"Infra"}
run_id = dt.datetime.now().strftime("run_%Y%m%d_%H%M%S")

# ---------- 1. Load ----------
df = pd.read_csv(CSV, parse_dates=["Date"]).drop_duplicates(["Date","Symbol"])
px = df.pivot(index="Date", columns="Symbol", values="Close").sort_index().ffill(limit=5)
tick = list(PORT); px = px.dropna(subset=tick)
bench = 100*(1+px.pct_change().mean(axis=1).fillna(0)).cumprod()   # equal-weight index proxy (swap in ^NSEI close if available)

# ---------- 2. ETL -> SQLite ----------
con = sqlite3.connect("data/portfolio.db"); con.executescript(open("schema.sql").read())
for t in ("prices","benchmark","weights"): con.execute(f"DELETE FROM {t}")
pt = px[tick]; pt.index = pt.index.strftime("%Y-%m-%d")
pt.stack().rename("close").rename_axis(["date","ticker"]).reset_index().to_sql("prices", con, if_exists="append", index=False)
pd.DataFrame({"date":bench.index.strftime("%Y-%m-%d"),"close":bench.values}).to_sql("benchmark", con, if_exists="append", index=False)
pd.DataFrame({"ticker":tick,"weight":1/len(tick),"sector":list(PORT.values())}).to_sql("weights", con, if_exists="append", index=False)
con.commit()

# ---------- 3. SQL -> returns ----------
q = open("queries.sql").read().split(";")
ar = pd.read_sql(q[0], con).dropna().pivot(index="date", columns="ticker", values="ret")
br = pd.read_sql(q[1], con).dropna().set_index("date")["ret"]
w = pd.read_sql("SELECT * FROM weights", con).set_index("ticker")
pr = (ar*w["weight"]).sum(axis=1); pr.index = pd.to_datetime(pr.index); br.index = pd.to_datetime(br.index)

# ---------- 4. Risk analytics ----------
def metrics(r, b):
    cum = (1+r).cumprod(); dd = cum/cum.cummax()-1; down = r[r<0].std()*np.sqrt(AF)
    beta = np.cov(r,b)[0,1]/np.var(b,ddof=1)
    cagr = cum.iloc[-1]**(AF/len(r))-1; bc = (1+b).prod()**(AF/len(b))-1
    te = (r-b).std()*np.sqrt(AF); var = np.percentile(r,(1-CONF)*100)
    return {"CAGR":cagr,"Volatility":r.std()*np.sqrt(AF),"Sharpe":(r.mean()*AF-RF)/(r.std()*np.sqrt(AF)),
            "Sortino":(r.mean()*AF-RF)/down,"Max Drawdown":dd.min(),"Calmar":cagr/abs(dd.min()),
            "Beta":beta,"Alpha":cagr-(RF+beta*(bc-RF)),"Tracking Error":te,
            "Info Ratio":(cagr-bc)/te if te>0 else np.nan,"VaR 95%":var,"CVaR 95%":r[r<=var].mean()}
m = pd.DataFrame({"Portfolio":metrics(pr,br),"Benchmark":metrics(br,br)}).round(4); print(m)
m.reset_index().rename(columns={"index":"metric","Portfolio":"portfolio","Benchmark":"benchmark"}).assign(run_id=run_id)\
 [["run_id","metric","portfolio","benchmark"]].to_sql("risk_metrics", con, if_exists="append", index=False)
cum = pd.DataFrame({"Portfolio":(1+pr).cumprod(),"Benchmark":(1+br).cumprod()}); dd = cum/cum.cummax()-1
roll_vol = pr.rolling(30).std()*np.sqrt(AF); contrib = (ar.mean()*AF*w["weight"]).rename("return_contribution")

# ---------- 5. ML: pooled 5-day forward return model (all NSE/BSE symbols) ----------
r1 = px.pct_change()
feats = {"r1":r1,"r5":px.pct_change(5),"r20":px.pct_change(20),"r60":px.pct_change(60),
         "vol20":r1.rolling(20).std(),"vol60":r1.rolling(60).std(),"dist_hi":px/px.rolling(252,min_periods=60).max()-1}
X = pd.concat({k:v.stack() for k,v in feats.items()}, axis=1).dropna()
X.index.names = ["Date","Symbol"]
y = (px.shift(-H)/px-1).stack().rename("y"); y.index.names = ["Date","Symbol"]
D = X.join(y, how="inner").dropna()
cut = D.index.get_level_values(0).unique().sort_values()[int(.8*D.index.get_level_values(0).nunique())]
tr, te_ = D[D.index.get_level_values(0) < cut], D[D.index.get_level_values(0) >= cut]
mdl = HistGradientBoostingRegressor(max_depth=4, learning_rate=.05, max_iter=200, random_state=1).fit(tr.drop(columns="y"), tr["y"])
p = mdl.predict(te_.drop(columns="y"))
r2 = mdl.score(te_.drop(columns="y"), te_["y"]); acc = float((np.sign(p)==np.sign(te_["y"])).mean())
print(f"ML  R2={r2:.3f}  DirAcc={acc:.3f}  train={len(tr)} test={len(te_)}")

# ---------- 6. Save predictions to SQL ----------
last = X.index.get_level_values(0).max()
Xl = X.xs(last, level=0)
pred = pd.DataFrame({"run_id":run_id,"as_of_date":last.strftime("%Y-%m-%d"),"ticker":Xl.index,
                     "horizon_days":H,"pred_return":mdl.predict(Xl)})
pred.to_sql("predictions", con, if_exists="append", index=False)
pd.DataFrame([{"run_id":run_id,"run_ts":dt.datetime.now().isoformat(timespec="seconds"),"model":"HistGradientBoosting",
               "horizon_days":H,"train_rows":len(tr),"test_rows":len(te_),"r2":r2,"dir_acc":acc}]).to_sql("model_runs", con, if_exists="append", index=False)
con.commit()
print(pd.read_sql(q[2], con).head(10))

# ---------- 7. Power BI / chart exports ----------
m.index.name = "metric"; m.to_csv("output/metrics.csv"); m.to_csv("powerbi/metrics.csv")
pd.read_sql("SELECT * FROM model_runs", con).to_csv("powerbi/model_runs.csv", index=False)
cum.join(dd.add_suffix("_DD")).join(roll_vol.rename("RollVol30")).to_csv("powerbi/timeseries.csv")
contrib.to_frame().join(w).to_csv("powerbi/contribution.csv"); ar.corr().to_csv("powerbi/correlation.csv")
pd.read_sql("SELECT * FROM predictions", con).to_csv("powerbi/predictions.csv", index=False)
fig, ax = plt.subplots(2,2, figsize=(13,8))
cum.plot(ax=ax[0,0], title="Cumulative Return"); dd.plot(ax=ax[0,1], title="Drawdown")
roll_vol.plot(ax=ax[1,0], title="30d Rolling Vol"); pred.set_index("ticker")["pred_return"].sort_values().tail(15).plot.barh(ax=ax[1,1], title="Top 15 Predicted 5d Return")
plt.tight_layout(); plt.savefig("output/dashboard.png", dpi=110)
