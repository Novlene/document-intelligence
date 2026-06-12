"use client";
import { useState, useRef, useEffect } from "react";
import { chat, getPageImageUrl, Citation } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [modalImage, setModalImage] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await chat(input);
      const assistantMsg: Message = {
        role: "assistant",
        content: res.answer,
        citations: res.citations,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error: could not reach the API." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <div className="bg-white border-b px-6 py-4 flex justify-between items-center shadow-sm">
        <h1 className="text-xl font-bold text-gray-900">Document Intelligence</h1>
        <a href="/bulk-upload" className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 transition">Bulk Upload</a>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6 max-w-4xl mx-auto w-full">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-20">
            <p className="text-2xl mb-2">💬</p>
            <p>Ask a question about your documents</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-2xl rounded-2xl px-5 py-3 shadow-sm ${msg.role === "user" ? "bg-blue-600 text-white" : "bg-white text-gray-800 border border-gray-100"}`}>
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wide">Sources</p>
                  <div className="flex flex-wrap gap-3">
                    {msg.citations.map((c, j) => (
                      <button key={j} onClick={() => setModalImage(getPageImageUrl(c.page_image_path))} title={`${c.doc_name} - Page ${c.page_num}`} className="relative">
                        <img src={getPageImageUrl(c.page_image_path)} alt={`Page ${c.page_num}`} className="w-20 h-28 object-cover rounded border border-gray-200 hover:border-blue-400 transition shadow-sm" onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
                        <span className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-xs py-1 rounded-b text-center">p.{c.page_num}</span>
                      </button>
                    ))}
                  </div>
                  <div className="mt-2 space-y-1">
                    {msg.citations.map((c, j) => (
                      <p key={j} className="text-xs text-gray-400">[{j + 1}] {c.doc_name}, page {c.page_num}</p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-100 rounded-2xl px-5 py-3 shadow-sm">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="bg-white border-t px-4 py-4">
        <div className="max-w-4xl mx-auto flex gap-3">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && sendMessage()} placeholder="Ask a question about your documents..." className="flex-1 border border-gray-200 rounded-xl px-4 py-3 text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <button onClick={sendMessage} disabled={loading} className="bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 disabled:opacity-50 transition font-medium">Send</button>
        </div>
      </div>
      {modalImage && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={() => setModalImage(null)}>
          <img src={modalImage} alt="Full page" className="max-h-[90vh] max-w-[90vw] rounded-lg shadow-2xl" />
        </div>
      )}
    </div>
  );
}
