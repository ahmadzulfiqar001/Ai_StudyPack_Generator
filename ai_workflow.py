import json
import os
import re
from typing import Any, Dict, Callable, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ============================================================
# GROQ CONFIGURATION
# ============================================================

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

DEFAULT_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
)


class StudyPackWorkflow:
    """
    Five-stage AI study-pack workflow.

    Workflow:
        Planning
        ↓
        Content Generation
        ↓
        Assessment
        ↓
        Review
        ↓
        Refinement

    Uses Groq through the OpenAI-compatible API.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        # ----------------------------------------------------
        # API KEY
        # ----------------------------------------------------

        self.api_key = (
            api_key
            or os.getenv("GROQ_API_KEY", "")
        ).strip()

        # ----------------------------------------------------
        # MODEL
        # ----------------------------------------------------

        self.model = (
            model
            or os.getenv(
                "GROQ_MODEL",
                DEFAULT_MODEL,
            )
        ).strip()

        # ----------------------------------------------------
        # CLIENT
        # ----------------------------------------------------

        self.client = None

        if self.api_key and OpenAI:

            self.client = OpenAI(
                api_key=self.api_key,
                base_url=GROQ_BASE_URL,
            )


    # ========================================================
    # JSON AI CALL
    # ========================================================

    def _call_json(
        self,
        system: str,
        user: str,
    ) -> Dict[str, Any]:

        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured."
            )

        if OpenAI is None:
            raise RuntimeError(
                "The openai package is not installed. "
                "Add openai to requirements.txt."
            )

        if self.client is None:
            raise RuntimeError(
                "Groq client could not be initialized."
            )

        try:

            response = self.client.responses.create(
                model=self.model,
                instructions=system,
                input=user,
            )

        except Exception as exc:

            raise RuntimeError(
                f"Groq API error using model "
                f"'{self.model}': {exc}"
            ) from exc

        # ----------------------------------------------------
        # Extract response text
        # ----------------------------------------------------

        text = getattr(
            response,
            "output_text",
            "",
        )

        if not text:
            raise ValueError(
                "Groq returned an empty response."
            )

        text = text.strip()

        # ----------------------------------------------------
        # Remove Markdown code fences
        # ----------------------------------------------------

        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        text = text.strip()

        # ----------------------------------------------------
        # Parse JSON directly
        # ----------------------------------------------------

        try:

            result = json.loads(text)

            if not isinstance(result, dict):
                raise ValueError(
                    "AI response JSON must be an object."
                )

            return result

        except json.JSONDecodeError:
            pass

        # ----------------------------------------------------
        # Try extracting JSON object
        # ----------------------------------------------------

        match = re.search(
            r"\{.*\}",
            text,
            re.DOTALL,
        )

        if not match:

            raise ValueError(
                "Groq returned invalid JSON. "
                f"Response received: {text[:500]}"
            )

        try:

            result = json.loads(
                match.group(0)
            )

        except json.JSONDecodeError as exc:

            raise ValueError(
                "Groq returned malformed JSON."
            ) from exc

        if not isinstance(result, dict):

            raise ValueError(
                "AI response JSON must be an object."
            )

        return result


    # ========================================================
    # STAGE 1 — PLANNING
    # ========================================================

    def planning_stage(
        self,
        subject: str,
        level: str,
        material: str,
        pack_size: str,
    ):

        system = """
You are the Planning Agent in an AI Study Pack Generator.

Your job is to analyze the supplied study material and create
a structured study plan.

Rules:
- Return ONLY valid JSON.
- Do not use Markdown.
- Do not invent facts that are not supported by the material.
- Identify the most important concepts.
- Adapt the plan to the student's level.
- Adapt the depth to the requested pack size.
"""

        user = f"""
Subject:
{subject}

Student Level:
{level}

Pack Size:
{pack_size}

Study Material:
{material}

Return exactly this JSON structure:

{{
  "learning_objectives": [],
  "main_topics": [],
  "difficulty": "",
  "important_concepts": [],
  "recommended_focus": [],
  "generation_plan": []
}}
"""

        return self._call_json(
            system,
            user,
        )


    # ========================================================
    # STAGE 2 — CONTENT GENERATION
    # ========================================================

    def content_stage(
        self,
        context: Dict[str, Any],
    ):

        system = """
You are the Content Generation Agent.

Create high-quality study material based ONLY on the
original study material and planning information.

Rules:
- Return ONLY valid JSON.
- Do not use Markdown.
- Do not invent unsupported facts.
- Keep explanations appropriate for the student's level.
- Make the content clear and useful for exam preparation.
"""

        user = f"""
Original Study Material:

{json.dumps(
    context["input"],
    ensure_ascii=False,
    indent=2,
)}

Planning Context:

{json.dumps(
    context["planning"],
    ensure_ascii=False,
    indent=2,
)}

Return exactly this JSON structure:

{{
  "summary": "",
  "key_concepts": [],
  "definitions": [],
  "facts_and_formulas": [],
  "examples": [],
  "flashcards": [
    {{
      "question": "",
      "answer": ""
    }}
  ]
}}
"""

        return self._call_json(
            system,
            user,
        )


    # ========================================================
    # STAGE 3 — ASSESSMENT
    # ========================================================

    def assessment_stage(
        self,
        context: Dict[str, Any],
    ):

        system = """
You are the Assessment Agent.

Create an assessment based strictly on the supplied
study material, planning, and generated content.

Rules:
- Return ONLY valid JSON.
- Do not use Markdown.
- Questions must be answerable from the supplied material.
- Include correct answers.
- Include explanations where appropriate.
- Match the student's level.
"""

        user = f"""
Planning:

{json.dumps(
    context["planning"],
    ensure_ascii=False,
    indent=2,
)}

Generated Content:

{json.dumps(
    context["content"],
    ensure_ascii=False,
    indent=2,
)}

Return exactly this JSON structure:

{{
  "mcqs": [
    {{
      "question": "",
      "options": [],
      "answer": "",
      "explanation": ""
    }}
  ],
  "short_questions": [
    {{
      "question": "",
      "answer": ""
    }}
  ],
  "conceptual_questions": [
    {{
      "question": "",
      "answer": ""
    }}
  ],
  "application_questions": [
    {{
      "question": "",
      "answer": ""
    }}
  ]
}}
"""

        return self._call_json(
            system,
            user,
        )


    # ========================================================
    # STAGE 4 — REVIEW
    # ========================================================

    def review_stage(
        self,
        context: Dict[str, Any],
    ):

        system = """
You are a strict Study Pack Review Agent.

Evaluate the generated study pack for:

1. Source grounding
2. Topic coverage
3. Accuracy
4. Clarity
5. Student-level suitability
6. Assessment quality
7. Personalization

Rules:
- Return ONLY valid JSON.
- Do not use Markdown.
- Give a quality score from 0 to 100.
- Identify concrete issues.
- Identify missing topics.
- Provide actionable recommendations.
"""

        user = f"""
Planning:

{json.dumps(
    context["planning"],
    ensure_ascii=False,
    indent=2,
)}

Content:

{json.dumps(
    context["content"],
    ensure_ascii=False,
    indent=2,
)}

Assessment:

{json.dumps(
    context["assessment"],
    ensure_ascii=False,
    indent=2,
)}

Return exactly this JSON structure:

{{
  "quality_score": 0,
  "issues": [],
  "missing_topics": [],
  "recommendations": []
}}
"""

        return self._call_json(
            system,
            user,
        )


    # ========================================================
    # STAGE 5 — REFINEMENT
    # ========================================================

    def refinement_stage(
        self,
        context: Dict[str, Any],
    ):

        if not self.client:

            raise RuntimeError(
                "Groq AI client is unavailable."
            )

        system = """
You are the final Refinement Agent.

Create a polished, personalized Markdown study pack
using the supplied material and all previous workflow stages.

Rules:
- Stay grounded in the original study material.
- Do not invent unsupported facts.
- Incorporate useful recommendations from the review.
- Make the result clear and exam-friendly.
- Return ONLY the final Markdown study pack.
- Do not wrap the answer in a Markdown code fence.
"""

        user = f"""
Original Input:

{json.dumps(
    context["input"],
    ensure_ascii=False,
    indent=2,
)}

Planning:

{json.dumps(
    context["planning"],
    ensure_ascii=False,
    indent=2,
)}

Content:

{json.dumps(
    context["content"],
    ensure_ascii=False,
    indent=2,
)}

Assessment:

{json.dumps(
    context["assessment"],
    ensure_ascii=False,
    indent=2,
)}

Review:

{json.dumps(
    context["review"],
    ensure_ascii=False,
    indent=2,
)}

Create the final study pack using this structure:

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

        try:

            response = self.client.responses.create(
                model=self.model,
                instructions=system,
                input=user,
            )

        except Exception as exc:

            raise RuntimeError(
                f"Groq API error during refinement "
                f"using model '{self.model}': {exc}"
            ) from exc

        text = getattr(
            response,
            "output_text",
            "",
        )

        if not text:

            raise ValueError(
                "Groq returned an empty final study pack."
            )

        return text.strip()


    # ========================================================
    # FALLBACK STUDY PACK
    # ========================================================

    def fallback_pack(
        self,
        subject: str,
        level: str,
        material: str,
        pack_size: str,
    ) -> str:

        paragraphs = [
            p.strip()
            for p in re.split(
                r"\n\s*\n",
                material,
            )
            if p.strip()
        ]

        sentences = re.split(
            r"(?<=[.!?])\s+",
            material.strip(),
        )

        useful = [
            item
            for item in (
                paragraphs + sentences
            )
            if len(item) > 25
        ][:10]

        if not useful:

            useful = [
                material.strip()
            ] if material.strip() else [
                "No study material was provided."
            ]

        lines = [
            f"# Final Study Pack — "
            f"{subject or 'Study Pack'}",
            "",
            f"**Student Level:** {level}",
            f"**Pack Size:** {pack_size}",
            "",
            "## Summary",
            "",
            "The following information was extracted "
            "from the supplied study material.",
            "",
        ]

        lines.extend(
            f"- {item}"
            for item in useful[:5]
        )

        lines.extend(
            [
                "",
                "## Key Concepts",
                "",
            ]
        )

        lines.extend(
            f"{index}. {item}"
            for index, item in enumerate(
                useful[:7],
                1,
            )
        )

        lines.extend(
            [
                "",
                "## Flashcards",
                "",
            ]
        )

        for index, item in enumerate(
            useful[:7],
            1,
        ):

            lines.extend(
                [
                    f"**Q{index}.** "
                    f"What is the main idea of this point?",
                    "",
                    f"**A{index}.** {item}",
                    "",
                ]
            )

        lines.extend(
            [
                "## Practice Questions",
                "",
            ]
        )

        lines.extend(
            f"{index}. Explain the main idea "
            f"of the following point: {item}"
            for index, item in enumerate(
                useful[:7],
                1,
            )
        )

        lines.extend(
            [
                "",
                "## 7-Day Study Plan",
                "",
                "### Day 1",
                "Read and annotate the material.",
                "",
                "### Day 2",
                "Review the key concepts.",
                "",
                "### Day 3",
                "Practice the flashcards.",
                "",
                "### Day 4",
                "Answer the practice questions.",
                "",
                "### Day 5",
                "Review difficult or weak areas.",
                "",
                "### Day 6",
                "Take a self-test without looking at the answers.",
                "",
                "### Day 7",
                "Perform a final review of the complete material.",
                "",
            ]
        )

        return "\n".join(lines)


    # ========================================================
    # RUN COMPLETE WORKFLOW
    # ========================================================

    def run(
        self,
        subject: str,
        level: str,
        material: str,
        pack_size: str,
        progress: Callable[
            [int, str],
            None
        ] | None = None,
    ) -> Dict[str, Any]:

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

        # ----------------------------------------------------
        # Stage definitions
        # ----------------------------------------------------

        stages = [
            (
                "Planning",
                lambda: self.planning_stage(
                    subject,
                    level,
                    material,
                    pack_size,
                ),
            ),
            (
                "Content Generation",
                lambda: self.content_stage(
                    context
                ),
            ),
            (
                "Assessment",
                lambda: self.assessment_stage(
                    context
                ),
            ),
            (
                "Review",
                lambda: self.review_stage(
                    context
                ),
            ),
            (
                "Refinement",
                lambda: self.refinement_stage(
                    context
                ),
            ),
        ]

        result_keys = [
            "planning",
            "content",
            "assessment",
            "review",
            "final_pack",
        ]

        # ----------------------------------------------------
        # Execute stages
        # ----------------------------------------------------

        for index, (
            name,
            function,
        ) in enumerate(
            stages,
            1,
        ):

            if progress:

                progress(
                    index,
                    name,
                )

            try:

                result = function()

                context[
                    result_keys[index - 1]
                ] = result

            except Exception as exc:

                error_message = (
                    f"{type(exc).__name__}: {exc}"
                )

                context["errors"].append(
                    {
                        "stage": name,
                        "error": error_message,
                    }
                )

                # ------------------------------------------------
                # If refinement fails, create fallback pack.
                # ------------------------------------------------

                if name == "Refinement":

                    context["final_pack"] = (
                        self.fallback_pack(
                            subject,
                            level,
                            material,
                            pack_size,
                        )
                    )

                    break

                # ------------------------------------------------
                # Earlier-stage failure means dependencies
                # are unavailable, so stop the AI chain.
                # ------------------------------------------------

                context["final_pack"] = (
                    self.fallback_pack(
                        subject,
                        level,
                        material,
                        pack_size,
                    )
                )

                break

        # ----------------------------------------------------
        # Guarantee final pack
        # ----------------------------------------------------

        if not context["final_pack"]:

            context["final_pack"] = (
                self.fallback_pack(
                    subject,
                    level,
                    material,
                    pack_size,
                )
            )

        return context
