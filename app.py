import streamlit as st
from src.resume_parser import parse_resume, generate_overview
from src.jd_parser import parse_jd
from src.embedder import TextEmbedder
from src.matcher import compute_skill_coverage, compute_overall_score
from src.ats import compute_ats_score

st.set_page_config(page_title="Smart Resume Analyzer", layout="wide", initial_sidebar_state="expanded")

# simple CSS
st.markdown(
    '''
    <style>
    .title {font-size:34px; font-weight:700; margin-bottom:6px;}
    .big-score {font-size:40px; font-weight:800; color:#0f5132;}
    </style>
    ''',
    unsafe_allow_html=True
)

st.markdown('<div class="title">🧠 Smart Resume Analyzer — Final (Polished)</div>', unsafe_allow_html=True)
st.write("Upload a resume (PDF) and paste the job description. The app computes semantic match, ATS compatibility, and gives clean suggestions.")

embedder = TextEmbedder()

# Sidebar: instructions only
with st.sidebar:
    st.header("Quick Tips")
    st.write("- Place key skills and summary near the top of your resume.")
    st.write("- Use clear section headers: Experience, Projects, Education, Skills.")
    st.markdown("---")
    st.write("Upload resume -> paste JD -> Analyze.")

# Layout: single left column for inputs (full width), results below across the page
uploaded = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
jd_text = st.text_area("Paste Job Description here", height=320)
analyze = st.button("Analyze Match", type="primary")

if analyze:
    if uploaded is None or not jd_text.strip():
        st.error("Please upload a resume and paste a job description.")
    else:
        with st.spinner("Running analysis..."):
            resume = parse_resume(uploaded)
            jd = parse_jd(jd_text)
            semantic_sim = embedder.similarity(resume['raw_text'], jd['raw_text'])
            skill_cov, matched_skills, missing_skills = compute_skill_coverage(resume['skills'], jd['required_skills'])
            overall_match = compute_overall_score(semantic_sim, skill_cov)
            ats = compute_ats_score(resume['raw_text'], jd['required_skills'], resume['skills'])
            overview_md = generate_overview(resume['raw_text'], resume['skills'])

        # derive components safely
        comps = ats.get('components') or {}
        # fallback: try to compute from details if components missing
        details = ats.get('details', {})

        def safe_percent(x):
            try:
                return round(float(x), 2)
            except Exception:
                return 0.0

        kw_percent = comps.get('keyword_score_percent') or comps.get('keyword') or safe_percent(details.get('keyword_density', {}).get('overall_coverage', 0.0) * 100)
        section_percent = comps.get('section_score_percent') or comps.get('sections') or safe_percent(details.get('sections', {}).get('score', 0.0) * 100)
        action_percent = comps.get('action_component_percent') or comps.get('action') or safe_percent(details.get('action_passive', {}).get('action_rate', 0.0) * 100)
        length_percent = comps.get('length_component_percent') or comps.get('length') or safe_percent((details.get('length', {}).get('value', 0.0) * 100) if isinstance(details.get('length', {}), dict) else 0.0)

        # Header metrics (three columns)
        h1, h2, h3 = st.columns([1, 1, 1])

        with h1:
            st.markdown("**🎯 Overall Match**")
            st.markdown(f"<div class='big-score'>{overall_match} / 100</div>", unsafe_allow_html=True)
            st.write(f"Semantic similarity: **{semantic_sim:.2f}**")
            st.write(f"Skill coverage: **{skill_cov*100:.1f}%**")
            st.progress(int(overall_match))

        with h2:
            st.markdown("**📑 ATS Compatibility**")
            st.markdown(f"<div class='big-score'>{safe_percent(ats.get('score', 0))} / 100</div>", unsafe_allow_html=True)
            st.write(f"Keywords: **{safe_percent(kw_percent)}%**")
            st.write(f"Sections: **{safe_percent(section_percent)}%**")
            st.write(f"Action/Passive: **{safe_percent(action_percent)}%**")
            st.write(f"Length: **{safe_percent(length_percent)}%**")
            st.progress(int(safe_percent(ats.get('score', 0))))

        with h3:
            st.markdown("**🔧 Quick Suggestions**")
            suggestions = ats.get('suggestions') or []
            if suggestions:
                for s in suggestions[:4]:
                    st.info(s)
            else:
                st.success("No quick suggestions — looks good!")

        st.markdown("---")

        # Main content: left (overview + skills) and right (ATS details)
        left, right = st.columns([2, 1])
        with left:
            st.markdown("### 📄 Resume Overview")
            st.markdown(overview_md, unsafe_allow_html=True)

            st.markdown("### ✅ Matched Skills")
            st.write(", ".join(matched_skills) if matched_skills else "_No matched skills detected._")

            st.markdown("### ❌ Missing Skills")
            st.write(", ".join(missing_skills) if missing_skills else "_No missing skills detected._")

        with right:
            st.markdown("### ATS Details")
            top_matched = details.get('keyword_density', {}).get('top_matched') or []
            all_matched = details.get('keyword_density', {}).get('all_matched') or []
            sections_present = details.get('sections', {}).get('present') or []
            ap = details.get('action_passive') or {"action_verbs": 0, "passive_phrases": 0}
            st.write("**Top Keyword Matches (top section):**")
            st.write(", ".join(top_matched) or "_None_")
            st.write("**All matched keywords:**")
            st.write(", ".join(all_matched) or "_None_")
            st.markdown("**Sections present:**")
            st.write(", ".join(sections_present) or "_None_")
            st.markdown("**Action verbs vs passive phrases**")
            st.write(f"Action verbs found: {ap.get('action_verbs', 0)}")
            st.write(f"Passive-like phrases: {ap.get('passive_phrases', 0)}")

        st.markdown("---")
        st.markdown("#### Full ATS Suggestions")
        for s in suggestions:
            st.write("- " + s)

else:
    st.write("Upload a resume and paste a job description, then click 'Analyze Match'.")
