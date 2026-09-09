import json
import os
import re
from typing import Any, Dict, Callable

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class StudyPackWorkflow:
    """Five-stage AI workflow with context passing and fallback handling."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-5"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5")
        self.client = OpenAI(api_key=self.api_key) if self.api_key and OpenAI else None

    def _call_json(self, system: str, user: str) -> Dict[str, Any]:
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        response = self.client.responses.create(
            model=self.model,
            instructions=system,
            input=user,
        )
        text = response.output_text.strip()

        # Remove Markdown code fences if a model returns them.
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.S)
            if not match:
                raise ValueError("AI returned invalid JSON.")
            return json.loads(match.group(0))

    def planning_stage(self, subject: str, level: str, material: str, pack_size: str):
        system = """You are the Planning Agent for a study-pack workflow.
Return ONLY valid JSON. Do not invent information not supported by the material."""
        user = f"""
Subject: {subject}
Student level: {level}
Pack size: {pack_size}

Study material:
{material}

Return:
{{
  "learning_objectives": [],
  "main_topics": [],
  "difficulty": "",
  "important_concepts": [],
  "recommended_focus": [],
  "generation_plan": []
}}
"""
        return self._call_json(system, user)

    def content_stage(self, context: Dict[str, Any]):
        system = """You are the Content Generation Agent.
Return ONLY valid JSON and stay grounded in the supplied study material."""
        user = f"""
Original input:
{json.dumps(context["input"], ensure_ascii=False)}

Planning context:
{json.dumps(context["planning"], ensure_ascii=False)}

Return:
{{
  "summary": "",
  "key_concepts": [],
  "definitions": [],
  "facts_and_formulas": [],
  "examples": [],
  "flashcards": [
    {{"question": "", "answer": ""}}
  ]
}}
"""
        return self._call_json(system, user)

    def assessment_stage(self, context: Dict[str, Any]):
        system = """You are the Assessment Agent.
Return ONLY valid JSON. Questions must be answerable from the supplied material."""
        user = f"""
Planning:
{json.dumps(context["planning"], ensure_ascii=False)}

Content:
{json.dumps(context["content"], ensure_ascii=False)}

Return:
{{
  "mcqs": [
    {{"question": "", "options": [], "answer": "", "explanation": ""}}
  ],
  "short_questions": [
    {{"question": "", "answer": ""}}
  ],
  "conceptual_questions": [
    {{"question": "", "answer": ""}}
  ],
  "application_questions": [
    {{"question": "", "answer": ""}}
  ]
}}
"""
        return self._call_json(system, user)

    def review_stage(self, context: Dict[str, Any]):
        system = """You are a strict Study Pack Review Agent.
Return ONLY valid JSON."""
        user = f"""
Planning:
{json.dumps(context["planning"], ensure_ascii=False)}

Content:
{json.dumps(context["content"], ensure_ascii=False)}

Assessment:
{json.dumps(context["assessment"], ensure_ascii=False)}

Review for source grounding, coverage, clarity, level suitability, assessment quality,
and personalization.

Return:
{{
  "quality_score": 0,
  "issues": [],
  "missing_topics": [],
  "recommendations": []
}}
"""
        return self._call_json(system, user)

    def refinement_stage(self, context: Dict[str, Any]):
        system = """You are the Refinement Agent.
Return a polished Markdown study pack. Do not invent unsupported facts."""
        user = f"""
Original input:
{json.dumps(context["input"], ensure_ascii=False)}

Planning:
{json.dumps(context["planning"], ensure_ascii=False)}

Content:
{json.dumps(context["content"], ensure_ascii=False)}

Assessment:
{json.dumps(context["assessment"], ensure_ascii=False)}

Review:
{json.dumps(context["review"], ensure_ascii=False)}

Create the final personalized study pack with:
# Final Study Pack
## Summary
## Learning Objectives
## Key Concepts
## Important Definitions
## Important Facts / Formulas
## Examples
## Flashcards
## Practice Questions
## 7-Day Study Plan
## Final Self-Test
## Answer Key
"""
        if not self.client:
            raise RuntimeError("AI unavailable; using fallback.")
        response = self.client.responses.create(
            model=self.model,
            instructions=system,
            input=user,
        )
        return response.output_text.strip()

    def fallback_pack(self, subject: str, level: str, material: str, pack_size: str) -> str:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", material) if p.strip()]
        sentences = re.split(r"(?<=[.!?])\s+", material.strip())
        useful = [x for x in (paragraphs + sentences) if len(x) > 25][:10]

        lines = [
            f"# Final Study Pack — {subject or 'Study Pack'}",
            f"**Level:** {level}",
            f"**Mode:** {pack_size}",
            "",
            "## Summary",
            "The following points were extracted from your supplied material:",
        ]
        lines += [f"- {x}" for x in useful[:5]]
        lines += ["", "## Key Concepts"]
        lines += [f"{i}. {x}" for i, x in enumerate(useful[:7], 1)]
        lines += ["", "## Flashcards"]

        for i, x in enumerate(useful[:7], 1):
            lines += [
                f"**Q{i}.** Explain this idea: {x}",
                f"**A{i}.** Review the source material and explain it in your own words.",
                "",
            ]

        lines += [
            "## Practice Questions",
            *[f"{i}. Explain the main idea in: {x}" for i, x in enumerate(useful[:7], 1)],
            "",
            "## 7-Day Study Plan",
            "1. Read and annotate the material.",
            "2. Review the key concepts.",
            "3. Practice the flashcards.",
            "4. Answer the practice questions.",
            "5. Review weak areas.",
            "6. Take a self-test.",
            "7. Perform a final review.",
        ]
        return "\n".join(lines)

    def run(self, subject: str, level: str, material: str, pack_size: str,
            progress: Callable[[int, str], None] | None = None) -> Dict[str, Any]:

        context: Dict[str, Any] = {
            "input": {
                "subject": subject,
                "level": level,
                "pack_size": pack_size,
                "material": material,
            },
            "planning": None,
            "content": None,
            "assessment": None,
            "review": None,
            "final_pack": None,
            "errors": [],
        }

        stages = [
            ("Planning", lambda: self.planning_stage(subject, level, material, pack_size)),
            ("Content Generation", lambda: self.content_stage(context)),
            ("Assessment", lambda: self.assessment_stage(context)),
            ("Review", lambda: self.review_stage(context)),
            ("Refinement", lambda: self.refinement_stage(context)),
        ]

        for index, (name, function) in enumerate(stages, 1):
            if progress:
                progress(index, name)

            try:
                result = function()
                context[["planning", "content", "assessment", "review", "final_pack"][index - 1]] = result
            except Exception as exc:
                context["errors"].append({
                    "stage": name,
                    "error": f"{type(exc).__name__}: {exc}"
                })

                if name == "Refinement":
                    context["final_pack"] = self.fallback_pack(
                        subject, level, material, pack_size
                    )
                    break

                # Stop AI chain if an earlier dependency fails.
                if index < 5:
                    context["final_pack"] = self.fallback_pack(
                        subject, level, material, pack_size
                    )
                    break

        if not context["final_pack"]:
            context["final_pack"] = self.fallback_pack(
                subject, level, material, pack_size
            )

        return context
