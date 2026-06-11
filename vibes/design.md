# Repository Design: Comprehensive AI/Tech Curriculum

## 1. Core Philosophy

**Type:** Educational curriculum repository combining:
- Structured prose notes (progressive complexity)
- Runnable code labs (hands-on practice)
- Interview Q&A banks (knowledge verification)
- Production system designs (real-world patterns)

**Goal:** Bridge gap between theory and practice with depth-first progressions

---

## 2. Directory Architecture

### Top-Level Structure
```
repository/
├── docs/                    ← MkDocs-served prose curriculum
├── Codes/ or setup/         ← Runnable notebooks/scripts
├── Resources/               ← Reference materials (PDFs, papers)
├── Interview-Questions/     ← Q&A by topic
├── vibes/                   ← Meta documentation & planning
├── mkdocs.yml              ← MkDocs configuration
├── README.md               ← Project overview
└── LICENSE, CNAME          ← Hosting & legal
```

### Content Organization Pattern

Each major topic gets a dedicated folder with consistent structure:

```
docs/
├── 01-Topic-Name/
│   ├── INDEX.md              ← Topic overview & navigation
│   ├── Notes/                ← Prose curriculum (numbered files)
│   │   ├── 01-Fundamentals.md
│   │   ├── 02-Core-Concepts.md
│   │   ├── ...
│   │   ├── N-1-Production.md
│   │   └── N-Interview-QA-Bank.md
│   ├── CodeLabs/             ← Optional: code implementations
│   ├── Resources/            ← Optional: reference links
│   └── SystemDesigns/        ← Optional: architecture patterns
```

**Numbering Convention:**
- Topics are numbered: `01-`, `02-`, etc.
- Notes within topics follow natural progression (fundamentals → advanced)
- Interview Q&A is always the last numbered file in a topic

---

## 3. Content Strategy

### Progression Pattern (Depth-First)

Each topic follows this sequence:

| Phase | Purpose | Notes Content |
|-------|---------|---------------|
| 1 | **Foundations** | Core concepts, definitions, mental models |
| 2 | **Building Blocks** | Components, how they work, connections |
| 3 | **Architecture** | System design, patterns, trade-offs |
| 4 | **Production** | Deployment, optimization, failure modes |
| 5 | **Interview Q&A** | Consolidated knowledge check |

### Topic Design Example

```markdown
01-LLM-Models (12 notes)
├── 01-Fundamentals           ← What is an LLM?
├── 02-Architecture           ← Transformer basics
├── 03-Attention-Mechanisms   ← The engine
├── 04-Model-Architecture     ← Variants (decoder-only, etc.)
├── 05-KV-Cache               ← Optimization
├── 06-Training               ← Pretraining process
├── 07-Fine-Tuning            ← Adaptation
├── 08-GPU-Hardware           ← Infrastructure
├── 09-Failure-Modes          ← Edge cases & traps
├── 10-Production-Deployment  ← Real-world systems
├── 11-Prompting-Strategies   ← Using LLMs effectively
└── 12-Interview-QA-Bank      ← Knowledge verification
```

**Scalability:** Add or remove notes; Q&A consolidates all into one searchable file.

---

## 4. Code Lab Architecture (3D Approach)

If including code labs, use this structure:

### Three Dimensions of Practice

```
Codes/
├── setup/                          ← One-time configuration
│   ├── requirements.txt             ← Dependencies
│   ├── .env.example                 ← Configuration template
│   └── setup-guide.md               ← First-time setup
│
├── 01-Concepts/                     ← Single focused concepts
│   ├── 01-concept-simple/
│   ├── 02-concept-intermediate/
│   └── 03-concept-advanced/
│
├── 02-Architectures/                ← Pattern implementations
│   ├── 01-Sequential/
│   ├── 02-Parallel/
│   ├── 03-Hierarchical/
│   └── ...
│
└── 03-End-to-End-Systems/           ← Complete applications
    ├── 01-System-A/
    ├── 02-System-B/
    └── ...
```

### Key Pattern: Multi-Framework Comparison

If supporting multiple frameworks (e.g., LangChain, LangGraph, CrewAI):

```
Each architecture/system is implemented 4 ways:
01-Sequential/
├── langchain_implementation.ipynb
├── langgraph_implementation.ipynb
├── crewai_implementation.ipynb
└── google_adk_implementation.ipynb
```

**Benefit:** Direct comparison of same logic in different frameworks

---

## 5. Technology Stack Template

### Documentation Delivery
- **Framework:** MkDocs with Material theme
- **Serves:** Prose notes from `docs/` folder
- **Benefits:** Fast, searchable, GitHub Pages ready

### Code Execution
- **Notebooks:** Jupyter for interactive exploration
- **Scripts:** Python for production code
- **Orchestration:** Poetry or virtual environments

### Frameworks & Libraries (Example)

```
Core:
  - python-dotenv (config management)

AI/ML Frameworks:
  - langchain
  - langgraph
  - crewai
  - google-adk / google-cloud-aiplatform
  - google-generativeai

Development:
  - jupyter
  - jupyter-book
```

---

## 6. File Naming Conventions

### Markdown Files
```
✅ GOOD:
01-Topic-Name.md                    ← Numbered, hyphenated
02-Core-Concepts.md

❌ AVOID:
topic.md                            ← No numbering
Topic Name.md                       ← Spaces instead of hyphens
01_Topic_Name.md                    ← Underscores
```

### Code Files
```
✅ GOOD:
01_concept_simple.ipynb             ← snake_case, numbered
02_pattern_parallel.py

❌ AVOID:
concept-simple.ipynb                ← Hyphens (inconsistent with Python)
ConceptSimple.py                    ← CamelCase for notebooks
```

### Folders
```
✅ GOOD:
01-Topic-Name/                      ← Numbered, hyphenated
CodeLabs/                           ← PascalCase for non-numbered

❌ AVOID:
01-topic-name/                      ← Lowercase (harder to scan)
codelabs/                           ← lowercase (hard to visually parse)
```

---

## 7. MkDocs Configuration Template

```yaml
site_name: "Learning Hub: Foundational → Advanced"
site_description: "Structured curriculum from basics to production"
docs_dir: docs
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.top
    - search.highlight
    - content.code.copy
extra_css:
  - stylesheets/extra.css
markdown_extensions:
  - attr_list
  - pymdownx.superfences
  - pymdownx.highlight
  - pymdownx.arithmatex
  - pymdownx.emoji
```

---

## 8. Topic INDEX.md Template

Each topic should have an INDEX.md file:

```markdown
# 01-Topic-Name

**Overview:** One-sentence description of the topic

**Learning Path:**
- Start with: `01-Fundamentals.md`
- Build up through: `02-*` → `03-*` → ...
- Check knowledge: `12-Interview-QA-Bank.md`

## Quick Links

| File | Purpose | Time |
|------|---------|------|
| [01-Fundamentals](Notes/01-Fundamentals.md) | Mental models | 15 min |
| [02-Core-Concepts](Notes/02-Core-Concepts.md) | Building blocks | 20 min |
| ... | ... | ... |
| [12-Interview-QA-Bank](Notes/12-Interview-QA-Bank.md) | Self-check | as needed |

## Code Labs (Optional)

- [Framework A Implementation](CodeLabs/01-example.ipynb)
- [Framework B Implementation](CodeLabs/02-example.ipynb)

## Resources

- [Paper: Important Research](Resources/paper.pdf)
- [External Reference](https://example.com)

## Interview Q&A Preview

See `12-Interview-QA-Bank.md` for topic-specific questions.
```

---

## 9. Interview Q&A Bank Pattern

### Structure
```
📄 Topic-Specific Q&A: docs/Topic/Notes/12-Interview-QA-Bank.md
  └─ Deep interview questions for that topic

📄 Consolidated Q&A: docs/Interview-Questions/INDEX.md
  └─ Links to all topic Q&A files + searchable index
```

### Format Example
```markdown
# Interview Q&A Bank: Topic Name

## Beginner Level (Understanding)
**Q: What is X?**
A: Explanation (2-3 sentences)

## Intermediate Level (Application)
**Q: How would you implement X given Y constraint?**
A: Detailed explanation with code/example

## Advanced Level (Design & Trade-offs)
**Q: Design a system with X, considering Y and Z**
A: Architectural deep-dive with trade-offs
```

---

## 10. README.md Structure Template

```markdown
# [Project Name]

**One-liner:** What this curriculum covers

**Live site:** [link]

## Curriculum Topics

| # | Topic | Notes | Code Labs | Q&A | Status |
|---|-------|-------|-----------|-----|--------|
| 01 | Name | X files | ✅/— | Y+ Q&A | Complete/WIP |

## Quick Start

### Read the notes
```bash
pip install mkdocs-material
mkdocs serve
```

### Run code labs
```bash
cd Codes
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter notebook
```

## Repo Structure
[Folder tree]

## Contributing
[Guidelines if open source]
```

---

## 11. Scalability Patterns

### Adding a New Topic

1. Create folder: `docs/NN-New-Topic/`
2. Create structure:
   ```
   NN-New-Topic/
   ├── INDEX.md
   ├── Notes/
   │   ├── 01-Fundamentals.md
   │   ├── 02-Core-Concepts.md
   │   ├── ...
   │   └── N-Interview-QA-Bank.md
   ├── CodeLabs/ (optional)
   └── Resources/ (optional)
   ```
3. Update main `INDEX.md` and `mkdocs.yml` nav
4. Link from `docs/All_Questions.md` if using global Q&A

### Adding Code Labs to Existing Topic

1. Create `Topic/CodeLabs/` folder
2. Create multi-framework implementations: `01_pattern_langchain.ipynb`, etc.
3. Add `CodeLabs.md` linking implementations
4. Update `README.md` status

### Version Control Best Practices

```
.gitignore should include:
- .venv/
- __pycache__/
- .ipynb_checkpoints/
- .env (never commit secrets)
- *.pyc
- node_modules/
- site/ (MkDocs build output)
```

---

## 12. Meta-Documentation (vibes/ folder)

Use this folder to track repository evolution:

```
vibes/
├── design.md               ← This document
├── status.md               ← Content completion tracker
├── 30-4-CourseContentImprements.md  ← Version log
└── roadmap.md              ← Future topics/features
```

---

## 13. Deployment Strategy

### Option A: GitHub Pages (Recommended)
1. MkDocs generates static site in `site/`
2. GitHub Actions automates build on push
3. Deploy to `gh-pages` branch
4. Use CNAME for custom domain

### Option B: Self-Hosted
- Build locally, upload to server
- Use Docker for reproducible builds

### Option C: Cloud Platforms
- Google Cloud Storage + CDN
- AWS S3 + CloudFront
- Netlify (auto-deploy on git push)

---

## 14. Example Topic Progression

**Raw distribution for 6-topic curriculum:**

| Topic | Files | Code | Q&A | Estimated Hours |
|-------|-------|------|-----|-----------------|
| Fundamentals | 12 | — | 68 | 20 |
| Intermediate-A | 8 | 12 patterns | 50 | 25 |
| Intermediate-B | 10 | 8 patterns | 60 | 22 |
| Advanced-A | 6 | 3 systems | 40 | 18 |
| Advanced-B | 8 | 4 systems | 45 | 20 |
| Advanced-C | 6 | — | 35 | 15 |
| **Total** | **50 notes** | **27 code labs** | **298 Q&A** | **120 hours** |

---

## 15. Customization Checklist

When creating a new repo using this design:

- [ ] Choose topic areas (6-8 recommended)
- [ ] Decide on code lab frameworks
- [ ] Set up MkDocs with Material theme
- [ ] Create root INDEX.md for navigation
- [ ] Populate topic folders with INDEX.md templates
- [ ] Set up GitHub Actions for auto-deploy
- [ ] Create .env.example for secrets
- [ ] Add CNAME for custom domain
- [ ] Create initial status.md tracker
- [ ] Write first 1-2 topic notes

---

## Summary: The System

This design creates a **modular, scalable educational system** where:

✅ **Progression is clear:** Each topic goes fundamentals → production  
✅ **Code is runnable:** Multi-framework implementations, not just theory  
✅ **Knowledge is verified:** Q&A banks provide self-check mechanisms  
✅ **Hosting is free:** MkDocs + GitHub Pages  
✅ **Scalability is built-in:** Add topics/codes without restructuring  
✅ **Meta-tracking is easy:** vibes/ folder documents the evolution  

The result: A professional, maintainable curriculum repository.
