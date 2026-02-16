import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import type { ReactNode } from "react";

interface MarkdownRendererProps {
  content: string;
  onWikiLinkClick?: (target: string) => void;
}

/**
 * Pre-process wiki-links: [[Page Name]] -> clickable links
 * and [[Page Name|Display Text]] -> clickable with custom text
 */
function processWikiLinks(
  content: string,
  onWikiLinkClick?: (target: string) => void,
): ReactNode[] {
  const parts = content.split(/(\[\[[^\]]+\]\])/g);

  return parts.map((part, i) => {
    const match = part.match(/^\[\[([^\]|]+)(?:\|([^\]]+))?\]\]$/);
    if (match) {
      const target = match[1].trim();
      const display = match[2]?.trim() || target;
      return (
        <button
          key={i}
          className="wiki-link"
          onClick={() => onWikiLinkClick?.(target)}
        >
          {display}
        </button>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

export function MarkdownRenderer({
  content,
  onWikiLinkClick,
}: MarkdownRendererProps) {
  // Pre-process to extract wiki-links for inline rendering
  // We replace [[...]] with a placeholder for markdown, then handle them in components
  const processedContent = content.replace(
    /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g,
    (_match, target: string, display?: string) => {
      const linkText = display?.trim() || target.trim();
      return `[${linkText}](wikilink://${encodeURIComponent(target.trim())})`;
    },
  );

  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex, rehypeHighlight]}
        components={{
          a: ({ href, children }) => {
            if (href?.startsWith("wikilink://")) {
              const target = decodeURIComponent(
                href.replace("wikilink://", ""),
              );
              return (
                <button
                  className="wiki-link"
                  onClick={() => onWikiLinkClick?.(target)}
                >
                  {children}
                </button>
              );
            }
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
              >
                {children}
              </a>
            );
          },
        }}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
}

// Keep the processWikiLinks function exported for inline use if needed
export { processWikiLinks };
