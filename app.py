import os
import tempfile

import streamlit as st

from ai_workflow import StudyPackWorkflow
from utils import read_uploaded_file, validate_material


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Study Pack Generator",
    page_icon="📚",
    layout="wide",
)


# ============================================================
# GROQ CONFIGURATION
# ============================================================

DEFAULT_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
)


def get_api_key():
    """Get the Groq API key from Streamlit Secrets or environment."""

    try:
        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return str(key).strip()
    except Exception:
        pass

    return os.getenv("GROQ_API_KEY", "").strip()


# ============================================================
# HEADER
# ============================================================

st.title("📚 AI Study Pack Generator")

st.caption(
    "A multi-stage AI workflow for planning, generating, assessing, "
    "reviewing, and refining personalized study material."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Study Settings")

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


# ============================================================
# STUDY MATERIAL
# ============================================================

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


# ============================================================
# FILE UPLOAD
# ============================================================

uploaded = st.file_uploader(
    "Or upload a file",
    type=["pdf", "txt", "md", "csv"],
)

if uploaded:
    temp_path = None

    try:
        suffix = os.path.splitext(uploaded.name)[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:
            temp_file.write(uploaded.getbuffer())
            temp_path = temp_file.name

        uploaded_text = read_uploaded_file(temp_path)

        if st.button(
            "Use Uploaded Material",
            use_container_width=True,
        ):
            st.session_state["material"] = uploaded_text
            st.rerun()

    except Exception as exc:
        st.error(
            f"Could not read the uploaded file: {exc}"
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


# ============================================================
# GENERATE BUTTON
# ============================================================

st.divider()

generate = st.button(
    "Generate Personalized Study Pack",
    type="primary",
    use_container_width=True,
)


# ============================================================
# GENERATE STUDY PACK
# ============================================================

if generate:

    try:
        validate_material(material)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    api_key = get_api_key()

    if not api_key:
        st.error("Groq API key is missing.")
        st.info(
            "Add GROQ_API_KEY to Streamlit Secrets "
            "and restart the app."
        )
        st.stop()

    try:
        workflow = StudyPackWorkflow(
            api_key=api_key,
            model=model,
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
            max(float(index) / 5.0, 0.0),
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
                subject=subject,
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

    errors = result.get("errors", [])

    if errors:
        with st.expander("Workflow warnings"):
            for item in errors:
                if isinstance(item, dict):
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
                    st.warning(str(item))

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
        planning = result.get("planning")
        if planning:
            st.json(planning)
        else:
            st.info("Planning stage was not available.")

    with tabs[1]:
        content = result.get("content")
        if content:
            st.json(content)
        else:
            st.info(
                "Content generation stage was not available."
            )

    with tabs[2]:
        assessment = result.get("assessment")
        if assessment:
            st.json(assessment)
        else:
            st.info(
                "Assessment stage was not available."
            )

    with tabs[3]:
        review = result.get("review")

        if review:
            if isinstance(review, dict):
                score = review.get("quality_score")

                if isinstance(score, (int, float)):
                    st.metric(
                        "Quality Score",
                        score,
                    )

                st.json(review)
            else:
                st.write(review)
        else:
            st.info("Review stage was not available.")

    with tabs[4]:
        final_pack = result.get(
            "final_pack",
            "",
        )

        if final_pack:
            st.markdown(final_pack)

            st.download_button(
                label="Download Study Pack",
                data=final_pack,
                file_name="ai_study_pack.md",
                mime="text/markdown",
                use_container_width=True,
            )
        else:
            st.warning(
                "Final study pack was not generated."
            )


# ============================================================
# INITIAL STATE
# ============================================================

else:
    st.info(
        "Enter study material, choose your settings, and click "
        "Generate Personalized Study Pack to start the "
        "five-stage AI workflow."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AI Study Pack Generator | Streamlit | Groq | "
    "Multi-stage AI Workflow"
)
