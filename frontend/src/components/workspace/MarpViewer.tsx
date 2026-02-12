import { useState, useMemo } from "react";
import { MarkdownViewer } from "./MarkdownViewer";

interface MarpViewerProps {
  content: string;
}

interface SlideData {
  content: string;
  notes: string | null;
}

function parseMarp(raw: string): { header: string | null; footer: string | null; slides: SlideData[] } {
  let body = raw;
  let header: string | null = null;
  let footer: string | null = null;

  // Strip YAML frontmatter
  const fmMatch = body.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (fmMatch) {
    const fm = fmMatch[1];
    const headerMatch = fm.match(/^header:\s*(.+)$/m);
    const footerMatch = fm.match(/^footer:\s*(.+)$/m);
    if (headerMatch) header = headerMatch[1].trim();
    if (footerMatch) footer = footerMatch[1].trim();
    body = body.slice(fmMatch[0].length);
  }

  // Split by slide separators (--- on its own line)
  const parts = body.split(/\n---\n/);

  const slides: SlideData[] = parts.map((part) => {
    const trimmed = part.trim();
    if (!trimmed) return { content: "", notes: null };

    // Extract speaker notes: <!-- ... -->
    const noteMatch = trimmed.match(/<!--\s*([\s\S]*?)\s*-->/);
    const notes = noteMatch ? noteMatch[1].trim() : null;
    const content = trimmed.replace(/<!--[\s\S]*?-->/g, "").trim();

    return { content, notes };
  });

  // Filter out empty slides
  return { header, footer, slides: slides.filter((s) => s.content.length > 0) };
}

export function MarpViewer({ content }: MarpViewerProps) {
  const { header, footer, slides } = useMemo(() => parseMarp(content), [content]);
  const [expandedNotes, setExpandedNotes] = useState<Set<number>>(new Set());

  const toggleNotes = (idx: number) => {
    setExpandedNotes((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  return (
    <div className="marp-viewer">
      {(header || footer) && (
        <div className="marp-meta">
          {header && <span className="marp-meta-item">Header: {header}</span>}
          {footer && <span className="marp-meta-item">Footer: {footer}</span>}
        </div>
      )}
      {slides.map((slide, idx) => (
        <div key={idx} className="marp-slide-wrapper">
          <div className="marp-slide">
            <span className="marp-slide-badge">
              {idx + 1} / {slides.length}
            </span>
            <div className="marp-slide-content">
              <MarkdownViewer content={slide.content} />
            </div>
          </div>
          {slide.notes && (
            <div className="marp-notes">
              <button
                className="marp-notes-toggle"
                onClick={() => toggleNotes(idx)}
              >
                {expandedNotes.has(idx) ? "▾" : "▸"} Speaker Notes
              </button>
              {expandedNotes.has(idx) && (
                <div className="marp-notes-body">{slide.notes}</div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
