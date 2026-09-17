import { request } from './api';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export async function sendChatMessage(message: string, history: ChatMessage[] = []): Promise<{ reply: string }> {
  const messages = [...history];
  if (!messages.some(m => m.content === message && m.role === 'user')) {
    messages.push({ role: 'user', content: message });
  }

  return request('/api/ai/chat', {
    method: 'POST',
    body: JSON.stringify({ message, history, messages }),
  });
}
