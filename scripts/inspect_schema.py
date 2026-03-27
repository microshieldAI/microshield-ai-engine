import sqlite3
p = r"c:\Users\mayan\microshield-npm\data\microshield_events.sqlite"
con = sqlite3.connect(p)
cur = con.cursor()
print(cur.execute("PRAGMA table_info(security_events)").fetchall())
con.close()
