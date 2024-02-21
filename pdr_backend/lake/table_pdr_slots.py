from polars import Float64, Int64, Utf8, Boolean

slots_table_name = "pdr_slots"

# RAW SLOT SCHEMA
slots_schema = {
    "ID": Utf8,
    "timestamp": Int64,
    "slot": Int64,
    "trueval": Boolean,
    "roundSumStakesUp": Float64,
    "roundSumStakes": Float64,
}
