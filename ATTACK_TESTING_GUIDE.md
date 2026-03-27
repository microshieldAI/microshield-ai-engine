# MicroShield Attack Testing Guide

## Overview
This guide covers all attacks you'll perform against your vulnerable app at `http://127.0.0.1:4100`. Attacks are categorized by:
1. **Detection Method**: Static Rules (immediate 403) vs AI-based (behavioral detection)
2. **Execution Type**: Manual (UI/console) vs Bot-based (sqlmap/gobuster/hydra)
3. **Expected Outcome**: What you'll see in dashboard

---

## SECTION 1: MANUAL ATTACKS (Static Rule Detection)

These attacks trigger **instant 403 Forbidden** responses due to pattern matching in static rules.

### Attack 1.1: XSS (Cross-Site Scripting) - Static Rule
**Endpoint**: `POST http://127.0.0.1:4100/api/comment`
**Detection**: Static rule (XSS_PATTERN)
**Why It's Blocked Instantly**: Contains `<img src=x onerror=` which matches XSS regex pattern

**Manual Steps:**
1. Open browser DevTools Console on http://127.0.0.1:4100
2. Execute:
```javascript
fetch('/api/comment', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ comment: '<img src=x onerror=alert(1)>' })
})
.then(r => r.text())
.then(t => console.log(t))
```

Or use the **Comment Form** on the vulnerable app UI:
- In "Comments" section, paste: `<img src=x onerror=alert(1)>`
- Click Send → **Expected: 403 Forbidden**

**Dashboard Check:**
- Go to http://127.0.0.1:5174/api/observability/events?limit=1
- Look for: `source: STATIC_RULE`, `rule_id: XSS_PATTERN`, `blocked: 1`

**Other XSS Payloads to Try:**
- `<svg onload=fetch(1)>`
- `<iframe src="javascript:alert(1)">`
- `"><script>alert(1)</script>`
- `<body onload=alert(1)>`

---

### Attack 1.2: SQL Injection - Static Rule
**Endpoint**: `GET http://127.0.0.1:4100/api/search?q=PAYLOAD`
**Detection**: Static rule (SQL_INJECTION)
**Why It's Blocked Instantly**: Contains SQL keywords like `' OR '1'='1` which match SQL injection regex

**Manual Steps:**
1. In browser address bar, visit:
```
http://127.0.0.1:4100/api/search?q=' OR '1'='1
```
→ **Expected: 403 Forbidden**

Or use DevTools Console:
```javascript
fetch('/api/search?q=\' OR \'1\'=\'1')
  .then(r => r.text())
  .then(t => console.log(t))
```

Or use the **Search Form** on vulnerable app UI:
- In "Search" section, enter: `' OR '1'='1`
- Click Search → **Expected: 403 Forbidden**

**Dashboard Check:**
- Look for: `source: STATIC_RULE`, `rule_id: SQL_INJECTION`, `blocked: 1`

**Other SQL Payloads to Try:**
- `' AND '1'='2`
- `'; DROP TABLE users; --`
- `' UNION SELECT * FROM users --`
- `admin' --`

---

### Attack 1.3: XXE (XML External Entity) - Static Rule
**Endpoint**: `POST http://127.0.0.1:4100/api/xml/import`
**Detection**: Static rule (XXE_PATTERN)
**Why It's Blocked Instantly**: Contains `<!DOCTYPE` or `<!ENTITY` which match XXE regex

**Manual Steps:**
1. Use DevTools Console:
```javascript
fetch('/api/xml/import', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    xmlData: '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>'
  })
})
.then(r => r.text())
.then(t => console.log(t))
```

Or use the **XML Import Form** on vulnerable app UI:
- In "XML Import" section, paste the XML above
- Click Import → **Expected: 403 Forbidden**

**Dashboard Check:**
- Look for: `source: STATIC_RULE`, `rule_id: XXE_PATTERN`, `blocked: 1`

**Other XXE Payloads to Try:**
- `<!DOCTYPE foo [<!ENTITY file SYSTEM "file:///c:/windows/win.ini">]>`
- `<!DOCTYPE foo [<!ENTITY % file SYSTEM "php://filter/resource=/etc/passwd">]>`

---

### Attack 1.4: Command Injection - Static Rule
**Endpoint**: `POST http://127.0.0.1:4100/api/admin/run`
**Detection**: Static rule (COMMAND_INJECTION)
**Why It's Blocked Instantly**: Contains shell metacharacters like `; ls` or `| cat`

**Manual Steps:**
1. Use DevTools Console:
```javascript
fetch('/api/admin/run', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    command: 'echo test; cat /etc/passwd'
  })
})
.then(r => r.text())
.then(t => console.log(t))
```

Or use the **Admin Task Form** on vulnerable app UI:
- In "Admin Task" section, enter: `echo test; cat /etc/passwd`
- Click Execute → **Expected: 403 Forbidden**

**Dashboard Check:**
- Look for: `source: STATIC_RULE`, `rule_id: COMMAND_INJECTION`, `blocked: 1`

**Other Command Payloads to Try:**
- `whoami`
- `dir` or `ls -la`
- `net user`
- `curl http://attacker.com`
- `| powershell Get-Process`

---

### Attack 1.5: Path Traversal - Static Rule
**Endpoint**: `GET http://127.0.0.1:4100/api/file?path=PAYLOAD`
**Detection**: Static rule (PATH_TRAVERSAL)
**Why It's Blocked Instantly**: Contains `../` or encoded equivalents

**Manual Steps:**
1. In browser address bar:
```
http://127.0.0.1:4100/api/file?path=../../../../etc/passwd
```
→ **Expected: 403 Forbidden**

Or DevTools:
```javascript
fetch('/api/file?path=..%2F..%2F..%2Fetc%2Fpasswd')
  .then(r => r.text())
  .then(t => console.log(t))
```

Or use **Path Probe Form** on vulnerable app UI:
- In "Test Path" section, enter: `../../../../etc/passwd`
- Click Test → **Expected: 403 Forbidden**

**Dashboard Check:**
- Look for: `source: STATIC_RULE`, `rule_id: PATH_TRAVERSAL`, `blocked: 1`

**Other Path Traversal Payloads to Try:**
- `..\\..\\..\\windows\\system32\\drivers\\etc\\hosts`
- `....//....//....//etc/passwd` (double slash bypass)
- `..%2F..%2F..%2Fetc%2Fpasswd` (URL encoded)
- `..%252F..%252F..%252Fetc%2Fpasswd` (double encoded)

---

## SECTION 2: MANUAL ATTACKS (AI-Based Detection)

These attacks **bypass static rules** but are detected by AI behavioral analysis. You'll see **403 Forbidden** after AI scoring.

### Attack 2.1: Rate Limiting / Brute Force Detection - AI
**Endpoint**: `POST http://127.0.0.1:4100/api/login`
**Detection**: AI behavioral (excessive login attempts from same IP)
**Why AI Detects It**: Pattern of repeated failed attempts triggers behavioral risk score

**Manual Steps:**
1. Use DevTools Console to send 10+ rapid login attempts:
```javascript
async function bruteForce() {
  for (let i = 0; i < 15; i++) {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: 'admin',
        password: `wrongpass${i}`
      })
    });
    console.log(`Attempt ${i+1}:`, response.status, await response.text());
    await new Promise(r => setTimeout(r, 100)); // 100ms delay between attempts
  }
}
bruteForce();
```

Or use the **Login Form** on vulnerable app UI:
- Click "Login" form repeatedly with different passwords
- Try: admin/wrong1, admin/wrong2, admin/wrong3, etc.
- After 10+ failures, request should return **403 Forbidden**

**Dashboard Check:**
- Look for: `source: AI_ENGINE`, behavior shows `risk_score > 0.7`, `action: BLOCK`
- View in Monitor tab → Events should show multiple login attempts followed by block

**Expected AI Detection Signals:**
- High frequency of login attempts (>10 in 1 minute)
- Same IP address
- Rapid request timing
- Failed authentication pattern

---

### Attack 2.2: Scanner Behavior Detection - AI
**Endpoint**: `GET http://127.0.0.1:4100/` (various paths in sequence)
**Detection**: AI behavioral (scanner footprint - probing multiple paths)
**Why AI Detects It**: Sequential requests to discovery paths like /admin, /phpmyadmin, /backup.zip in quick succession

**Manual Steps:**
1. In DevTools Console, simulate scanner probing:
```javascript
async function scannerBehavior() {
  const paths = [
    '/admin',
    '/admin/login',
    '.env',
    '/.env',
    '/backup.zip',
    '/phpmyadmin',
    '/phpmyadmin/index.php',
    '/wp-admin',
    '/config.php',
    '/database.yml'
  ];
  
  for (const path of paths) {
    const response = await fetch(path);
    console.log(`${path}:`, response.status);
    await new Promise(r => setTimeout(r, 50)); // 50ms between requests
  }
}
scannerBehavior();
```

Or manually visit in quick succession:
1. http://127.0.0.1:4100/admin → 404
2. http://127.0.0.1:4100/.env → 404
3. http://127.0.0.1:4100/backup.zip → 404
4. http://127.0.0.1:4100/phpmyadmin → 404
5. (repeat for 8-10 paths)

**Dashboard Check:**
- Look for: `source: AI_ENGINE`, behavior shows scanner pattern detected
- Should see anomalous request frequency from single IP

**Expected AI Detection Signals:**
- High request frequency (>20 requests/minute)
- 404 responses (probing non-existent paths)
- Systematic path enumeration pattern
- User-Agent consistency (same client)

---

### Attack 2.3: Data Exfiltration Pattern - AI
**Endpoint**: `GET http://127.0.0.1:4100/api/export`
**Detection**: AI behavioral (unusual data dump request)
**Why AI Detects It**: Requesting full data exports multiple times in short window

**Manual Steps:**
1. Rapidly request data exports in DevTools Console:
```javascript
async function exfiltrateData() {
  for (let i = 0; i < 5; i++) {
    const response = await fetch('/api/export?format=json');
    const size = await response.text().then(t => t.length);
    console.log(`Request ${i+1}: Downloaded ${size} bytes`);
    await new Promise(r => setTimeout(r, 200));
  }
}
exfiltrateData();
```

Or use the **Export Form** on vulnerable app UI:
- In "Data Export" section, select format (JSON/CSV/SQL)
- Click Export 5+ times rapidly
- After 3-4 rapid exports, request returns **403 Forbidden**

**Dashboard Check:**
- Look for: `source: AI_ENGINE`, behavior shows data exfiltration pattern
- Multiple large data requests from same IP in short time

**Expected AI Detection Signals:**
- Large response sizes (bulk data)
- High request frequency for export endpoints
- Same IP, rapid succession
- Systematic data retrieval pattern

---

## SECTION 3: BOT-BASED ATTACKS

These use automated tools. Run each in a **separate terminal** while monitoring the dashboard.

### Attack 3.1: SQLMap - SQL Injection Testing
**Tool Purpose**: Automated SQL injection detection and exploitation
**Target Endpoints**: /api/search?q=, /api/users?sort=, /api/orders?sort=

**Step-by-Step Instructions:**

1. **Open new terminal** (Terminal 5)

2. **Install sqlmap** (if not already installed):
```powershell
pip install sqlmap
```

3. **Basic SQL injection scan on search endpoint:**
```powershell
cd c:\Users\mayan
sqlmap -u "http://127.0.0.1:4100/api/search?q=*" --batch --level=3 --risk=3
```

**Breakdown:**
- `-u "URL"`: Target URL with `*` marking injection point
- `--batch`: Auto-answer prompts
- `--level=3`: Test 3 levels of payloads (1-5, higher = more payloads)
- `--risk=3`: Use risky SQL commands (1-3, higher = riskier operations)

**Expected Output:**
```
[WARNING] GET parameter 'q' does not appear to be dynamic
[CRITICAL] Heuristic (parsing) test showed that GET parameter 'q' is injectable
... [various payloads tested] ...
[XX-XX] testing for 'UNION query SQL-injection'
```

**Dashboard During Test:**
- Monitor http://127.0.0.1:5174 Monitor tab
- Watch events appear with STATIC_RULE blocks (sqlmap sends `' OR '1'='1` type payloads)
- Count how many attempts blocked; should be high frequency

4. **Advanced scan with database enumeration:**
```powershell
sqlmap -u "http://127.0.0.1:4100/api/users?sort=*" --batch --dbs --level=2 --risk=2
```

**Breakdown:**
- `--dbs`: Try to enumerate database names
- Targets the sort parameter (another typical SQLi point)

5. **Specify techniques to use:**
```powershell
sqlmap -u "http://127.0.0.1:4100/api/search?q=*" --batch --technique=EETU --level=2 --risk=2
```

**Techniques:**
- `E`: Error-based
- `U`: Union-based
- `T`: Time-based
- `S`: Stacked queries

**Dashboard Outcome:**
- Should see 100+ events all with STATIC_RULE (SQL_INJECTION pattern)
- All should show 403 Forbidden
- Event rate should peak during sqlmap run

---

### Attack 3.2: Gobuster - Directory/Path Enumeration
**Tool Purpose**: Brute-force discover hidden paths and directories
**Target**: http://127.0.0.1:4100

**Step-by-Step Instructions:**

1. **Open new terminal** (Terminal 6)

2. **Install gobuster** (if not already installed):
```powershell
# Using choco (if installed)
choco install gobuster

# Or download from GitHub: https://github.com/OJ/gobuster/releases
```

3. **Basic directory enumeration:**
```powershell
cd c:\Users\mayan
gobuster dir -u "http://127.0.0.1:4100/" -w "C:\Program Files\GoBuster\wordlists\common.txt" --status-codes 200,301,302,401,403 -q
```

**Breakdown:**
- `dir`: Directory enumeration mode
- `-u "URL"`: Target URL
- `-w "wordlist"`: Path to wordlist (common.txt usually has 4700+ entries)
- `--status-codes`: Report these HTTP status codes
- `-q`: Quiet mode (less verbose)

**Expected Output:**
```
Found: /api (Status: 200)
Found: /api/login (Status: 200)
Found: /api/search (Status: 200)
Found: /admin (Status: 404)
Found: /backup (Status: 404)
...
```

4. **Advanced scan with extension targeting:**
```powershell
gobuster dir -u "http://127.0.0.1:4100/" -w "C:\Program Files\GoBuster\wordlists\common.txt" -x "js,json,txt,php,html" --status-codes 200,301,302,403 -q
```

**Breakdown:**
- `-x "extensions"`: Also test these file extensions (.js, .json, etc.)

5. **Recursive directory search (max depth 2):**
```powershell
gobuster dir -u "http://127.0.0.1:4100/api/" -w "C:\Program Files\GoBuster\wordlists\common.txt" --status-codes 200,301,302 -q --timeout 3s
```

**Dashboard During Test:**
- Should see 1000+ 404 responses (most paths don't exist)
- Watch for AI scanner pattern detection after 50+ rapid 404s
- Expected: Initial events blocked by static rules, then AI behavioral blocking kicks in

**Typical Gobuster Wordlist Locations:**
- `C:\Program Files\GoBuster\wordlists\common.txt`
- Or use an online wordlist: `https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt`

---

### Attack 3.3: Hydra - Brute Force Login
**Tool Purpose**: Automated credential guessing against /api/login
**Target**: POST http://127.0.0.1:4100/api/login

**Step-by-Step Instructions:**

1. **Open new terminal** (Terminal 7)

2. **Install hydra** (if not already installed):
```powershell
# Using choco
choco install hydra

# Or download from GitHub: https://github.com/vanhauser-thc/thc-hydra/releases
```

3. **Create wordlist file** (save as `c:\Users\mayan\passwords.txt`):
```
password123
admin123
letmein
welcome
123456
password
admin
root
test
demo
```

4. **Basic HTTP POST brute force:**
```powershell
hydra -l admin -P c:\Users\mayan\passwords.txt -t 4 http://127.0.0.1:4100 http-post-form "/api/login:username=^USER^&password=^PASS^:Invalid credentials" -v
```

**Breakdown:**
- `-l admin`: Username to test
- `-P c:\Users\mayan\passwords.txt`: Password wordlist
- `-t 4`: 4 parallel threads
- `http-post-form "path:data:fail_string"`: POST to /api/login with data, look for "Invalid credentials" as failure indicator
- `-v`: Verbose output

**Expected Output:**
```
[3306][http-post-form] user: admin password: admin123
[3307][http-post-form] user: admin password: letmein
...
[INFO] Waiting for the last tasks to finish, please wait...
```

5. **Brute force multiple usernames:**
```powershell
# Create usernames.txt with:
# admin
# root
# testuser
# alice
# bob

hydra -L c:\Users\mayan\usernames.txt -P c:\Users\mayan\passwords.txt -t 4 http://127.0.0.1:4100 http-post-form "/api/login:username=^USER^&password=^PASS^:Invalid" -v
```

**Dashboard During Test:**
- Should see high frequency of login attempts (100+)
- First few attempts may return 200 OK (incorrect password)
- After ~10-15 attempts from same IP, AI should detect brute force pattern
- Subsequent requests return **403 Forbidden** with AI_ENGINE source

**Key Hydra Parameters:**
- `-L file`: Multiple usernames
- `-P file`: Multiple passwords
- `-e nsr`: Try null password (`-e n`), same as login (`-e s`), reverse login (`-e r`)
- `-t N`: Parallel threads (higher = faster but may overwhelm target)
- `-W N`: Waiting time between connections
- `-c N`: Timeout per connection

---

## SECTION 4: COMBINATION ATTACKS & TESTING SEQUENCE

Follow this order for comprehensive testing:

### Phase 1: Static Rule Validation (Manual, 10-15 minutes)
1. **Start all 4 servers** in separate terminals:
   - Terminal 1: AI Engine on 8001
   - Terminal 2: testapp on 3012
   - Terminal 3: Vulnerable app on 4100
   - Terminal 4: Dashboard on 5174

2. **Open vulnerable app UI**: http://127.0.0.1:4100
3. **Open dashboard Monitor tab**: http://127.0.0.1:5174
4. **Perform each manual attack from Section 1** (XSS, SQLi, XXE, Command Injection, Path Traversal)
   - Use the vulnerable app forms or DevTools console
   - Expect: 403 Forbidden + event in dashboard within 1-2 seconds
   - Verify event shows `source: STATIC_RULE` and specific `rule_id`

**Dashboard Observation:**
- Monitor tab shows real-time events
- All 5 attack types should appear with different rule IDs
- All should be blocked (blocked: 1)

---

### Phase 2: AI Behavioral Detection (Manual, 10-15 minutes)
1. **Keep all servers running**
2. **Perform brute force attack** (Section 2.1):
   - Send 15 login attempts with wrong passwords
   - Watch dashboard for AI detection kick in around attempt 10-12
   - Verify event shows `source: AI_ENGINE`

3. **Perform scanner behavior** (Section 2.2):
   - Visit /admin, /.env, /backup.zip, /phpmyadmin, etc. rapidly
   - Should see AI detect scanner pattern
   - Verify high request frequency causes block

4. **Perform data exfiltration** (Section 2.3):
   - Rapidly export data 5+ times
   - AI should detect unusual bulk data access

**Dashboard Observation:**
- Monitor tab should show different event types
- Mix of STATIC_RULE and AI_ENGINE sources
- Policies tab should show these are preventable with different presets

---

### Phase 3: Bot-Based Attacks (Automated, 10-20 minutes each)
**Run one at a time, monitor dashboard:**

1. **SQLMap Phase** (5 minutes):
   - Run basic scan: `sqlmap -u "http://127.0.0.1:4100/api/search?q=*" --batch --level=3 --risk=3`
   - Watch dashboard: 100+ events, all STATIC_RULE blocks
   - Switch policy to "Observe-Only", run again
   - Watch: Events logged but NOT blocked (status 200)

2. **Gobuster Phase** (10-15 minutes):
   - Run directory enum: `gobuster dir -u "http://127.0.0.1:4100/" -w wordlist.txt -q`
   - Watch dashboard: 1000s of 404s, then AI scanner detection
   - Verify: Initially STATIC_RULE blocks, then AI behavioral blocks
   - Switch policy to "Balanced", run again
   - Compare: More requests allowed but still AI-detected

3. **Hydra Phase** (5 minutes):
   - Run login brute force: `hydra -l admin -P passwords.txt http://127.0.0.1:4100 http-post-form "/api/login:..."`
   - Watch dashboard: Login attempts, ~10-12 allowed, then blocked
   - Verify: Event shows brute force pattern detection
   - Switch policy to "Observe-Only", run again
   - Watch: All requests logged, none blocked

---

## SECTION 5: DASHBOARD MONITORING GUIDE

### What to Watch

**Monitor Tab - Events List:**
```
Time        | Endpoint      | Method | Status | Source       | Rule/Reason
09:15:23    | /api/comment  | POST   | 403    | STATIC_RULE  | XSS_PATTERN
09:15:24    | /api/search   | GET    | 403    | STATIC_RULE  | SQL_INJECTION
09:15:45    | /api/login    | POST   | 200    | AI_ENGINE    | (attempt 1)
09:15:46    | /api/login    | POST   | 200    | AI_ENGINE    | (attempt 2)
09:16:02    | /api/login    | POST   | 403    | AI_ENGINE    | Brute force detected
```

**Monitor Tab - Metrics:**
- **Requests/sec**: Should spike during bot attacks (50-200 req/s)
- **Blocked/sec**: Normal 0-5, spikes during attacks
- **Top Rules Triggered**: XSS_PATTERN, SQL_INJECTION, etc.
- **Top Endpoints Targeted**: /api/search, /api/login, /api/comment

**Policies Tab:**
- View/edit default policy
- Try "Strict" preset → more blocks
- Try "Balanced" preset → only major threats blocked
- Try "Observe-Only" preset → nothing blocked, all logged

**Policy Audit Tab:**
- View history of policy changes
- See timestamp when you switched presets
- Shows before/after policy JSON

---

## SECTION 6: EXPECTED RESULTS TABLE

| Attack       | Method        | Static Rule | AI Detects | Expected Status | Dashboard Source    |
|--------------|---------------|-------------|-----------|-----------------|-------------------|
| XSS          | Manual/sqlmap | ✅ YES      | N/A       | 403 Forbidden   | STATIC_RULE       |
| SQLi         | Manual/sqlmap | ✅ YES      | N/A       | 403 Forbidden   | STATIC_RULE       |
| XXE          | Manual        | ✅ YES      | N/A       | 403 Forbidden   | STATIC_RULE       |
| Command Inj. | Manual        | ✅ YES      | N/A       | 403 Forbidden   | STATIC_RULE       |
| Path Trav.   | Manual        | ✅ YES      | N/A       | 403 Forbidden   | STATIC_RULE       |
| Brute Force  | Manual/hydra  | ❌ NO       | ✅ YES     | 200 OK→403      | AI_ENGINE         |
| Scanner      | Manual/gobuster| ❌ NO      | ✅ YES     | 404→403         | AI_ENGINE         |
| Exfiltration | Manual        | ❌ NO       | ✅ YES     | 200→403         | AI_ENGINE         |

---

## SECTION 7: COMMAND REFERENCE

**Copy-paste ready commands:**

### SQLMap
```powershell
# Basic check
sqlmap -u "http://127.0.0.1:4100/api/search?q=*" --batch --level=3 --risk=3

# With database enum
sqlmap -u "http://127.0.0.1:4100/api/users?sort=*" --batch --dbs

# Time-based only
sqlmap -u "http://127.0.0.1:4100/api/search?q=*" --batch --technique=T
```

### Gobuster
```powershell
# Directory scan
gobuster dir -u "http://127.0.0.1:4100/" -w "wordlist.txt" --status-codes 200,301,302,403,404 -q

# With extensions
gobuster dir -u "http://127.0.0.1:4100/" -w "wordlist.txt" -x "js,json,php" -q

# Subdomain scan (if applicable)
gobuster dns -d 127.0.0.1 -w "subdomains.txt" -q
```

### Hydra
```powershell
# Basic login brute force
hydra -l admin -P passwords.txt -t 4 http://127.0.0.1:4100 http-post-form "/api/login:username=^USER^&password=^PASS^:Invalid" -v

# Multiple users
hydra -L users.txt -P passwords.txt -t 4 http://127.0.0.1:4100 http-post-form "/api/login:username=^USER^&password=^PASS^:Invalid" -v

# Try common passwords
hydra -l admin -P /usr/share/wordlists/rockyou.txt http://127.0.0.1:4100 http-post-form "/api/login:..." -t 8
```

### Manual API Calls
```powershell
# XSS attack
Invoke-RestMethod -Uri "http://127.0.0.1:4100/api/comment" -Method POST -ContentType "application/json" -Body '{"comment":"<img src=x onerror=alert(1)>"}'

# SQLi
Invoke-RestMethod -Uri "http://127.0.0.1:4100/api/search?q=' OR '1'='1"

# Path traversal
Invoke-RestMethod -Uri "http://127.0.0.1:4100/api/file?path=../../../../etc/passwd"

# Command injection
Invoke-RestMethod -Uri "http://127.0.0.1:4100/api/admin/run" -Method POST -ContentType "application/json" -Body '{"command":"whoami"}'

# Brute force loop
for ($i = 1; $i -le 20; $i++) {
  Invoke-RestMethod -Uri "http://127.0.0.1:4100/api/login" -Method POST -ContentType "application/json" -Body "{`"username`":`"admin`",`"password`":`"wrong$i`"}" 2>&1 | Select-Object -First 1
  Start-Sleep -Milliseconds 100
}
```

---

## FINAL TESTING CHECKLIST

- [ ] All 4 servers running (AI, testapp, vulnerable-app, dashboard)
- [ ] Dashboard accessible at http://127.0.0.1:5174
- [ ] XSS attack blocked with 403 + STATIC_RULE event
- [ ] SQLi attack blocked with 403 + STATIC_RULE event
- [ ] XXE attack blocked with 403 + STATIC_RULE event
- [ ] Command injection blocked with 403 + STATIC_RULE event
- [ ] Path traversal blocked with 403 + STATIC_RULE event
- [ ] Brute force detected after 10+ attempts + AI_ENGINE block
- [ ] Gobuster campaign shows 1000+ events in dashboard
- [ ] SQLMap campaign shows 100+ SQL_INJECTION blocks
- [ ] Hydra campaign shows brute force pattern detected
- [ ] Policy switching (Strict/Balanced/Observe-Only) changes blocking behavior
- [ ] All events visible in Monitor tab with correct timestamps
- [ ] Policy audit tab shows preset change history

---

## TROUBLESHOOTING

### No events appearing in dashboard?
- Check testapp is running: `curl http://127.0.0.1:3012/observability/events?limit=1`
- Check vulnerable app telemetry DB path in terminal output
- Verify AI_URL in testapp is correct: `http://127.0.0.1:8001/predict`

### Attacks return 200 OK instead of 403?
- Verify MICROSHIELD_MODULE_PATH env var is set in vulnerable-app terminal
- Check vulnerable-app status: `curl http://127.0.0.1:4100/api/status`
- Ensure `ENABLE_MICROSHIELD=1` in vulnerable-app terminal

### Bot tools not finding targets?
- SQLMap: Try `--level=1` for faster, simpler payloads
- Gobuster: Ensure wordlist file exists and has read permissions
- Hydra: Use `-e nsr` to try empty password and username=password

### High AI latency (events delayed in dashboard)?
- Check AI engine is responsive: `curl http://127.0.0.1:8001/docs`
- Monitor CPU/memory usage during bot scans
- Reduce bot thread count (`-t 2` instead of `-t 4`) to lower load
