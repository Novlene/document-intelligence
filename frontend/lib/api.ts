import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "x-api-key": API_KEY },
});

export interface Citation {
  doc_id: string;
  doc_name: string;
  page_num: number;
  chunk_text: string;
  page_image_path: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  sources_found: boolean;
}

export interface UploadResponse {
  doc_id: string;
  filename: string;
  status: string;
}

export interface StatusResponse {
  doc_id: string;
  status: string;
  page_count: number | null;
  classification: Record<string, unknown> | null;
  error: string | null;
}

export const uploadDocument = async (file: File): Promise<UploadResponse> => {
  const form = new FormData();
  form.append("file", file);
  const res = await api.post("/upload", form);
  return res.data;
};

export const getStatus = async (doc_id: string): Promise<StatusResponse> => {
  const res = await api.get(`/status/${doc_id}`);
  return res.data;
};

export const chat = async (
  message: string,
  doc_ids?: string[]
): Promise<ChatResponse> => {
  const res = await api.post("/chat", { message, doc_ids });
  return res.data;
};

export const getPageImageUrl = (filename: string) =>
  `${API_BASE}/pages/${filename.replace("pages/", "")}?x-api-key=${API_KEY}`;

export default api;
