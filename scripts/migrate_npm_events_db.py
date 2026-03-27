import sqlite3
p = r"c:\Users\mayan\microshield-npm\data\microshield_events.sqlite"
con = sqlite3.connect(p)
cur = con.cursor()
cols = [r[1].lower() for r in cur.execute("PRAGMA table_info(security_events)").fetchall()]
if "tenant_id" not in cols:
    cur.execute("ALTER TABLE security_events ADD COLUMN tenant_id TEXT")
if "user_id" not in cols:
    cur.execute("ALTER TABLE security_events ADD COLUMN user_id TEXT")
cur.execute("UPDATE security_events SET tenant_id='public' WHERE tenant_id IS NULL OR tenant_id='' ")
cur.execute("UPDATE security_events SET user_id='anonymous' WHERE user_id IS NULL OR user_id='' ")
con.commit()
print(cur.execute("SELECT COUNT(*) FROM security_events").fetchone()[0])
print(cur.execute("SELECT COUNT(*) FROM security_events WHERE tenant_id IS NULL OR tenant_id='' OR user_id IS NULL OR user_id='' ").fetchone()[0])
print(cur.execute("SELECT id,tenant_id,user_id,route,source FROM security_events ORDER BY id DESC LIMIT 5").fetchall())
con.close()
