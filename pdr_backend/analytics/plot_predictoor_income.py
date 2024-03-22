import asyncio

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
import polars as pl
import streamlit as st
from polars import DataFrame
import matplotlib.pyplot as plt
#from matplotlib.figure import Figure
from matplotlib.axes import Axes
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.lake.etl import ETL
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.table_silver_pdr_predictions import (
    silver_pdr_predictions_table_name,
)


def load_data(user_addrs, contract_addrs):
    with st.spinner("Loading data..."):
        ppss = PPSS(
            yaml_filename="ppss.yaml",
            network="sapphire-mainnet",
            nested_override_args=None,
        )
        gql_data_factory = GQLDataFactory(ppss)
        etl = ETL(ppss, gql_data_factory)
        etl.do_etl()

        user_addrs = ["0x04a5e9f565dfa83c77581d1022b9ef041f55210b" ,"0xac82646af513586dbe301415e6df32ec71d95f04","0xfbbac3a1d6782195399fe9070c8b170e65c803c5"]
        contract_addrs = ["0x30f1c55e72fe105e4a1fbecdff3145fc14177695", "0xbe09c6e3f2341a79f74898b8d68c4b5818a2d434", "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553"]

        silver_predictions_table_df = etl.tables[silver_pdr_predictions_table_name].df
        #print(silver_predictions_table_df["user"][0], silver_predictions_table_df["contract"][0])

        #filter by user and contract addresses
        user_contract_predictions_df = silver_predictions_table_df.filter(
            (silver_predictions_table_df["user"].is_in(user_addrs))
            & (silver_predictions_table_df["contract"].is_in(contract_addrs))
        )

        fileds_to_plot_df = user_contract_predictions_df.select(
            "slot",
            "sum_revenue",
            "sum_revenue_df",
            "sum_revenue_user",
            "sum_revenue_stake",
            "stake",
            "payout",
        )

        #sum values per slot
        fileds_to_plot_df = fileds_to_plot_df.group_by('slot').agg(
            pl.col('sum_revenue').sum().alias('revenue'),
            pl.col('sum_revenue_df').sum().alias('revenue_df'),
            pl.col('sum_revenue_user').sum().alias('revenue_user'),
            pl.col('sum_revenue_stake').sum().alias('revenue_stake'),
            pl.col('stake').sum().alias('sum_stake'),
            pl.col('payout').sum().alias('sum_payout')
        )

        #sort by slot
        fileds_to_plot_df = fileds_to_plot_df.sort("slot")

        return fileds_to_plot_df

def plot_revenue_data(df:DataFrame, ax:Axes):
    # st.line_chart(df.set_index('slot'))
    df = df.to_pandas()
    ax[0].set_title("Revenues")
    ax[0].plot(df["slot"], df["revenue"], label="Revenue")
    ax[0].plot(df["slot"], df["revenue_df"], label="Revenue DF")
    ax[0].plot(df["slot"], df["revenue_user"], label="Revenue Subscription")
    ax[0].plot(df["slot"], df["revenue_stake"], label="Revenue Stake")
    # ax.set_xticks(df['slot'])
    # ax.set_xticklabels(df['slot'], rotation=45)

    ax[0].set_xlabel("Slot")
    ax[0].set_ylabel("OCEAN")
    ax[0].legend()

def plot_income_data(df:DataFrame, ax:Axes):
    df = df.with_columns([
        (pl.col("revenue_df") + pl.col("revenue_user") + pl.col("revenue_stake")).alias("gross_income")
    ])
    df = df.to_pandas()
    ax.set_title("Income")
    ax.plot(df["slot"], df["revenue"], label="Net income")
    ax.plot(df["slot"], df["gross_income"], label="Gross income")
    # ax.set_xticks(df['slot'])
    # ax.set_xticklabels(df['slot'], rotation=45)

    ax.set_xlabel("Slot")
    ax.set_ylabel("OCEAN")
    ax.legend()

def main():
    # Set Streamlit app width to page width
    st.set_page_config(layout="wide")

    st.title("Revenue Over Time")

    # Add inputs
    user_address = st.text_input(
        "User Address", "0x04a5e9f565dfa83c77581d1022b9ef041f55210b"
    )
    contract_address = st.text_input(
        "Contract Address", "0x30f1c55e72fe105e4a1fbecdff3145fc14177695"
    )

    # Load data
    df = load_data(user_address, contract_address)

    # Plot data
    fig, ax = plt.subplots(1,1)
    #plot_revenue_data(df, ax)
    plot_income_data(df, ax)

    # Show plot
    st.pyplot(fig)

    # Show data
    #st.write("Raw Data:")
    #st.write(df)


if __name__ == "__main__":
    main()
