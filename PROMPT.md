# MASTER PROMPT — AI Study Pack Generator

Act as a Senior AI Engineer, Python Developer, Prompt Engineer, Streamlit Expert, and AI Workflow Architect.

Build a production-ready AI Study Pack Generator using Python and Streamlit.

## Architecture

The project has exactly these application files:

ai-study-pack-generator/
├── app.py
├── ai_workflow.py
├── utils.py
├── workflow.md
└── requirements.txt

app.py is the main entry point.

## AI workflow

Implement a sequential multi-stage workflow:

1. PLANNING
2. CONTENT GENERATION
3. ASSESSMENT
4. REVIEW
5. REFINEMENT

The workflow must pass context from one stage to the next.

Use a shared workflow state containing:
- user input
- planning
- content
- assessment
- review
- final_pack
- errors

Each AI stage should have a focused prompt rather than one giant prompt.

## Planning stage

Analyze:
- subject
- student level
- study material
- pack size

Return structured JSON with:
- learning_objectives
- main_topics
- difficulty
- important_concepts
- recommended_focus
- generation_plan

## Content stage

Use the original study material plus planning context.

Generate:
- summary
- key concepts
- definitions
- important facts
- formulas when supported
- examples
- flashcards

Only use information supported by the source material. Do not invent unsupported facts.

## Assessment stage

Use planning and generated content.

Generate:
- MCQs
- short-answer questions
- conceptual questions
- application questions
- answers

Match difficulty to the student's level.

## Review stage

Act as a strict quality reviewer.

Check:
- factual/source grounding
- topic coverage
- clarity
- student-level suitability
- assessment quality
- personalization

Return:
- quality_score
- issues
- missing_topics
- recommendations

## Refinement stage

Use all previous context and review feedback.

Fix problems and produce the final study pack with:

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

## Error handling

The app must:
- validate empty input
- handle missing API key
- handle API/network errors
- handle malformed JSON
- handle PDF extraction errors
- keep the UI alive when one stage fails
- use a deterministic fallback generator when AI is unavailable

## Streamlit UI

Create a professional student-focused interface.

Sidebar:
- Subject
- Student Level
- Pack Size
- AI Model

Main area:
- Study material textbox
- PDF/TXT/MD/CSV uploader
- Generate Study Pack button
- workflow progress
- stage results in tabs
- final pack
- download button

Show progress:
Stage 1/5 — Planning
Stage 2/5 — Content Generation
Stage 3/5 — Assessment
Stage 4/5 — Review
Stage 5/5 — Refinement

Use Streamlit secrets for OPENAI_API_KEY.

Never hard-code API credentials.

## Deployment

The final project must run with:

streamlit run app.py

and deploy to Streamlit Community Cloud with app.py as the main file.

Return complete runnable code for all files. Do not provide pseudocode.
