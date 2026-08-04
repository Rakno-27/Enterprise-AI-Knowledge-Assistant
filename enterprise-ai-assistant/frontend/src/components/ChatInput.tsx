import React, { useState, KeyboardEvent } from 'react';
import { Send, Paperclip, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (content: string) => void;
  isLoading: boolean;
  onOpenUpload: () => void;
  selectedModel: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading,
  onOpenUpload,
  selectedModel,
}) => {
  const [text, setText] = useState('');

  const handleSubmit = () => {
    if (!text.trim() || isLoading) return;
    onSendMessage(text.trim());
    setText('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="p-4 bg-bg-secondary border-t border-border-subtle">
      <div className="relative bg-bg-tertiary rounded-lg border border-border-subtle shadow-lg p-3">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={`Ask Enterprise AI or query documents using ${selectedModel}...`}
          rows={2}
          className="w-full bg-transparent border-none text-text-primary text-[0.9375rem] resize-none outline-none font-inherit"
        />

        <div className="flex justify-between items-center mt-2">
          <div className="flex items-center gap-2">
            <button
              onClick={onOpenUpload}
              title="Attach Document to Knowledge Base"
              className="bg-white/5 border border-border-subtle text-text-secondary rounded-sm px-2.5 py-1.5 cursor-pointer hover:bg-white/10 transition-colors flex items-center gap-1.5 text-[0.75rem]"
            >
              <Paperclip size={14} /> Attach Doc
            </button>
            <span className="text-[0.75rem] text-text-muted">
              Press Shift + Enter for newline
            </span>
          </div>

          <button
            className={`btn-primary px-4 py-2 rounded-md ${
              !text.trim() || isLoading ? 'opacity-50 pointer-events-none' : 'opacity-100'
            }`}
            onClick={handleSubmit}
            disabled={!text.trim() || isLoading}
          >
            {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            <span>Send</span>
          </button>
        </div>
      </div>
    </div>
  );
};
