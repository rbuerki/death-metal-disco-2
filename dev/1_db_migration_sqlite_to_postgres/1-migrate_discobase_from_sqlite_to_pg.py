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

# # What
#
# First step in this project is to migrate the DB from Sqlite to PostgreSQL. This is not a 1:1 migration, as there will be some tweaks to the schema.
#
# I used two connections and sqlalchemy/pandas for the transfer (and the data manipulation), code is messy, but it worked well.
#
# Addendum: I had to reset the indexing sequence to max(id)+1 in the db, because Django wanted to start with id 1 ...
# (see [here](https://stackoverflow.com/a/118402/13797028))
# +
import sys
from datetime import datetime
import yaml
from pathlib import Path

import numpy as np
import pandas as pd
import sqlalchemy

# %load_ext sql
# -

print(sys.executable)
print(sys.version)
print(f"Pandas {pd.__version__}")

# +
# Create connectin string for sqlalchemy or ipython-sql

config_file_path = Path.cwd().parent.parent / "config.yaml"

with open(config_file_path, "r") as f:
    yaml_content = yaml.safe_load(f)

sqlite_path = yaml_content["SQLITE_OLD"]["FULL_PATH"]
sqlite_conn_str = f"sqlite:///{sqlite_path}"
# -

# Create connectin string for sqlalchemy or ipython-sql
sqlite_conn_str = f"sqlite:///{'DiscoBase_migration.db'}"

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
# Drop link tables
# - Drop genre-label-link
# - Drop artist-label-link
# - Drop artist-genre-link
#
# Clean RecordFormat
# - 2xLP is not used and will no longer be used, insert the rest in the db
# - Merge 12"(id=1) and MLP(id=7)
#
# Artist
# - fill all country fields, clean them
#
# Countries
# - create new table, with codes
#
# Credit_Trx
# - apply some naming changes and copy one-to-one
#
# Record
# - vinyl_color = color
# - ratings have to be reduced by -5
# - credit_value is new field -> how to befill?
# - num and lim have to be integrated into remarks
# - set format_id 1 to format_id 7
#

# ## Make changes
#
# ### Drop Link Tables

drop_query = """
    DROP TABLE genre_label_link;
    DROP TABLE artist_label_link;
    DROP TABLE artist_genre_link;
"""

# %sql $drop_query

# ### Clean RecordFormat

format_query = """
    UPDATE records
    SET format_id = 7 WHERE format_id = 1;
    
    DELETE FROM formats WHERE format_id = 1;
"""

# %sql $format_query

# ### Clean Artists (countries)

distinct_country_query = "SELECT DISTINCT artist_country FROM artists"

# distinct_countries = %sql $distinct_country_query
distinct_countries = [a for (a,) in distinct_countries]

# +
# Load a full country list for a) check of correct names, b) country_codes

full_countries = pd.read_csv("country_list.csv")
full_countries.head()

all_countries = full_countries["Name"].to_list()
# -

set(distinct_countries) - set(all_countries)

artist_query = """
UPDATE artists
SET artist_country = 'United States' WHERE artist_id in (176, 179, 220);
UPDATE artists
SET artist_country = 'Poland' WHERE artist_id = 175;
UPDATE artists
SET artist_country = 'Australia' WHERE artist_id = 180;
UPDATE artists
SET artist_country = 'United Kingdom' WHERE artist_country in ('England', 'Scotland', 'UK');
UPDATE artists
SET artist_country = 'United States' WHERE artist_country = 'USA';
"""

# %sql $artist_query

# ### Create New Country Table
#

df_countries = pd.DataFrame(distinct_countries, columns=["country_name"])
df_countries = pd.merge(
    df_countries,
    full_countries,
    how="left",
    left_on="country_name",
    right_on="Name",
    validate="one_to_one",
)
df_countries.drop(["Name"], axis=1, inplace=True)
df_countries.fillna("XX", inplace=True)
df_countries = df_countries.reset_index()
df_countries.columns = ["id", "country_name", "country_code"]
df_countries["id"] = df_countries["id"] + 1

assert len(df_countries) == len(distinct_countries)
df_countries


# "Connect" to sqlalchemy
engine = sqlalchemy.create_engine(sqlite_conn_str)
engine

df_countries.to_sql(
    "countries", engine, index=False, index_label="pk", if_exists="replace"
)

# ### Labels
#
# Many records have a placehoder label "NA", I will just leave that right now

# %sql SELECT * FROM labels LIMIT 2

# +
label_query = """
    SELECT 
        r.record_id,
        r.title
    FROM records r
        JOIN record_label_link l on l.record_id = r.record_id
    WHERE label_id = 1
"""

label_query_2 = """
    SELECT
        label_name
    FROM labels l
        JOIN record_label_link ll on l.label_id = ll.label_id
    WHERE record_id = 1
"""
# -

# %sql $label_query_2

# ### CreditTrx

# %sql SELECT * FROM credit_trx LIMIT 10

trx_query = """
    ALTER TABLE credit_trx
    RENAME COLUMN credit_trx_date TO trx_date;
        ALTER TABLE credit_trx
    RENAME COLUMN credit_trx_type TO trx_type;
        ALTER TABLE credit_trx
    RENAME COLUMN credit_value TO trx_value;
"""

# %sql $trx_query

# ### Change records
#

df_records = pd.read_sql(
    "SELECT * FROM records",
    engine,
    coerce_float=True,
    parse_dates=["purchase_date", "created_at", "updated_at"],
)
df_records.head()

df_records = df_records.replace("None", "")
df_records[["lim_edition", "number", "remarks"]] = df_records[
    ["lim_edition", "number", "remarks"]
].fillna("")


# #### Merge number, lim_edition and remarks

# +
def numbered(num, lim):
    if len(num) > 0:
        return f"numbered: {num}/{lim}"
    else:
        return ""


def limited(num, lim):
    if len(num) > 0:
        return num
    elif lim == "lim":
        return " limited: unknown"
    elif (len(lim) > 0) and (lim != "lim"):
        return f" limited: {lim}"
    else:
        return ""


def remarks(lim, rem):
    if (len(rem) > 0) and (len(lim) > 0):
        return lim + ", " + rem
    elif (len(rem) > 0) and not (len(lim) > 0):
        return rem
    elif (len(lim) > 0) and not (len(rem) > 0):
        return lim
    else:
        return ""


# +
df_1 = df_records.copy()
df_1["number"] = df_1.apply(lambda x: numbered(x["number"], x["lim_edition"]), axis=1)
df_1["lim_edition"] = df_1.apply(
    lambda x: limited(x["number"], x["lim_edition"]), axis=1
)

df_1[df_1["lim_edition"] != ""].sample(5).T
# -

df_2 = df_1.copy()
df_2["remarks"] = df_2.apply(lambda x: remarks(x["lim_edition"], x["remarks"]), axis=1)

df_2[df_2["remarks"] != ""]["remarks"].sample(10)
# df_2["remarks"].str.len().max()

df_2.info()

# +
df_3 = df_2.drop(["number", "lim_edition"], axis=1).copy()

df_3 = df_3.rename(columns={"vinyl_color": "color", "format_id": "record_format_id"})

df_3["rating"] = df_3["rating"].replace("", 0)
df_3["rating"] = df_3["rating"].fillna(0).astype(int)
df_3["rating"] = df_3["rating"] - 5
df_3["rating"] = np.where(df_3["rating"] < 0, np.nan, df_3["rating"])
df_3["rating"] = np.where(df_3["rating"] == 0, 1, df_3["rating"])

df_3["review"] = ""

df_3["credit_value"] = np.where(
    (
        df_3["record_format_id"].isin([3, 4, 5, 7, 8, 9, 10])
        & (df_3["is_active"] == True)
    ),
    1,
    0,
)

for col in ["is_active", "is_digitized"]:
    df_3[col] = df_3[col].map({1: True, 0: False})


df_3["updated_at"] = datetime.now()
# -

df_3.sample(4).T
# df_3.info()

# ## Write Data to new PostgresDB

# +
config_file_path = Path.cwd().parent.parent / "config.yaml"

with open(config_file_path, "r") as f:
    yaml_content = yaml.safe_load(f)

pg = yaml_content["POSTGRES"]
pg_conn_str = f'postgresql://{pg["USER"]}:{pg["PASSWORD"]}@{pg["HOST"]}:{pg["PORT"]}/{pg["DATABASE"]}'

engine_pg = sqlalchemy.create_engine(pg_conn_str)
engine_pg


# -


def migrate_data(engine_pg, engine_sqlite, table_pg, table_sqlite, cols_to_rename):
    # Read sqlite into df
    df = pd.read_sql(f"SELECT * FROM {table_sqlite}", engine_sqlite)

    # Replace updated at with actual timestamp
    df["updated_at"] = datetime.now()
    df = df.rename(columns=cols_to_rename)

    # Write into pg_table
    df.to_sql(
        table_pg,
        engine_pg,
        index=False,
        index_label="id",  # NOTE: you have to rename sqlite_index to "id"
        if_exists="append",
    )


# ### Write Countries to db

# +
countries = pd.read_sql("SELECT * FROM countries", engine)

countries["created_at"] = datetime.now()
countries["updated_at"] = datetime.now()

countries.to_sql(
    "discobase_country", engine_pg, index=False, index_label="id", if_exists="append"
)
# -

# ### Write Genres to db

migrate_data(
    engine_pg=engine_pg,
    engine_sqlite=engine,
    table_pg="discobase_genre",
    table_sqlite="genres",
    cols_to_rename={"genre_id": "id"},
)

# %sql SELECT * FROM genres LIMIT 2

pd.read_sql("SELECT * FROM discobase_genre", engine_pg)

# ### Write Formats to db

# +

migrate_data(
    engine_pg=engine_pg,
    engine_sqlite=engine,
    table_pg="discobase_recordformat",
    table_sqlite="formats",
    cols_to_rename={"format_id": "id"},
)

# -

pd.read_sql("SELECT * FROM discobase_recordformat", engine_pg)

# ### Write Artists to db
#
# Here we need to map names to ids first

cmap = dict(zip(countries["country_name"], countries["id"]))
list(cmap.items())[:3]

# +
artists = pd.read_sql("SELECT * FROM artists", engine)

artists["artist_country"] = artists["artist_country"].map(cmap)

artists.head(3)

# +
# Replace updated at with actual timestamp
artists["updated_at"] = datetime.now()
artists = artists.rename(columns={"artist_country": "country_id", "artist_id": "id"})

# Write into pg_table
artists.to_sql(
    "discobase_artist",
    engine_pg,
    index=False,
    index_label="id",  # NOTE: you have to rename sqlite_index to "id"
    if_exists="append",
)
# -

# ### Write Labels to db

migrate_data(
    engine_pg=engine_pg,
    engine_sqlite=engine,
    table_pg="discobase_label",
    table_sqlite="labels",
    cols_to_rename={"label_id": "id"},
)

# %sql SELECT * FROM labels

# ### Write Records to db

pd.read_sql("SELECT * FROM discobase_record", engine_pg)

df_3.head(2).T

# +
# Replace updated at with actual timestamp
df_3["updated_at"] = datetime.now()
df_3 = df_3.rename(columns={"record_id": "id"})

# Write into pg_table
df_3.to_sql(
    "discobase_record",
    engine_pg,
    index=False,
    index_label="id",  # NOTE: you have to rename sqlite_index to "id"
    if_exists="append",
)

# +
df_3[df_3["title"] == "Split"]

df_3.loc[314, "title"] = "Crime And Punishment"
# -

df_3.iloc[314]

# ### Write TrxCredit to db

migrate_data(
    engine_pg=engine_pg,
    engine_sqlite=engine,
    table_pg="discobase_trxcredit",
    table_sqlite="credit_trx",
    cols_to_rename={"credit_trx_id": "id"},
)

pd.read_sql("SELECT * FROM discobase_trxcredit", engine_pg)

# %sql SELECT * FROM credit_trx LIMIT 5

# ### Write links to db

pd.read_sql("SELECT * FROM discobase_record_artists", engine_pg)


# %sql SELECT * FROM artist_record_link LIMIT 5


def migrate_data_without_id(
    engine_pg, engine_sqlite, table_pg, table_sqlite, cols_to_rename
):
    # Read sqlite into df
    df = pd.read_sql(f"SELECT * FROM {table_sqlite}", engine_sqlite)
    df = df.reset_index()
    df["index"] = df["index"] + 1

    # Replace updated at with actual timestamp
    df = df.rename(columns=cols_to_rename)

    # Write into pg_table
    df.to_sql(
        table_pg,
        engine_pg,
        index=False,
        index_label="id",  # NOTE: you have to rename sqlite_index to "id"
        if_exists="append",
    )


migrate_data_without_id(
    engine_pg=engine_pg,
    engine_sqlite=engine,
    table_pg="discobase_record_artists",
    table_sqlite="artist_record_link",
    cols_to_rename={"index": "id"},
)

# + active=""
# migrate_data_without_id(
#     engine_pg=engine_pg,
#     engine_sqlite=engine,
#     table_pg="discobase_record_labels",
#     table_sqlite="record_label_link",
#     cols_to_rename={"index": "id"}
# )
