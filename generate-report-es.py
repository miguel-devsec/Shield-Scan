"""
Converts docs-es/technical-report.md to a print-ready HTML file (Spanish).
Open the output in Chrome and use File -> Print -> Save as PDF.
"""
import markdown
import pathlib

SRC = pathlib.Path(__file__).parent / "docs-es" / "technical-report.md"
OUT = pathlib.Path(__file__).parent / "ShieldScan-Informe-Tecnico.html"

md_text = SRC.read_text(encoding="utf-8")

body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "toc", "attr_list"],
)

HTML = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ShieldScan v2.0 — Informe Técnico</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    @page {{
      size: A4;
      margin: 2.5cm 2cm 2.5cm 2cm;
    }}
    * {{ box-sizing: border-box; }}

    body {{
      font-family: "Segoe UI", Arial, sans-serif;
      font-size: 11pt;
      line-height: 1.6;
      color: #1a1a2e;
      max-width: 900px;
      margin: 0 auto;
      padding: 40px 40px;
      background: #ffffff;
    }}

    h1 {{
      font-size: 26pt;
      color: #0f3460;
      border-bottom: 3px solid #e94560;
      padding-bottom: 10px;
      margin-top: 0;
      page-break-before: avoid;
    }}
    h2 {{
      font-size: 16pt;
      color: #16213e;
      border-left: 5px solid #e94560;
      padding-left: 12px;
      margin-top: 36px;
      page-break-after: avoid;
    }}
    h3 {{
      font-size: 13pt;
      color: #0f3460;
      margin-top: 24px;
      page-break-after: avoid;
    }}
    h4 {{
      font-size: 11pt;
      color: #16213e;
      font-weight: 600;
      page-break-after: avoid;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;
      font-size: 10pt;
      page-break-inside: avoid;
    }}
    th {{
      background: #0f3460;
      color: #ffffff;
      padding: 8px 12px;
      text-align: left;
      font-weight: 600;
    }}
    td {{
      padding: 7px 12px;
      border: 1px solid #dde1e7;
      vertical-align: top;
    }}
    tr:nth-child(even) td {{
      background: #f4f6fa;
    }}
    tr:hover td {{
      background: #e8eef8;
    }}

    pre {{
      background: #1a1a2e;
      color: #e8e8e8;
      padding: 16px;
      border-radius: 6px;
      overflow-x: auto;
      font-size: 9pt;
      line-height: 1.5;
      page-break-inside: avoid;
    }}
    code {{
      font-family: "Cascadia Code", "Consolas", monospace;
      font-size: 9.5pt;
    }}
    p > code, li > code, td > code {{
      background: #eef0f8;
      padding: 2px 5px;
      border-radius: 3px;
      color: #c0392b;
    }}

    .mermaid {{
      background: #f8f9fd;
      border: 1px solid #dde1e7;
      border-radius: 8px;
      padding: 20px;
      margin: 20px 0;
      text-align: center;
      page-break-inside: avoid;
    }}

    blockquote {{
      border-left: 4px solid #e94560;
      background: #fff5f6;
      margin: 16px 0;
      padding: 10px 16px;
      border-radius: 0 6px 6px 0;
    }}

    hr {{
      border: none;
      border-top: 2px solid #dde1e7;
      margin: 32px 0;
    }}

    a {{ color: #0f3460; }}

    @media print {{
      body {{ padding: 0; max-width: 100%; }}
      pre {{ white-space: pre-wrap; word-break: break-all; }}
      h2 {{ page-break-before: always; }}
      h2:first-of-type {{ page-break-before: avoid; }}
    }}
  </style>
</head>
<body>
  {body}
  <script>
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'default',
      themeVariables: {{
        primaryColor: '#0f3460',
        primaryTextColor: '#ffffff',
        primaryBorderColor: '#e94560',
        lineColor: '#16213e',
        secondaryColor: '#f4f6fa',
        tertiaryColor: '#eef0f8'
      }}
    }});

    document.querySelectorAll('pre > code.language-mermaid').forEach(el => {{
      const div = document.createElement('div');
      div.className = 'mermaid';
      div.textContent = el.textContent;
      el.parentElement.replaceWith(div);
    }});
    mermaid.run();
  </script>
</body>
</html>"""

OUT.write_text(HTML, encoding="utf-8")
print(f"Informe generado: {OUT}")
print("Abre el archivo en Chrome, luego Archivo -> Imprimir -> Guardar como PDF")
print("  Configuración recomendada: A4, márgenes Por defecto, Gráficos en segundo plano ACTIVADO")
