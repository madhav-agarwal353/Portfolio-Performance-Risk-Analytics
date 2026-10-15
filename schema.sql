CREATE TABLE IF NOT EXISTS prices(date TEXT, ticker TEXT, close REAL, PRIMARY KEY(date,ticker));
CREATE TABLE IF NOT EXISTS benchmark(date TEXT PRIMARY KEY, close REAL);
CREATE TABLE IF NOT EXISTS weights(ticker TEXT PRIMARY KEY, weight REAL, sector TEXT);
CREATE TABLE IF NOT EXISTS model_runs(run_id TEXT PRIMARY KEY, run_ts TEXT, model TEXT, horizon_days INT, train_rows INT, test_rows INT, r2 REAL, dir_acc REAL);
CREATE TABLE IF NOT EXISTS predictions(run_id TEXT, as_of_date TEXT, ticker TEXT, horizon_days INT, pred_return REAL, PRIMARY KEY(run_id,as_of_date,ticker));
CREATE TABLE IF NOT EXISTS risk_metrics(run_id TEXT, metric TEXT, portfolio REAL, benchmark REAL, PRIMARY KEY(run_id,metric));
