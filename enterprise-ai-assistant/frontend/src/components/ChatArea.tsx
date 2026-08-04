import React, { useRef, useEffect } from 'react';
import { Sparkles, Shield, FileSearch, Code2, Zap } from 'lucide-react';
import { ChatMessage, DocumentSource } from '../lib/api';
import { MessageItem } from './MessageItem';

interface ChatAreaProps {
  messages: ChatMessage[];
  lastSources?: DocumentSource[];
  isLoading: boolean;
  onSelectPrompt: (prompt: string) => void;
}

const SAMPLE_PROMPTS = [
  {
    icon: <Shield size={20} className="text-accent-primary" />,
    title: "Summarize Enterprise AI Policy",
    desc: "Retrieve and analyze data privacy, governance, and MFA guidelines from PDF",
    prompt: "Summarize the Enterprise AI Policy 2026 guidelines on data privacy and MFA."
  },
  {
    icon: <FileSearch size={20} className="text-accent-emerald" />,
    title: "RAG Knowledge Base Query",
    desc: "Perform semantic retrieval over indexed internal documentation",
    prompt: "What are the compliance evaluation requirements for deploying AI models?"
  },
  {
    icon: <Code2 size={20} className="text-pink-500" />,
    title: "Draft FastAPI Integration",
    desc: "Generate Python boilerplate code with Pydantic validation",
    prompt: "Write a FastAPI async router snippet for streaming chat completion endpoint."
  }
];

export const ChatArea: React.FC<ChatAreaProps> = ({
  messages,
  lastSources,
  isLoading,
  onSelectPrompt,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto flex flex-col">
      {messages.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-10 px-5 max-w-[800px] mx-auto text-center">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center mb-6 shadow-glow">
            <Sparkles size={32} className="text-white" />
          </div>

          <h2 className="text-2xl font-bold mb-3 text-text-primary">
            Enterprise Conversational Intelligence
          </h2>
          <p className="text-text-secondary text-sm max-w-[580px] mb-10 leading-relaxed">
            Ask questions, analyze enterprise documents with RAG context, or automate multi-step workflows securely.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
            {SAMPLE_PROMPTS.map((item, idx) => (
              <div
                key={idx}
                className="glass-panel p-5 rounded-lg cursor-pointer text-left hover:scale-[1.02] active:scale-[0.98] transition-transform"
                onClick={() => onSelectPrompt(item.prompt)}
              >
                <div className="mb-3">{item.icon}</div>
                <h4 className="text-sm font-semibold mb-1.5 text-text-primary">{item.title}</h4>
                <p className="text-xs text-text-muted leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col">
          {messages.map((msg, index) => (
            <MessageItem
              key={index}
              message={msg}
              sources={index === messages.length - 1 && msg.role === 'assistant' ? lastSources : undefined}
            />
          ))}
          {isLoading && (
            <div className="p-5 flex items-center gap-3 text-text-muted">
              <Zap size={16} className="pulse-dot text-accent-primary" />
              <span className="text-xs">Enterprise AI is reasoning & retrieving context...</span>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
};
