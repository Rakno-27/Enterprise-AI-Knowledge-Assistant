import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { ChatInput } from './components/ChatInput';
import { DocumentModal } from './components/DocumentModal';
import {
  ChatMessage,
  DocumentSource,
  DocumentMetadata,
  AIModel,
  fetchModels,
  fetchDocuments,
  fetchHealthStatus,
  sendChatMessage,
  deleteDocument,
  getAuthToken,
  setAuthToken,
} from './lib/api';
import { ShieldCheck, User, ShieldAlert } from 'lucide-react';

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [lastSources, setLastSources] = useState<DocumentSource[]>([]);
  const [models, setModels] = useState<AIModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('gpt-4o-mini');
  const [useRag, setUseRag] = useState<boolean>(true);
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [serverStatus, setServerStatus] = useState<string>('connecting');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  // Authentication State
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!getAuthToken());
  const [userRole, setUserRole] = useState<string>(
    getAuthToken() === 'mock_admin' ? 'admin' : getAuthToken() ? 'user' : ''
  );
  const [userEmail, setUserEmail] = useState<string>(
    getAuthToken() === 'mock_admin' ? 'admin@enterprise.com' : getAuthToken() ? 'user@enterprise.com' : ''
  );

  useEffect(() => {
    async function initData() {
      const health = await fetchHealthStatus();
      setServerStatus(health.status);

      const modelsData = await fetchModels();
      setModels(modelsData);
      if (modelsData.length > 0) {
        setSelectedModel(modelsData[0].id);
      }

      if (isAuthenticated) {
        try {
          const docsData = await fetchDocuments();
          setDocuments(docsData);
        } catch (err) {
          console.error("Failed to load documents: ", err);
        }
      }
    }
    initData();
  }, [isAuthenticated]);

  const handleLogin = (role: 'admin' | 'user') => {
    const token = role === 'admin' ? 'mock_admin' : 'mock_user';
    setAuthToken(token);
    setUserRole(role);
    setUserEmail(role === 'admin' ? 'admin@enterprise.com' : 'user@enterprise.com');
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setAuthToken(null);
    setIsAuthenticated(false);
    setUserRole('');
    setUserEmail('');
    setMessages([]);
    setLastSources([]);
    setDocuments([]);
  };

  const handleSendMessage = async (text: string) => {
    const userMsg: ChatMessage = { role: 'user', content: text };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setIsLoading(true);

    try {
      const response = await sendChatMessage(updatedMessages, selectedModel, useRag);
      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: response.content,
      };
      setMessages([...updatedMessages, assistantMsg]);
      if (response.sources) {
        setLastSources(response.sources);
      }
    } catch (err) {
      setMessages([
        ...updatedMessages,
        {
          role: 'assistant',
          content: '⚠️ Connection Error: Unable to reach Enterprise AI Backend. Please ensure the backend server is running on port 8000.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setLastSources([]);
  };

  const handleDeleteDoc = async (docId: string) => {
    const success = await deleteDocument(docId);
    if (success) {
      setDocuments(documents.filter((d) => d.id !== docId));
    }
  };

  const handleDocumentUploaded = (doc: DocumentMetadata) => {
    setDocuments((prev) => [doc, ...prev]);
  };

  if (!isAuthenticated) {
    return (
      <div className="flex w-screen h-screen items-center justify-center bg-bg-primary p-5 relative overflow-hidden">
        {/* Decorative ambient background glows */}
        <div className="absolute w-[400px] h-[400px] rounded-full bg-indigo-500/10 blur-[120px] -top-20 -left-20" />
        <div className="absolute w-[400px] h-[400px] rounded-full bg-pink-500/10 blur-[120px] -bottom-20 -right-20" />

        <div className="glass-panel max-w-[420px] w-full p-8 rounded-2xl flex flex-col items-center shadow-glow text-center border border-white/10 relative z-10">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center mb-6 shadow-glow text-white">
            <ShieldCheck size={28} />
          </div>

          <h2 className="text-xl font-bold mb-2 text-text-primary">Enterprise AI Portal</h2>
          <p className="text-xs text-text-muted mb-8 leading-relaxed max-w-[280px]">
            Please sign in using your corporate account to access document retrieval systems.
          </p>

          <div className="flex flex-col gap-4.5 w-full">
            <button
              onClick={() => handleLogin('admin')}
              className="w-full flex items-center justify-center gap-3 px-5 py-3 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-sm transition-all shadow-glow hover:scale-[1.01] cursor-pointer"
            >
              <ShieldCheck size={18} />
              <span>Sign in as Administrator</span>
            </button>

            <button
              onClick={() => handleLogin('user')}
              className="w-full flex items-center justify-center gap-3 px-5 py-3 rounded-lg bg-white/5 hover:bg-white/10 text-text-primary border border-border-subtle hover:border-white/20 font-semibold text-sm transition-all hover:scale-[1.01] cursor-pointer"
            >
              <User size={18} className="text-text-secondary" />
              <span>Sign in as Standard User</span>
            </button>
          </div>

          <div className="mt-8 pt-6 border-t border-border-subtle w-full text-[0.7rem] text-text-muted flex items-center justify-center gap-1.5 leading-none">
            <ShieldAlert size={12} className="text-accent-primary" />
            <span>Secure Federated SSO Session (Auth0 / JWT)</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-screen h-screen overflow-hidden bg-bg-primary">
      <Sidebar
        onNewChat={handleNewChat}
        models={models}
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        useRag={useRag}
        onToggleRag={setUseRag}
        documents={documents}
        onOpenUploadModal={() => setIsModalOpen(true)}
        onDeleteDoc={handleDeleteDoc}
        serverStatus={serverStatus}
        userRole={userRole}
        userEmail={userEmail}
        onLogout={handleLogout}
      />

      <main className="flex-1 flex flex-col min-w-0 bg-bg-primary relative">
        <ChatArea
          messages={messages}
          lastSources={lastSources}
          isLoading={isLoading}
          onSelectPrompt={handleSendMessage}
        />

        <ChatInput
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          onOpenUpload={() => setIsModalOpen(true)}
          selectedModel={selectedModel}
        />
      </main>

      <DocumentModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onDocumentUploaded={handleDocumentUploaded}
      />
    </div>
  );
}

export default App;
