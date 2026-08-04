import React, { useState } from 'react';
import { Bot, User, Copy, Check, BookOpen } from 'lucide-react';
import { ChatMessage, DocumentSource } from '../lib/api';

interface MessageItemProps {
  message: ChatMessage;
  sources?: DocumentSource[];
}

export const MessageItem: React.FC<MessageItemProps> = ({ message, sources }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={`flex gap-4 p-5 md:px-6 border-b border-border-subtle transition-colors ${
        isUser ? 'bg-transparent' : 'bg-white/[0.02]'
      }`}
    >
      {/* Avatar */}
      <div
        className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
          isUser
            ? 'bg-bg-tertiary text-text-secondary'
            : 'bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 shadow-glow text-white'
        }`}
      >
        {isUser ? <User size={18} /> : <Bot size={20} />}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-center mb-1.5">
          <span className={`text-sm font-semibold ${isUser ? 'text-text-secondary' : 'text-accent-primary'}`}>
            {isUser ? 'You' : 'Enterprise AI Assistant'}
          </span>
          {!isUser && (
            <button
              onClick={handleCopy}
              className="bg-transparent border-none text-text-muted hover:text-text-primary transition-colors cursor-pointer flex items-center gap-1 text-xs"
            >
              {copied ? <Check size={14} className="text-accent-emerald" /> : <Copy size={14} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          )}
        </div>

        <div className="text-[0.9375rem] leading-relaxed text-text-primary whitespace-pre-wrap">
          {message.content}
        </div>

        {/* RAG Retrieved Sources Badges */}
        {!isUser && sources && sources.length > 0 && (
          <div className="mt-4 pt-3 border-t border-dashed border-border-subtle">
            <div className="flex items-center gap-1.5 text-xs text-accent-emerald font-semibold mb-2">
              <BookOpen size={14} /> Retrieved Knowledge Sources ({sources.length}):
            </div>
            <div className="flex flex-wrap gap-2">
              {sources.map((src, idx) => (
                <div
                  key={idx}
                  className="bg-accent-emerald/8 border border-accent-emerald/25 rounded-md p-2 max-w-[280px] text-xs"
                >
                  <p className="font-semibold text-text-primary truncate">{src.title}</p>
                  <p className="text-text-muted text-[0.7rem] truncate mt-0.5">
                    {src.snippet}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
