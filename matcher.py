"""Lightweight matcher — keyword Jaccard + cosine similarity over term vectors."""
import re
import math
from collections import Counter
from typing import Dict, List


def _tokenize(text: str) -> List[str]:
    text = re.sub(r'[^a-z0-9\s]', ' ', text.lower())
    tokens = [t for t in text.split() if len(t) > 1]
    return tokens


def _build_vocab(*texts: str) -> Dict[str, int]:
    vocab = {}
    for text in texts:
        for tok in set(_tokenize(text)):
            if tok not in vocab:
                vocab[tok] = len(vocab)
    return vocab


def _vectorize(text: str, vocab: Dict[str, int]) -> List[float]:
    vec = [0.0] * len(vocab)
    counts = Counter(_tokenize(text))
    for token, count in counts.items():
        if token in vocab:
            vec[vocab[token]] = count
    return vec


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _jaccard_similarity(skills_a: Counter, skills_b: Counter) -> float:
    if not skills_a or not skills_b:
        return 0.0
    set_a = set(skills_a.keys())
    set_b = set(skills_b.keys())
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union else 0.0


def score_job(resume_parse: dict, job_text: str) -> dict:
    """Score a job against parsed resume. Returns dict with metrics."""
    job_text_clean = re.sub(r'[^a-z0-9\s]', ' ', job_text.lower())

    # Extract skills from job text using same keyword list + word boundaries
    job_skills = Counter()
    from resume_parser import SKILL_KEYWORDS
    for skill in SKILL_KEYWORDS:
        if ' ' in skill:
            count = job_text_clean.count(skill)
        else:
            pattern = r'\b' + re.escape(skill) + r'\b'
            count = len(re.findall(pattern, job_text_clean))
        if count:
            job_skills[skill] = count

    # Jaccard on skills
    skill_jaccard = _jaccard_similarity(resume_parse['skills'], job_skills)

    # Cosine on full text vectors
    vocab = _build_vocab(resume_parse['cleaned_text'], job_text_clean)
    resume_vec = _vectorize(resume_parse['cleaned_text'], vocab)
    job_vec = _vectorize(job_text_clean, vocab)
    text_cosine = _cosine_similarity(resume_vec, job_vec)

    # Weighted composite score
    score = 0.6 * skill_jaccard + 0.4 * text_cosine

    return {
        'score': round(score, 4),
        'skill_jaccard': round(skill_jaccard, 4),
        'text_cosine': round(text_cosine, 4),
        'matched_skills': list(set(resume_parse['skills'].keys()) & set(job_skills.keys())),
    }


if __name__ == '__main__':
    from resume_parser import parse_resume
    import sys
    if len(sys.argv) < 3:
        print("Usage: python matcher.py <resume.pdf> <'job description text'>")
        sys.exit(1)
    resume_data = parse_resume(sys.argv[1])
    result = score_job(resume_data, sys.argv[2])
    print(f"Score: {result['score']}")
    print(f"  Skill Jaccard: {result['skill_jaccard']}")
    print(f"  Text Cosine: {result['text_cosine']}")
    print(f"  Matched skills: {', '.join(result['matched_skills'])}")
