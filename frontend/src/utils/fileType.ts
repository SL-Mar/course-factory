export function isMarpFile(path: string): boolean {
  return path.toLowerCase().endsWith(".marp.md");
}

export function isMarkdownFile(path: string): boolean {
  return path.toLowerCase().endsWith(".md");
}
