"""Concatenate chapters/*.md into one HTML + PDF (build/)."""
import pathlib, re
import markdown
from weasyprint import HTML

root = pathlib.Path(__file__).resolve().parent.parent
out = root / "build"
out.mkdir(exist_ok=True)

md = markdown.Markdown(
    extensions=["fenced_code", "codehilite", "tables", "toc", "sane_lists"],
    extension_configs={"codehilite": {"guess_lang": False, "css_class": "hl"},
                       "toc": {"toc_depth": "2-3"}},
)

parts = []
for f in sorted((root / "chapters").glob("*.md")):
    parts.append(f.read_text())
body = md.convert("\n\n".join(parts))

# every H1 starts a new page; chapter 0 title acts as cover
from pygments.formatters import HtmlFormatter
css = (root / "tools" / "style.css").read_text() + HtmlFormatter(style="friendly", cssclass="hl").get_style_defs(".hl")

html = f"<!doctype html><html><head><meta charset='utf-8'><title>GNOME Application Development Guide</title><style>{css}</style></head><body>{body}</body></html>"
(out / "GnomeDevGuide.html").write_text(html)
HTML(string=html, base_url=str(root)).write_pdf(out / "GnomeDevGuide.pdf")
print("wrote", out / "GnomeDevGuide.pdf")
