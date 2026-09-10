import os
import tempfile

import streamlit as st

from ai_workflow import StudyPackWorkflow
from utils import read_uploaded_file, validate_material

st.set_page_config(
page_title="AI Study Pack Generator",
page_icon="📚",
layout="wide",
)

DEFAULT_MODEL = os.getenv(
"GROQ_MODEL",
"openai/gpt-oss-20b",
)

def get_api_key():
try:
key = st.secrets.get("GROQ_API_KEY", "")

```
    if key:
        return str(key).strip()

except Exception:
    pass

return os.getenv(
    "GROQ_API_KEY",
    "",
).strip()
```

def create_pdf_file(content, title):
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
getSampleStyleSheet,
ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
SimpleDocTemplate,
Paragraph,
Spacer,
ListFlowable,
ListItem,
)

```
file = tempfile.NamedTemporaryFile(
    delete=False,
    suffix=".pdf",
)
file.close()

document = SimpleDocTemplate(
    file.name,
    pagesize=A4,
    rightMargin=18 * mm,
    leftMargin=18 * mm,
    topMargin=18 * mm,
    bottomMargin=18 * mm,
    title=title,
)

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "StudyPackTitle",
    parent=styles["Title"],
    fontSize=20,
    leading=24,
    alignment=TA_CENTER,
    spaceAfter=16,
)

heading1_style = ParagraphStyle(
    "StudyPackHeading1",
    parent=styles["Heading1"],
    fontSize=16,
    leading=20,
    spaceBefore=12,
    spaceAfter=8,
)

heading2_style = ParagraphStyle(
    "StudyPackHeading2",
    parent=styles["Heading2"],
    fontSize=13,
    leading=17,
    spaceBefore=10,
    spaceAfter=6,
)

body_style = ParagraphStyle(
    "StudyPackBody",
    parent=styles["BodyText"],
    fontSize=10.5,
    leading=15,
    spaceAfter=6,
)

story = []
bullet_items = []

def flush_bullets():
    nonlocal bullet_items

    if not bullet_items:
        return

    items = [
        ListItem(
            Paragraph(
                item,
                body_style,
            )
        )
        for item in bullet_items
    ]

    story.append(
        ListFlowable(
            items,
            bulletType="bullet",
            leftIndent=15,
        )
    )

    story.append(
        Spacer(1, 6)
    )

    bullet_items = []

for raw_line in content.splitlines():
    line = raw_line.strip()

    if not line:
        flush_bullets()
        story.append(
            Spacer(1, 4)
        )
        continue

    safe_line = (
        line
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    safe_line = safe_line.replace(
        "**",
        "",
    )

    safe_line = safe_line.replace(
        "__",
        "",
    )

    if line.startswith("# "):
        flush_bullets()

        story.append(
            Paragraph(
                safe_line[2:].strip(),
                title_style,
            )
        )

    elif line.startswith("## "):
        flush_bullets()

        story.append(
            Paragraph(
                safe_line[3:].strip(),
                heading1_style,
            )
        )

    elif line.startswith("### "):
        flush_bullets()

        story.append(
            Paragraph(
                safe_line[4:].strip(),
                heading2_style,
            )
        )

    elif line.startswith("- "):
        bullet_items.append(
            safe_line[2:].strip()
        )

    elif line.startswith("* "):
        bullet_items.append(
            safe_line[2:].strip()
        )

    else:
        flush_bullets()

        story.append(
            Paragraph(
                safe_line,
                body_style,
            )
        )

flush_bullets()

document.build(story)

return file.name
```

def create_word_file(content):
from docx import Document
from docx.shared import Pt

```
document = Document()

normal_style = document.styles["Normal"]
normal_style.font.name = "Arial"
normal_style.font.size = Pt(11)

for raw_line in content.splitlines():
    line = raw_line.strip()

    if not line:
        document.add_paragraph("")
        continue

    if line.startswith("# "):
        document.add_heading(
            line[2:].strip(),
            level=1,
        )

    elif line.startswith("## "):
        document.add_heading(
            line[3:].strip(),
            level=2,
        )

    elif line.startswith("### "):
        document.add_heading(
            line[4:].strip(),
            level=3,
        )

    elif line.startswith("- "):
        document.add_paragraph(
            line[2:].strip(),
            style="List Bullet",
        )

    elif line.startswith("* "):
        document.add_paragraph(
            line[2:].strip(),
            style="List Bullet",
        )

    else:
        paragraph = document.add_paragraph()

        parts = line.split("**")

        for index, part in enumerate(parts):
            run = paragraph.add_run(part)

            if index % 2 == 1:
                run.bold = True

file = tempfile.NamedTemporaryFile(
    delete=False,
    suffix=".docx",
)
file.close()

document.save(file.name)

return file.name
```

st.title(
"📚 AI Study Pack Generator"
)

st.caption(
"A multi-stage AI workflow for planning, generating, assessing, "
"reviewing, and refining personalized study material."
)

with st.sidebar:
st.header("⚙️ Study Settings")

```
subject = st.text_input(
    "Subject",
    placeholder="e.g. Machine Learning",
)

level = st.selectbox(
    "Student Level",
    [
        "School",
        "College",
        "University",
        "Professional",
    ],
    index=2,
)

pack_size = st.selectbox(
    "Pack Size",
    [
        "Quick",
        "Standard",
        "Detailed",
    ],
    index=1,
)

model = st.text_input(
    "AI Model",
    value=DEFAULT_MODEL,
    help="Groq model used for generating the study pack.",
)

st.divider()

api_key = get_api_key()

if api_key:
    st.success("Groq API key detected")
    st.caption(f"Model: {model}")
else:
    st.error("Groq API key not detected")
    st.info("Add GROQ_API_KEY in Streamlit Secrets.")

st.divider()

st.markdown(
    """
    **Workflow**

    1. Planning
    2. Content Generation
    3. Assessment
    4. Review
    5. Refinement
    """
)
```

st.subheader("📖 Study Material")

saved_material = st.session_state.get(
"material",
"",
)

material = st.text_area(
"Paste your notes or lecture material",
value=saved_material,
height=300,
placeholder=(
"Paste the material you want to turn into "
"a personalized study pack..."
),
)

uploaded = st.file_uploader(
"Or upload a file",
type=[
"pdf",
"txt",
"md",
"csv",
],
)

if uploaded:
temp_path = None

```
try:
    suffix = os.path.splitext(
        uploaded.name
    )[1]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as temp_file:
        temp_file.write(
            uploaded.getbuffer()
        )
        temp_path = temp_file.name

    uploaded_text = read_uploaded_file(
        temp_path
    )

    if st.button(
        "Use Uploaded Material",
        use_container_width=True,
    ):
        st.session_state["material"] = (
            uploaded_text
        )
        st.rerun()

except Exception as exc:
    st.error(
        f"Could not read the uploaded file: {exc}"
    )

finally:
    if (
        temp_path
        and os.path.exists(temp_path)
    ):
        try:
            os.remove(temp_path)
        except OSError:
            pass
```

st.divider()

generate = st.button(
"Generate Personalized Study Pack",
type="primary",
use_container_width=True,
)

if generate:

```
try:
    validate_material(material)

except ValueError as exc:
    st.error(str(exc))
    st.stop()

api_key = get_api_key()

if not api_key:
    st.error(
        "Groq API key is missing."
    )
    st.info(
        "Add GROQ_API_KEY to Streamlit Secrets "
        "and restart the app."
    )
    st.stop()

try:
    workflow = StudyPackWorkflow(
        api_key=api_key,
        model=model.strip(),
    )

except Exception as exc:
    st.error(
        f"Could not initialize AI workflow: {exc}"
    )
    st.stop()

status = st.empty()
progress_bar = st.progress(0)

def update_progress(index, name):
    progress = min(
        max(
            float(index) / 5.0,
            0.0,
        ),
        1.0,
    )

    progress_bar.progress(progress)

    status.info(
        f"Stage {index}/5 - {name}..."
    )

try:
    with st.spinner(
        "Running AI workflow with Groq..."
    ):
        result = workflow.run(
            subject=subject.strip(),
            level=level,
            material=material,
            pack_size=pack_size,
            progress=update_progress,
        )

except Exception as exc:
    st.error(
        f"Study pack generation failed: {exc}"
    )
    st.stop()

progress_bar.progress(1.0)

status.success(
    "Study pack generation complete!"
)

errors = result.get(
    "errors",
    [],
)

if errors:
    with st.expander(
        "⚠️ Workflow warnings"
    ):
        for item in errors:

            if isinstance(
                item,
                dict,
            ):
                stage = item.get(
                    "stage",
                    "Unknown stage",
                )

                error = item.get(
                    "error",
                    "Unknown error",
                )

                st.warning(
                    f"{stage}: {error}"
                )

            else:
                st.warning(
                    str(item)
                )

tabs = st.tabs(
    [
        "Planning",
        "Content",
        "Assessment",
        "Review",
        "Final Pack",
    ]
)

with tabs[0]:
    planning = result.get(
        "planning"
    )

    if planning:
        st.json(planning)
    else:
        st.info(
            "Planning stage was not available."
        )

with tabs[1]:
    content = result.get(
        "content"
    )

    if content:
        st.json(content)
    else:
        st.info(
            "Content generation stage was not available."
        )

with tabs[2]:
    assessment = result.get(
        "assessment"
    )

    if assessment:
        st.json(assessment)
    else:
        st.info(
            "Assessment stage was not available."
        )

with tabs[3]:
    review = result.get(
        "review"
    )

    if review:

        if isinstance(
            review,
            dict,
        ):
            score = review.get(
                "quality_score"
            )

            if isinstance(
                score,
                (int, float),
            ):
                st.metric(
                    "Quality Score",
                    score,
                )

            st.json(review)

        else:
            st.write(review)

    else:
        st.info(
            "Review stage was not available."
        )

with tabs[4]:

    final_pack = result.get(
        "final_pack",
        "",
    )

    if final_pack:

        st.markdown(
            final_pack
        )

    else:

        st.warning(
            "Final study pack was not generated."
        )


if final_pack:

    st.divider()

    st.subheader(
        "⬇️ Download Study Pack"
    )

    st.write(
        "Download your completed study pack "
        "in Markdown, PDF, or Word format."
    )

    safe_subject = (
        subject.strip()
        .replace("/", "-")
        .replace("\\", "-")
        .replace(":", "-")
        .replace("*", "-")
        .replace("?", "")
        .replace('"', "")
        .replace("<", "-")
        .replace(">", "-")
        .replace("|", "-")
    )

    if not safe_subject:
        safe_subject = "AI_Study_Pack"

    markdown_data = final_pack.encode(
        "utf-8"
    )

    pdf_data = None

    try:

        pdf_path = create_pdf_file(
            final_pack,
            subject.strip()
            or "AI Study Pack",
        )

        with open(
            pdf_path,
            "rb",
        ) as pdf_file:
            pdf_data = pdf_file.read()

        try:
            os.remove(pdf_path)
        except OSError:
            pass

    except Exception as exc:

        st.warning(
            f"PDF generation failed: {exc}"
        )

    word_data = None

    try:

        word_path = create_word_file(
            final_pack
        )

        with open(
            word_path,
            "rb",
        ) as word_file:
            word_data = word_file.read()

        try:
            os.remove(word_path)
        except OSError:
            pass

    except Exception as exc:

        st.warning(
            f"Word document generation failed: {exc}"
        )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.download_button(
            label="⬇️ Download Markdown",
            data=markdown_data,
            file_name=f"{safe_subject}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col2:

        if pdf_data:

            st.download_button(
                label="📄 Download PDF",
                data=pdf_data,
                file_name=f"{safe_subject}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        else:

            st.button(
                "📄 PDF unavailable",
                disabled=True,
                use_container_width=True,
            )

    with col3:

        if word_data:

            st.download_button(
                label="📝 Download Word",
                data=word_data,
                file_name=f"{safe_subject}.docx",
                mime=(
                    "application/vnd.openxmlformats-"
                    "officedocument.wordprocessingml.document"
                ),
                use_container_width=True,
            )

        else:

            st.button(
                "📝 Word unavailable",
                disabled=True,
                use_container_width=True,
            )

    st.success(
        "Your study pack is ready to download "
        "in Markdown, PDF, and Word formats."
    )

else:

st.info(
    "Enter study material, choose your settings, and click "
    "Generate Personalized Study Pack to start the "
    "five-stage AI workflow."
)

st.divider()

st.caption(
"AI Study Pack Generator | Streamlit | Groq | "
"Multi-stage AI Workflow"
)
