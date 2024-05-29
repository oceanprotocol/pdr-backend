from required_sqletl_predictions import _process_predictions_query
from required_sqletl_payouts.py import _process_payouts_query
from required_sqletl_bronze_predictions.py import _process_bronze_predictions_query

# We shouldn't have to adjust anything here...
def do_etl(self):
    """
    @description
        Run the ETL process
    """

    st_ts = time.time_ns() / 1e9
    logger.info("do_etl - Start ETL.")

    try:
        # Drop any build tables if they already exist
        self._drop_temp_sql_tables()
        logger.info("do_etl - Drop build tables.")

        # Sync data
        self.gql_data_factory.get_gql_tables()
        logger.info("do_etl - Synced data. Start bronze_step.")

        self.do_bronze_queries() 

        end_ts = time.time_ns() / 1e9
        logger.info("do_etl - Completed bronze_step in %s sec.", end_ts - st_ts)

        # Move data to live at end of ETL
        self._deploy_build_to_live()
        
        logger.info(
            "do_etl - Moved build tables to permanent tables. ETL Complete."
        )
    except Exception as e:
        logger.info("Error when executing ETL: %s", e)


_ETL_REGISTERED_QUERIES = [
    _process_predictions_query,
    _process_payouts_query,
    _process_bronze_predictions_query
]

def do_bronze_queries(self):
        """
        @description
            Update bronze tables
        """
        logger.info("update_bronze_pdr - Update bronze tables.")

        # st_timestamp and fin_timestamp should be valid UnixTimeMS
        st_timestamp, fin_timestamp = self._calc_bronze_start_end_ts()

        for etl_query in _ETL_REGISTERED_QUERIES:
            etl_query(
                path=self.ppss.lake_ss.lake_dir,
                st_ms=st_timestamp,
                fin_ms=fin_timestamp,
            )

            logger.info(
                "update_bronze_pdr - completed query %s",
                etl_query,
            )

def _deploy_build_to_live():
    """
    @description
        Merge the ETL tables
    """
    db = DuckDBDataStore(ppss.lake_ss.lake_dir, read_only=False)
    
    etl_tables = ["bronze_predictions"]
    for table_name in etl_tables:
        permanent_table = MainTable(table_name)
        temp_table = TempTable(table_name)
        update_table = UpdateTable(table_name)
        if db.table_exists(update_table.fullname):
            # Insert new records into live tables
            db.move_table_data(temp_table, permanent_table)
            
            # drop all records that were updated
            db.drop_records_from_table_by_ids(
                drop_tabe=permanent_table,
                ids=update_table.ids
            )

            # Finally, insert the updated records into live table
            db.move_table_data(update_table, permanent_table)

            # Drop the update table 
            db.drop_table(update_table.fullname)

    raw_tables = ["pdr_predictions", "pdr_payouts"]
    for table_name in raw_tables:
        db.drop_table(update_table.fullname)
