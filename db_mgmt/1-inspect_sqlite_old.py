# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.8
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # Intro
#
# First step in this project is to migrate the DB from Sqlite to PostgreSQL. This is not a 1:1 migration, as there will be some tweaks to the schema. 
#
# **Goal of this notebook**: To inspect the actual data in the Sqlite DB and to list the changes to be made.

# +
import sys
import yaml
from pathlib import Path

import pandas as pd

# %load_ext sql
# -

print(sys.executable)
print(sys.version)
print(f'Pandas {pd.__version__}')

# +
# Create connectin string for sqlalchemy or ipython-sql

config_file_path = Path.cwd().parent / "config.yaml"

with open(config_file_path, "r") as f:
    yaml_content = yaml.safe_load(f)

sqlite_path = yaml_content["SQLITE_OLD"]["FULL_PATH"]
sqlite_conn_str = f"sqlite:///{sqlite_path}"

# +
# Connect to ipython-sql

# %sql $sqlite_conn_str
# -

# ## Inspect MetaData

query = """
    SELECT 
      m.name AS table_name, 
      p.name AS column_name,
      p.type AS data_type,
      p.'notnull' AS null_constraint,
      p.dflt_value AS default_value,
      p.pk AS primary_key
    FROM 
      sqlite_master AS m
    JOIN 
      pragma_table_info(m.name) AS p
    ORDER BY 
      m.name, 
      p.cid;
"""


# %sql $query

# **Schema-Changes:**
#
# - Drop genre-label-link
# - Drop artist-label-link
# - Drop artist-genre-link
#
# Rating
#  - ...
#  
# Credit_Trx
# - ...
#
# Record
# - vinyl_color = color
# - rating is foreign key
#
# Also I will have to complete all country fields for artists

# +
# "Connect" to sqlalchemy 

engine = sqlalchemy.create_engine(sqlite_conn_str)

engine
# -

# ## Query DB
#
# I show 5 of the possible ways to query the DB
# 1. using ipython-sql
# 2. using sqlite functionality 'raw'
# 3. using my query_read wrapper from sqlite_utils
# 4. using pandas with sqlite connection
# 5. using pandas with sqlalchemy engine (sqlalchemy core, but not SQL Expression Language)
# 6. (using sqlalchemy SQL Expression Language)
# 7. (using sqlalchemy ORM)
#

query = (
    """
    SELECT * 
      FROM records 
      -- WHERE title = 'Only Self'
      LIMIT 3
    ;"""
)

# +
# 1. Read using sqlite connection
# Returns a cursor containing the data tuples

# %sql $query

# +
# 2. Read using sqlite connection
# Returns a cursor containing the data tuples

with conn:
    data = conn.execute(query)
    for row in data:
        print(row)

# +
# 3. Read using cursor and my utils function
# Returns a list of tuples

# print(sqlite_utils.query_read(query, cur))

# +
# 4. Read with pandas, using sqlite connection
# Returns a dataframe

pd.read_sql(query, conn, index_col="record_id")

# +
# 5. Read with pandas, using sqlalchemy engine
# Returns a dataframe

pd.read_sql(query, conn, index_col="record_id")
# -

# ## Inspect sqlite Metadata

query = ("""
SELECT 
  m.name AS table_name, 
  p.name AS column_name,
  p.type AS data_type,
  p.'notnull' AS null_constraint,
  p.dflt_value AS default_value,
  p.pk AS primary_key
FROM 
  sqlite_master AS m
JOIN 
  pragma_table_info(m.name) AS p
ORDER BY 
  m.name, 
  p.cid
;"""
)

# %sql $query

conn.close()
