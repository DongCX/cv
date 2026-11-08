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
        "lang": "zh-TW",
        "sections": ["簡介", "技術與能力", "工作經歷", "學歷"],
        "skip": "跳至主要內容",
        "navigation": "段落導覽",
        "language_navigation": "語言切換",
        "top": "回到頁首",
    },
    "en": {
        "source": "30-frontend-resume-en-v2.md",
        "lang": "en",
        "sections": ["Profile", "Technical Skills and Collaboration", "Experience", "Education"],
        "navigation_labels": ["Profile", "Skills", "Experience", "Education"],
        "skip": "Skip to content",
        "navigation": "On this page",
        "language_navigation": "Language",
        "top": "Back to top",
    },
}
SECTION_IDS = ["profile", "skills", "experience", "education"]
CONTACT_ICONS = {
    "Email": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "GitHub": '<path fill="currentColor" stroke="none" d="M12 .75a11.25 11.25 0 0 0-3.56 21.92c.56.1.77-.24.77-.54v-2.1c-3.13.68-3.8-1.33-3.8-1.33-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.68.08-.68 1.13.08 1.73 1.16 1.73 1.16 1 1.72 2.64 1.22 3.29.93.1-.73.39-1.22.72-1.5-2.5-.29-5.13-1.25-5.13-5.56 0-1.23.44-2.23 1.16-3.02-.12-.28-.5-1.43.11-2.98 0 0 .95-.3 3.1 1.15a10.8 10.8 0 0 1 5.64 0c2.15-1.46 3.1-1.15 3.1-1.15.61 1.55.23 2.7.11 2.98.72.79 1.16 1.79 1.16 3.02 0 4.32-2.64 5.27-5.15 5.55.4.35.76 1.04.76 2.1v3.08c0 .3.2.65.77.54A11.25 11.25 0 0 0 12 .75Z"/>',
    "LinkedIn": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="7.5" cy="8" r="1" fill="currentColor" stroke="none"/><path d="M7.5 11v6.5M11.5 11v6.5M11.5 14a3 3 0 0 1 6 0v3.5"/>',
}


def render_contacts(contacts):
    links = []
    for label, url in contacts:
        if url.startswith("mailto:"):
            icon_name = "Email"
        elif url == "https://github.com/DongCX":
            label = icon_name = "GitHub"
        else:
            icon_name = label
        icon = CONTACT_ICONS[icon_name]
        svg = f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{icon}</svg>'
        links.append(f'<a href="{html.escape(url, quote=True)}">{svg}<span>{html.escape(label)}</span></a>')
    return "".join(links)


def inline(text):
    """The sources only use bold spans and plain text within body paragraphs."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(text))


def split_title(text):
    parts = re.split(r"\s*[｜|]\s*", text, maxsplit=1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def render_dates(text):
    """Preserve displayed dates while exposing only their known precision."""
    months = {name: f"{index:02}" for index, name in enumerate(
        "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
    pattern = r"\b(?:" + "|".join(months) + r") \d{4}\b|\b\d{4}\.\d{2}\b|\b\d{4}\b"

    def time_tag(match):
        label = match.group()
        if " " in label:
            month, year = label.split()
            value = f"{year}-{months[month]}"
        else:
            value = label.replace(".", "-")
        return f'<time datetime="{value}">{label}</time>'

    return re.sub(pattern, time_tag, html.escape(text))


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
    job_index = 0
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
            job_index += 1
            output.append(f'<article class="job" aria-labelledby="job-{job_index}"><header class="job-header"><h3 id="job-{job_index}">{html.escape(name)}</h3><p>{render_dates(detail)}</p></header>')
            job_open = True
        elif line.startswith("#### "):
            if project_open:
                output.append("</section>")
            project_index += 1
            title, date = split_title(line[5:])
            date_span = f'<p class="project-date">{render_dates(date)}</p>' if date else ""
            output.append(f'<section class="project" aria-labelledby="project-{project_index}"><header class="project-heading"><h4 id="project-{project_index}">{html.escape(title)}</h4>{date_span}</header>')
            project_open = True
        elif line.startswith("- "):
            if not list_open:
                output.append("<ul>")
                list_open = True
            output.append(f"<li>{inline(line[2:])}</li>")
        elif not line.startswith("#"):
            kind = "project-purpose" if project_open else "job-dates"
            content = inline(line) if project_open else render_dates(line)
            output.append(f'<p class="{kind}">{content}</p>')
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
    name_html = html.escape(name)
    if language == "zh":
        local_name, latin_name = name.split(" ", 1)
        name_html = f'<span class="name-local">{html.escape(local_name)}</span> <span class="name-latin" lang="en">{html.escape(latin_name)}</span>'
    prefix = "../" if language == "en" else "./"
    current_url = BASE_URL + ("en/" if language == "en" else "")
    description = sections[0]["lines"][0]
    contact_links = render_contacts(contacts)
    navigation_labels = settings.get("navigation_labels", settings["sections"])
    navigation = "".join(f'<li><a href="#{anchor}">{html.escape(label)}</a></li>' for anchor, label in zip(SECTION_IDS, navigation_labels))
    body = []
    for anchor, section in zip(SECTION_IDS, sections):
        if anchor == "skills":
            content = render_skills(section["lines"])
        elif anchor == "experience":
            content = render_experience(section["lines"])
        else:
            content = "\n".join(f"<p>{render_dates(line) if anchor == 'education' else inline(line)}</p>" for line in section["lines"])
        body.append(f'<section id="{anchor}" class="resume-section" aria-labelledby="{anchor}-title"><h2 id="{anchor}-title">{html.escape(section["title"])}</h2>{content}</section>')
    language_links = '<span aria-hidden="true" class="language-divider">/</span>'.join(
        f'<a href="{prefix}{"en/" if lang == "en" else ""}" lang="{LANGUAGES[lang]["lang"]}" hreflang="{LANGUAGES[lang]["lang"]}"{ " aria-current=\"page\"" if lang == language else ""}>{label}</a>'
        for lang, label in [("zh", "zh-tw"), ("en", "en")]
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
  <link rel="alternate" hreflang="zh-TW" href="{BASE_URL}">
  <link rel="alternate" hreflang="en" href="{BASE_URL}en/">
  <link rel="alternate" hreflang="x-default" href="{BASE_URL}">
  <link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{prefix}assets/site.css">
</head>
<body id="top">
  <a class="skip-link" href="#main">{settings["skip"]}</a>
  <div class="page">
    <header class="masthead">
      <nav class="language-switch" aria-label="{settings['language_navigation']}">{language_links}</nav>
      <div class="identity"><h1 id="resume-name">{name_html}</h1><p class="role">{html.escape(role)}</p><address class="contacts" aria-labelledby="resume-name">{contact_links}</address></div>
    </header>
    <div class="layout">
      <div class="sidebar"><nav aria-label="{settings["navigation"]}"><ul>{navigation}</ul></nav></div>
      <main id="main" tabindex="-1">{"".join(body)}</main>
    </div>
    <footer><span>{html.escape(name)}</span><a href="#top">{settings["top"]}<span aria-hidden="true"> ↑</span></a></footer>
  </div>
</body>
</html>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, help="Import the two approved resumes from a local inventory")
    args = parser.parse_args()
    if args.inventory:
        (ROOT / "content").mkdir(exist_ok=True)
        for language, settings in LANGUAGES.items():
            shutil.copy2(args.inventory / settings["source"], ROOT / "content" / f"resume-{language}.md")
    docs = ROOT / "docs"
    (docs / "en").mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "assets", docs / "assets", dirs_exist_ok=True)
    for language, destination in [("zh", docs / "index.html"), ("en", docs / "en" / "index.html")]:
        destination.write_text(build_page(language), encoding="utf-8")
    (docs / ".nojekyll").touch()
    print("Built Chinese and English CV pages.")


if __name__ == "__main__":
    main()
