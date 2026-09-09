# AI Study Pack Generator — Workflow Specification

## Objective
Build a personalized study-pack generator as a multi-stage AI workflow.

## Pipeline
1. Planning
   - Analyze subject, student level, study material, and pack size.
   - Produce learning objectives, topics, difficulty, priorities, and a generation plan.

2. Content Generation
   - Receive the original input plus planning context.
   - Generate summary, concepts, definitions, facts/formulas, examples, and flashcards.

3. Assessment
   - Receive planning + generated content.
   - Generate MCQs, short-answer questions, conceptual/application questions, and answer key.

4. Review
   - Receive planning + content + assessment.
   - Check source grounding, topic coverage, level appropriateness, assessment quality, and clarity.
   - Return score, issues, missing topics, and recommendations.

5. Refinement
   - Receive all previous context plus review feedback.
   - Fix identified problems and produce the final polished study pack.

## Context passing
Every stage receives the outputs required from previous stages. The workflow state is kept in a dictionary so each stage can be inspected in Streamlit.

## Error handling
- Validate study material before starting.
- Handle missing API keys.
- Handle OpenAI/network failures.
- Handle invalid model JSON.
- Handle PDF extraction failures.
- Preserve successful earlier stages if a later stage fails.
- Provide a deterministic fallback study pack when AI generation cannot run.

## Deployment
- Main entry point: app.py
- AI workflow: ai_workflow.py
- Utilities/file processing: utils.py
- Dependencies: requirements.txt
- Target: Streamlit Community Cloud
- Store OPENAI_API_KEY in Streamlit Secrets; never commit it.
