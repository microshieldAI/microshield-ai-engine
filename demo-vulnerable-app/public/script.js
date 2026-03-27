function setOutput(payload) {
  const output = document.getElementById("output");
  output.textContent = JSON.stringify(payload, null, 2);
}

async function apiCall(url, options = {}) {
  try {
    const response = await fetch(url, options);
    const text = await response.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
    setOutput({ status: response.status, url, method: options.method || "GET", data });
  } catch (error) {
    setOutput({ error: error.message });
  }
}

document.getElementById("loginForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  apiCall("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: form.get("username"),
      password: form.get("password"),
    }),
  });
});

document.getElementById("searchForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const query = encodeURIComponent(String(form.get("q") || ""));
  apiCall(`/api/search?q=${query}`, { method: "GET" });
});

document.getElementById("usersForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const sort = encodeURIComponent(String(form.get("sort") || "id"));
  apiCall(`/api/users?sort=${sort}`, { method: "GET" });
});

document.getElementById("ordersForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const user = encodeURIComponent(String(form.get("user") || ""));
  apiCall(`/api/orders?user=${user}`, { method: "GET" });
});

document.getElementById("commentForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  apiCall("/api/comment", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: form.get("text") }),
  });
});

document.getElementById("fileForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const filePath = encodeURIComponent(String(form.get("path") || ""));
  apiCall(`/api/file?path=${filePath}`, { method: "GET" });
});

document.getElementById("adminRunForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  apiCall("/api/admin/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task: form.get("task") }),
  });
});

document.getElementById("exportForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const format = encodeURIComponent(String(form.get("format") || "json"));
  apiCall(`/api/export?format=${format}`, { method: "GET" });
});

document.getElementById("xmlForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  apiCall("/api/xml/import", {
    method: "POST",
    headers: { "Content-Type": "application/xml" },
    body: String(form.get("xml") || ""),
  });
});

document.getElementById("probeForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const probePath = String(form.get("path") || "/").trim();
  apiCall(probePath.startsWith("/") ? probePath : `/${probePath}`, { method: "GET" });
});

document.getElementById("customRequestForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const method = String(form.get("method") || "GET").toUpperCase();
  const requestPath = String(form.get("path") || "/").trim();
  const rawBody = String(form.get("body") || "").trim();
  const url = requestPath.startsWith("/") ? requestPath : `/${requestPath}`;

  const options = { method };
  if (rawBody && method !== "GET") {
    options.headers = { "Content-Type": "application/json" };
    options.body = rawBody;
  }
  apiCall(url, options);
});

document.getElementById("clearBtn").addEventListener("click", () => {
  setOutput({ info: "Output cleared" });
});
