import { request } from './api';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatContext {
  space_id?: number;
  current_path?: string;
  language_preference?: string;
}

export interface AssistantResponse {
  success?: boolean;
  reply: string;
  intent?: string;
  entities?: Record<string, any>;
  detected_language?: string;
  response_language?: string;
  confidence?: number;
  requires_clarification?: boolean;
  is_code_mixed?: boolean;
}

export async function sendChatMessage(
  message: string,
  history: ChatMessage[] = [],
  context?: ChatContext
): Promise<AssistantResponse> {
  const messages = [...history];
  if (!messages.some(m => m.content === message && m.role === 'user')) {
    messages.push({ role: 'user', content: message });
  }

  return request('/api/assistant', {
    method: 'POST',
    body: JSON.stringify({
      message,
      history,
      messages,
      space_id: context?.space_id,
      current_path: context?.current_path,
      language_preference: context?.language_preference,
    }),
  });
}
