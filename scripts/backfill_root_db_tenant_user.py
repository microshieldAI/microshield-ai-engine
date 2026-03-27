import sqlite3
p = r"c:\Users\mayan\microshield-ai-engine\data\microshield_events.sqlite"
con = sqlite3.connect(p)
cur = con.cursor()
cur.execute("UPDATE security_events SET tenant_id='public' WHERE tenant_id IS NULL OR tenant_id='' ")
cur.execute("UPDATE security_events SET user_id='anonymous' WHERE user_id IS NULL OR user_id='' ")
con.commit()
print("total", cur.execute("SELECT COUNT(*) FROM security_events").fetchone()[0])
print("nulls", cur.execute("SELECT COUNT(*) FROM security_events WHERE tenant_id IS NULL OR tenant_id='' OR user_id IS NULL OR user_id='' ").fetchone()[0])
print(cur.execute("SELECT id, tenant_id, user_id, route, source FROM security_events ORDER BY id DESC LIMIT 5").fetchall())
con.close()
