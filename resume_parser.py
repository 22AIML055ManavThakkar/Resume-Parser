# src/resume_parser.py (FINAL — aggressive cleaning + robust summary/education)
import pdfplumber
import re

# Try to import skills db; fallback to empty list
try:
    from src.skills_db import ALL_SKILLS
except Exception:
    ALL_SKILLS = []

# ---- regex helpers ----
_email_re = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
_phone_re = re.compile(r'(\+?\d{1,3}[-\s]?)?(\d{10}|\d{5}[-\s]\d{5}|\d{3}[-\s]\d{3}[-\s]\d{4})')
_cid_re = re.compile(r'\(cid:\d+\)')
_weird_chars_re = re.compile(r'[\uf000-\uffff]')
_url_re = re.compile(r'https?://\S+|www\.\S+')
_social_token_re = re.compile(r'\b(linkedin|hackerrank|github|portfolio|behance|dribbble)\b', re.IGNORECASE)

_SECTION_HEADERS = [
    "summary", "profile", "professional summary", "objective",
    "education", "experience", "projects", "skills",
    "certifications", "work experience", "achievements", "projects", "education:"
]

_LOCATION_TOKENS = {
    "india","gujarat","ahmedabad","mumbai","delhi","bangalore","bengaluru","pune","chennai","hyderabad",
    "rajkot","surat","vadodara","karnataka","maharashtra","united states","usa","uk","united kingdom"
}

# Tech keywords used for detecting parenthetical tech fragments or project titles
_TECH_KEYWORDS = [
    "gan","flask","tensorflow","pytorch","llm","web scraping","scrapy","docker",
    "aws","azure","gcp","image","resolution","nlp","deep learning","computer vision",
    "opencv","streamlit","scikit","keras","dl","api","r","sql","react","node","mongodb","fastapi"
]

# build regexes for parentheses removal
_TECH_PAREN_RE = re.compile(r'\([^)]*(?:' + r'|'.join(re.escape(tok) for tok in _TECH_KEYWORDS) + r')[^)]*\)', re.I)
_PAREN_ACRONYM_RE = re.compile(r'\(\s*[A-Z]{1,6}(?:\s*,\s*[A-Z]{1,6})*\s*\)')  # (GAN), (GAN, FLASK)

# ---- pdf extraction ----
def extract_text_from_pdf(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                text += t + "\n"
    except Exception:
        try:
            file.seek(0)
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    t = page.extract_text() or ""
                    text += t + "\n"
        except Exception:
            return ""
    return text

# ---- cleaning preserving newlines ----
def clean_text(text):
    if not text:
        return ""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = _cid_re.sub(" ", text)
    text = _url_re.sub(" ", text)
    text = _social_token_re.sub(" ", text)
    text = _weird_chars_re.sub(" ", text)
    text = re.sub(r'[^\x00-\x7F]+', " ", text)
    lines = []
    for raw_line in text.split("\n"):
        line = raw_line.replace('\t', ' ').replace('•', ' ').replace('–', '-')
        line = re.sub(r'\s+', ' ', line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)

# ---- skills extraction ----
def extract_skills_from_text(text, skills_list=None):
    if skills_list is None:
        skills_list = ALL_SKILLS or []
    t = (text or "").lower()
    found = set()
    for sk in skills_list:
        if sk.lower() in t:
            found.add(sk.lower())
    return sorted(found)

# ---- small helpers ----
def _is_name_line(line):
    if not line:
        return False
    if len(line) > 100:
        return False
    if _email_re.search(line) or _phone_re.search(line) or _url_re.search(line):
        return False
    alpha = sum(1 for c in line if c.isalpha())
    if alpha < 3:
        return False
    low = line.lower()
    if any(k in low for k in ("summary","experience","education","skills","projects","address","profile")):
        return False
    return True

def _clean_name_candidate(raw):
    if not raw:
        return None
    s = raw
    s = _email_re.sub(" ", s)
    s = _phone_re.sub(" ", s)
    s = _url_re.sub(" ", s)
    s = _social_token_re.sub(" ", s)
    s = re.split(r'\||,|-|•', s)[0].strip()
    tokens = [t.strip() for t in re.split(r'\s+', s) if t.strip()]
    while tokens and tokens[-1].lower() in _LOCATION_TOKENS:
        tokens.pop()
    name = " ".join(tokens[:4])
    name = re.sub(r'[^A-Za-z\s]', '', name).strip()
    return name or None

def _is_section_header(line):
    if not line:
        return False
    low = line.lower().strip().rstrip(':')
    if low in _SECTION_HEADERS:
        return True
    for h in _SECTION_HEADERS:
        if low.startswith(h + " ") or low.startswith(h + ":"):
            return True
    if line.strip().isupper() and len(line.strip()) < 40:
        return True
    return False

def _remove_tech_parentheses(s):
    """Remove parentheses that are likely tech stacks or short acronyms."""
    if not s:
        return s
    s = _TECH_PAREN_RE.sub(" ", s)
    s = _PAREN_ACRONYM_RE.sub(" ", s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def _looks_like_project_title(l):
    """Heuristic: short line (<12 words) containing many tech keywords => project title."""
    low = l.lower()
    tech_matches = sum(1 for tok in _TECH_KEYWORDS if tok in low)
    if tech_matches >= 2 and len(low.split()) <= 12:
        return True
    # if line contains '(' and many commas with tech tokens -> project
    if "(" in l and any(tok in low for tok in _TECH_KEYWORDS):
        return True
    return False

# ---- summary generator (improved) ----
def _generate_summary_from_resume(text, detected_skills, max_sentences=3):
    if not text:
        return "_No clear summary found._"
    # first aggressively strip tech parentheses for sentence-level processing
    cleaned_text = _remove_tech_parentheses(text)
    sents = re.split(r'(?<=[.!?])\s+', cleaned_text)
    sents = [s.strip() for s in sents if len(s.strip()) > 15]
    personal_tokens = ["student","passionate","dedicated","enthusiast","seeking","intern","professional","graduate","undergraduate","research","aspiring"]
    action_verbs = ["developed","implemented","designed","built","trained","optimized","deployed","created","engineered","improved","led","analyzed","automated"]
    chosen = []
    for s in sents:
        low = s.lower()
        if _looks_like_project_title(s):
            continue
        if any(tok in low for tok in personal_tokens) and len(chosen) < max_sentences:
            chosen.append(re.sub(r'\s+', ' ', s))
        elif any(v in low for v in action_verbs) and len(chosen) < max_sentences:
            chosen.append(re.sub(r'\s+', ' ', s))
        if len(chosen) >= max_sentences:
            break
    if chosen:
        return " ".join(chosen[:max_sentences])[:900]
    # fallback: construct from top skills
    skills = detected_skills or []
    top = ", ".join(skills[:4]) if skills else ""
    if top:
        s = f"Skilled in {top}. Experienced in building machine learning models and data-driven solutions."
    else:
        s = "Passionate Machine Learning practitioner with experience in applied ML and data-driven solutions."
    return " ".join(re.split(r'(?<=[.!?])\s+', s)[:max_sentences])

# ---- stricter education extraction ----
def _extract_education_from_lines(lines):
    if not lines:
        return []
    edu = []
    edu_keys = ["b.tech","bachelor","master","university","college","cgpa","hsc","ssc","diploma","degree","graduation","expected"]
    for i, l in enumerate(lines):
        low = l.lower()
        # remove tech parens first
        line_clean = _remove_tech_parentheses(l)
        lowc = line_clean.lower()
        # skip if looks like project title
        if _looks_like_project_title(l):
            continue
        # accept if contains education markers, year, cgpa, percentage
        if any(k in lowc for k in edu_keys) or re.search(r'\b(19|20)\d{2}\b', line_clean) or re.search(r'\b\d{1,3}%|\bpercent\b|\bpercentile\b', lowc) or re.search(r'\bcgpa\b', lowc):
            # combine with next line if next line is a year or CGPA
            entry = line_clean.strip()
            if i + 1 < len(lines):
                nxt = lines[i+1].strip()
                if re.match(r'^\(?\d{4}[-–]\d{4}\)?$', nxt) or re.search(r'\b(19|20)\d{2}\b', nxt):
                    entry = entry + " " + nxt
            edu.append(entry)
    # fallback: pick short lines that look like institution names (contain 'university' or are Title Case)
    if not edu:
        for l in lines[:8]:
            if _is_section_header(l):
                continue
            if "university" in l.lower() or "institute" in l.lower() or (len(l.split()) < 8 and sum(1 for c in l if c.isupper()) >= 2):
                edu.append(_remove_tech_parentheses(l).strip())
            if len(edu) >= 3:
                break
    return list(dict.fromkeys(edu))[:5]

# ---- main parse + overview ----
def parse_resume(file, skills_list=None):
    raw = extract_text_from_pdf(file)
    cleaned = clean_text(raw)
    skills = extract_skills_from_text(cleaned, skills_list)
    return {"raw_text": cleaned, "skills": skills}

def generate_overview(resume_text, detected_skills, max_skill_show=10):
    text = (resume_text or "").strip()
    if not text:
        return "_No resume text available._"
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    # NAME
    name = None
    for l in lines[:10]:
        if _is_name_line(l):
            nc = _clean_name_candidate(l)
            if nc:
                name = nc
                break
    if not name and lines:
        name = _clean_name_candidate(lines[0]) or "Not found"

    # CONTACT
    email_m = _email_re.search(text)
    phone_m = _phone_re.search(text)
    email = email_m.group(0) if email_m else "Not found"
    phone = phone_m.group(0) if phone_m else "Not found"

    # SUMMARY: try inline label, block under header (filter project-like), fallback to generated
    summary = None
    # inline labelled
    for l in lines[:20]:
        m = re.match(r'^(profile summary|profile|summary|professional summary|objective)[:\-\s]+(.+)$', l, flags=re.I)
        if m:
            cand = _remove_tech_parentheses(m.group(2).strip())
            if cand and len(cand) > 15 and not _looks_like_project_title(cand):
                summary = cand
                break
    # block header
    if not summary:
        for idx, l in enumerate(lines):
            low = l.lower().strip()
            if low in ("profile summary","profile","summary","professional summary","objective") or low.startswith(("profile summary:","profile:","summary:","professional summary:","objective:")):
                collected = []
                for nl in lines[idx+1: idx+8]:
                    if not nl:
                        continue
                    if _email_re.search(nl) or _phone_re.search(nl) or _url_re.search(nl):
                        continue
                    if _is_section_header(nl) and len(collected) > 0:
                        break
                    cleaned_nl = _remove_tech_parentheses(nl)
                    if _looks_like_project_title(cleaned_nl) and len(cleaned_nl.split()) <= 12:
                        # skip project-like short lines
                        continue
                    collected.append(cleaned_nl)
                if collected:
                    # prefer first 1-3 collected that look like profile sentences
                    candidate_sentences = []
                    for c in collected:
                        if len(c) > 40 and not _looks_like_project_title(c):
                            candidate_sentences.append(c)
                        if len(candidate_sentences) >= 3:
                            break
                    if candidate_sentences:
                        summary = " ".join(candidate_sentences)[:900]
                    else:
                        # fallback to joining collected
                        summary = " ".join(collected)[:900]
                break

    # fallback: first long non-contact, non-project line
    if not summary:
        for l in lines[:12]:
            if l != name and not _email_re.search(l) and not _phone_re.search(l):
                cand = _remove_tech_parentheses(l)
                if not _looks_like_project_title(cand):
                    if len(cand) > 40:
                        summary = cand
                        break

    # final fallback: auto-generate
    if not summary or summary.strip() == "":
        summary = _generate_summary_from_resume(text, detected_skills, max_sentences=3)

    # EDUCATION: prefer block under Education header, else scan lines
    edu = []
    edu_idx = None
    for i, l in enumerate(lines):
        if re.search(r'\beducation\b', l, flags=re.I):
            edu_idx = i
            break
    if edu_idx is not None:
        block = []
        for nl in lines[edu_idx+1: edu_idx+16]:
            if _is_section_header(nl) and len(block) > 0:
                break
            block.append(nl)
        edu = _extract_education_from_lines(block)
    else:
        edu = _extract_education_from_lines(lines)
    if not edu:
        edu = ["No education details detected."]

    # skills
    top_skills = detected_skills[:max_skill_show] if detected_skills else ["No skills detected"]

    # build md
    md = []
    md.append("### 📄 Resume Overview")
    md.append("")
    md.append("#### 👤 Name")
    md.append(name or "Not found")
    md.append("")
    md.append("#### 📬 Contact")
    md.append(f"- Email: {email}")
    md.append(f"- Phone: {phone}")
    md.append("")
    md.append("---")
    md.append("")
    md.append("#### 📝 Professional Summary")
    md.append(summary)
    md.append("")
    md.append("---")
    md.append("")
    md.append("#### 🎯 Top Skills")
    md.append(", ".join(top_skills))
    md.append("")
    md.append("---")
    md.append("")
    md.append("#### 🎓 Education")
    for e in edu:
        md.append(f"- {e}")
    md.append("")
    md.append("---")
    md.append("_Generated clean overview._")
    return "\n\n".join(md)

# ---- debug helper ----
def debug_parse_file(path_or_file):
    """
    Print raw -> cleaned -> line-by-line view, found summary and education (useful to paste here).
    """
    if isinstance(path_or_file, str):
        with open(path_or_file, "rb") as f:
            raw = extract_text_from_pdf(f)
    else:
        raw = extract_text_from_pdf(path_or_file)
    cleaned = clean_text(raw)
    skills = extract_skills_from_text(cleaned)
    print("----- RAW (first 900 chars) -----")
    print(raw[:900])
    print("\n----- CLEANED (first 900 chars) -----")
    print(cleaned[:900])
    print("\n----- LINES (first 40 lines) -----")
    lines = [ln for ln in cleaned.split("\n")]
    for i, ln in enumerate(lines[:40]):
        print(f"{i:02d}: {ln}")
    print("\n----- SKILLS DETECTED -----")
    print(skills[:80])
    print("\n----- GENERATED OVERVIEW -----")
    print(generate_overview(cleaned, skills))
