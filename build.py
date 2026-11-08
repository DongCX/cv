#!/usr/bin/env python3
"""Build a dependency-free bilingual CV from the approved Markdown sources."""

import argparse
import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE_URL = "https://dongcx.github.io/cv/"
LANGUAGES = {
    "zh": {
        "source": "08-frontend-resume-zh-v2.md",
        "lang": "zh-Hant",
        "sections": ["簡介", "技術與能力", "工作經歷", "學歷"],
        "skip": "跳至主要內容",
        "navigation": "段落導覽",
        "download": "下載中文 PDF",
        "top": "回到頁首",
    },
    "en": {
        "source": "30-frontend-resume-en-v2.md",
        "lang": "en",
        "sections": ["Profile", "Technical Skills and Collaboration", "Experience", "Education"],
        "skip": "Skip to content",
        "navigation": "On this page",
        "download": "Download English PDF",
        "top": "Back to top",
    },
}
SECTION_IDS = ["profile", "skills", "experience", "education"]


def inline(text):
    """The sources only use bold spans and plain text within body paragraphs."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(text))


def split_title(text):
    parts = re.split(r"\s*[｜|]\s*", text, maxsplit=1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def parse_resume(text, language):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines[0].startswith("# "):
        raise ValueError("Resume must begin with its name and role")
    name, role = split_title(lines[0][2:])
    contacts = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", lines[1])
    if len(contacts) != 3 or not all(url.startswith(("https://", "mailto:")) for _, url in contacts):
        raise ValueError("Expected three approved contact links")
    sections = []
    for line in lines[2:]:
        if line.startswith("## "):
            sections.append({"title": line[3:], "lines": []})
        elif sections:
            sections[-1]["lines"].append(line)
        else:
            raise ValueError(f"Unexpected content: {line}")
    if [section["title"] for section in sections] != LANGUAGES[language]["sections"]:
        raise ValueError("Unexpected section structure")
    return name, role, contacts, sections


def render_skills(lines):
    items = []
    for line in lines:
        match = re.fullmatch(r"- \*\*(.+?)\*\*\s+(.+)", line)
        if not match:
            raise ValueError(f"Unexpected skill item: {line}")
        title, description = match.groups()
        items.append(f"<div><dt>{html.escape(title)}</dt><dd>{inline(description)}</dd></div>")
    return '<dl class="skills-grid">' + "\n".join(items) + "</dl>"


def render_experience(lines):
    output = []
    job_open = project_open = list_open = False
    project_index = 0
    for line in lines:
        if not line.startswith("- ") and list_open:
            output.append("</ul>")
            list_open = False
        if line.startswith("### "):
            if project_open:
                output.append("</section>")
                project_open = False
            if job_open:
                output.append("</article>")
            name, detail = split_title(line[4:])
            output.append(f'<article class="job"><header class="job-header"><h3>{html.escape(name)}</h3><p>{html.escape(detail)}</p></header>')
            job_open = True
        elif line.startswith("#### "):
            if project_open:
                output.append("</section>")
            project_index += 1
            title, date = split_title(line[5:])
            date_span = f'<span class="project-date">{html.escape(date)}</span>' if date else ""
            output.append(f'<section class="project" aria-labelledby="project-{project_index}"><h4 id="project-{project_index}">{html.escape(title)}{date_span}</h4>')
            project_open = True
        elif line.startswith("- "):
            if not list_open:
                output.append("<ul>")
                list_open = True
            output.append(f"<li>{inline(line[2:])}</li>")
        elif not line.startswith("#"):
            kind = "project-purpose" if project_open else "job-dates"
            output.append(f'<p class="{kind}">{inline(line)}</p>')
        else:
            raise ValueError(f"Unexpected experience line: {line}")
    if list_open:
        output.append("</ul>")
    if project_open:
        output.append("</section>")
    if job_open:
        output.append("</article>")
    if project_index != 7:
        raise ValueError(f"Expected seven approved projects, found {project_index}")
    return "\n".join(output)


def build_page(language):
    settings = LANGUAGES[language]
    text = (ROOT / "content" / f"resume-{language}.md").read_text()
    name, role, contacts, sections = parse_resume(text, language)
    prefix = "../" if language == "en" else "./"
    current_url = BASE_URL + ("en/" if language == "en" else "")
    pdf_name = f"chung-hsuan-tung-frontend-resume-{language}.pdf"
    description = sections[0]["lines"][0]
    contact_links = "".join(f'<a href="{html.escape(url, quote=True)}">{html.escape(label)}</a>' for label, url in contacts)
    navigation = "".join(f'<a href="#{anchor}">{html.escape(section["title"])}</a>' for anchor, section in zip(SECTION_IDS, sections))
    body = []
    for anchor, section in zip(SECTION_IDS, sections):
        if anchor == "skills":
            content = render_skills(section["lines"])
        elif anchor == "experience":
            content = render_experience(section["lines"])
        else:
            content = "\n".join(f"<p>{inline(line)}</p>" for line in section["lines"])
        body.append(f'<section id="{anchor}" class="resume-section" aria-labelledby="{anchor}-title"><h2 id="{anchor}-title">{html.escape(section["title"])}</h2>{content}</section>')
    language_links = "".join(
        f'<a href="{prefix}{"en/" if lang == "en" else ""}" lang="{LANGUAGES[lang]["lang"]}" hreflang="{LANGUAGES[lang]["lang"]}"{ " aria-current=\"page\"" if lang == language else ""}>{label}</a>'
        for lang, label in [("zh", "中文"), ("en", "English")]
    )
    return f'''<!doctype html>
<html lang="{settings["lang"]}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(name)} — {html.escape(role)}</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <meta name="color-scheme" content="light">
  <meta property="og:type" content="profile">
  <meta property="og:title" content="{html.escape(name)} — {html.escape(role)}">
  <meta property="og:description" content="{html.escape(description, quote=True)}">
  <meta property="og:url" content="{current_url}">
  <link rel="canonical" href="{current_url}">
  <link rel="alternate" hreflang="zh-Hant" href="{BASE_URL}">
  <link rel="alternate" hreflang="en" href="{BASE_URL}en/">
  <link rel="alternate" hreflang="x-default" href="{BASE_URL}">
  <link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{prefix}assets/site.css">
</head>
<body id="top">
  <a class="skip-link" href="#main">{settings["skip"]}</a>
  <div class="page">
    <header class="masthead">
      <div class="identity"><h1>{html.escape(name)}</h1><p class="role">{html.escape(role)}</p><div class="contacts">{contact_links}</div></div>
      <div class="utilities"><nav class="language-switch" aria-label="Language">{language_links}</nav><a class="pdf-link" href="{prefix}assets/{pdf_name}" download>{settings["download"]}<span aria-hidden="true"> ↗</span></a></div>
    </header>
    <div class="layout">
      <aside class="sidebar"><nav aria-label="{settings["navigation"]}">{navigation}</nav></aside>
      <main id="main">{"".join(body)}</main>
    </div>
    <footer><span>{html.escape(name)}</span><a href="#top">{settings["top"]}<span aria-hidden="true"> ↑</span></a></footer>
  </div>
</body>
</html>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, help="Import the two approved resumes and PDFs from a local inventory")
    args = parser.parse_args()
    if args.inventory:
        (ROOT / "content").mkdir(exist_ok=True)
        (ROOT / "assets").mkdir(exist_ok=True)
        for language, settings in LANGUAGES.items():
            shutil.copy2(args.inventory / settings["source"], ROOT / "content" / f"resume-{language}.md")
            name = f"chung-hsuan-tung-frontend-resume-{language}.pdf"
            shutil.copy2(args.inventory / "output" / name, ROOT / "assets" / name)
    docs = ROOT / "docs"
    (docs / "en").mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "assets", docs / "assets", dirs_exist_ok=True)
    for language, destination in [("zh", docs / "index.html"), ("en", docs / "en" / "index.html")]:
        destination.write_text(build_page(language), encoding="utf-8")
    (docs / ".nojekyll").touch()
    print("Built Chinese and English CV pages with matching PDF downloads.")


if __name__ == "__main__":
    main()
