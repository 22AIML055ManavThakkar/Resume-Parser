
def compute_skill_coverage(resume_skills, jd_skills):
    r=set([s.lower() for s in (resume_skills or [])])
    j=set([s.lower() for s in (jd_skills or [])])
    matched=sorted(list(r&j))
    missing=sorted(list(j-r))
    cov=len(matched)/len(j) if j else 0
    return cov, matched, missing

def compute_overall_score(sem, cov, w1=0.6, w2=0.4):
    return round((w1*sem + w2*cov)*100,2)
