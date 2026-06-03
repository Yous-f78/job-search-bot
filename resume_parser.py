"""Resume parser — extracts text + skills from PDF and DOCX files."""
import re
from pathlib import Path
from collections import Counter

SKILL_KEYWORDS = {
    # Programming
    'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'go', 'rust', 'ruby',
    'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'bash', 'powershell',
    # Web
    'react', 'vue', 'angular', 'svelte', 'next.js', 'nuxt', 'django', 'flask',
    'fastapi', 'express', 'nodejs', 'html', 'css', 'sass', 'tailwind',
    # Data / ML
    'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras',
    'jupyter', 'matplotlib', 'seaborn', 'spark', 'hadoop', 'kafka',
    # DevOps / Cloud
    'docker', 'kubernetes', 'aws', 'gcp', 'azure', 'terraform', 'ansible',
    'jenkins', 'github actions', 'gitlab ci', 'ci/cd',
    # Databases
    'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'sqlite',
    'dynamodb', 'firebase', 'cassandra',
    # Mobile
    'flutter', 'react native', 'android', 'ios', 'xamarin',
    # Virtualization / 3D
    'virtualbox', 'vmware', 'openscad', 'tinkercad', 'cura', 'blender',
    # Other
    'git', 'linux', 'agile', 'scrum', 'rest api', 'graphql', 'microservices',
    'blockchain', 'solidity', 'machine learning', 'deep learning', 'nlp',
    'computer vision', 'data engineering', 'data science', 'ai',
}


def _clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9+/#\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _extract_skills(text: str) -> Counter:
    cleaned = _clean_text(text)
    found = Counter()
    for skill in SKILL_KEYWORDS:
        # Use word boundaries to avoid matching 'r' inside 'programmer'
        # For multi-word skills like 'machine learning', use simple substring
        # For single-word skills, require word boundaries
        if ' ' in skill:
            count = cleaned.count(skill)
        else:
            import re
            pattern = r'\b' + re.escape(skill) + r'\b'
            count = len(re.findall(pattern, cleaned))
        if count:
            found[skill] = count
    return found


def parse_pdf(path: Path) -> str:
    import pdfplumber
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return '\n'.join(text_parts)


def parse_docx(path: Path) -> str:
    import docx
    doc = docx.Document(path)
    return '\n'.join([para.text for para in doc.paragraphs])


def parse_resume(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Resume not found: {path}")

    suffix = p.suffix.lower()
    if suffix == '.pdf':
        raw_text = parse_pdf(p)
    elif suffix == '.docx':
        raw_text = parse_docx(p)
    else:
        raise ValueError(f"Unsupported resume format: {suffix}")

    cleaned = _clean_text(raw_text)
    skills = _extract_skills(raw_text)

    return {
        'raw_text': raw_text,
        'cleaned_text': cleaned,
        'skills': skills,
        'skill_count': len(skills),
        'top_skills': skills.most_common(15),
    }


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python resume_parser.py <resume.pdf|docx>")
        sys.exit(1)
    result = parse_resume(sys.argv[1])
    print(f"Skills found ({result['skill_count']}):")
    for skill, count in result['top_skills']:
        print(f"  {skill}: {count}")
