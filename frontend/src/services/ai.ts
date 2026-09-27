import { request } from './api';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatContext {
  space_id?: number;
  current_path?: string;
}

export async function sendChatMessage(
  message: string,
  history: ChatMessage[] = [],
  context?: ChatContext
): Promise<{ reply: string }> {
  const messages = [...history];
  if (!messages.some(m => m.content === message && m.role === 'user')) {
    messages.push({ role: 'user', content: message });
  }

  return request('/api/ai/chat', {
    method: 'POST',
    body: JSON.stringify({
      message,
      history,
      messages,
      space_id: context?.space_id,
      current_path: context?.current_path,
    }),
  });
}
