// Power BI: Home > Transform data > New Source > Blank Query > Advanced Editor. One query per block.
// First create Parameter: DataPath (Text) = C:\path\to\portfolio_risk\powerbi\

// ---- ts ----
let S = Csv.Document(File.Contents(DataPath & "timeseries.csv"), [Delimiter=",", Encoding=65001]),
    H = Table.PromoteHeaders(S),
    T = Table.TransformColumnTypes(H, {{"date", type date}, {"Portfolio", type number}, {"Benchmark", type number},
        {"Portfolio_DD", type number}, {"Benchmark_DD", type number}, {"RollVol30", type number}})
in T

// ---- metrics ----
let S = Csv.Document(File.Contents(DataPath & "metrics.csv"), [Delimiter=",", Encoding=65001]),
    H = Table.PromoteHeaders(S),
    T = Table.TransformColumnTypes(H, {{"metric", type text}, {"Portfolio", type number}, {"Benchmark", type number}})
in T

// ---- contrib ----
let S = Csv.Document(File.Contents(DataPath & "contribution.csv"), [Delimiter=",", Encoding=65001]),
    H = Table.PromoteHeaders(S),
    T = Table.TransformColumnTypes(H, {{"return_contribution", type number}, {"weight", type number}})
in T

// ---- corr (unpivoted for matrix) ----
let S = Csv.Document(File.Contents(DataPath & "correlation.csv"), [Delimiter=",", Encoding=65001]),
    H = Table.PromoteHeaders(S),
    U = Table.UnpivotOtherColumns(H, {"ticker"}, "ticker2", "corr"),
    T = Table.TransformColumnTypes(U, {{"corr", type number}})
in T

// ---- preds ----
let S = Csv.Document(File.Contents(DataPath & "predictions.csv"), [Delimiter=",", Encoding=65001]),
    H = Table.PromoteHeaders(S),
    T = Table.TransformColumnTypes(H, {{"as_of_date", type date}, {"horizon_days", Int64.Type}, {"pred_return", type number}})
in T

// ---- model_runs ----
let S = Csv.Document(File.Contents(DataPath & "model_runs.csv"), [Delimiter=",", Encoding=65001]),
    H = Table.PromoteHeaders(S),
    T = Table.TransformColumnTypes(H, {{"r2", type number}, {"dir_acc", type number}, {"train_rows", Int64.Type}, {"test_rows", Int64.Type}})
in T
