-- daily asset returns
SELECT date, ticker, close/LAG(close) OVER (PARTITION BY ticker ORDER BY date)-1 AS ret FROM prices;
-- benchmark returns
SELECT date, close/LAG(close) OVER (ORDER BY date)-1 AS ret FROM benchmark;
-- latest predictions ranked
SELECT p.ticker, p.pred_return, RANK() OVER (ORDER BY p.pred_return DESC) AS rnk FROM predictions p WHERE p.run_id=(SELECT run_id FROM model_runs ORDER BY run_ts DESC LIMIT 1);
-- model history
SELECT * FROM model_runs ORDER BY run_ts DESC;
