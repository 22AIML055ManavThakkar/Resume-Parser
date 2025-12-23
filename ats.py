import re

ACTION = {
    "achieved","built","created","designed","developed","engineered","improved",
    "implemented","led","managed","optimized","reduced","increased","deployed",
    "automated","trained","analyzed","spearheaded","orchestrated","delivered","launched"
}

WEAK = {
    "worked on","responsible for","helped with","assisted","involved in",
    "duties included","tasked with","worked as","participated in"
}

PASSIVE = re.compile(r'\b(am|is|are|was|were|be|been|being)\b\s+\b[\w-]+\b', re.I)
SECTIONS = ["experience","education","projects","skills","certifications","summary","profile"]

def top_fraction(t, f=0.3):
    w = t.split()
    return " ".join(w[:int(len(w) * f)])

def keyword_density(resume, jd):
    resume = resume.lower()
    jd = set([s.lower() for s in jd])

    top = top_fraction(resume, 0.3)
    matched_top = sorted([k for k in jd if k in top])
    matched_any = sorted([k for k in jd if k in resume])
    missing = sorted(list(jd - set(matched_any)))

    return {
        "top_matched": matched_top,
        "all_matched": matched_any,
        "missing": missing,
        "top_coverage": len(matched_top) / len(jd) if jd else 0,
        "overall_coverage": len(matched_any) / len(jd) if jd else 0
    }

def section_presence(text):
    t = text.lower()
    present = [h for h in SECTIONS if h in t]
    missing = [h for h in SECTIONS if h not in t]
    return {"present": present, "missing": missing, "score": len(present)/len(SECTIONS)}

def action_vs_passive(text):
    words = re.findall(r'\b[a-zA-Z-]+\b', text.lower())
    wc = len(words)

    action_count = sum(1 for w in words if w in ACTION)
    passive_count = len(PASSIVE.findall(text))

    return {
        "action_verbs": action_count,
        "passive_phrases": passive_count,
        "action_rate": action_count / wc if wc else 0
    }

def compute_ats_score(text, jd_skills, resume_skills):
    kd = keyword_density(text, jd_skills or [])
    sp = section_presence(text)
    av = action_vs_passive(text)

    score = (
        0.5 * ((0.7 * kd["top_coverage"]) + (0.3 * kd["overall_coverage"])) +
        0.2 * sp["score"] +
        0.15 * min(1, av["action_rate"] * 50) +
        0.1 * 1 + 
        0.05 * sp["score"]
    )

    return {
        "score": round(score * 100, 2),
        "details": {"keyword_density": kd, "sections": sp, "action_passive": av},
        "suggestions": []
    }
