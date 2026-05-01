# Appendix: Development Process and Rationale

## 1. Initial Problem Brainstorming

The project started from a broad question: what kind of AI agent would be genuinely useful to software builders, especially at the early stage of a project?

Several agent ideas were considered:

- a code review agent
- a bug triage agent
- a documentation generator
- a project planning assistant
- a system design agent

The strongest option was the system design agent because system design is one of the highest-leverage stages of software development. Before code is written, teams need to understand the product domain, identify actors, define workflows, choose service boundaries, model data, and think through scaling risks. Mistakes at this stage can become architectural debt that is expensive to fix later. 
Also, being a backend engineer, i understand the need for a proper system design, hence why i went with this.

## 2. Alternative Ideas Discarded

### Code review agent

A code review agent was considered because reviewing code is a common developer workflow. However, it was less compelling for this project because code review depends heavily on an existing codebase, project conventions, test suite, and historical context.

It would also be harder to benchmark fairly across generic prompts, since review quality depends on the quality and complexity of the submitted code.

### Documentation generator

A documentation agent was also considered. It would be useful, but mostly after a project already exists. The goal here was to support the earliest phase of building, before implementation begins.

### Project planning assistant

A planning assistant could help break ideas into tasks, but task planning without architectural direction can still lead to shallow implementation choices. System design felt more foundational.

## 3. Why System Design Was More Impactful

System design was chosen because it directly supports high-value engineering decisions:

- what services should exist
- what data should be stored
- how users interact with the system
- which APIs are needed
- how the system scales
- what tradeoffs the team must accept

This problem is also well suited to an AI-native workflow. A human might normally start with a whiteboard session. The agent replaces the first blank-whiteboard pass by generating a structured architecture draft that the team can critique and refine.

The agent is not meant to replace senior engineers. It is meant to accelerate the first draft and make architectural thinking more accessible.

## 4. Final App Architecture

The app is intentionally small and modular:

- `main.py` defines the CLI entrypoint.
- `config.py` loads environment variables and model settings.
- `prompt.py` builds the system and user prompts.
- `generator.py` calls the Groq chat completion API.
- `file_writer.py` saves markdown output.
- `outputs/` stores generated designs from the custom agent.
- `cursor-test/` stores comparable outputs from Cursor Claude.
- `scores/` stores assigned benchmark scores.
- `scoring.md` defines the scoring rubric.
- `benchmark.md` compares both tools.

The small-file design makes the agent easy to understand, test, and extend.

## 5. Top Architectural Decision: Prompt-Enforced Structure

The most important design choice was enforcing a fixed output structure through the system prompt.

The required sections are:

1. Problem Interpretation
2. High-Level Architecture
3. Service Breakdown
4. Data Model
5. API Design
6. Scalability Strategy
7. Tradeoffs

This was chosen because consistency matters more than novelty for this workflow. A system design document is only useful if it is easy to scan, compare, and evaluate.

Without an enforced structure, LLMs can produce impressive but inconsistent documents. One answer might focus on infrastructure, another on product goals, another on APIs. That makes benchmarking and reuse harder.

With an enforced structure, every output becomes a comparable architecture decision package.

## 6. Prompt Iterations

The prompt evolved toward stricter structure and more concrete engineering output.

### Early prompt idea

The earliest version was likely close to:

```text
Design a scalable system for this product idea.
```

This kind of prompt can produce useful text, but it is too open-ended. The model may skip APIs, omit data relationships, or avoid tradeoffs.

### Improved prompt direction

The prompt then became more explicit:

```text
Generate a production-oriented software design in markdown.
Include architecture, services, database, APIs, scalability, and tradeoffs.
```

This improved coverage, but the order and naming of sections could still vary.

### Final prompt pattern

The final system prompt enforces exact sections:

```text
You are a senior backend system architect.
Generate a production-oriented software design in markdown.
Include at least one Mermaid diagram and explicit sections in this exact order:
- 1. Problem Interpretation
- 2. High-Level Architecture
- 3. Service Breakdown
- 4. Data Model
- 5. API Design
- 6. Scalability Strategy
- 7. Tradeoffs
```

This made the output more reliable and directly aligned with the scoring rubric.

## 7. Model and Temperature Choice

The app uses:

```env
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.2
```

A low temperature was chosen because system design should be consistent and evaluable. Higher temperatures can make outputs more creative, but they can also increase variation in section coverage, naming, and depth.

For this project, the priority is repeatable architecture reasoning, not surprising prose.

## 8. Test Case Evolution

The benchmark uses three product ideas:

- digital contribution app
- food delivery app like Uber Eats
- doctor appointment platform

These were useful because they test different design pressures.

### Digital contribution app

This tests payments, campaigns, user trust, contribution tracking, and analytics.

Important architecture concerns:

- user accounts
- campaign management
- payment processing
- contribution records
- analytics
- fraud and trust

### Food delivery app

This tests marketplace complexity, logistics, high read/write volume, and real-time delivery workflows.

Important architecture concerns:

- users
- restaurants
- menus
- orders
- payments
- delivery logistics
- tracking
- peak traffic

### Doctor appointment platform

This tests scheduling correctness, role-based access, notifications, and healthcare-like privacy needs.

Important architecture concerns:

- patients
- doctors
- appointment booking
- doctor availability
- schedule conflicts
- reminders
- sensitive data

## 9. Metric Definition Rationale

The scoring model uses 10,000 total points across seven categories:

| Category | Max Score |
|---|---:|
| Requirement Understanding | 1400 |
| Architecture Quality | 2400 |
| Data Model Design | 1400 |
| API Design Quality | 1400 |
| Scalability & Reliability | 1400 |
| Tradeoff Reasoning | 1000 |
| Clarity & Structure | 1000 |
| **Total** | **10000** |

The largest weight goes to architecture quality because the core purpose of the agent is system design. Requirement understanding, data modeling, API design, and scalability each receive strong weights because they represent the practical substance of a useful architecture document.

Tradeoff reasoning receives its own category because mature system design is not only about listing components. It is about explaining why one approach is chosen over another.

Clarity and structure are also scored because a design document must be readable to be useful.

## 10. Benchmark Findings

The benchmark compared My System Design Agent against default Cursor Claude.

| Tool | Average Score |
|---|---:|
| My System Design Agent | 9400 |
| Cursor Claude | 9100 |

My agent won by **300 points**.

The most important difference was tradeoff reasoning:

| Category | My Agent Avg | Cursor Avg |
|---|---:|---:|
| Tradeoff Reasoning | 966.67 | 300 |
| Clarity & Structure | 1000 | 866.67 |

Cursor Claude often produced broader and more production-heavy outputs. It included strong sections on observability, capacity planning, security, compliance, phased rollout, and operational risks.

However, the custom agent was better aligned to the target workflow: a concise, repeatable system design brief with explicit tradeoffs.

## 11. Lessons Learned About LLM Consistency

### Structure is a control mechanism

The biggest lesson was that prompt structure can significantly improve consistency. LLMs are capable of producing strong architecture ideas, but without structure they may over-focus on some areas and under-focus on others.

The fixed seven-section format made outputs easier to score and compare.

### Low temperature helps repeatability

A low temperature reduced unnecessary variation. For system design, stable output is more valuable than creative formatting.

### Explicit sections improve benchmarking

The benchmark was easier because every custom-agent output used the same shape. Cursor outputs were richer but harder to compare because section choices varied more.

### Mermaid diagrams need validation

Requiring Mermaid diagrams made the output more visual, but generated diagrams can contain syntax issues. A future version should validate Mermaid syntax before saving the final document.

## 12. What I Would Improve Next

### Mermaid validation and repair loop

Add a post-processing step that:

1. extracts Mermaid code blocks
2. validates Mermaid syntax
3. sends invalid diagrams back to the model for repair
4. saves only the corrected final markdown

### Score-aware self-review

Add a second model pass that checks the output against the scoring rubric before saving:

- Are all seven sections present?
- Is there a Mermaid diagram?
- Are APIs included with examples?
- Does the data model include relationships?
- Are tradeoffs explicit?

### Richer domain-specific prompting

The agent could detect the domain and add deeper design requirements:

- payments for marketplaces
- scheduling locks for appointment systems
- real-time location for delivery systems
- audit logs for healthcare or financial systems

### Output quality gates

Future versions could reject outputs that are too short, missing required sections, or lack concrete APIs.

## 13. Cursor Chat Screenshots

No Cursor chat screenshot files are currently committed in this repository.

Suggested screenshot section once images are added:

```md
![Cursor digital contribution prompt](docs/screenshots/cursor-digital-contribution.png)
![Cursor food delivery prompt](docs/screenshots/cursor-food-delivery.png)
![Cursor doctor appointment prompt](docs/screenshots/cursor-doctor-appointment.png)
```

Recommended folder:

```text
docs/screenshots/
```

The screenshots should show:

- the prompt sent to Cursor
- the generated Cursor response
- enough visible output to prove the comparison source

## 14. Final Reflection

The final project demonstrates that a specialized agent can beat a general-purpose coding assistant on a focused workflow, even if the general assistant produces longer and more detailed documents.

The reason is specialization. The custom agent knows exactly what a system design answer should contain, produces it in a repeatable structure, and emphasizes tradeoff reasoning. That makes it especially valuable for early-stage architectural decision-making.
