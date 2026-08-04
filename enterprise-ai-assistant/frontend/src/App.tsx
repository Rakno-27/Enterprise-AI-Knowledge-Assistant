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
} from './lib/api';

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

  useEffect(() => {
    async function initData() {
      const health = await fetchHealthStatus();
      setServerStatus(health.status);

      const modelsData = await fetchModels();
      setModels(modelsData);
      if (modelsData.length > 0) {
        setSelectedModel(modelsData[0].id);
      }

      const docsData = await fetchDocuments();
      setDocuments(docsData);
    }
    initData();
  }, []);

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
