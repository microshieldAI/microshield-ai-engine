import sqlite3

def inspect(label, path):
    con = sqlite3.connect(path)
    cur = con.cursor()
    total = cur.execute("SELECT COUNT(*) FROM security_events").fetchone()[0]
    nulls = cur.execute(
        "SELECT COUNT(*) FROM security_events WHERE tenant_id IS NULL OR tenant_id = '' OR user_id IS NULL OR user_id = ''"
    ).fetchone()[0]
    latest = cur.execute(
        "SELECT id, tenant_id, user_id, route, source, blocked FROM security_events ORDER BY id DESC LIMIT 5"
    ).fetchall()
    con.close()
    print(label, "total:", total)
    print(label, "null tenant/user:", nulls)
    print(label, "latest:", latest)

inspect("demo", r"c:\Users\mayan\microshield-ai-engine\demo-vulnerable-app\data\microshield_events.sqlite")
inspect("npm", r"c:\Users\mayan\microshield-npm\data\microshield_events.sqlite")
