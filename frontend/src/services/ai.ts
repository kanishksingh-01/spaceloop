import { request } from './api';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  response_type?: string;
  data?: any;
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

export interface LoopBotChatResponse {
  success: boolean;
  conversation_id: string;
  message: string;
  response_type: string;
  data: Record<string, any>;
  context: Record<string, any>;
  error?: string;
}

/**
 * Sends a message to the native SpaceLoop LoopBot concierge endpoint.
 * Returns structured response types (space_results, booking_preview, confirmation_required, etc.).
 */
export async function sendLoopBotMessage(
  message: string,
  conversationId?: string,
  confirm?: boolean,
  context?: Record<string, any>
): Promise<LoopBotChatResponse> {
  return request('/api/v1/loopbot/chat', {
    method: 'POST',
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      confirm,
      context,
      space_id: context?.space_id,
    }),
  });
}

/**
 * Legacy assistant endpoint for backward compatibility with existing tests.
 */
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
