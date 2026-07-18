const API_BASE = "http://localhost:8000";

export const getRecommendations = async (userId) => {
  const response = await fetch(`${API_BASE}/v1/recommendations/homepage/${userId}`);
  return response.json();
};

export const sendEvent = async (event) => {
  await fetch(`${API_BASE}/v1/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(event),
  });
};