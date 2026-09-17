import React, { useState, useRef, useEffect } from 'react';
import { View, Text, Pressable, TextInput, ScrollView } from 'react-native';
import { sendChatMessage, ChatMessage } from '../../services/ai';

export const LoopBot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        "Hi! I'm LoopBot, your SpaceLoop AI assistant. Looking for temporary studio, storage, parking, or pop-up space? Or want tips on monetizing your own unused square footage? Ask away!",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  const handleSend = async (messageText?: string) => {
    const textToSend = (messageText || input).trim();
    if (!textToSend || loading) return;

    setInput('');
    const newHistory: ChatMessage[] = [...messages, { role: 'user', content: textToSend }];
    setMessages(newHistory);
    setLoading(true);

    try {
      const resp = await sendChatMessage(textToSend, newHistory);
      setMessages([...newHistory, { role: 'assistant', content: resp.reply }]);
    } catch {
      setMessages([
        ...newHistory,
        {
          role: 'assistant',
          content: 'Sorry, I had trouble reaching the SpaceLoop AI brain. Please try again.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating LoopBot Concierge Launcher */}
      <div className="fixed bottom-20 md:bottom-6 right-4 sm:right-6 z-40">
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2.5 bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-700 text-white px-3.5 py-2.5 sm:px-4 sm:py-3 rounded-full shadow-2xl shadow-indigo-500/30 hover:scale-105 transition-all duration-200 border border-indigo-400/30"
        >
          <div className="relative">
            <i className="fa-solid fa-robot text-sm sm:text-base" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-slate-900" />
          </div>
          <span className="text-xs sm:text-sm font-semibold tracking-wide">Ask LoopBot</span>
        </button>
      </div>

      {/* AI Concierge Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
          <div className="bg-slate-900 border border-slate-800 w-full sm:max-w-lg rounded-t-2xl sm:rounded-2xl shadow-2xl flex flex-col h-[560px] max-h-[90vh] overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="p-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                  <i className="fa-solid fa-robot text-sm" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">LoopBot AI Concierge</h3>
                  <p className="text-xs text-emerald-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Online & Ready
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
              >
                <i className="fa-solid fa-xmark text-lg" />
              </button>
            </div>

            {/* Message History */}
            <div className="flex-grow p-4 overflow-y-auto space-y-3.5 text-sm">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex gap-2.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-7 h-7 rounded-full bg-indigo-600/30 text-indigo-300 flex items-center justify-center shrink-0 text-xs">
                      <i className="fa-solid fa-robot" />
                    </div>
                  )}
                  <div
                    className={`p-3 rounded-2xl max-w-[85%] leading-relaxed text-xs sm:text-sm whitespace-pre-wrap break-words ${
                      msg.role === 'user'
                        ? 'bg-indigo-600 text-white rounded-tr-sm'
                        : 'bg-slate-800/90 text-slate-200 rounded-tl-sm border border-slate-700/50'
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex gap-2.5 items-center text-slate-400 text-xs">
                  <div className="w-7 h-7 rounded-full bg-indigo-600/30 text-indigo-300 flex items-center justify-center shrink-0 text-xs">
                    <i className="fa-solid fa-robot animate-spin" />
                  </div>
                  <span>Thinking...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Quick Suggested Chips */}
            <div className="px-4 py-2 bg-slate-950/50 border-t border-slate-800/60 flex items-center gap-2 overflow-x-auto text-xs whitespace-nowrap scrollbar-none">
              <button
                type="button"
                onClick={() => handleSend('How do AI micro-lease agreements protect owners?')}
                className="px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 border border-slate-700 transition"
              >
                🛡️ Micro-Lease Protections
              </button>
              <button
                type="button"
                onClick={() => handleSend('How much can I earn renting an empty garage?')}
                className="px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 border border-slate-700 transition"
              >
                💰 Garage Earnings
              </button>
              <button
                type="button"
                onClick={() => handleSend('Find me a podcast studio with natural light')}
                className="px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 border border-slate-700 transition"
              >
                🎙️ Find Podcast Studio
              </button>
            </div>

            {/* Input Bar */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="p-3 bg-slate-950 border-t border-slate-800 flex gap-2"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about spaces, rules, or earnings..."
                className="flex-grow bg-slate-900 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
              />
              <button
                type="submit"
                disabled={loading}
                className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 rounded-xl font-medium text-sm transition shrink-0 flex items-center justify-center disabled:opacity-50"
              >
                <i className="fa-solid fa-arrow-up" />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
