# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# <div class='alert alert-block alert-info'>
# <b>Note:</b> Py3 env
# </div>

# +
import sys
import typing
import yaml
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import matplotlib.pyplot as plt
import seaborn as sns
import sqlalchemy

from codebook import clean, EDA, style

# %load_ext sql

# +
# %load_ext autoreload
# %autoreload 2

# %matplotlib inline
plt.style.use('raph-base')

from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = 'all'

pd.options.display.float_format = '{:,.2f}'.format
pd.set_option('display.max_columns', 30)
pd.set_option('display.expand_frame_repr', False)
pd.set_option('max_colwidth', 800)

pio.templates.default = 'simple_white'
px.defaults.color_continuous_scale = style.plasma_long
px.defaults.color_discrete_sequence = style.purple_yellow_grey_long
px.defaults.width = 1000
px.defaults.height = 500

np.random.seed(666)
# -

print(sys.executable)
print(sys.version)
print(f"Pandas {pd.__version__}")

# ## Connect to PostgresDB

# +
config_file_path = Path.cwd().parent.parent / "config.yaml"

with open(config_file_path, "r") as f:
    yaml_content = yaml.safe_load(f)

pg = yaml_content["POSTGRES"]
pg_conn_str = f'postgresql://{pg["USER"]}:{pg["PASSWORD"]}@{pg["HOST"]}:{pg["PORT"]}/{pg["DATABASE"]}'

engine_pg = sqlalchemy.create_engine(pg_conn_str)
engine_pg


# +
# Connect to ipython-sql

# %sql $pg_conn_str
# -

# ## TrxCredit-History

# +
query = """
    SELECT 
        tc.*
    FROM 
        public.discobase_trxcredit tc
        -- LEFT JOIN public.discobase_record r ON r.Id = tc.record_id
    WHERE tc.trx_date >= (CURRENT_DATE -INTERVAL '6 MONTH')
    
"""

trx_df_raw = pd.read_sql(query, engine_pg)
# -

trx_df_raw.info()
trx_df_raw.head(2)

EDA.display_value_counts(trx_df_raw["trx_type"])

# +
df_plot = trx_df_raw.sort_values(["trx_date", "trx_type"]).copy()
df_plot["trx_date"] = pd.to_datetime(df_plot["trx_date"], format="%Y-%m-%d")
# df_plot["dummy_group"] = 1


px.scatter(
    data_frame=df_plot,
    x="trx_date",
    y="credit_saldo",
#     line_group="dummy_group",
    color="trx_type",
)

# +
color_dict = {
    "Addition": "green",
    "Removal": "red",
    "Purchase": "blue"
}

fig = go.Figure(
    data=go.Scatter(
        x=df_plot["trx_date"], 
        y=df_plot["credit_saldo"],
        #         text = df_plot["trx_type"],

        mode="lines",
        line = {"color": "lightgray"},
        showlegend=False
    )
)

fig.update_layout(
    title="Credit Saldo Movement, past 6 months",
    xaxis_title="Credit Saldo",
    yaxis_title="Date",
    legend_title="Trx Types",
#     font={
#         family: "Courier New, monospace",
#         size: 18,
#         color: "RebeccaPurple"
#     }
)
    
    
for trx_type in df_plot["trx_type"].unique():
    df_plot_type = df_plot[df_plot["trx_type"] == trx_type]

    fig.add_trace(
        go.Scatter(
            x=df_plot_type["trx_date"],
            y=df_plot_type["credit_saldo"],
            mode = 'markers',
            marker = {"color": color_dict[trx_type]},
            name = trx_type,
            customdata = df_plot_type[["id", "record_id", "trx_type"]],
            hovertemplate =
                "%{x}<br>"+
                'Saldo: %{y}<br>'+
                'Trx Id: %{customdata[0]}<br>'+
                'Record Id: %{customdata[1]}<br>'+
                "<extra>%{customdata[2]}</extra>",
        )
    )
# -

fig.show()

np.dstack((df_plot["id"], df_plot["record_id"], df_plot["trx_type"]))

z1, z2, z3 = np.random.random((3, 7, 7))
np.dstack((z1, z3))


