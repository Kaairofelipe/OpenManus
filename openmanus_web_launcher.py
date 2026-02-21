from __future__ import annotations

import argparse
import html
import subprocess
import tomllib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs


REPO_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = REPO_ROOT / "config" / "config.toml"
PYTHON_EXE = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
MAIN_PY = REPO_ROOT / "main.py"
PLACEHOLDER_KEYS = {
    "",
    "YOUR_API_KEY",
    "AZURE API KEY",
    "your Jiekou.AI api key",
}


def check_llm_config() -> tuple[bool, str]:
    if not CONFIG_PATH.exists():
        return False, "Arquivo config/config.toml nao encontrado."
    try:
        parsed = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"Falha ao ler config.toml: {exc}"

    llm_cfg = parsed.get("llm", {})
    api_key = str(llm_cfg.get("api_key", "")).strip()
    if api_key in PLACEHOLDER_KEYS or "YOUR_" in api_key:
        return False, "Defina [llm].api_key com uma chave valida no config/config.toml."
    return True, "Configuracao LLM valida."


def run_openmanus(prompt: str, timeout_sec: int = 900) -> tuple[int, str]:
    if not PYTHON_EXE.exists():
        return 2, f"Python do venv nao encontrado em: {PYTHON_EXE}"
    if not MAIN_PY.exists():
        return 2, f"Arquivo main.py nao encontrado em: {MAIN_PY}"

    command = [str(PYTHON_EXE), str(MAIN_PY), "--prompt", prompt]
    try:
        completed = subprocess.run(
            command,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as exc:
        partial = (exc.stdout or "") + ("\n" + exc.stderr if exc.stderr else "")
        return 124, (partial.strip() or "Execucao excedeu o tempo limite.")

    merged = (completed.stdout or "") + (
        "\n" + completed.stderr if completed.stderr else ""
    )
    return completed.returncode, (merged.strip() or "(sem saida)")


def render_page(prompt: str = "", result: str = "", run_code: int | None = None) -> str:
    config_ok, config_message = check_llm_config()
    status_color = "#0a7d33" if config_ok else "#a30f2d"
    status_bg = "#eaf7ef" if config_ok else "#ffeef1"
    status_title = "Pronto" if config_ok else "Configuracao pendente"

    result_block = ""
    if run_code is not None:
        escaped_result = html.escape(result)
        result_block = f"""
        <h2>Resultado</h2>
        <p><strong>Exit code:</strong> {run_code}</p>
        <pre>{escaped_result}</pre>
        """

    escaped_prompt = html.escape(prompt)
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>OpenManus Interativo</title>
  <style>
    :root {{
      --bg: #f5f7fb;
      --card: #ffffff;
      --ink: #121826;
      --muted: #4a5160;
      --accent: #0b5fff;
      --line: #d9dfeb;
    }}
    body {{ margin: 0; font-family: "Segoe UI", Tahoma, sans-serif; background: var(--bg); color: var(--ink); }}
    .wrap {{ max-width: 980px; margin: 24px auto; padding: 0 16px; }}
    .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 18px; box-shadow: 0 8px 22px rgba(18,24,38,.06); }}
    h1 {{ margin: 0 0 12px; font-size: 1.5rem; }}
    h2 {{ margin: 18px 0 10px; font-size: 1.1rem; }}
    p {{ margin: 8px 0; color: var(--muted); }}
    .status {{ border-radius: 10px; padding: 10px 12px; margin: 10px 0 16px; background: {status_bg}; color: {status_color}; border: 1px solid {status_color}33; }}
    textarea {{ width: 100%; min-height: 120px; border: 1px solid var(--line); border-radius: 10px; padding: 10px; font-size: 0.95rem; }}
    button {{ margin-top: 10px; background: var(--accent); color: #fff; border: none; border-radius: 9px; padding: 10px 14px; font-weight: 600; cursor: pointer; }}
    button:hover {{ filter: brightness(.95); }}
    pre {{ white-space: pre-wrap; word-wrap: break-word; background: #0e1422; color: #e7ebf5; border-radius: 10px; padding: 12px; max-height: 420px; overflow: auto; }}
    code {{ background: #eef2ff; padding: 2px 5px; border-radius: 4px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>OpenManus Interativo</h1>
      <p>Executa <code>main.py --prompt</code> no ambiente <code>.venv</code> e mostra a saida em tempo real por requisicao.</p>
      <div class="status"><strong>{status_title}:</strong> {html.escape(config_message)}</div>
      <form method="post">
        <label for="prompt"><strong>Prompt</strong></label>
        <textarea id="prompt" name="prompt" placeholder="Digite aqui sua tarefa para o OpenManus...">{escaped_prompt}</textarea>
        <br />
        <button type="submit">Executar OpenManus</button>
      </form>
      {result_block}
    </div>
  </div>
</body>
</html>
"""


class OpenManusHandler(BaseHTTPRequestHandler):
    def _send_html(self, page: str) -> None:
        encoded = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        self._send_html(render_page())

    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8", errors="replace")
        prompt = parse_qs(body).get("prompt", [""])[0].strip()
        if not prompt:
            self._send_html(render_page(result="Prompt vazio.", run_code=1))
            return
        code, output = run_openmanus(prompt)
        self._send_html(render_page(prompt=prompt, result=output, run_code=code))

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenManus local web launcher")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), OpenManusHandler)
    print(f"OpenManus web launcher rodando em http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
