import io
from unittest.mock import MagicMock

from enforce_typing import enforce_types
import polars as pl

from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.lake_validate import LakeValidate

csv_string = """
pair,timeframe,slot,datetime,timedelta,count
ADA/USDT,1h,1714413600,29-04-2024 11:00,,1
ADA/USDT,1h,1714417200,29-04-2024 12:00,3600,1
ADA/USDT,1h,1714420800,29-04-2024 13:00,3600,1
ADA/USDT,1h,1714424400,29-04-2024 14:00,3600,1
ADA/USDT,1h,1714428000,29-04-2024 15:00,3600,1
ADA/USDT,1h,1714431600,29-04-2024 16:00,3600,1
ADA/USDT,5m,1711930200,31-03-2024 17:10,,1
ADA/USDT,5m,1711930500,31-03-2024 17:15,300,1
ADA/USDT,5m,1711930800,31-03-2024 17:20,300,1
ADA/USDT,5m,1711931100,31-03-2024 17:25,300,1
ADA/USDT,5m,1711931400,31-03-2024 17:30,300,1
ADA/USDT,5m,1711931700,31-03-2024 17:35,300,1
ADA/USDT,5m,1711932000,31-03-2024 17:40,300,1
ADA/USDT,5m,1711932300,31-03-2024 17:45,300,1
ADA/USDT,5m,1711932600,31-03-2024 17:50,300,1
ADA/USDT,5m,1711932900,31-03-2024 17:55,300,1
ADA/USDT,5m,1711933200,31-03-2024 18:00,300,1
ADA/USDT,5m,1711933500,31-03-2024 18:05,300,1
ADA/USDT,5m,1711933800,31-03-2024 18:10,300,1
ADA/USDT,5m,1711934100,31-03-2024 18:15,300,1
ADA/USDT,5m,1711934400,31-03-2024 18:20,300,1
ADA/USDT,5m,1711934700,31-03-2024 18:25,300,1
ADA/USDT,5m,1711935000,31-03-2024 18:30,300,1
ADA/USDT,5m,1711935300,31-03-2024 18:35,300,1
ADA/USDT,5m,1711935600,31-03-2024 18:40,300,1
ADA/USDT,5m,1711935900,31-03-2024 18:45,300,1
ADA/USDT,5m,1711936200,31-03-2024 18:50,300,1
ADA/USDT,5m,1711936500,31-03-2024 18:55,300,1
ADA/USDT,5m,1711936800,31-03-2024 19:00,300,1
ADA/USDT,5m,1711937100,31-03-2024 19:05,300,1
ADA/USDT,5m,1711937400,31-03-2024 19:10,300,1
ADA/USDT,5m,1711937700,31-03-2024 19:15,300,1
ADA/USDT,5m,1711938000,31-03-2024 19:20,300,1
ADA/USDT,5m,1711938300,31-03-2024 19:25,300,1
ADA/USDT,5m,1711938600,31-03-2024 19:30,300,1
ADA/USDT,5m,1711938900,31-03-2024 19:35,300,1
ADA/USDT,5m,1711939200,31-03-2024 19:40,300,1
ADA/USDT,5m,1711939500,31-03-2024 19:45,300,1
ADA/USDT,5m,1711939800,31-03-2024 19:50,300,1
ADA/USDT,5m,1711940100,31-03-2024 19:55,300,1
ADA/USDT,5m,1711940400,31-03-2024 20:00,300,1
ADA/USDT,5m,1711940700,31-03-2024 20:05,300,1
ADA/USDT,5m,1711941000,31-03-2024 20:10,300,1
ADA/USDT,5m,1711941300,31-03-2024 20:15,300,1
ADA/USDT,5m,1711941600,31-03-2024 20:20,300,1
ADA/USDT,5m,1711941900,31-03-2024 20:25,300,1
ADA/USDT,5m,1711942200,31-03-2024 20:30,300,1
ADA/USDT,5m,1711942500,31-03-2024 20:35,300,1
ADA/USDT,5m,1711942800,31-03-2024 20:40,300,1
ADA/USDT,5m,1711943100,31-03-2024 20:45,300,1
ADA/USDT,5m,1711943400,31-03-2024 20:50,300,1
ADA/USDT,5m,1711943700,31-03-2024 20:55,300,1
ADA/USDT,5m,1711944000,31-03-2024 21:00,300,1
ADA/USDT,5m,1711944300,31-03-2024 21:05,300,1
ADA/USDT,5m,1711944600,31-03-2024 21:10,300,1
ADA/USDT,5m,1711944900,31-03-2024 21:15,300,1
ADA/USDT,5m,1711945200,31-03-2024 21:20,300,1
ADA/USDT,5m,1711945500,31-03-2024 21:25,300,1
ADA/USDT,5m,1711945800,31-03-2024 21:30,300,1
ADA/USDT,5m,1711946100,31-03-2024 21:35,300,1
ADA/USDT,5m,1711946400,31-03-2024 21:40,300,1
ADA/USDT,5m,1711946700,31-03-2024 21:45,300,1
ADA/USDT,5m,1711947000,31-03-2024 21:50,300,1
ADA/USDT,5m,1711947300,31-03-2024 21:55,300,1
ADA/USDT,5m,1711947600,31-03-2024 22:00,300,1
ADA/USDT,5m,1711947900,31-03-2024 22:05,300,1
ADA/USDT,5m,1711948200,31-03-2024 22:10,300,1
ADA/USDT,5m,1711948500,31-03-2024 22:15,300,1
ADA/USDT,5m,1711948800,31-03-2024 22:20,300,1
ADA/USDT,5m,1711949100,31-03-2024 22:25,300,1
ADA/USDT,5m,1711949400,31-03-2024 22:30,300,1
ADA/USDT,5m,1711949700,31-03-2024 22:35,300,1
ADA/USDT,5m,1711950000,31-03-2024 22:40,300,1
ADA/USDT,5m,1711950300,31-03-2024 22:45,300,1
ADA/USDT,5m,1711950600,31-03-2024 22:50,300,1
ADA/USDT,5m,1711950900,31-03-2024 22:55,300,1
ADA/USDT,5m,1711951200,31-03-2024 23:00,300,1
ADA/USDT,5m,1711951500,31-03-2024 23:05,300,1
ADA/USDT,5m,1711951800,31-03-2024 23:10,300,1
ADA/USDT,5m,1711952100,31-03-2024 23:15,300,1
ADA/USDT,5m,1711952400,31-03-2024 23:20,300,1
ADA/USDT,5m,1711952700,31-03-2024 23:25,300,1
ADA/USDT,5m,1711953000,31-03-2024 23:30,300,1
ADA/USDT,5m,1711953300,31-03-2024 23:35,300,1
ADA/USDT,5m,1711953600,31-03-2024 23:40,300,1
ADA/USDT,5m,1711953900,31-03-2024 23:45,300,1
ADA/USDT,5m,1711954200,31-03-2024 23:50,300,1
ADA/USDT,5m,1711954500,31-03-2024 23:55,300,1
ADA/USDT,5m,1711954800,01-04-2024 00:00,300,1
ADA/USDT,5m,1711955100,01-04-2024 00:05,300,1
ADA/USDT,5m,1711955400,01-04-2024 00:10,300,1
ADA/USDT,5m,1711955700,01-04-2024 00:15,300,1
ADA/USDT,5m,1711956000,01-04-2024 00:20,300,1
ADA/USDT,5m,1711956300,01-04-2024 00:25,300,1
ADA/USDT,5m,1711956600,01-04-2024 00:30,300,1
ADA/USDT,5m,1711956900,01-04-2024 00:35,300,1
ADA/USDT,5m,1711957200,01-04-2024 00:40,300,1
ADA/USDT,5m,1711957500,01-04-2024 00:45,300,1
ADA/USDT,5m,1711957800,01-04-2024 00:50,300,1
ADA/USDT,5m,1711958100,01-04-2024 00:55,300,1
ADA/USDT,5m,1711958400,01-04-2024 01:00,300,1
ADA/USDT,5m,1711958700,01-04-2024 01:05,300,1
ADA/USDT,5m,1711959000,01-04-2024 01:10,300,1
ADA/USDT,5m,1711959300,01-04-2024 01:15,300,1
ADA/USDT,5m,1711959600,01-04-2024 01:20,300,1
ADA/USDT,5m,1711959900,01-04-2024 01:25,300,1
ADA/USDT,5m,1711960200,01-04-2024 01:30,300,1
ADA/USDT,5m,1711960500,01-04-2024 01:35,300,1
ADA/USDT,5m,1711960800,01-04-2024 01:40,300,1
ADA/USDT,5m,1711961100,01-04-2024 01:45,300,1
ADA/USDT,5m,1711961400,01-04-2024 01:50,300,1
ADA/USDT,5m,1711961700,01-04-2024 01:55,300,1
ADA/USDT,5m,1711962000,01-04-2024 02:00,300,1
ADA/USDT,5m,1711962300,01-04-2024 02:05,300,1
ADA/USDT,5m,1711962600,01-04-2024 02:10,300,1
ADA/USDT,5m,1711962900,01-04-2024 02:15,300,1
ADA/USDT,5m,1711963200,01-04-2024 02:20,300,1
ADA/USDT,5m,1711963500,01-04-2024 02:25,300,1
ADA/USDT,5m,1711963800,01-04-2024 02:30,300,1
ADA/USDT,5m,1711964100,01-04-2024 02:35,300,1
ADA/USDT,5m,1711964400,01-04-2024 02:40,300,1
ADA/USDT,5m,1711964700,01-04-2024 02:45,300,1
ADA/USDT,5m,1711965000,01-04-2024 02:50,300,1
ADA/USDT,5m,1711965300,01-04-2024 02:55,300,1
ADA/USDT,5m,1711965600,01-04-2024 03:00,300,1
ADA/USDT,5m,1711965900,01-04-2024 03:05,300,1
ADA/USDT,5m,1711966200,01-04-2024 03:10,300,1
ADA/USDT,5m,1711966500,01-04-2024 03:15,300,1
ADA/USDT,5m,1711966800,01-04-2024 03:20,300,1
ADA/USDT,5m,1711967100,01-04-2024 03:25,300,1
ADA/USDT,5m,1711967400,01-04-2024 03:30,300,1
ADA/USDT,5m,1711967700,01-04-2024 03:35,300,1
ADA/USDT,5m,1711968000,01-04-2024 03:40,300,1
ADA/USDT,5m,1711968300,01-04-2024 03:45,300,1
ADA/USDT,5m,1711968600,01-04-2024 03:50,300,1
ADA/USDT,5m,1711968900,01-04-2024 03:55,300,1
ADA/USDT,5m,1711969200,01-04-2024 04:00,300,1
ADA/USDT,5m,1711969500,01-04-2024 04:05,300,1
ADA/USDT,5m,1711969800,01-04-2024 04:10,300,1
ADA/USDT,5m,1711970100,01-04-2024 04:15,300,1
ADA/USDT,5m,1711970400,01-04-2024 04:20,300,1
ADA/USDT,5m,1711970700,01-04-2024 04:25,300,1
ADA/USDT,5m,1711971000,01-04-2024 04:30,300,1
ADA/USDT,5m,1711971300,01-04-2024 04:35,300,1
ADA/USDT,5m,1711971600,01-04-2024 04:40,300,1
ADA/USDT,5m,1711971900,01-04-2024 04:45,300,1
ADA/USDT,5m,1711972200,01-04-2024 04:50,300,1
ADA/USDT,5m,1711972500,01-04-2024 04:55,300,1
ADA/USDT,5m,1711972800,01-04-2024 05:00,300,1
ADA/USDT,5m,1711973100,01-04-2024 05:05,300,1
ADA/USDT,5m,1711973400,01-04-2024 05:10,300,1
ADA/USDT,5m,1711973700,01-04-2024 05:15,300,1
ADA/USDT,5m,1711974000,01-04-2024 05:20,300,1
ADA/USDT,5m,1711974300,01-04-2024 05:25,300,1
ADA/USDT,5m,1711974600,01-04-2024 05:30,300,1
ADA/USDT,5m,1711974900,01-04-2024 05:35,300,1
ADA/USDT,5m,1711975200,01-04-2024 05:40,300,1
ADA/USDT,5m,1711975500,01-04-2024 05:45,300,1
"""


@enforce_types
def test_validate_lake_mock_sql(tmpdir):
    sql_result = pl.read_csv(io.StringIO(csv_string))
    assert isinstance(sql_result, pl.DataFrame)

    st_timestr = "2023-11-02_0:00"
    fin_timestr = "2023-11-07_0:00"

    ppss, _ = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    lake_validate = LakeValidate(ppss)

    # mock pds
    mock_pds = MagicMock()
    mock_pds.query_data.return_value = sql_result
    lake_validate.pds = mock_pds

    result = lake_validate.validate_lake_bronze_predictions_gaps()

    assert mock_pds.query_data.called, "lake_validate did not call pds.query_data()"

    assert result[0] is False
    assert result[1] == "Please review gap validation."
