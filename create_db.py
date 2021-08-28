from app import db
import sqlite3

con = sqlite3.connect(db, uri=True)
cur = con.cursor()

cur.execute("""CREATE TABLE "users" (
	"id" INTEGER NOT NULL UNIQUE, 
	"username"	varchar(255) NOT NULL UNIQUE
	"password"	varchar(255) NOT NULL UNIQUE
	"money"	INTEGER NOT NULL DEFAULT 1000,
	PRIMARY KEY("id" AUTOINCREMENT)
    )""")

con.commit()
con.close()

