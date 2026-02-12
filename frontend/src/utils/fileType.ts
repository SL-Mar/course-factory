export function isMarkdownFile(path: string): boolean {
  return path.toLowerCase().endsWith(".md");
}
