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
      --bg: #f6f3ec;
      --ink: #191510;
      --muted: #6f675f;
      --line: rgba(25, 21, 16, 0.1);
      --panel: rgba(255, 255, 255, 0.8);
      --accent: #111111;
      --accent-soft: #ece8e1;
      --danger: #a53a14;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(242, 230, 203, 0.75), transparent 28%),
        linear-gradient(180deg, #fcfbf8 0%, var(--bg) 100%);
    }
    button, textarea, summary { font: inherit; }
    .app {
      min-height: 100%;
      display: flex;
      flex-direction: column;
      padding: 24px 18px 40px;
    }
    .topbar {
      width: min(980px, 100%);
      margin: 0 auto;
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 16px;
      align-items: center;
    }
    .brand {
      font-size: 12px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--muted);
      font-weight: 700;
    }
    .progress {
      height: 6px;
      background: rgba(25, 21, 16, 0.08);
      border-radius: 999px;
      overflow: hidden;
    }
    .progress-bar {
      width: 0%;
      height: 100%;
      background: linear-gradient(90deg, #191510 0%, #4d4338 100%);
      transition: width 160ms ease;
    }
    .progress-label {
      font-size: 13px;
      color: var(--muted);
      min-width: 56px;
      text-align: right;
    }
    .stage {
      flex: 1;
      width: min(980px, 100%);
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px 0;
    }
    .card {
      width: min(720px, 100%);
      padding: 28px;
      border: 1px solid var(--line);
      border-radius: 28px;
      background: var(--panel);
      backdrop-filter: blur(10px);
      box-shadow: 0 24px 60px rgba(30, 24, 18, 0.08);
    }
    .intro-kicker, .question-kicker {
      margin: 0 0 14px;
      font-size: 12px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--muted);
      font-weight: 700;
    }
    h1, h2 {
      margin: 0;
      font-size: clamp(32px, 6vw, 56px);
      line-height: 0.98;
      letter-spacing: -0.04em;
    }
    .lead {
      margin: 16px 0 0;
      color: var(--muted);
      font-size: 18px;
      line-height: 1.5;
      max-width: 52ch;
    }
    .details {
      margin-top: 22px;
      border-top: 1px solid var(--line);
      padding-top: 16px;
    }
    details {
      border-bottom: 1px solid var(--line);
      padding: 10px 0;
    }
    summary {
      cursor: pointer;
      color: var(--muted);
      font-size: 14px;
      list-style: none;
    }
    summary::-webkit-details-marker { display: none; }
    .details p, .details ul {
      margin: 10px 0 0;
      color: var(--muted);
      line-height: 1.5;
    }
    .details ul {
      padding-left: 18px;
    }
    .cta-row, .footer-row {
      margin-top: 28px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .meta-row {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 20px;
    }
    .chip {
      padding: 7px 12px;
      border-radius: 999px;
      border: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      background: rgba(255, 255, 255, 0.72);
    }
    .chip-strong {
      color: var(--ink);
      font-weight: 700;
    }
    .question-text {
      margin-top: 0;
      font-size: clamp(30px, 5vw, 50px);
      line-height: 1.02;
      letter-spacing: -0.04em;
    }
    .subtle {
      margin-top: 14px;
      font-size: 16px;
      color: var(--muted);
      line-height: 1.45;
    }
    .options {
      display: grid;
      gap: 12px;
      margin-top: 26px;
    }
    .option {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      padding: 16px 18px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.76);
      color: var(--ink);
      cursor: pointer;
      transition: transform 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
    }
    .option:hover {
      transform: translateY(-1px);
      border-color: rgba(25, 21, 16, 0.2);
      box-shadow: 0 10px 30px rgba(25, 21, 16, 0.05);
    }
    .option.active {
      border-color: rgba(17, 17, 17, 0.7);
      box-shadow: 0 16px 32px rgba(17, 17, 17, 0.08);
    }
    .option-title {
      font-weight: 700;
    }
    .option-note {
      color: var(--muted);
      font-size: 14px;
      line-height: 1.45;
      text-align: right;
      max-width: 42ch;
    }
    textarea {
      width: 100%;
      min-height: 180px;
      margin-top: 16px;
      padding: 18px 20px;
      border: 1px solid var(--line);
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.86);
      color: var(--ink);
      resize: vertical;
      outline: none;
    }
    textarea:focus {
      border-color: rgba(17, 17, 17, 0.35);
      box-shadow: 0 0 0 4px rgba(17, 17, 17, 0.05);
    }
    textarea:disabled {
      opacity: 0.55;
      background: rgba(245, 242, 236, 0.82);
    }
    .validation, .status {
      min-height: 20px;
      margin-top: 12px;
      color: var(--danger);
      font-size: 14px;
      font-weight: 600;
    }
    .status.ok {
      color: #1d6f42;
    }
    .button-row {
      display: flex;
      gap: 10px;
      align-items: center;
    }
    .button {
      appearance: none;
      border: 0;
      border-radius: 999px;
      padding: 14px 22px;
      background: var(--accent);
      color: white;
      font-weight: 700;
      cursor: pointer;
      transition: transform 120ms ease, opacity 120ms ease;
    }
    .button:hover { transform: translateY(-1px); }
    .button:disabled {
      cursor: not-allowed;
      opacity: 0.45;
      transform: none;
    }
    .button-secondary {
      background: transparent;
      color: var(--ink);
      border: 1px solid var(--line);
    }
    .minimal {
      color: var(--muted);
      font-size: 14px;
    }
    [hidden] { display: none !important; }
    @media (max-width: 720px) {
      .app { padding: 18px 14px 28px; }
      .topbar { grid-template-columns: 1fr; gap: 10px; }
      .progress-label { text-align: left; }
      .card { padding: 22px; border-radius: 22px; }
      .cta-row, .footer-row { flex-direction: column; align-items: stretch; }
      .button-row { width: 100%; justify-content: space-between; }
      .option { flex-direction: column; align-items: flex-start; }
      .option-note { text-align: left; max-width: none; }
    }
  </style>
</head>
<body>
  <div class="app">
    <header class="topbar">
      <div class="brand">Solidify</div>
      <div class="progress"><div id="progressBar" class="progress-bar"></div></div>
      <div id="progressLabel" class="progress-label">0 / 0</div>
    </header>

    <main class="stage">
      <section id="introView" class="card">
        <p class="intro-kicker">Prompt hardening</p>
        <h1>Make your prompt production-ready before you let the agent cook.</h1>
        <p class="lead">Answer only what matters. Everything else stays out of the way.</p>
        <div class="details">
          <details>
            <summary>Prompt</summary>
            <p id="draftPrompt">Loading...</p>
          </details>
          <details>
            <summary>Context</summary>
            <ul id="contextList"></ul>
          </details>
        </div>
        <div class="cta-row">
          <span id="introCount" class="minimal"></span>
          <div class="button-row">
            <button id="startButton" type="button" class="button">Start</button>
          </div>
        </div>
      </section>

      <section id="questionView" class="card" hidden>
        <div class="meta-row">
          <span id="importanceChip" class="chip chip-strong">Required</span>
          <span id="categoryChip" class="chip">Scope</span>
        </div>
        <p id="questionIndex" class="question-kicker">Question 1</p>
        <h2 id="questionText" class="question-text"></h2>
        <p id="whyText" class="subtle"></p>
        <div class="details">
          <details>
            <summary>Default / skip</summary>
            <p id="defaultText"></p>
            <p id="skipText"></p>
          </details>
        </div>
        <div class="options">
          <button type="button" class="option" data-mode="custom">
            <span class="option-title">Custom answer</span>
            <span class="option-note">Required if selected.</span>
          </button>
          <button type="button" class="option" data-mode="default">
            <span class="option-title">Use default</span>
            <span class="option-note" id="defaultOptionText"></span>
          </button>
          <button type="button" class="option" data-mode="skip">
            <span class="option-title">Skip</span>
            <span class="option-note" id="skipOptionText"></span>
          </button>
        </div>
        <textarea id="answerInput" placeholder="Type your answer..."></textarea>
        <div id="validationMessage" class="validation"></div>
        <div class="footer-row">
          <button id="backButton" type="button" class="button button-secondary">Back</button>
          <div class="button-row">
            <button id="nextButton" type="button" class="button">Next</button>
          </div>
        </div>
      </section>

      <section id="notesView" class="card" hidden>
        <p class="question-kicker">Final step</p>
        <h2>Anything else?</h2>
        <textarea id="extraNotes" placeholder="Optional note for Claude."></textarea>
        <div id="status" class="status"></div>
        <div class="footer-row">
          <button id="notesBackButton" type="button" class="button button-secondary">Back</button>
          <div class="button-row">
            <button id="saveButton" type="button" class="button">Save</button>
          </div>
        </div>
      </section>
    </main>
  </div>

  <script>
    let sessionData = null;
    let answersState = [];
    let currentStep = -1;

    async function fetchJson(path, options) {
      const response = await fetch(path, options);
      if (!response.ok) {
        let details = `Request failed: ${response.status}`;
        try {
          const payload = await response.json();
          if (payload.error) {
            details = payload.error;
          }
        } catch (error) {}
        throw new Error(details);
      }
      return await response.json();
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

    function stateForQuestion(question, existing) {
      if (existing) {
        return {
          id: question.id,
          mode: existing.mode || "custom",
          value: existing.value || "",
        };
      }
      return {
        id: question.id,
        mode: "custom",
        value: "",
      };
    }

    function responseMap(existing) {
      const map = new Map();
      (existing.responses || []).forEach((response) => map.set(response.id, response));
      return map;
    }

    function totalSteps() {
      const questions = sessionData ? sessionData.questions.length : 0;
      return questions + 1;
    }

    function setProgress(stepNumber) {
      const total = totalSteps();
      const clamped = Math.max(0, Math.min(stepNumber, total));
      const percentage = total ? (clamped / total) * 100 : 0;
      byId("progressBar").style.width = `${percentage}%`;
      byId("progressLabel").textContent = `${clamped} / ${total}`;
    }

    function showView(viewId) {
      ["introView", "questionView", "notesView"].forEach((id) => {
        byId(id).hidden = id !== viewId;
      });
    }

    function currentQuestion() {
      return sessionData.questions[currentStep];
    }

    function currentAnswerState() {
      return answersState[currentStep];
    }

    function selectMode(mode) {
      const state = currentAnswerState();
      state.mode = mode;
      document.querySelectorAll(".option").forEach((option) => {
        option.classList.toggle("active", option.dataset.mode === mode);
      });
      const input = byId("answerInput");
      input.disabled = mode !== "custom";
      if (mode === "custom") {
        input.focus();
      }
      byId("validationMessage").textContent = "";
    }

    function renderQuestion() {
      const question = currentQuestion();
      const state = currentAnswerState();

      byId("importanceChip").textContent = question.importance;
      byId("categoryChip").textContent = question.category;
      byId("questionIndex").textContent = `Question ${currentStep + 1}`;
      byId("questionText").textContent = question.question;
      byId("whyText").textContent = question.whyItMatters;
      byId("defaultText").textContent = `Use default: ${question.recommendedDefault}`;
      byId("skipText").textContent = `Skip: ${question.assumptionIfSkipped}`;
      byId("defaultOptionText").textContent = question.recommendedDefault;
      byId("skipOptionText").textContent = question.assumptionIfSkipped;
      byId("answerInput").value = state.value || "";
      byId("backButton").disabled = currentStep === 0;
      byId("nextButton").textContent = currentStep === sessionData.questions.length - 1 ? "Continue" : "Next";

      selectMode(state.mode || "custom");
      setProgress(currentStep + 1);
      showView("questionView");
    }

    function renderNotes() {
      byId("status").textContent = "";
      byId("status").classList.remove("ok");
      setProgress(totalSteps());
      showView("notesView");
    }

    function validateCurrentQuestion() {
      const state = currentAnswerState();
      if (state.mode === "custom" && !state.value.trim()) {
        byId("validationMessage").textContent = "Custom answer cannot be blank.";
        return false;
      }
      byId("validationMessage").textContent = "";
      return true;
    }

    function moveNext() {
      const input = byId("answerInput");
      currentAnswerState().value = input.value;
      if (!validateCurrentQuestion()) {
        return;
      }
      if (currentStep === sessionData.questions.length - 1) {
        renderNotes();
      } else {
        currentStep += 1;
        renderQuestion();
      }
    }

    function moveBack() {
      if (currentStep > 0) {
        currentAnswerState().value = byId("answerInput").value;
        currentStep -= 1;
        renderQuestion();
      } else {
        showView("introView");
        setProgress(0);
      }
    }

    function buildPayload() {
      return {
        schemaVersion: 1,
        responses: sessionData.questions.map((question, index) => {
          const state = answersState[index];
          const customValue = state.value.trim();
          let finalValue = "";
          if (state.mode === "custom") {
            finalValue = customValue;
          } else if (state.mode === "default") {
            finalValue = question.recommendedDefault;
          } else {
            finalValue = question.assumptionIfSkipped;
          }
          return {
            id: question.id,
            mode: state.mode,
            value: customValue,
            finalValue,
          };
        }),
        extraNotes: byId("extraNotes").value.trim(),
      };
    }

    async function loadSession() {
      try {
        const payload = await fetchJson("/api/session");
        sessionData = payload.questionnaire;
        const existing = responseMap(payload.answers || {});
        answersState = sessionData.questions.map((question) => stateForQuestion(question, existing.get(question.id)));

        byId("draftPrompt").textContent = sessionData.draftPrompt || "(missing draft prompt)";
        renderList("contextList", [...(sessionData.riskSummary || []), ...(sessionData.repoFacts || [])], "No additional context.");
        byId("introCount").textContent = `${sessionData.questions.length} questions`;
        byId("extraNotes").value = (payload.answers && payload.answers.extraNotes) || "";
        setProgress(0);
      } catch (error) {
        byId("introCount").textContent = "Load failed";
        byId("draftPrompt").textContent = error.message;
      }
    }

    async function saveAnswers() {
      const payload = buildPayload();
      const hasBlankCustom = payload.responses.some((response) => response.mode === "custom" && !response.value);
      if (hasBlankCustom) {
        byId("status").textContent = "A custom answer is still blank.";
        byId("status").classList.remove("ok");
        return;
      }

      try {
        await fetchJson("/api/answers", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        byId("status").textContent = "Saved. Go back to Claude Code and reply done.";
        byId("status").classList.add("ok");
      } catch (error) {
        byId("status").textContent = error.message;
        byId("status").classList.remove("ok");
      }
    }

    document.addEventListener("DOMContentLoaded", () => {
      loadSession();

      byId("startButton").addEventListener("click", () => {
        if (!sessionData || !sessionData.questions.length) {
          renderNotes();
          return;
        }
        currentStep = 0;
        renderQuestion();
      });

      document.querySelectorAll(".option").forEach((option) => {
        option.addEventListener("click", () => selectMode(option.dataset.mode));
      });

      byId("answerInput").addEventListener("input", (event) => {
        if (currentStep >= 0) {
          currentAnswerState().value = event.target.value;
        }
      });

      byId("nextButton").addEventListener("click", moveNext);
      byId("backButton").addEventListener("click", moveBack);
      byId("notesBackButton").addEventListener("click", () => {
        if (sessionData && sessionData.questions.length) {
          currentStep = sessionData.questions.length - 1;
          renderQuestion();
        } else {
          showView("introView");
          setProgress(0);
        }
      });
      byId("saveButton").addEventListener("click", saveAnswers);
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

        questionnaire_path = self.session_dir / "questionnaire.json"
        if not questionnaire_path.exists():
            self._json_response({"error": "questionnaire.json not found"}, status=HTTPStatus.NOT_FOUND)
            return

        questionnaire = json.loads(questionnaire_path.read_text())
        questions = questionnaire.get("questions", [])
        question_map = {question.get("id"): question for question in questions}
        responses = payload.get("responses")
        if not isinstance(responses, list):
            self._json_response({"error": "responses must be an array"}, status=HTTPStatus.BAD_REQUEST)
            return

        seen_ids = set()
        for response in responses:
            question_id = response.get("id")
            if question_id not in question_map:
                self._json_response({"error": f"unknown question id: {question_id}"}, status=HTTPStatus.BAD_REQUEST)
                return
            if question_id in seen_ids:
                self._json_response({"error": f"duplicate question id: {question_id}"}, status=HTTPStatus.BAD_REQUEST)
                return
            seen_ids.add(question_id)

            mode = response.get("mode")
            if mode not in {"custom", "default", "skip"}:
                self._json_response({"error": f"invalid mode for {question_id}"}, status=HTTPStatus.BAD_REQUEST)
                return
            if mode == "custom" and not str(response.get("value", "")).strip():
                self._json_response({"error": f"custom answer cannot be blank for {question_id}"}, status=HTTPStatus.BAD_REQUEST)
                return

        missing_ids = [question_id for question_id in question_map if question_id not in seen_ids]
        if missing_ids:
            self._json_response({"error": f"missing responses for: {', '.join(missing_ids)}"}, status=HTTPStatus.BAD_REQUEST)
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
