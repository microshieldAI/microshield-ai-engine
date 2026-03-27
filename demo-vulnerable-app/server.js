const express = require("express");
const path = require("path");
const dotenv = require("dotenv");

dotenv.config();

const app = express();
const PORT = Number(process.env.PORT || 4100);
const tenantId = String(process.env.TENANT_ID || "tenantA");
const userId = String(process.env.USER_ID || "demo-user");
const telemetryDbPath = path.join(__dirname, "data", "microshield_events.sqlite");
let policyRefreshTimer = null;

const fakeUsers = [
  { id: 1, username: "analyst", role: "user" },
  { id: 2, username: "ops-admin", role: "admin" },
  { id: 3, username: "finance", role: "user" },
];
const fakeOrders = [
  { id: "ORD-100", user: "analyst", amount: 189.5 },
  { id: "ORD-101", user: "finance", amount: 999.99 },
  { id: "ORD-102", user: "ops-admin", amount: 48.0 },
];
const loginAttempts = new Map();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.text({ type: ["text/xml", "application/xml"] }));

app.use((req, _res, next) => {
  req.headers["x-tenant-id"] = req.headers["x-tenant-id"] || tenantId;
  req.headers["x-user-id"] = req.headers["x-user-id"] || userId;
  req._tenantId = req.headers["x-tenant-id"];
  req._userId = req.headers["x-user-id"];
  next();
});

function maybeLoadMicroShield() {
  if (String(process.env.ENABLE_MICROSHIELD || "0") !== "1") {
    return null;
  }

  const modulePath = String(process.env.MICROSHIELD_MODULE_PATH || "").trim();
  if (!modulePath) {
    console.warn("[demo] ENABLE_MICROSHIELD=1 but MICROSHIELD_MODULE_PATH is empty.");
    return null;
  }

  try {
    // eslint-disable-next-line import/no-dynamic-require,global-require
    const MicroShieldFactory = require(modulePath);
    const moduleDir = path.dirname(modulePath);
    // eslint-disable-next-line import/no-dynamic-require,global-require
    const createTelemetryStore = require(path.join(moduleDir, "lib", "telemetryStore"));
    // eslint-disable-next-line import/no-dynamic-require,global-require
    const createPolicyEngine = require(path.join(moduleDir, "lib", "policyEngine"));

    const telemetryStore = createTelemetryStore({ dbPath: telemetryDbPath });
    const policyEngine = createPolicyEngine();

    const refreshPolicies = async () => {
      try {
        const snapshot = await telemetryStore.loadPolicies();
        if (snapshot && (snapshot.defaultPolicy || (snapshot.routes && snapshot.routes.length))) {
          policyEngine.importSnapshot(snapshot);
        }
      } catch {
        // Keep server running even if policy snapshot read fails.
      }
    };

    telemetryStore.init().catch(() => {});
    refreshPolicies().catch(() => {});
    policyRefreshTimer = setInterval(() => {
      refreshPolicies().catch(() => {});
    }, 5000);

    return {
      MicroShieldFactory,
      telemetryStore,
      policyEngine,
    };
  } catch (err) {
    console.error("[demo] Failed loading MicroShield from path:", modulePath);
    console.error(err.message);
    return null;
  }
}

const microShieldBundle = maybeLoadMicroShield();
if (microShieldBundle) {
  const shield = microShieldBundle.MicroShieldFactory({
    aiUrl: process.env.MICROSHIELD_AI_URL || "http://127.0.0.1:8001/predict",
    mode: "protect",
    failOpen: true,
    telemetry: {
      enabled: true,
      dbPath: telemetryDbPath,
    },
    defaultTenantId: tenantId,
    telemetryStore: microShieldBundle.telemetryStore,
    policyEngine: microShieldBundle.policyEngine,
  });
  app.use(shield);
  console.log("[demo] MicroShield middleware enabled.");
  console.log("[demo] Telemetry DB:", telemetryDbPath);
} else {
  console.log("[demo] Running without MicroShield (vulnerable mode).");
}

app.use(express.static(path.join(__dirname, "public")));

app.post("/api/login", (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ ok: false, error: "username and password required" });
  }

  const key = `${req.ip}:${username}`;
  const state = loginAttempts.get(key) || { count: 0, last: null };
  state.count += 1;
  state.last = new Date().toISOString();
  loginAttempts.set(key, state);

  return res.json({
    ok: true,
    message: "Login accepted",
    user: username,
    role: username.includes("admin") ? "admin" : "user",
    passwordEcho: password,
    bruteForceSignal: {
      attemptCount: state.count,
      lastAttemptAt: state.last,
    },
    tenant: req._tenantId,
  });
});

app.get("/api/search", (req, res) => {
  const q = String(req.query.q || "");
  return res.json({
    ok: true,
    query: q,
    results: [
      `Result for: ${q}`,
      "This endpoint is intentionally weak for demo attacks",
    ],
  });
});

app.get("/api/users", (req, res) => {
  const sort = String(req.query.sort || "id");
  const users = fakeUsers.slice();

  if (sort === "username") {
    users.sort((a, b) => a.username.localeCompare(b.username));
  } else if (sort === "role") {
    users.sort((a, b) => a.role.localeCompare(b.role));
  }

  return res.json({
    ok: true,
    sort,
    users,
    note: "Pretend SQL: SELECT * FROM users ORDER BY " + sort,
  });
});

app.get("/api/orders", (req, res) => {
  const user = String(req.query.user || "");
  const rows = user ? fakeOrders.filter((o) => o.user.includes(user)) : fakeOrders;
  return res.json({
    ok: true,
    rows,
    count: rows.length,
  });
});

app.post("/api/comment", (req, res) => {
  const text = String((req.body || {}).text || "");
  return res.json({
    ok: true,
    saved: true,
    preview: text,
    note: "No sanitization in demo mode",
  });
});

app.get("/api/file", (req, res) => {
  const requested = String(req.query.path || "readme.txt");
  return res.json({
    ok: true,
    path: requested,
    content: `Pretend file read for ${requested}`,
  });
});

app.post("/api/admin/run", (req, res) => {
  const task = String((req.body || {}).task || "").trim();
  if (!task) {
    return res.status(400).json({ ok: false, error: "task required" });
  }

  return res.json({
    ok: true,
    command: task,
    stdout: `Executed: ${task}`,
    note: "Intentionally vulnerable command execution simulation",
  });
});

app.get("/api/export", (req, res) => {
  const format = String(req.query.format || "json").toLowerCase();
  if (format === "sql") {
    return res.json({
      ok: true,
      format,
      dump: "SELECT * FROM users; SELECT * FROM orders; -- demo export",
    });
  }
  if (format === "csv") {
    return res.json({
      ok: true,
      format,
      dump: "id,username,role\\n1,analyst,user\\n2,ops-admin,admin",
    });
  }
  return res.json({ ok: true, format: "json", users: fakeUsers, orders: fakeOrders });
});

app.post("/api/xml/import", (req, res) => {
  const xml = String(req.body || "");
  return res.json({
    ok: true,
    accepted: true,
    preview: xml.slice(0, 300),
    note: "XML parser simulation endpoint for XXE-style payload demos",
  });
});

app.get("/admin", (_req, res) => {
  return res.status(200).send("Admin panel placeholder");
});

app.get("/admin/login", (_req, res) => {
  return res.status(200).send("Legacy admin login endpoint");
});

app.get("/backup.zip", (_req, res) => {
  return res.status(200).send("PK\\u0003\\u0004 demo backup placeholder");
});

app.get("/.env", (_req, res) => {
  return res.status(200).send("DB_PASSWORD=demo-password\\nJWT_SECRET=demo-secret");
});

app.get("/phpmyadmin", (_req, res) => {
  return res.status(200).send("phpMyAdmin demo path");
});

app.get("/wp-admin", (_req, res) => {
  return res.status(200).send("WordPress admin probe hit");
});

app.get("/api/status", (_req, res) => {
  return res.json({
    ok: true,
    service: "demo-vulnerable-app",
    microshieldEnabled: Boolean(microShieldBundle),
    telemetryDbPath: Boolean(microShieldBundle) ? telemetryDbPath : null,
    tenantId,
    userId,
    routes: [
      "POST /api/login",
      "GET /api/search",
      "GET /api/users",
      "GET /api/orders",
      "POST /api/comment",
      "GET /api/file",
      "POST /api/admin/run",
      "GET /api/export",
      "POST /api/xml/import",
      "GET /admin",
      "GET /backup.zip",
      "GET /.env",
      "GET /phpmyadmin",
      "GET /wp-admin",
    ],
  });
});

app.listen(PORT, () => {
  console.log(`[demo] Vulnerable app running at http://127.0.0.1:${PORT}`);
});

process.on("SIGINT", () => {
  if (policyRefreshTimer) clearInterval(policyRefreshTimer);
  process.exit(0);
});
