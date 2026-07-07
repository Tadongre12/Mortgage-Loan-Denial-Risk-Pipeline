import duckdb
import os

con = duckdb.connect("data/hmda.duckdb")

with open("sql/01_clean.sql", "r") as f:
    sql = f.read()

con.execute(sql)
print("01 loaded!")

with open("sql/02_features.sql", "r") as f:
    sql = f.read()

con.execute(sql)
print("02 loaded!")


with open("sql/03_join_fred.sql", "r") as f:
    sql = f.read()

con.execute(sql)
print("03 loaded!")

con.close()