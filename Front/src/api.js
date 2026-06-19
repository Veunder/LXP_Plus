const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(data?.error || "Ошибка запроса к серверу");
  }
  return data;
}

export const api = {
  getTeachers: () => request("/teachers"),
  getClassrooms: () => request("/classrooms"),
  getLaptops: () => request("/laptops"),
  createIssue: (payload) => request("/issues", { method: "POST", body: JSON.stringify(payload) }),
  returnIssue: (issueId) => request(`/issues/${issueId}/return`, { method: "POST" }),
  releaseLaptop: (laptopId) => request(`/laptops/${laptopId}/release`, { method: "POST" }),
  getHistory: () => request("/history"),
};
