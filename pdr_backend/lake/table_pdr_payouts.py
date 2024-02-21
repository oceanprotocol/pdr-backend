from polars import Int64, Float64, Utf8, Boolean

payouts_table_name = "pdr_payouts"

# RAW PAYOUT SCHEMA
payouts_schema = {
    "ID": Utf8,
    "token": Utf8,
    "user": Utf8,
    "slot": Int64,
    "timestamp": Int64,
    "payout": Float64,
    "predictedValue": Boolean,
    "revenue": Float64,
    "roundSumStakesUp": Float64,
    "roundSumStakes": Float64,
    "stake": Float64,
}
