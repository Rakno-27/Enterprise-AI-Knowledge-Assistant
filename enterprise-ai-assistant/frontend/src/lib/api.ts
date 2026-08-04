export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface DocumentSource {
  id: string;
  title: string;
  snippet: string;
  score: number;
}

export interface ChatCompletionResponse {
  id: string;
  role: string;
  content: string;
  model: string;
  created: string;
  sources?: DocumentSource[];
}

export interface DocumentMetadata {
  id: string;
  filename: string;
  file_type: string;
  size_bytes: number;
  uploaded_at: string;
  chunks_count: number;
}

export interface AIModel {
  id: string;
  name: string;
  context_window: number;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export async function fetchHealthStatus(): Promise<{ status: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error('Backend health check failed');
    return await res.json();
  } catch (err) {
    return { status: 'offline' };
  }
}

export async function fetchModels(): Promise<AIModel[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/models`);
    if (!res.ok) throw new Error('Failed to fetch models');
    const data = await res.json();
    return data.models;
  } catch (err) {
    return [
      { id: 'gpt-4o-mini', name: 'GPT-4o Mini (Fast)', context_window: 128000 },
      { id: 'gpt-4o', name: 'GPT-4o (High Precision)', context_window: 128000 }
    ];
  }
}

export async function sendChatMessage(
  messages: ChatMessage[],
  model: string = 'gpt-4o-mini',
  useRag: boolean = true
): Promise<ChatCompletionResponse> {
  const res = await fetch(`${API_BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages,
      model,
      stream: false,
      use_rag: useRag
    })
  });

  if (!res.ok) {
    throw new Error(`Chat completion error: ${res.statusText}`);
  }

  return await res.json();
}

export async function fetchDocuments(): Promise<DocumentMetadata[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    const data = await res.json();
    return data.documents;
  } catch (err) {
    return [];
  }
}

export async function uploadDocument(file: File): Promise<DocumentMetadata> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData
  });

  if (!res.ok) {
    throw new Error('Failed to upload document');
  }

  const data = await res.json();
  return data.document;
}

export async function deleteDocument(docId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/documents/${docId}`, {
      method: 'DELETE'
    });
    return res.ok;
  } catch (err) {
    return false;
  }
}
