import os
import streamlit as st

from ai_workflow import StudyPackWorkflow
from utils import read_uploaded_file, validate_material

st.set_page_config(
    page_title="AI Study Pack Generator",
    page_icon="📚",
    layout="wide",
)

st.title("📚 AI Study Pack Generator")
st.caption("A multi-stage AI workflow for planning, generating, assessing, reviewing, and refining personalized study material.")

with st.sidebar:
    st.header("⚙️ Study Settings")

    subject = st.text_input(
        "Subject",
        placeholder="e.g. Machine Learning",
    )

    level = st.selectbox(
        "Student Level",
        ["School", "College", "University", "Professional"],
        index=2,
    )

    pack_size = st.selectbox(
        "Pack Size",
        ["Quick", "Standard", "Detailed"],
        index=1,
    )

    model = st.text_input(
        "AI Model",
        value=os.getenv("OPENAI_MODEL", "gpt-5"),
    )

    st.divider()
    st.markdown(
        "**Workflow:** Planning → Content → Assessment → Review → Refinement"
    )

st.subheader("📖 Study Material")

material = st.text_area(
    "Paste your notes or lecture material",
    height=300,
    placeholder="Paste the material you want to turn into a study pack...",
)

uploaded = st.file_uploader(
    "Or upload a file",
    type=["pdf", "txt", "md", "csv"],
)

if uploaded:
    temp_path = os.path.join("/tmp", uploaded.name)
    with open(temp_path, "wb") as f:
        f.write(uploaded.getbuffer())

    try:
        uploaded_text = read_uploaded_file(temp_path)
        if st.button("📥 Use Uploaded Material"):
            material = uploaded_text
            st.session_state["material"] = uploaded_text
            st.rerun()
    except Exception as exc:
        st.error(f"Could not read the uploaded file: {exc}")

if "material" in st.session_state and not material:
    material = st.session_state["material"]

st.divider()

generate = st.button(
    "✨ Generate Personalized Study Pack",
    type="primary",
    use_container_width=True,
)

if generate:
    try:
        validate_material(material)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    # Streamlit Cloud secrets take priority over environment variables.
    api_key = ""
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        api_key = ""

    api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    workflow = StudyPackWorkflow(
        api_key=api_key,
        model=model,
    )

    status = st.empty()
    progress_bar = st.progress(0)

    stage_names = [
        "Planning",
        "Content Generation",
        "Assessment",
        "Review",
        "Refinement",
    ]

    def update_progress(index, name):
        progress_bar.progress(index / 5)
        status.info(f"⏳ Stage {index}/5 — {name}...")

    with st.spinner("Running AI workflow..."):
        result = workflow.run(
            subject=subject,
            level=level,
            material=material,
            pack_size=pack_size,
            progress=update_progress,
        )

    progress_bar.progress(1.0)
    status.success("🎉 Study pack generation complete!")

    if result["errors"]:
        with st.expander("⚠️ Workflow warnings"):
            for item in result["errors"]:
                st.warning(f'{item["stage"]}: {item["error"]}')

    tabs = st.tabs(
        ["📋 Planning", "📚 Content", "📝 Assessment", "🔍 Review", "✨ Final Pack"]
    )

    import json

    with tabs[0]:
        st.json(result["planning"] or {"status": "Not available; fallback used."})

    with tabs[1]:
        st.json(result["content"] or {"status": "Not available; fallback used."})

    with tabs[2]:
        st.json(result["assessment"] or {"status": "Not available; fallback used."})

    with tabs[3]:
        review = result["review"]
        if review:
            score = review.get("quality_score")
            if isinstance(score, (int, float)):
                st.metric("Quality Score", score)
            st.json(review)
        else:
            st.info("Review stage was not available.")

    with tabs[4]:
        st.markdown(result["final_pack"])

        st.download_button(
            "📥 Download Study Pack",
            data=result["final_pack"],
            file_name="ai_study_pack.md",
            mime="text/markdown",
            use_container_width=True,
        )
else:
    st.info(
        "Enter study material, choose your settings, and click "
        "**Generate Personalized Study Pack** to start the five-stage AI workflow."
    )

st.divider()
st.caption("AI Study Pack Generator • Streamlit • Multi-stage AI Workflow")
