export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function trackEvent(userId: string, eventName: string, metadata: Record<string, unknown> = {}) {
  fetch(`${API_URL}/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, event_name: eventName, metadata }),
  });
}
