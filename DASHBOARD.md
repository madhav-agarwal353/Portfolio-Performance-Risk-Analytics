# Power BI Build
1. `python main.py` -> CSVs in `powerbi/`.
2. Transform data -> parameter `DataPath` -> add 6 queries from `load.pq`.
3. Relationships: dim_company[symbol] 1:* fact[symbol]; dim_company[symbol] 1:1 summary_stock[symbol]; dim_company[industry] *:1 summary_sector[industry] (set summary_sector on the 1 side); dim_company[symbol] 1:* yearly[symbol].
4. Paste each line of `measures.dax` as a measure (table: fact). Format returns/vol/drawdown as %.
5. Theme: dark blue/teal; green = gain, red = loss.

## Page 1 Market Overview
- Slicers: date range (fact[date]), industry
- Cards: Stocks Up, Stocks Down, Best Stock, Worst Stock, Total Turnover, Annual Volatility
- Line: Indexed Price by date, legend = industry (or top 10 symbols)
- Bar: summary_stock symbol x total_return, Top 10 / Bottom 10 filter
- Treemap: industry x Total Turnover

## Page 2 Stock Comparison
- Multi-select slicer: symbol
- Line: Indexed Price (date x symbol)
- Line: vol30 (date x symbol)
- Clustered column: Avg Daily Volume by symbol
- Scatter: x=ann_vol, y=cagr, size=avg_turnover, legend=industry, details=symbol
- Table: symbol, Period Return, Annual Volatility, Return per Risk, Max Drawdown, beta

## Page 3 Sector Performance
- Matrix: yearly industry rows x yr cols, Average of yearly_return, conditional color (red-white-green)
- Line: sector_monthly month x avg_return, legend industry
- Donut: summary_sector industry x avg_turnover
- Bar: summary_sector industry x avg_sharpe
- Cards: n_stocks per sector (slicer-linked)

## Page 4 Volume & Volatility
- Area: drawdown by date (selected symbols)
- Column: volume by date, line overlay vol_spike
- Table: Volume Spike Days by symbol, sorted desc
- Heatmap matrix: symbol x yr, Average of vol30 (fact[date] year hierarchy)

## SQL live option
Power BI -> ODBC (SQLite3) -> `data/stocks.db` -> tables fact_daily, summary_stock, summary_sector, prices, companies.
