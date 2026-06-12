"use client";
import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { uploadDocument, getStatus, StatusResponse } from "@/lib/api";

interface FileStatus {
  file: File;
  doc_id?: string;
  status: string;
  error?: string;
  classification?: Record<string, unknown>;
  page_count?: number;
}

export default function BulkUploadPage() {
  const [files, setFiles] = useState<FileStatus[]>([]);

  const onDrop = useCallback((accepted: File[]) => {
    const newFiles = accepted.map((f) => ({ file: f, status: "pending" }));
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [], "image/*": [], "text/plain": [] },
    multiple: true,
  });

  const processAll = async () => {
    for (let i = 0; i < files.length; i++) {
      if (files[i].status !== "pending") continue;

      setFiles((prev) =>
        prev.map((f, idx) => (idx === i ? { ...f, status: "uploading" } : f))
      );

      try {
        const res = await uploadDocument(files[i].file);
        const doc_id = res.doc_id;

        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === i ? { ...f, doc_id, status: "parsing" } : f
          )
        );

        // Poll status
        let status: StatusResponse;
        let attempts = 0;
        do {
          await new Promise((r) => setTimeout(r, 2000));
          status = await getStatus(doc_id);
          setFiles((prev) =>
            prev.map((f, idx) =>
              idx === i ? { ...f, status: status.status } : f
            )
          );
          attempts++;
        } while (
          !["indexed", "failed"].includes(status.status) &&
          attempts < 60
        );

        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === i
              ? {
                  ...f,
                  status: status.status,
                  classification: status.classification ?? undefined,
                  page_count: status.page_count ?? undefined,
                  error: status.error ?? undefined,
                }
              : f
          )
        );
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Upload failed";
        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === i ? { ...f, status: "failed", error: msg } : f
          )
        );
      }
    }
  };

  const statusColor = (s: string) => {
    if (s === "indexed") return "text-green-600";
    if (s === "failed") return "text-red-600";
    if (s === "pending") return "text-gray-400";
    return "text-yellow-600";
  };

  const statusLabel = (s: string) => {
    const labels: Record<string, string> = {
      pending: "Pending",
      uploading: "Uploading...",
      parsing: "Parsing...",
      classifying: "Classifying...",
      indexing: "Indexing...",
      indexed: "✅ Indexed",
      failed: "❌ Failed",
    };
    return labels[s] || s;
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Bulk Upload</h1>
        <p className="text-gray-500 mb-8">
          Upload multiple documents to the knowledge base.
        </p>

        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
            isDragActive
              ? "border-blue-500 bg-blue-50"
              : "border-gray-300 hover:border-blue-400 bg-white"
          }`}
        >
          <input {...getInputProps()} />
          <p className="text-lg text-gray-600">
            {isDragActive
              ? "Drop files here..."
              : "Drag & drop files here, or click to select"}
          </p>
          <p className="text-sm text-gray-400 mt-2">
            PDF, images, text files supported
          </p>
        </div>

        {files.length > 0 && (
          <div className="mt-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-800">
                {files.length} file(s)
              </h2>
              <button
                onClick={processAll}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
              >
                Process All
              </button>
            </div>

            <div className="space-y-3">
              {files.map((f, i) => (
                <div
                  key={i}
                  className="bg-white rounded-lg p-4 shadow-sm border border-gray-100"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-gray-800">{f.file.name}</p>
                      <p className="text-sm text-gray-400">
                        {(f.file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                    <span className={`font-semibold text-sm ${statusColor(f.status)}`}>
                      {statusLabel(f.status)}
                    </span>
                  </div>
                  {f.error && (
                    <p className="text-red-500 text-sm mt-2">{f.error}</p>
                  )}
                  {f.classification && (
                    <div className="mt-3 text-sm text-gray-600 bg-gray-50 rounded p-3">
                      <p><span className="font-medium">Type:</span> {String(f.classification.doc_type)}</p>
                      <p><span className="font-medium">Topic:</span> {String(f.classification.topic)}</p>
                      <p><span className="font-medium">Sensitivity:</span> {String(f.classification.sensitivity)}</p>
                      {f.page_count && <p><span className="font-medium">Pages:</span> {f.page_count}</p>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-8">
          <a href="/" className="text-blue-600 hover:underline text-sm">
            ← Back to Chat
          </a>
        </div>
      </div>
    </div>
  );
}