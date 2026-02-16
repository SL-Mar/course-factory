"""Markdown-to-PDF conversion using fpdf2."""

from __future__ import annotations

import re
from io import BytesIO

from fpdf import FPDF


class _MarkdownPDF(FPDF):
    """Simple PDF renderer for markdown content."""

    def __init__(self) -> None:
        super().__init__()
        self.add_page()
        self.set_auto_page_break(auto=True, margin=20)
        self.set_font("Helvetica", size=11)

    def _reset_x(self) -> None:
        """Always reset x to left margin before writing."""
        self.set_x(self.l_margin)

    def _write_title(self, title: str) -> None:
        self._reset_x()
        self.set_font("Helvetica", "B", 18)
        self.multi_cell(0, 12, title)
        self.ln(4)
        self.set_draw_color(180, 180, 180)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(8)
        self.set_font("Helvetica", size=11)

    def _write_body(self, content: str) -> None:
        lines = content.split("\n")
        in_code_block = False

        for line in lines:
            stripped = line.strip()

            # Code block toggle
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                if in_code_block:
                    self.set_font("Courier", size=9)
                else:
                    self.set_font("Helvetica", size=11)
                continue

            if in_code_block:
                self._reset_x()
                self.set_font("Courier", size=9)
                self.multi_cell(0, 5, line.rstrip())
                continue

            # Headings
            if stripped.startswith("######"):
                self._write_heading(stripped[6:].strip(), 11)
            elif stripped.startswith("#####"):
                self._write_heading(stripped[5:].strip(), 11)
            elif stripped.startswith("####"):
                self._write_heading(stripped[4:].strip(), 12)
            elif stripped.startswith("###"):
                self._write_heading(stripped[3:].strip(), 13)
            elif stripped.startswith("##"):
                self._write_heading(stripped[2:].strip(), 14)
            elif stripped.startswith("# "):
                self._write_heading(stripped[2:].strip(), 16)
            elif stripped.startswith("---") or stripped.startswith("***"):
                self._reset_x()
                self.ln(4)
                self.set_draw_color(180, 180, 180)
                self.line(10, self.get_y(), self.w - 10, self.get_y())
                self.ln(4)
            elif stripped.startswith("- ") or stripped.startswith("* "):
                self._write_paragraph(f"  -  {self._clean(stripped[2:])}")
            elif re.match(r"^\d+\.\s", stripped):
                self._write_paragraph(f"  {stripped}")
            elif stripped.startswith(">"):
                self._write_blockquote(stripped[1:].strip())
            elif stripped.startswith("|"):
                # Table row — render as-is
                self._write_paragraph(stripped)
            elif stripped == "":
                self.ln(3)
            else:
                self._write_paragraph(self._clean(stripped))

    def _write_heading(self, text: str, size: float) -> None:
        self._reset_x()
        self.ln(4)
        self.set_font("Helvetica", "B", size)
        self.multi_cell(0, size * 0.6, self._clean(text))
        self.ln(2)
        self.set_font("Helvetica", size=11)

    def _write_paragraph(self, text: str) -> None:
        self._reset_x()
        self.set_font("Helvetica", size=11)
        self.multi_cell(0, 6, text)

    def _write_blockquote(self, text: str) -> None:
        self._reset_x()
        self.set_font("Helvetica", "I", 10)
        self.set_text_color(120, 120, 120)
        self.multi_cell(0, 6, f"  | {self._clean(text)}")
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", size=11)

    @staticmethod
    def _clean(text: str) -> str:
        """Strip inline markdown formatting for plain-text PDF."""
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"__(.+?)__", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"_(.+?)_", r"\1", text)
        text = re.sub(r"`(.+?)`", r"\1", text)
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
        text = re.sub(r"!\[.*?\]\(.+?\)", "[image]", text)
        # Replace unicode chars that Helvetica can't render
        text = text.replace("\u2022", "-")  # bullet
        text = text.replace("\u2013", "-")  # en-dash
        text = text.replace("\u2014", "--")  # em-dash
        text = text.replace("\u2018", "'")  # left single quote
        text = text.replace("\u2019", "'")  # right single quote
        text = text.replace("\u201c", '"')  # left double quote
        text = text.replace("\u201d", '"')  # right double quote
        text = text.replace("\u2026", "...")  # ellipsis
        # Strip any remaining non-latin1 chars
        text = text.encode("latin-1", errors="replace").decode("latin-1")
        return text


def convert_to_pdf(title: str, content: str) -> bytes:
    """Convert a page title + markdown content to PDF bytes."""
    pdf = _MarkdownPDF()
    pdf._write_title(title)
    pdf._write_body(content)

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()
