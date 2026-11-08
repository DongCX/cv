# Chung-Hsuan Tung — Frontend Engineer

A bilingual CV, published with GitHub Pages.

- [中文](https://dongcx.github.io/cv/)
- [English](https://dongcx.github.io/cv/en/)

## Editing

The approved public text lives in `content/resume-zh.md` and `content/resume-en.md`. PDF downloads live in `assets/`. Keep both languages and PDF downloads in sync when editing the content.

Build with Python 3.12+ (standard library only):

```sh
python3 build.py
```

To import the two public resume drafts and matching PDFs from the local resume inventory:

```sh
python3 build.py --inventory ../resume-inventory
```

Only the two named resume files and their matching PDFs are imported. Research notes, source repositories, and internal evidence are not included.

Preview the generated site:

```sh
python3 -m http.server 8765 --directory docs --bind 127.0.0.1
```

GitHub Pages serves `docs/` on the `main` branch. Commit the generated files after building. No package installation, JavaScript runtime, external fonts, or analytics are required.
