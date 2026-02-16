import { useState, useRef } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faUpload, faLink, faXmark, faSpinner } from "@fortawesome/free-solid-svg-icons";

interface ImageUploadModalProps {
  onInsert: (markdown: string) => void;
  onClose: () => void;
}

export function ImageUploadModal({ onInsert, onClose }: ImageUploadModalProps) {
  const [tab, setTab] = useState<"upload" | "url">("upload");
  const [url, setUrl] = useState("");
  const [alt, setAlt] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("Only image files are allowed");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("File too large (max 10 MB)");
      return;
    }

    setUploading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/api/assets/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(data.detail || "Upload failed");
      }

      const data = await res.json();
      const altText = alt || file.name.replace(/\.[^.]+$/, "");
      onInsert(`![${altText}](${data.url})`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleUrlInsert = () => {
    if (!url.trim()) return;
    const altText = alt || "image";
    onInsert(`![${altText}](${url.trim()})`);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData.items;
    for (const item of items) {
      if (item.type.startsWith("image/")) {
        e.preventDefault();
        const file = item.getAsFile();
        if (file) handleFileUpload(file);
        return;
      }
    }
  };

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/60" onClick={onClose} />
      <div className="fixed z-50 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[420px] bg-content-secondary border border-content-border rounded-lg shadow-2xl animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-content-border">
          <span className="text-sm font-medium text-content-text">Insert Image</span>
          <button onClick={onClose} className="text-content-muted hover:text-content-text">
            <FontAwesomeIcon icon={faXmark} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-content-border">
          <button
            onClick={() => setTab("upload")}
            className={`flex-1 px-4 py-2 text-xs font-medium transition-colors ${
              tab === "upload" ? "text-accent border-b-2 border-accent" : "text-content-muted hover:text-content-text"
            }`}
          >
            <FontAwesomeIcon icon={faUpload} className="mr-1.5" /> Upload
          </button>
          <button
            onClick={() => setTab("url")}
            className={`flex-1 px-4 py-2 text-xs font-medium transition-colors ${
              tab === "url" ? "text-accent border-b-2 border-accent" : "text-content-muted hover:text-content-text"
            }`}
          >
            <FontAwesomeIcon icon={faLink} className="mr-1.5" /> URL
          </button>
        </div>

        {/* Body */}
        <div className="p-4" onPaste={handlePaste}>
          {/* Alt text (shared) */}
          <div className="mb-3">
            <label className="block text-[11px] text-content-muted mb-1">Alt text (optional)</label>
            <input
              type="text"
              value={alt}
              onChange={(e) => setAlt(e.target.value)}
              placeholder="Describe the image"
              className="w-full px-3 py-1.5 text-xs bg-content-tertiary border border-content-border rounded text-content-text outline-none focus:border-accent"
            />
          </div>

          {tab === "upload" ? (
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileRef.current?.click()}
              className="flex flex-col items-center justify-center gap-2 py-8 border-2 border-dashed border-content-border rounded-lg cursor-pointer hover:border-accent/50 transition-colors"
            >
              {uploading ? (
                <FontAwesomeIcon icon={faSpinner} className="text-accent text-lg animate-spin" />
              ) : (
                <>
                  <FontAwesomeIcon icon={faUpload} className="text-content-muted text-lg" />
                  <span className="text-xs text-content-muted">
                    Click, drag & drop, or paste an image
                  </span>
                  <span className="text-[10px] text-content-faint">PNG, JPG, GIF, WebP, SVG (max 10 MB)</span>
                </>
              )}
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFileUpload(file);
                }}
              />
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="block text-[11px] text-content-muted mb-1">Image URL</label>
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/image.png"
                  className="w-full px-3 py-1.5 text-xs bg-content-tertiary border border-content-border rounded text-content-text outline-none focus:border-accent"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleUrlInsert();
                  }}
                />
              </div>
              <button
                onClick={handleUrlInsert}
                disabled={!url.trim()}
                className="w-full py-2 text-xs font-medium bg-accent text-white rounded hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Insert
              </button>
            </div>
          )}

          {error && (
            <div className="mt-2 text-xs text-red-400">{error}</div>
          )}
        </div>
      </div>
    </>
  );
}
