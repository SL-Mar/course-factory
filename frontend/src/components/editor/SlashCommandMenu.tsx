import { useState, useEffect, useRef, useCallback } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faCode,
  faImage,
  faFileLines,
  faHeading,
  faListUl,
  faListOl,
  faSquareCheck,
  faQuoteLeft,
  faMinus,
  faTable,
  faCalculator,
} from "@fortawesome/free-solid-svg-icons";
import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";

export interface SlashCommandItem {
  id: string;
  label: string;
  description: string;
  icon: IconDefinition;
  category: string;
  insert?: string; // markdown to insert directly
  action?: string; // "image" | "page-embed" — triggers a modal
}

const COMMANDS: SlashCommandItem[] = [
  // Basic blocks
  { id: "h1", label: "Heading 1", description: "Large section heading", icon: faHeading, category: "Basic", insert: "# " },
  { id: "h2", label: "Heading 2", description: "Medium section heading", icon: faHeading, category: "Basic", insert: "## " },
  { id: "h3", label: "Heading 3", description: "Small section heading", icon: faHeading, category: "Basic", insert: "### " },
  { id: "bullet", label: "Bulleted list", description: "Unordered list", icon: faListUl, category: "Basic", insert: "- " },
  { id: "numbered", label: "Numbered list", description: "Ordered list", icon: faListOl, category: "Basic", insert: "1. " },
  { id: "todo", label: "To-do list", description: "Checkbox list", icon: faSquareCheck, category: "Basic", insert: "- [ ] " },
  { id: "quote", label: "Quote", description: "Blockquote", icon: faQuoteLeft, category: "Basic", insert: "> " },
  { id: "divider", label: "Divider", description: "Horizontal rule", icon: faMinus, category: "Basic", insert: "\n---\n" },
  // Rich blocks
  { id: "code", label: "Code block", description: "Syntax-highlighted code", icon: faCode, category: "Rich", insert: "```\n\n```" },
  { id: "table", label: "Table", description: "Markdown table", icon: faTable, category: "Rich", insert: "| Column 1 | Column 2 | Column 3 |\n| --- | --- | --- |\n| Cell | Cell | Cell |\n" },
  { id: "math", label: "Math block", description: "LaTeX equation", icon: faCalculator, category: "Rich", insert: "$$\n\n$$" },
  // Embeds
  { id: "image", label: "Image", description: "Upload or paste URL", icon: faImage, category: "Embed", action: "image" },
  { id: "page", label: "Page embed", description: "Link to another page", icon: faFileLines, category: "Embed", action: "page-embed" },
];

interface SlashCommandMenuProps {
  query: string;
  position: { top: number; left: number };
  onSelect: (command: SlashCommandItem) => void;
  onClose: () => void;
}

export function SlashCommandMenu({ query, position, onSelect, onClose }: SlashCommandMenuProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const menuRef = useRef<HTMLDivElement>(null);
  const itemRefs = useRef<(HTMLButtonElement | null)[]>([]);

  const filtered = COMMANDS.filter((cmd) => {
    if (!query) return true;
    const q = query.toLowerCase();
    return (
      cmd.label.toLowerCase().includes(q) ||
      cmd.description.toLowerCase().includes(q) ||
      cmd.id.toLowerCase().includes(q)
    );
  });

  // Reset selection when filter changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Scroll selected item into view
  useEffect(() => {
    itemRefs.current[selectedIndex]?.scrollIntoView({ block: "nearest" });
  }, [selectedIndex]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((i) => (i + 1) % filtered.length);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((i) => (i - 1 + filtered.length) % filtered.length);
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          onSelect(filtered[selectedIndex]);
        }
      } else if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    },
    [filtered, selectedIndex, onSelect, onClose],
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown, true);
    return () => window.removeEventListener("keydown", handleKeyDown, true);
  }, [handleKeyDown]);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onClose]);

  if (filtered.length === 0) {
    return null;
  }

  // Group by category
  const categories = [...new Set(filtered.map((c) => c.category))];

  return (
    <div
      ref={menuRef}
      className="fixed z-50 w-72 max-h-80 overflow-y-auto bg-content-secondary border border-content-border rounded-lg shadow-xl animate-fade-in"
      style={{ top: position.top, left: position.left }}
    >
      <div className="px-3 py-2 text-[10px] uppercase tracking-wider text-content-faint border-b border-content-border">
        Insert block
      </div>
      {categories.map((category) => (
        <div key={category}>
          <div className="px-3 py-1 text-[10px] uppercase tracking-wider text-content-faint">
            {category}
          </div>
          {filtered
            .filter((c) => c.category === category)
            .map((cmd) => {
              const globalIdx = filtered.indexOf(cmd);
              return (
                <button
                  key={cmd.id}
                  ref={(el) => { itemRefs.current[globalIdx] = el; }}
                  onClick={() => onSelect(cmd)}
                  className={`w-full flex items-center gap-3 px-3 py-1.5 text-left transition-colors ${
                    globalIdx === selectedIndex
                      ? "bg-accent/15 text-accent-light"
                      : "text-content-text hover:bg-content-tertiary"
                  }`}
                >
                  <FontAwesomeIcon
                    icon={cmd.icon}
                    className={`w-4 text-xs ${globalIdx === selectedIndex ? "text-accent" : "text-content-muted"}`}
                    fixedWidth
                  />
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium truncate">{cmd.label}</div>
                    <div className="text-[10px] text-content-muted truncate">{cmd.description}</div>
                  </div>
                </button>
              );
            })}
        </div>
      ))}
    </div>
  );
}
