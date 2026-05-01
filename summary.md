# Project Summary

- Built an **AI System Design Agent** that converts natural-language product ideas into structured, production-oriented architecture documents.

- The agent is implemented as a Python CLI using Groq's `llama-3.3-70b-versatile` model, with output saved as markdown files in `outputs/` or to a custom path via `--output`.

- The model choice was also practical: Groq provided a free-access path with higher usage limits, making it suitable for repeated prompt testing, benchmarking, and iteration without adding cost pressure.

- The problem matters because early architecture decisions shape delivery speed, system complexity, scalability, and long-term technical debt. A fast first-pass system design agent helps teams move from vague ideas to reviewable engineering plans quickly.

- The agent is especially useful for newer engineers because it creates a repeatable design pattern: interpret the problem, propose architecture, break down services, model data, define APIs, plan scalability, and explain tradeoffs.

- Top architectural choice: **prompt-enforced structure**. The system prompt requires seven ordered sections:
  - Problem Interpretation
  - High-Level Architecture
  - Service Breakdown
  - Data Model
  - API Design
  - Scalability Strategy
  - Tradeoffs

- This structure makes outputs easier to compare, score, and improve across multiple prompts.

- The agent also requires at least one Mermaid diagram, making the generated architecture easier to visualize directly in markdown.

- Final benchmark score: **9400 / 10000**, compared with **9100 / 10000** for default Cursor Claude on the same three prompts.

- The agent's biggest strengths were **clarity and structure** and **explicit tradeoff reasoning**.

- One improvement I would add next: a feedback loop that validates generated Mermaid syntax, detects malformed diagrams, and asks the model to repair the diagram before saving the final markdown.
