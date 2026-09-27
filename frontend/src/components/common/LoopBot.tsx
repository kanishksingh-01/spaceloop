import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { sendChatMessage, ChatMessage } from '../../services/ai';

export const LoopBot: React.FC = () => {
  const location = useLocation();
  const spaceMatch = location.pathname.match(/^\/space\/(\d+)/);
  const currentSpaceId = spaceMatch ? parseInt(spaceMatch[1], 10) : undefined;

  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        "Hi! I'm LoopBot, your SpaceLoop AI concierge. Whether you need a focus desk, client meeting suite, podcast studio, maker workshop, or want to monetize idle square footage — ask away!",
    },
  ]);
  const [loading, setLoading] = useState(false);

  // Position and Size state for draggable and resizable window
  const [size, setSize] = useState({ width: 410, height: 530 });
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Ref tracking to avoid stale closures in window event listeners
  const dragRef = useRef({
    startX: 0,
    startY: 0,
    initPosX: 0,
    initPosY: 0,
  });

  const resizeRef = useRef({
    startX: 0,
    startY: 0,
    initW: 0,
    initH: 0,
  });

  const sizeRef = useRef(size);
  sizeRef.current = size;

  const positionRef = useRef(position);
  positionRef.current = position;

  // Initialize position when first opened
  useEffect(() => {
    if (isOpen && !position) {
      const isMobile = window.innerWidth < 640;
      const defaultW = isMobile ? Math.min(390, window.innerWidth - 16) : Math.min(410, window.innerWidth - 24);
      const defaultH = isMobile ? Math.min(500, window.innerHeight - 90) : Math.min(530, window.innerHeight - 100);
      const defaultX = Math.max(8, window.innerWidth - defaultW - (isMobile ? 8 : 20));
      const defaultY = Math.max(8, window.innerHeight - defaultH - (isMobile ? 75 : 24));

      setSize({ width: defaultW, height: defaultH });
      setPosition({ x: defaultX, y: defaultY });
    }
  }, [isOpen, position]);

  // Keep window clamped within visible viewport on window resize
  useEffect(() => {
    const handleViewportResize = () => {
      const currentSize = sizeRef.current;
      const currentPos = positionRef.current;
      const isMobile = window.innerWidth < 640;

      const maxAllowedW = Math.min(720, window.innerWidth - 16);
      const maxAllowedH = Math.min(850, window.innerHeight - (isMobile ? 80 : 20));

      const minW = isMobile ? Math.min(290, window.innerWidth - 16) : 310;
      const minH = 360;

      const clampedW = Math.max(minW, Math.min(currentSize.width, maxAllowedW));
      const clampedH = Math.max(minH, Math.min(currentSize.height, maxAllowedH));

      setSize({ width: clampedW, height: clampedH });

      if (currentPos) {
        const clampedX = Math.max(8, Math.min(currentPos.x, window.innerWidth - clampedW - 8));
        const clampedY = Math.max(8, Math.min(currentPos.y, window.innerHeight - clampedH - (isMobile ? 75 : 8)));
        setPosition({ x: clampedX, y: clampedY });
      }
    };

    window.addEventListener('resize', handleViewportResize);
    return () => window.removeEventListener('resize', handleViewportResize);
  }, []);

  // Auto scroll messages smoothly
  useEffect(() => {
    if (isOpen && !isMinimized && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen, isMinimized]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && !isMinimized && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen, isMinimized]);

  // Dragging logic
  const handleHeaderPointerDown = (e: React.MouseEvent | React.TouchEvent) => {
    const target = e.target as HTMLElement;
    // Don't drag if clicking buttons, inputs, links, or controls
    if (
      target.closest('button') ||
      target.closest('input') ||
      target.closest('a') ||
      target.closest('form')
    ) {
      return;
    }

    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;

    const currentX = positionRef.current?.x ?? Math.max(8, window.innerWidth - size.width - 20);
    const currentY = positionRef.current?.y ?? Math.max(8, window.innerHeight - size.height - 24);

    dragRef.current = {
      startX: clientX,
      startY: clientY,
      initPosX: currentX,
      initPosY: currentY,
    };

    setIsDragging(true);
    document.body.style.userSelect = 'none';

    const onPointerMove = (moveEvt: MouseEvent | TouchEvent) => {
      const curX = 'touches' in moveEvt ? moveEvt.touches[0].clientX : moveEvt.clientX;
      const curY = 'touches' in moveEvt ? moveEvt.touches[0].clientY : moveEvt.clientY;

      const deltaX = curX - dragRef.current.startX;
      const deltaY = curY - dragRef.current.startY;

      const currentW = sizeRef.current.width;
      const currentH = sizeRef.current.height;
      const isMobile = window.innerWidth < 640;

      // Keep within visible viewport
      const boundedX = Math.max(8, Math.min(dragRef.current.initPosX + deltaX, window.innerWidth - currentW - 8));
      const boundedY = Math.max(8, Math.min(dragRef.current.initPosY + deltaY, window.innerHeight - currentH - (isMobile ? 75 : 8)));

      setPosition({ x: boundedX, y: boundedY });
    };

    const onPointerUp = () => {
      setIsDragging(false);
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', onPointerMove);
      window.removeEventListener('mouseup', onPointerUp);
      window.removeEventListener('touchmove', onPointerMove);
      window.removeEventListener('touchend', onPointerUp);
    };

    window.addEventListener('mousemove', onPointerMove, { passive: true });
    window.addEventListener('mouseup', onPointerUp);
    window.addEventListener('touchmove', onPointerMove, { passive: true });
    window.addEventListener('touchend', onPointerUp);
  };

  // Resizing logic
  const handleResizePointerDown = (e: React.MouseEvent | React.TouchEvent) => {
    e.stopPropagation();
    e.preventDefault();

    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;

    resizeRef.current = {
      startX: clientX,
      startY: clientY,
      initW: sizeRef.current.width,
      initH: sizeRef.current.height,
    };

    setIsResizing(true);
    document.body.style.userSelect = 'none';

    const onPointerMove = (moveEvt: MouseEvent | TouchEvent) => {
      const curX = 'touches' in moveEvt ? moveEvt.touches[0].clientX : moveEvt.clientX;
      const curY = 'touches' in moveEvt ? moveEvt.touches[0].clientY : moveEvt.clientY;

      const deltaX = curX - resizeRef.current.startX;
      const deltaY = curY - resizeRef.current.startY;

      const posX = positionRef.current?.x ?? 0;
      const posY = positionRef.current?.y ?? 0;
      const isMobile = window.innerWidth < 640;

      // Constraints: sensible min and max, bounded by viewport
      const minW = isMobile ? Math.min(290, window.innerWidth - 16) : 310;
      const minH = 360;
      const maxW = Math.max(minW, Math.min(720, window.innerWidth - posX - 8));
      const maxH = Math.max(minH, Math.min(850, window.innerHeight - posY - (isMobile ? 75 : 8)));

      const newW = Math.max(minW, Math.min(resizeRef.current.initW + deltaX, maxW));
      const newH = Math.max(minH, Math.min(resizeRef.current.initH + deltaY, maxH));

      setSize({ width: newW, height: newH });
    };

    const onPointerUp = () => {
      setIsResizing(false);
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', onPointerMove);
      window.removeEventListener('mouseup', onPointerUp);
      window.removeEventListener('touchmove', onPointerMove);
      window.removeEventListener('touchend', onPointerUp);
    };

    window.addEventListener('mousemove', onPointerMove);
    window.addEventListener('mouseup', onPointerUp);
    window.addEventListener('touchmove', onPointerMove);
    window.addEventListener('touchend', onPointerUp);
  };

  const handleSend = async (messageText?: string) => {
    const textToSend = (messageText || input).trim();
    if (!textToSend || loading) return;

    setInput('');
    const newHistory: ChatMessage[] = [...messages, { role: 'user', content: textToSend }];
    setMessages(newHistory);
    setLoading(true);

    try {
      const resp = await sendChatMessage(textToSend, newHistory, {
        space_id: currentSpaceId,
        current_path: location.pathname,
      });
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

  const renderCleanMessage = useCallback((rawText: string) => {
    if (!rawText) return null;
    const cleaned = rawText
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<[^>]+>/g, '');

    const lines = cleaned.split('\n');

    return (
      <div className="space-y-1.5" style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
        {lines.map((line, lIdx) => {
          if (!line.trim()) {
            return <div key={lIdx} className="h-1" />;
          }

          const parts = line.split(/(\b\*\*.*?\*\*\b|\*\*.*?\*\*)/g);
          const formattedLine = parts.map((part, pIdx) => {
            if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
              return (
                <strong key={pIdx} className="font-semibold text-white">
                  {part.slice(2, -2)}
                </strong>
              );
            }
            return <span key={pIdx}>{part}</span>;
          });

          const isBullet = line.trim().startsWith('•') || line.trim().startsWith('-');
          return (
            <p key={lIdx} className={isBullet ? 'pl-2 text-slate-300 flex items-start gap-1.5' : ''}>
              {isBullet ? <span className="text-purple-400 select-none">•</span> : null}
              <span>{formattedLine}</span>
            </p>
          );
        })}
      </div>
    );
  }, []);

  return (
    <>
      {/* 1. Floating Launcher Button (Bottom-Right, zero background overlay) */}
      {(!isOpen || isMinimized) && (
        <div className="fixed bottom-20 md:bottom-6 right-4 sm:right-6 z-40 animate-in fade-in duration-200 pointer-events-auto">
          <button
            type="button"
            onClick={() => {
              setIsOpen(true);
              setIsMinimized(false);
            }}
            className="group flex items-center gap-2.5 px-4 py-3 rounded-full bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 text-white font-bold text-xs shadow-lg shadow-indigo-950/60 hover:shadow-[0_0_24px_rgba(168,85,247,0.55)] border border-indigo-400/40 hover:border-purple-300 transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
            title="Open SpaceLoop AI Concierge"
          >
            <div className="relative flex items-center justify-center">
              <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center">
                <i className="fa-solid fa-robot text-xs text-white group-hover:rotate-12 transition-transform duration-300" />
              </div>
              <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-slate-900 animate-pulse" />
            </div>
            <span className="tracking-wide">Ask LoopBot</span>
            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-white/15 text-purple-100 border border-white/10 group-hover:bg-purple-500/25 transition-colors">
              AI
            </span>
          </button>
        </div>
      )}

      {/* 2. Floating, Freely Draggable & Resizable Window (Zero Fullscreen Backdrop) */}
      {isOpen && !isMinimized && position && (
        <aside
          role="complementary"
          aria-label="LoopBot AI Assistant"
          style={{
            position: 'fixed',
            left: `${position.x}px`,
            top: `${position.y}px`,
            width: `${size.width}px`,
            height: `${size.height}px`,
            zIndex: 50,
          }}
          className={`rounded-2xl sm:rounded-3xl bg-slate-900/95 backdrop-blur-2xl border ${
            isDragging || isResizing
              ? 'border-purple-400/80 ring-2 ring-purple-500/40 shadow-[0_20px_60px_-10px_rgba(0,0,0,0.85),0_0_35px_rgba(168,85,247,0.35)]'
              : 'border-indigo-500/30 hover:border-purple-500/40 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.8),0_0_30px_rgba(99,102,241,0.2)]'
          } flex flex-col overflow-hidden animate-in fade-in duration-150 pointer-events-auto select-auto`}
        >
          {/* Header - Acts as Draggable Handle */}
          <div
            onMouseDown={handleHeaderPointerDown}
            onTouchStart={handleHeaderPointerDown}
            className={`px-3.5 sm:px-4 py-3 bg-slate-950/90 border-b border-slate-800/80 flex items-center justify-between gap-2.5 shrink-0 cursor-grab ${
              isDragging ? 'cursor-grabbing bg-slate-900/90' : 'hover:bg-slate-950'
            } transition-colors select-none`}
            title="Drag header to reposition anywhere"
          >
            <div className="flex items-center gap-2.5 min-w-0 pointer-events-none">
              <div className="relative">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-indigo-700 flex items-center justify-center text-white text-xs shadow-md shadow-purple-600/30 border border-white/10">
                  <i className="fa-solid fa-robot" />
                </div>
                <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-slate-900 animate-pulse" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-bold text-white tracking-tight truncate">
                    LoopBot AI
                  </span>
                  <span className="px-1.5 py-0.2 rounded-full text-[9px] font-mono font-bold bg-cyan-500/10 text-cyan-300 border border-cyan-500/25">
                    Concierge
                  </span>
                  {currentSpaceId && (
                    <span className="px-1.5 py-0.2 rounded-full text-[9px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      Space #{currentSpaceId}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1.5 text-[10px] text-emerald-400 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span>Online</span>
                  <span className="text-slate-500 font-normal hidden sm:inline">• Drag header to move</span>
                </div>
              </div>
            </div>

            {/* Window Controls */}
            <div className="flex items-center gap-1 shrink-0">
              {/* Reset Position Button */}
              <button
                type="button"
                onClick={() => {
                  const isMobile = window.innerWidth < 640;
                  const defaultW = isMobile ? Math.min(390, window.innerWidth - 16) : Math.min(410, window.innerWidth - 24);
                  const defaultH = isMobile ? Math.min(500, window.innerHeight - 90) : Math.min(530, window.innerHeight - 100);
                  setSize({ width: defaultW, height: defaultH });
                  setPosition({
                    x: Math.max(8, window.innerWidth - defaultW - (isMobile ? 8 : 20)),
                    y: Math.max(8, window.innerHeight - defaultH - (isMobile ? 75 : 24)),
                  });
                }}
                className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg text-slate-400 hover:text-purple-300 hover:bg-purple-950/40 hover:shadow-[0_0_12px_rgba(168,85,247,0.35)] transition-all flex items-center justify-center text-[10px] cursor-pointer"
                title="Reset position & size"
                aria-label="Reset position & size"
              >
                <i className="fa-solid fa-arrows-rotate" />
              </button>
              {/* Minimize Button */}
              <button
                type="button"
                onClick={() => setIsMinimized(true)}
                className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg text-slate-400 hover:text-purple-300 hover:bg-purple-950/40 hover:shadow-[0_0_12px_rgba(168,85,247,0.35)] transition-all flex items-center justify-center text-xs cursor-pointer"
                title="Minimize chat"
                aria-label="Minimize chat"
              >
                <i className="fa-solid fa-minus" />
              </button>
              {/* Close Button */}
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg text-slate-400 hover:text-rose-300 hover:bg-rose-950/40 hover:shadow-[0_0_12px_rgba(244,63,94,0.35)] transition-all flex items-center justify-center text-xs cursor-pointer"
                title="Close chat"
                aria-label="Close chat"
              >
                <i className="fa-solid fa-xmark text-sm" />
              </button>
            </div>
          </div>

          {/* Scrollable Message History */}
          <div className="flex-1 p-3.5 sm:p-4 overflow-y-auto space-y-3 text-xs sm:text-[13px] scrollbar-thin scrollbar-thumb-slate-800">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-2.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-6 h-6 rounded-lg bg-indigo-600/25 border border-indigo-500/30 text-indigo-300 flex items-center justify-center shrink-0 text-[10px] mt-0.5">
                    <i className="fa-solid fa-robot" />
                  </div>
                )}
                <div
                  className={`p-3 rounded-2xl max-w-[85%] leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-tr-xs shadow-md shadow-indigo-600/20 whitespace-pre-wrap'
                      : 'bg-slate-800/90 text-slate-200 rounded-tl-xs border border-slate-700/60 shadow-sm'
                  }`}
                  style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}
                >
                  {msg.role === 'user' ? msg.content : renderCleanMessage(msg.content)}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-2 items-center text-slate-400 text-xs">
                <div className="w-6 h-6 rounded-lg bg-indigo-600/25 border border-indigo-500/30 text-indigo-300 flex items-center justify-center shrink-0 text-[10px]">
                  <i className="fa-solid fa-robot animate-spin" />
                </div>
                <div className="flex items-center gap-1.5 bg-slate-800/80 px-3 py-2 rounded-2xl rounded-tl-xs border border-slate-700/50">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Suggested Topic Chips (RAG & Orchestrator Powered) */}
          <div className="px-3 py-2 bg-slate-950/60 border-t border-slate-800/60 flex items-center gap-1.5 overflow-x-auto text-[11px] whitespace-nowrap scrollbar-none shrink-0">
            {(currentSpaceId
              ? [
                  { label: '⚡ Amenities (RAG)', prompt: 'What amenities does this space have?' },
                  { label: '🥪 Food Policy (RAG)', prompt: 'Can I bring food?' },
                  { label: '👥 Team Meeting Fit', prompt: 'Is this good for a team meeting?' },
                  { label: '💰 4-Hour Price Breakdown', prompt: 'How much for 4 hours?' },
                  { label: '🚀 Book Space', prompt: 'Book this space' },
                ]
              : [
                  { label: '🔍 Spaces for 8 (Search)', prompt: 'Find spaces for 8 people' },
                  { label: '📅 Availability Tomorrow', prompt: "What's available tomorrow?" },
                  { label: '💰 Calculate 4 Hours', prompt: 'How much for 4 hours?' },
                  { label: '⚖️ Compare Spaces (DB+RAG)', prompt: 'Compare these spaces' },
                  { label: '💼 Quiet Work Desk', prompt: 'Find a quiet workspace for 3 hours with fiber WiFi' },
                  { label: '🛡️ Section 52 & Escrow', prompt: 'How do AI micro-leases and ₹100 UPI escrow protect hosts?' },
                ]
            ).map((chip, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSend(chip.prompt)}
                className="px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-purple-950/50 text-slate-300 hover:text-purple-200 border border-slate-700/60 hover:border-purple-500/50 hover:shadow-[0_0_12px_rgba(168,85,247,0.3)] transition-all shrink-0 cursor-pointer"
              >
                {chip.label}
              </button>
            ))}
          </div>

          {/* Input Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="p-3 bg-slate-950 border-t border-slate-800/80 flex items-center gap-2 shrink-0 relative"
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about spaces, rules, or earnings..."
              className="flex-1 bg-slate-900 border border-slate-700/80 rounded-xl px-3.5 py-2 pr-2 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/40 transition"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="w-9 h-9 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 hover:from-indigo-500 hover:to-purple-500 text-white font-medium text-xs transition shrink-0 flex items-center justify-center disabled:opacity-40 shadow-sm shadow-indigo-600/30 hover:shadow-[0_0_16px_rgba(168,85,247,0.5)] cursor-pointer"
              title="Send message"
            >
              <i className="fa-solid fa-arrow-up" />
            </button>
          </form>

          {/* 3. Resize Handle at Bottom-Right Corner */}
          <div
            onMouseDown={handleResizePointerDown}
            onTouchStart={handleResizePointerDown}
            title="Drag to resize window"
            aria-label="Resize chatbot window"
            className="absolute bottom-0 right-0 w-6 h-6 cursor-se-resize flex items-end justify-end p-1.5 text-slate-500 hover:text-purple-400 active:text-purple-300 transition-colors z-20 group select-none hover:drop-shadow-[0_0_8px_rgba(168,85,247,0.6)]"
          >
            <svg
              width="11"
              height="11"
              viewBox="0 0 10 10"
              className="fill-current opacity-60 group-hover:opacity-100 group-hover:scale-110 transition-all"
            >
              <circle cx="8" cy="8" r="1.1" />
              <circle cx="5" cy="8" r="1.1" />
              <circle cx="8" cy="5" r="1.1" />
              <circle cx="2" cy="8" r="1.1" />
              <circle cx="5" cy="5" r="1.1" />
              <circle cx="8" cy="2" r="1.1" />
            </svg>
          </div>
        </aside>
      )}
    </>
  );
};

export default LoopBot;
