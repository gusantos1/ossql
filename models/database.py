import sqlite3
import duckdb
import pandas as pd
from interface import SqlDatabaseAdapter


class SQLiteAdapter(SqlDatabaseAdapter):
    def __init__(self):
        self.con = sqlite3.connect(':memory:', check_same_thread=False)

    def create_table(self, file: str, table_name: str):
        df = pd.read_csv(file)
        df.to_sql(table_name, self.con, index=False, if_exists='replace')

    def select_query(self, query: str) -> pd.DataFrame:
        result = pd.read_sql_query(query, self.con)
        return result

class DuckDBAdapter(SqlDatabaseAdapter):
    def __init__(self):
        self.con = duckdb.connect(database=':memory:', read_only=False)

    def create_table(self, file: str, table_name: str):
        df = pd.read_csv(file)
        self.con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")

    def select_query(self, query: str) -> pd.DataFrame:
        result = self.con.execute(query).fetchdf()
        return result