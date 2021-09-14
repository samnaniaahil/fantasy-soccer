import sqlite3

db = "soccer.db"

con = sqlite3.connect(db)
cur = con.cursor()


# Create tables
cur.execute(
  """CREATE TABLE "users" (
  "id"	INTEGER NOT NULL UNIQUE,
  "username"	varchar(255) NOT NULL UNIQUE,
  "password"	varchar(255) NOT NULL UNIQUE,
  "money"	INTEGER NOT NULL DEFAULT 1000,
  PRIMARY KEY("id" AUTOINCREMENT)
  )"""
)

cur.execute(
  """CREATE TABLE "team" (
  "id"	INTEGER NOT NULL UNIQUE,
  "user_id"	INTEGER NOT NULL,
  "name"	varchar(255) NOT NULL,
  "web_name"	varchar(255) NOT NULL,
  "position"	varchar(255) NOT NULL,
  "team"	varchar(255) NOT NULL,
  "now_cost"	INTEGER NOT NULL,
  "form"	NUMERIC NOT NULL,
  "points"	INTEGER NOT NULL,
  PRIMARY KEY("id" AUTOINCREMENT),
  FOREIGN KEY("user_id") REFERENCES "users"("id")
  )"""
)

cur.execute(
  """CREATE TABLE searches (
  "id"	INTEGER NOT NULL UNIQUE,
  "user_id"	INTEGER NOT NULL,
  "name"	varchar(255) NOT NULL,
  "web_name"	varchar(255) NOT NULL,
  "position"	varchar(255) NOT NULL,
  "team"	varchar(255) NOT NULL,
  "now_cost"	INTEGER NOT NULL,
  "form"	NUMERIC NOT NULL,
  "points"	INTEGER NOT NULL,
  PRIMARY KEY("id" AUTOINCREMENT),
  FOREIGN KEY("user_id") REFERENCES "users"("id")
  )"""
)

cur.execute(
  """CREATE TABLE "transfers" (
  "id"	INTEGER NOT NULL UNIQUE,
  "user_id"	INTEGER NOT NULL,
  "name"	varchar(255) NOT NULL,
  "position"	varchar(255) NOT NULL,
  "team"	varchar(255) NOT NULL,
  "now_cost"	INTEGER NOT NULL,
  "time"	varchar(255) NOT NULL,
  "type"	varchar(255) NOT NULL,
  PRIMARY KEY("id" AUTOINCREMENT),
  FOREIGN KEY("user_id") REFERENCES "users"("id")
  )"""
)


con.commit()
con.close()