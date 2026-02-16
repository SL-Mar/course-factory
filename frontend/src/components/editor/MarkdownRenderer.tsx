import { Component, type ReactNode, type ErrorInfo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";

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

// Error boundary to catch rendering failures
class MarkdownErrorBoundary extends Component<
  { children: ReactNode; fallback: string },
  { error: Error | null }
> {
  state: { error: Error | null } = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("MarkdownRenderer error:", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="text-red-400 text-xs p-2 border border-red-400/30 rounded">
          <p className="font-bold mb-1">Markdown render error:</p>
          <pre className="text-[10px] whitespace-pre-wrap">{this.state.error.message}</pre>
          <pre className="mt-2 text-content-muted whitespace-pre-wrap">{this.props.fallback}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

export function MarkdownRenderer({
  content,
  onWikiLinkClick,
}: MarkdownRendererProps) {
  // Pre-process to extract wiki-links for inline rendering
  const processedContent = content.replace(
    /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g,
    (_match, target: string, display?: string) => {
      const linkText = display?.trim() || target.trim();
      return `[${linkText}](wikilink://${encodeURIComponent(target.trim())})`;
    },
  );

  return (
    <div className="markdown-body">
      <MarkdownErrorBoundary fallback={content}>
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
      </MarkdownErrorBoundary>
    </div>
  );
}

export { processWikiLinks };
