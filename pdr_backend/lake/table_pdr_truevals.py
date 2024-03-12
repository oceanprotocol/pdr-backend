from polars import Boolean, Int64, Utf8

truevals_table_name = "pdr_truevals"

# RAW TRUEVAL SCHEMA
truevals_schema = {
    "ID": Utf8,
    "token": Utf8,
    "timestamp": Int64,
    "truevalue": Boolean,
    "slot": Int64,
}
