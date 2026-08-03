"""Pluggable narrative layer: turns numeric scores/evidence into bull/bear cases
and red flags. The numbers are never computed here — this layer only explains
what the scorecard already found.

StubBackend needs no LLM at all (pure template rendering over the evidence
already produced by scorecard.py) so the system is fully useful before you
ever install a local model. OllamaBackend swaps in a real local LLM
(https://ollama.com) for richer prose once you have one running.
"""
from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod

import requests

CATEGORY_LABELS = {
    "business_quality": "business quality",
    "growth": "growth",
    "financial_strength": "financial strength",
    "valuation": "valuation",
}


class LLMBackend(ABC):
    @abstractmethod
    def generate_analysis(self, context: dict) -> dict:
        """context has: ticker, company_name, scores, trends, evidence, valuation_range.

        Must return {"bull_case": str, "bear_case": str, "red_flags": list[str], "source": str}.
        """


class StubBackend(LLMBackend):
    """No LLM required — renders bull/bear/red-flags directly from the evidence
    the numeric scorecard already generated."""

    def generate_analysis(self, context: dict) -> dict:
        scores = context.get("scores", {})
        evidence = context.get("evidence", {})
        trends = context.get("trends", {})

        strong = [(CATEGORY_LABELS[c], evidence[c][0]) for c in CATEGORY_LABELS
                  if scores.get(c) is not None and scores[c] >= 65 and evidence.get(c)]
        weak = [(CATEGORY_LABELS[c], evidence[c][0]) for c in CATEGORY_LABELS
                if scores.get(c) is not None and scores[c] < 45 and evidence.get(c)]

        if strong:
            bull_case = ("Strengths in " + ", ".join(name for name, _ in strong) + ". "
                         + " ".join(text for _, text in strong))
        else:
            bull_case = "No standout strengths identified from the reported financials alone."

        if weak:
            bear_case = ("Weaknesses in " + ", ".join(name for name, _ in weak) + ". "
                        + " ".join(text for _, text in weak))
        else:
            bear_case = "No major weaknesses identified from the reported financials alone."

        red_flags = []
        if trends.get("debt_position") == "High":
            red_flags.append("Debt load is high relative to equity.")
        if trends.get("fcf_status") == "Negative":
            red_flags.append("Free cash flow was negative in the latest fiscal year.")
        if trends.get("share_dilution") == "High":
            red_flags.append("Shareholders are being diluted meaningfully (>3%/yr average, trailing 3 years).")
        if scores.get("risk_label") == "High":
            red_flags.append("Overall risk score is High.")
        if scores.get("valuation") is not None and scores["valuation"] < 20:
            red_flags.append("Valuation multiples are rich relative to the heuristic bands used here.")
        if not red_flags:
            red_flags.append("No major red flags detected from the metrics tracked here.")

        return {"bull_case": bull_case, "bear_case": bear_case, "red_flags": red_flags, "source": "template (no LLM)"}


class OllamaBackend(LLMBackend):
    """Calls a local Ollama server (https://ollama.com) for richer natural-language analysis."""

    def __init__(self, model: str = "llama3.1", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")

    def _build_prompt(self, context: dict) -> str:
        scores = context.get("scores", {})
        trends = context.get("trends", {})
        evidence = context.get("evidence", {})
        lines = [
            f"You are analyzing {context.get('company_name', context.get('ticker'))} "
            f"({context.get('ticker')}) using only the figures below, which come from its SEC filings.",
            "Scores (0-100, already computed numerically):",
        ]
        for cat, label in CATEGORY_LABELS.items():
            lines.append(f"- {label}: {scores.get(cat)}")
        lines.append(f"- risk: {scores.get('risk_label')} ({scores.get('risk_score')}/100)")
        lines.append("Trends: " + ", ".join(f"{k}={v}" for k, v in trends.items()))
        lines.append("Evidence behind the scores:")
        for cat, items in evidence.items():
            for item in items:
                lines.append(f"- [{cat}] {item}")
        lines.append(
            "\nWrite a concise, evidence-grounded response with exactly these sections:\n"
            "Bull case: <2-3 sentences>\nBear case: <2-3 sentences>\nRed flags: <bullet list, or 'None'>"
        )
        return "\n".join(lines)

    def generate_analysis(self, context: dict) -> dict:
        prompt = self._build_prompt(context)
        resp = requests.post(
            f"{self.host}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        text = resp.json().get("response", "")
        parsed = self._parse(text)
        parsed["source"] = f"ollama:{self.model}"
        return parsed

    @staticmethod
    def _parse(text: str) -> dict:
        bull = re.search(r"bull case:(.*?)(?:bear case:|$)", text, re.IGNORECASE | re.DOTALL)
        bear = re.search(r"bear case:(.*?)(?:red flags:|$)", text, re.IGNORECASE | re.DOTALL)
        flags = re.search(r"red flags:(.*)$", text, re.IGNORECASE | re.DOTALL)

        def clean(m) -> str:
            return m.group(1).strip() if m else ""

        red_flags_text = clean(flags)
        red_flags = [line.strip("-* ").strip() for line in red_flags_text.splitlines() if line.strip()] or ["None"]

        if not bull and not bear:
            return {"bull_case": text.strip(), "bear_case": "", "red_flags": []}
        return {"bull_case": clean(bull), "bear_case": clean(bear), "red_flags": red_flags}


def get_backend(name: str | None = None) -> LLMBackend:
    name = (name or os.environ.get("MCSTOCK_LLM_BACKEND", "stub")).lower()
    if name == "ollama":
        model = os.environ.get("MCSTOCK_OLLAMA_MODEL", "llama3.1")
        host = os.environ.get("MCSTOCK_OLLAMA_HOST", "http://localhost:11434")
        return OllamaBackend(model=model, host=host)
    return StubBackend()
