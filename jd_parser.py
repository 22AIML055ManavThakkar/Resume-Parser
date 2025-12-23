import re
from src.skills_db import ALL_SKILLS

def clean_text(t):
    t = t.replace("\t", " ")
    return re.sub(r"\s+", " ", t).strip()

def extract_skills_from_jd(t):
    t = t.lower()
    return sorted({s for s in ALL_SKILLS if s in t})

def parse_jd(t):
    c = clean_text(t)
    return {"raw_text": c, "required_skills": extract_skills_from_jd(c)}
