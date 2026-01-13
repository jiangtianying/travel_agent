export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface ChatResponse {
  response: string;
  session_id: string;
}

export interface ModelsResponse {
  models: string[];
  current_model: string;
}
