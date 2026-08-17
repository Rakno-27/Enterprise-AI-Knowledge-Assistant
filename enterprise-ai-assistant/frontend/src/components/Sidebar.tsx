import React from 'react';
import { Plus, Database, Cpu, Trash2, ShieldCheck, FileText } from 'lucide-react';
import { DocumentMetadata, AIModel } from '../lib/api';

interface SidebarProps {
  onNewChat: () => void;
  models: AIModel[];
  selectedModel: string;
  onSelectModel: (modelId: string) => void;
  useRag: boolean;
  onToggleRag: (val: boolean) => void;
  documents: DocumentMetadata[];
  onOpenUploadModal: () => void;
  onDeleteDoc: (docId: string) => void;
  serverStatus: string;
  userRole: string;
  userEmail: string;
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  onNewChat,
  models,
  selectedModel,
  onSelectModel,
  useRag,
  onToggleRag,
  documents,
  onOpenUploadModal,
  onDeleteDoc,
  serverStatus,
  userRole,
  userEmail,
  onLogout,
}) => {
  return (
    <aside className="w-[300px] h-full bg-bg-secondary border-r border-border-subtle flex flex-col p-5 gap-5 shrink-0">
      {/* Header Branding */}
      <div className="flex items-center gap-3 pb-3 border-b border-border-subtle">
        <div className="w-[38px] h-[38px] rounded-lg bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-glow">
          <ShieldCheck size={22} className="text-white" />
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight text-text-primary">
            Enterprise <span className="gradient-text">AI</span>
          </h1>
          <div className="flex items-center gap-1.5 text-[0.75rem] text-text-muted">
            <span className={`w-1.5 h-1.5 rounded-full ${serverStatus === 'healthy' ? 'bg-accent-emerald' : 'bg-red-500'}`} />
            <span>{serverStatus === 'healthy' ? 'v1.0.0 Online' : 'Connecting...'}</span>
          </div>
        </div>
      </div>

      {/* New Chat Button */}
      <button className="btn-primary w-full justify-center" onClick={onNewChat}>
        <Plus size={18} /> New Conversation
      </button>

      {/* Model Selector & Settings */}
      <div className="flex flex-col gap-3">
        <label className="text-[0.75rem] font-semibold text-text-muted uppercase tracking-wider">
          Intelligence Model
        </label>
        <div className="flex items-center gap-2 bg-white/5 px-3 py-2 rounded-md border border-border-subtle">
          <Cpu size={16} className="text-accent-primary" />
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            className="bg-transparent border-none text-text-primary text-sm w-full outline-none cursor-pointer"
          >
            {models.map((m) => (
              <option key={m.id} value={m.id} className="bg-bg-secondary text-text-primary">
                {m.name}
              </option>
            ))}
          </select>
        </div>

        {/* RAG Context Toggle */}
        <div className="flex items-center justify-between px-3 py-2.5 bg-white/[0.03] rounded-md border border-border-subtle">
          <div className="flex items-center gap-2">
            <Database size={16} className="text-accent-emerald" />
            <span className="text-sm font-medium text-text-primary">RAG Context</span>
          </div>
          <input
            type="checkbox"
            checked={useRag}
            onChange={(e) => onToggleRag(e.target.checked)}
            className="cursor-pointer w-4 h-4 accent-accent-primary"
          />
        </div>
      </div>

      {/* Knowledge Base Section */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex justify-between items-center mb-2.5">
          <span className="text-[0.75rem] font-semibold text-text-muted uppercase tracking-wider">
            Knowledge Base ({documents.length})
          </span>
          <button
            onClick={onOpenUploadModal}
            className="bg-transparent border-none text-accent-primary text-xs font-semibold cursor-pointer hover:text-accent-hover transition-colors"
          >
            + Ingest
          </button>
        </div>

        <div className="flex-1 overflow-y-auto flex flex-col gap-2">
          {documents.length === 0 ? (
            <p className="text-xs text-text-muted italic text-center mt-5">
              No documents indexed. Click Ingest to upload.
            </p>
          ) : (
            documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-2.5 bg-white/[0.03] rounded-md border border-border-subtle text-xs"
              >
                <div className="flex items-center gap-2 overflow-hidden mr-2">
                  <FileText size={14} className="text-text-muted shrink-0" />
                  <span className="truncate text-text-primary">
                    {doc.filename}
                  </span>
                </div>
                <button
                  onClick={() => onDeleteDoc(doc.id)}
                  className="bg-transparent border-none text-red-400 opacity-60 hover:opacity-100 transition-opacity cursor-pointer"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* User Info / Logout */}
      <div className="pt-4 border-t border-border-subtle flex flex-col gap-2.5">
        <div className="flex items-center justify-between text-xs text-text-muted">
          <span>Active Session:</span>
          <span className="font-semibold text-text-primary capitalize">{userRole}</span>
        </div>
        <div className="flex items-center justify-between gap-2">
          <span className="text-[0.75rem] text-text-muted truncate">{userEmail}</span>
          <button
            onClick={onLogout}
            className="text-[0.75rem] text-red-400 font-semibold bg-transparent border-none cursor-pointer hover:underline"
          >
            Logout
          </button>
        </div>
      </div>
    </aside>
  );
};

