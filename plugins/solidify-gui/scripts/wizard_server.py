#!/usr/bin/env python3
"""Serve the Solidify browser wizard for a questionnaire session."""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Solidify Wizard</title>
  <style>
    :root {
      --bg: #f7f4ed;
      --panel: #fffdf8;
      --ink: #1f1a14;
      --muted: #6b6258;
      --accent: #0f766e;
      --border: #d9cfbf;
      --warn: #8a5a00;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #f8ecd1 0, transparent 28%),
        linear-gradient(180deg, #fbf8f1 0%, var(--bg) 100%);
    }
    .shell {
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 64px;
    }
    .hero, .panel, .question {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: 0 10px 30px rgba(52, 41, 25, 0.06);
    }
    .hero {
      padding: 28px;
      margin-bottom: 18px;
    }
    .eyebrow {
      display: inline-block;
      margin-bottom: 8px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--accent);
    }
    h1 {
      margin: 0 0 8px;
      font-size: clamp(28px, 4vw, 44px);
      line-height: 1;
    }
    .subtitle {
      margin: 0;
      max-width: 720px;
      color: var(--muted);
      font-size: 16px;
      line-height: 1.5;
    }
    .grid {
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 18px;
      margin-bottom: 18px;
    }
    .panel {
      padding: 22px;
    }
    .panel h2 {
      margin-top: 0;
      font-size: 18px;
    }
    .panel ul {
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
    }
    .panel p, .panel li {
      line-height: 1.45;
    }
    .question {
      padding: 22px;
      margin-bottom: 16px;
    }
    .question h3 {
      margin: 8px 0 10px;
      font-size: 20px;
      line-height: 1.3;
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .chip {
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: #fcfaf5;
    }
    .label {
      font-weight: 700;
      color: var(--ink);
    }
    .block {
      margin-top: 14px;
      color: var(--muted);
      line-height: 1.45;
    }
    .choices {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 14px;
    }
    .choice {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: #fcfaf5;
    }
    textarea {
      width: 100%;
      min-height: 110px;
      margin-top: 12px;
      padding: 12px 14px;
      border-radius: 12px;
      border: 1px solid var(--border);
      font: inherit;
      background: white;
      color: var(--ink);
      resize: vertical;
    }
    button {
      appearance: none;
      border: 0;
      border-radius: 14px;
      padding: 14px 18px;
      font: inherit;
      font-weight: 700;
      color: white;
      background: var(--accent);
      cursor: pointer;
    }
    #status {
      margin-top: 14px;
      color: var(--warn);
      font-weight: 600;
    }
    .footer-note {
      margin-top: 16px;
      color: var(--muted);
    }
    @media (max-width: 900px) {
      .grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="eyebrow">Solidify Wizard</div>
      <h1>Make your prompt production-ready before you let the agent cook.</h1>
      <p class="subtitle">Review the repo-aware clarification questions below, answer only what matters, and save the result. Then return to Claude Code and reply <code>done</code>.</p>
    </section>

    <div class="grid">
      <section class="panel">
        <h2>Draft Prompt</h2>
        <p id="draftPrompt">Loading...</p>
      </section>
      <section class="panel">
        <h2>Risk Summary</h2>
        <ul id="riskSummary"></ul>
      </section>
    </div>

    <div class="grid">
      <section class="panel">
        <h2>Repo Facts</h2>
        <ul id="repoFacts"></ul>
      </section>
      <section class="panel">
        <h2>How To Use</h2>
        <ul>
          <li>Choose <strong>Custom answer</strong> if you want to steer the implementation directly.</li>
          <li>Choose <strong>Use default</strong> when the recommended default matches your intent.</li>
          <li>Choose <strong>Skip</strong> only when the assumption is safe enough for this run.</li>
        </ul>
      </section>
    </div>

    <form id="wizardForm">
      <div id="questions"></div>

      <section class="panel">
        <h2>Extra Notes</h2>
        <textarea id="extraNotes" placeholder="Optional notes for Claude before it compiles the production-ready prompt."></textarea>
        <div style="margin-top: 16px;">
          <button type="submit">Save Answers</button>
        </div>
        <div id="status"></div>
        <p class="footer-note">After saving, go back to Claude Code and reply <code>done</code>.</p>
      </section>
    </form>
  </div>

  <script>
    let sessionData = null;

    async function fetchJson(path, options) {
      const response = await fetch(path, options);
      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }
      return await response.json();
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    function byId(id) {
      return document.getElementById(id);
    }

    function renderList(id, items, emptyText) {
      const node = byId(id);
      node.innerHTML = "";
      const values = Array.isArray(items) && items.length ? items : [emptyText];
      values.forEach((item) => {
        const li = document.createElement("li");
        li.textContent = item;
        node.appendChild(li);
      });
    }

    function responseMap(existing) {
      const map = new Map();
      (existing.responses || []).forEach((response) => map.set(response.id, response));
      return map;
    }

    function renderQuestions(questionnaire, existing) {
      const responses = responseMap(existing);
      const container = byId("questions");
      container.innerHTML = "";

      questionnaire.questions.forEach((question, index) => {
        const current = responses.get(question.id) || {};
        const mode = current.mode || "default";
        const value = current.value || "";

        const section = document.createElement("section");
        section.className = "question";
        section.dataset.questionId = question.id;
        section.innerHTML = `
          <div class="meta">
            <span class="chip">${escapeHtml(question.importance)}</span>
            <span class="chip">${escapeHtml(question.category)}</span>
            <span class="chip">Question ${index + 1}</span>
          </div>
          <h3>${escapeHtml(question.question)}</h3>
          <div class="block"><span class="label">Why it matters:</span> ${escapeHtml(question.whyItMatters)}</div>
          <div class="block"><span class="label">Recommended default:</span> ${escapeHtml(question.recommendedDefault)}</div>
          <div class="block"><span class="label">Assumption if skipped:</span> ${escapeHtml(question.assumptionIfSkipped)}</div>
          <div class="choices">
            <label class="choice">
              <input type="radio" name="mode-${escapeHtml(question.id)}" value="custom" ${mode === "custom" ? "checked" : ""}>
              Custom answer
            </label>
            <label class="choice">
              <input type="radio" name="mode-${escapeHtml(question.id)}" value="default" ${mode === "default" ? "checked" : ""}>
              Use default
            </label>
            <label class="choice">
              <input type="radio" name="mode-${escapeHtml(question.id)}" value="skip" ${mode === "skip" ? "checked" : ""}>
              Skip
            </label>
          </div>
          <textarea data-role="value" placeholder="Enter your answer here.">${escapeHtml(value)}</textarea>
        `;
        container.appendChild(section);
      });

      container.querySelectorAll(".question").forEach((questionNode) => {
        const textarea = questionNode.querySelector("textarea");
        const updateState = () => {
          const mode = questionNode.querySelector("input[type=radio]:checked").value;
          textarea.disabled = mode !== "custom";
          if (mode !== "custom" && !textarea.dataset.preserved) {
            textarea.value = "";
          }
        };
        questionNode.querySelectorAll("input[type=radio]").forEach((radio) => {
          radio.addEventListener("change", updateState);
        });
        updateState();
      });
    }

    async function loadSession() {
      try {
        const payload = await fetchJson("/api/session");
        sessionData = payload.questionnaire;
        byId("draftPrompt").textContent = sessionData.draftPrompt || "(missing draft prompt)";
        renderList("riskSummary", sessionData.riskSummary || [], "No risk summary was provided.");
        renderList("repoFacts", sessionData.repoFacts || [], "No repo facts were recorded.");
        renderQuestions(sessionData, payload.answers || {});
        byId("extraNotes").value = (payload.answers && payload.answers.extraNotes) || "";
      } catch (error) {
        byId("status").textContent = `Failed to load session: ${error.message}`;
      }
    }

    async function saveAnswers(event) {
      event.preventDefault();
      if (!sessionData) {
        byId("status").textContent = "Session data is not loaded yet.";
        return;
      }

      const responses = sessionData.questions.map((question) => {
        const section = document.querySelector(`[data-question-id="${question.id}"]`);
        const mode = section.querySelector("input[type=radio]:checked").value;
        const value = section.querySelector("textarea").value.trim();
        let finalValue = "";
        if (mode === "custom") {
          finalValue = value;
        } else if (mode === "default") {
          finalValue = question.recommendedDefault;
        } else {
          finalValue = question.assumptionIfSkipped;
        }
        return {
          id: question.id,
          mode,
          value,
          finalValue
        };
      });

      const payload = {
        schemaVersion: 1,
        responses,
        extraNotes: byId("extraNotes").value.trim()
      };

      try {
        await fetchJson("/api/answers", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        byId("status").textContent = "Saved. Return to Claude Code and reply `done`.";
      } catch (error) {
        byId("status").textContent = `Save failed: ${error.message}`;
      }
    }

    document.addEventListener("DOMContentLoaded", () => {
      loadSession();
      byId("wizardForm").addEventListener("submit", saveAnswers);
    });
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the Solidify GUI wizard.")
    parser.add_argument("--session-dir", required=True, help="Session directory containing questionnaire.json")
    parser.add_argument("--port", required=True, type=int, help="Localhost port to serve")
    return parser.parse_args()


class WizardHandler(BaseHTTPRequestHandler):
    session_dir: Path

    def _json_response(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _text_response(self, text: str, status: int = HTTPStatus.OK) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html_response(self, html: str, status: int = HTTPStatus.OK) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._html_response(HTML_PAGE)
            return
        if path == "/health":
            self._text_response("ok")
            return
        if path == "/api/session":
            questionnaire_path = self.session_dir / "questionnaire.json"
            if not questionnaire_path.exists():
                self._json_response({"error": "questionnaire.json not found"}, status=HTTPStatus.NOT_FOUND)
                return
            questionnaire = json.loads(questionnaire_path.read_text())
            answers_path = self.session_dir / "answers.json"
            answers = json.loads(answers_path.read_text()) if answers_path.exists() else {}
            self._json_response({"questionnaire": questionnaire, "answers": answers})
            return
        self._text_response("not found", status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/answers":
            self._text_response("not found", status=HTTPStatus.NOT_FOUND)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._json_response({"error": "invalid JSON"}, status=HTTPStatus.BAD_REQUEST)
            return

        answers_path = self.session_dir / "answers.json"
        answers_path.write_text(json.dumps(payload, indent=2) + "\n")
        self._json_response({"ok": True})


def main() -> int:
    args = parse_args()
    session_dir = Path(args.session_dir).expanduser().resolve()
    session_dir.mkdir(parents=True, exist_ok=True)

    WizardHandler.session_dir = session_dir
    server = ThreadingHTTPServer(("127.0.0.1", args.port), WizardHandler)

    server_info = {
      "port": args.port,
      "url": f"http://127.0.0.1:{args.port}/"
    }
    (session_dir / "server.json").write_text(json.dumps(server_info, indent=2) + "\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
