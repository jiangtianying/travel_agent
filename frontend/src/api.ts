import type { ChatResponse, ModelsResponse } from "./types";

const API_BASE = "http://localhost:8000";

export async function sendMessage(
  message: string,
  sessionId: string = "default"
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

export async function resetSession(sessionId: string = "default"): Promise<void> {
  const response = await fetch(`${API_BASE}/api/reset?session_id=${sessionId}`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
}

export async function getModels(): Promise<ModelsResponse> {
  const response = await fetch(`${API_BASE}/api/models`);

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

export async function changeModel(modelDisplayName: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/models`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ model_display_name: modelDisplayName }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
}
