import React, { useState } from 'react';
import { Upload, X, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { uploadDocument, DocumentMetadata } from '../lib/api';

interface DocumentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDocumentUploaded: (doc: DocumentMetadata) => void;
}

export const DocumentModal: React.FC<DocumentModalProps> = ({
  isOpen,
  onClose,
  onDocumentUploaded,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setError(null);
      setSuccess(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setError(null);
    try {
      const doc = await uploadDocument(selectedFile);
      setSuccess(`Successfully indexed "${doc.filename}"`);
      onDocumentUploaded(doc);
      setTimeout(() => {
        setSuccess(null);
        setSelectedFile(null);
        onClose();
      }, 1500);
    } catch (err) {
      setError('Failed to upload and index document. Check backend connection.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm">
      <div className="w-[90%] max-w-[520px] bg-bg-secondary border border-border-subtle rounded-lg p-6 shadow-card">
        <div className="flex justify-between items-center mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-md bg-accent-primary/15 flex items-center justify-center text-accent-primary">
              <Upload size={20} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Knowledge Base Ingestion</h3>
              <p className="text-xs text-text-muted">Index PDF, TXT, or MD documents for RAG context</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-primary transition-colors cursor-pointer"
          >
            <X size={20} />
          </button>
        </div>

        <div
          className={`border-2 border-dashed border-border-subtle rounded-md py-8 px-4 text-center cursor-pointer transition-colors ${
            selectedFile ? 'bg-accent-primary/5 border-accent-primary/45' : 'hover:border-text-muted'
          }`}
          onClick={() => document.getElementById('file-input-modal')?.click()}
        >
          <input
            id="file-input-modal"
            type="file"
            accept=".pdf,.txt,.md,.doc,.docx"
            className="hidden"
            onChange={handleFileChange}
          />
          <FileText size={40} className={`mx-auto mb-3 ${selectedFile ? 'text-accent-primary' : 'text-text-muted'}`} />
          {selectedFile ? (
            <div>
              <p className="font-semibold text-text-primary">{selectedFile.name}</p>
              <p className="text-xs text-text-muted">{(selectedFile.size / 1024).toFixed(1)} KB</p>
            </div>
          ) : (
            <div>
              <p className="font-medium text-text-primary mb-1">Click or drag file to upload</p>
              <p className="text-xs text-text-muted">Supports PDF, TXT, Markdown (Max 25MB)</p>
            </div>
          )}
        </div>

        {error && (
          <div className="mt-4 flex items-center gap-2 text-red-400 text-sm">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mt-4 flex items-center gap-2 text-emerald-400 text-sm">
            <CheckCircle2 size={16} />
            <span>{success}</span>
          </div>
        )}

        <div className="flex justify-end gap-3 mt-6">
          <button className="btn-secondary" onClick={onClose} disabled={uploading}>
            Cancel
          </button>
          <button className="btn-primary" onClick={handleUpload} disabled={!selectedFile || uploading}>
            {uploading ? (
              <>
                <Loader2 size={16} className="animate-spin" /> Ingesting...
              </>
            ) : (
              'Upload & Index'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
