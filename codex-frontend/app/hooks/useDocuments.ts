"use client";

import { useState, useCallback } from "react";
import type { Document } from "../lib/types";
import { API_BASE } from "../lib/constants";
import { toast } from "sonner";

export function useDocuments(authFetch: (url: string, options?: RequestInit) => Promise<Response>) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [sessionFiles, setSessionFiles] = useState<Document[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadingFile, setUploadingFile] = useState(false);
  const [showDocManager, setShowDocManager] = useState(false);

  const fetchDocuments = useCallback(async () => {
    setLoadingDocs(true);
    try {
      const res = await authFetch(`${API_BASE}/documents`);
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (err) {
      console.error("Failed to fetch documents:", err);
    } finally {
      setLoadingDocs(false);
    }
  }, [authFetch]);

  const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadStatus("Uploading...");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await authFetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });
      if (response.ok) {
        setUploadStatus(`Success: ${file.name} uploaded and ingested.`);
        toast.success(`${file.name} uploaded and ingested`);
        fetchDocuments();
        setTimeout(() => setUploadStatus(""), 2000);
      } else {
        const err = await response.text().catch(() => "Unknown error");
        setUploadStatus("Upload failed. Check server logs.");
        toast.error(`Upload failed: ${err}`);
      }
    } catch (error) {
      setUploadStatus("Network error during upload.");
      toast.error("Network error during upload.");
    }
  }, [authFetch, fetchDocuments]);

  const handleTemporalFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>, threadId: string) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingFile(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await authFetch(`${API_BASE}/upload/temporal?thread_id=${threadId}`, {
        method: "POST",
        body: formData,
      });
      if (response.ok) {
        fetchDocuments();
      }
    } catch (error) {
      console.error("Error uploading temporal document:", error);
    } finally {
      setUploadingFile(false);
    }
  }, [authFetch, fetchDocuments]);

  const handleDeleteDocument = useCallback(async (filename: string, docThreadId?: string) => {
    if (!confirm(`Are you sure you want to delete ${filename} and all its chunks from the vector database?`)) return;
    try {
      const url = new URL(`${API_BASE}/documents/${encodeURIComponent(filename)}`);
      if (docThreadId) url.searchParams.append("thread_id", docThreadId);
      const res = await authFetch(url.toString(), { method: "DELETE" });
      if (res.ok) {
        setUploadStatus(`Deleted: ${filename}`);
        toast.success(`Deleted: ${filename}`);
        fetchDocuments();
        setTimeout(() => setUploadStatus(""), 2000);
      } else {
        setUploadStatus("Failed to delete document.");
        toast.error(`Failed to delete: ${filename}`);
      }
    } catch (err) {
      setUploadStatus("Error deleting document.");
      toast.error("Error deleting document.");
    }
  }, [authFetch, fetchDocuments]);

  const handleReingestDocument = useCallback(async (filename: string, docThreadId?: string) => {
    setUploadStatus(`Re-ingesting: ${filename}...`);
    try {
      const url = new URL(`${API_BASE}/documents/${encodeURIComponent(filename)}/reingest`);
      if (docThreadId) url.searchParams.append("thread_id", docThreadId);
      const res = await authFetch(url.toString(), { method: "POST" });
      if (res.ok) {
        setUploadStatus(`Re-ingestion triggered for ${filename}`);
        toast.success(`Re-ingestion triggered for ${filename}`);
        fetchDocuments();
        setTimeout(() => setUploadStatus(""), 2000);
      } else {
        const errorData = await res.json();
        setUploadStatus(`Re-ingestion failed: ${errorData.message || "Unknown error"}`);
        toast.error(`Re-ingestion failed: ${errorData.message || "Unknown error"}`);
      }
    } catch (err) {
      setUploadStatus("Error triggering re-ingestion.");
      toast.error("Error triggering re-ingestion.");
    }
  }, [authFetch, fetchDocuments]);

  const handleRemoveTemporalFile = useCallback(async (filename: string, threadId: string) => {
    try {
      const res = await authFetch(`${API_BASE}/documents/${encodeURIComponent(filename)}?thread_id=${threadId}`, {
        method: "DELETE",
      });
      if (res.ok) fetchDocuments();
    } catch (err) {
      console.error("Error removing temporal file:", err);
    }
  }, [authFetch, fetchDocuments]);

  return {
    documents, setDocuments,
    sessionFiles, setSessionFiles,
    loadingDocs,
    uploadStatus, setUploadStatus,
    uploadingFile,
    showDocManager, setShowDocManager,
    fetchDocuments,
    handleFileUpload,
    handleTemporalFileUpload,
    handleDeleteDocument,
    handleReingestDocument,
    handleRemoveTemporalFile,
  };
}
