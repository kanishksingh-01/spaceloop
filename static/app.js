function getUser() {
  const raw = localStorage.getItem("user");
  return raw ? JSON.parse(raw) : null;
}

function setUser(user) {
  localStorage.setItem("user", JSON.stringify(user));
}

function logout() {
  localStorage.removeItem("user");
  window.location.href = "/login";
}

async function apiPost(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Something went wrong");
  return data;
}

async function apiGet(url) {
  const res = await fetch(url);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Something went wrong");
  return data;
}

// Redirect helper: guard pages that need a logged-in user.
function requireUser(expectedRole) {
  const user = getUser();
  if (!user) {
    window.location.href = "/login";
    return null;
  }
  if (expectedRole && user.role !== expectedRole) {
    window.location.href = user.role === "self" ? "/dashboard" : "/partner";
    return null;
  }
  return user;
}
