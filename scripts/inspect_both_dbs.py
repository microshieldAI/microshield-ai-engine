import sqlite3

def inspect(path):
    con = sqlite3.connect(path)
    cur = con.cursor()
    cols = [r[1] for r in cur.execute("PRAGMA table_info(security_events)").fetchall()]
    total = cur.execute("SELECT COUNT(*) FROM security_events").fetchone()[0]
    if "tenant_id" in cols and "user_id" in cols:
        nulls = cur.execute("SELECT COUNT(*) FROM security_events WHERE tenant_id IS NULL OR tenant_id='' OR user_id IS NULL OR user_id=''").fetchone()[0]
        latest = cur.execute("SELECT id, tenant_id, user_id, route, source, blocked FROM security_events ORDER BY id DESC LIMIT 5").fetchall()
    else:
        nulls = "n/a"
        latest = cur.execute("SELECT id, route, source, blocked FROM security_events ORDER BY id DESC LIMIT 5").fetchall()
    con.close()
    print("DB:", path)
    print("columns:", cols)
    print("total:", total)
    print("nulls:", nulls)
    print("latest:", latest)
    print("---")

inspect(r"c:\Users\mayan\microshield-ai-engine\data\microshield_events.sqlite")
inspect(r"c:\Users\mayan\microshield-ai-engine\demo-vulnerable-app\data\microshield_events.sqlite")
