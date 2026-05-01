# AI System Design Agent

## Overview & Capabilities

This app is an AI agent that turns a plain-English product idea into a structured, production-oriented system design document.

It is optimized for early-stage architecture work: interpreting requirements, proposing service boundaries, modeling data, defining APIs, explaining scale strategy, and documenting tradeoffs in a format engineers can review quickly.

Example input:

```bash
python main.py "Build a doctor appointment platform for patients and doctors" --output design.md
```

Example output shape:

```md
# Doctor Appointment Platform Design

## 1. Problem Interpretation
Identifies patients, doctors, admins, appointment booking, doctor availability, and reminder workflows.

## 2. High-Level Architecture
Includes web/mobile clients, API gateway, user service, appointment service, notification service, and database.

## 3. Service Breakdown
Explains each service boundary and responsibility.

## 4. Data Model
Defines users, doctors, appointments, notifications, and relationships.

## 5. API Design
Provides REST endpoints with request/response examples.

## 6. Scalability Strategy
Covers load balancing, autoscaling, queues, and database replication.

## 7. Tradeoffs
Explains complexity, consistency, security, and usability tradeoffs.
```

## Problem Specialisation

Automated system design is the agent's number one priority because architecture is one of the most important early-stage decisions in any software project.

Good design decisions made early can accelerate delivery, reduce architectural debt, expose hidden requirements, and help newer engineers understand how real systems are assembled. Instead of starting with a blank whiteboard, the user can start with a complete architecture draft that is structured enough to critique, revise, and implement.

This makes system design a strong fit for an AI-native workflow. The agent can replace the first pass of a whiteboard session by producing a consistent design package in seconds: requirements, services, data model, APIs, scaling plan, and tradeoffs.

## Design Decisions

- **Prompt-enforced structure:** `prompt.py` requires seven sections in a fixed order so every generated design is easy to compare, score, and review.
- **Practical model choice:** The app uses Groq with `llama-3.3-70b-versatile` because it provides strong reasoning quality while also offering a free-access option with higher limits, which made repeated testing and benchmarking practical.
- **Low temperature setting:** `GROQ_TEMPERATURE` defaults to `0.2`, prioritizing consistency and repeatable architecture reasoning over creative variation.
- **Mermaid diagrams:** The system prompt requires at least one Mermaid diagram, making architecture and entity relationships readable directly inside markdown.
- **Modular code:** The app separates configuration, prompt construction, generation, file writing, and CLI entrypoint across small files: `config.py`, `prompt.py`, `generator.py`, `file_writer.py`, and `main.py`.
- **Markdown-first output:** Designs are saved as timestamped markdown files in `outputs/` by default, or to a custom path with `--output`.

## Performance Metrics & Score

The agent is scored out of 10,000 points using the rubric in `scoring.md`.

| Category | Max Score | Agent Average |
|---|---:|---:|
| Requirement Understanding | 1400 | 1400 |
| Architecture Quality | 2400 | 2200 |
| Data Model Design | 1400 | 1200 |
| API Design Quality | 1400 | 1233.33 |
| Scalability & Reliability | 1400 | 1400 |
| Tradeoff Reasoning | 1000 | 966.67 |
| Clarity & Structure | 1000 | 1000 |
| **Total** | **10000** | **9400** |

Calculation method:

```text
final_score = sum(weighted_category_scores)
average_score = mean(final_score across benchmark prompts)
```

Final score: **9400 / 10000**.

Grade band: **Production Candidate**, close to the `9500+` Elite Architect band.

## Benchmark Comparison

The same three prompts were tested against this agent and Cursor Claude using the scoring rubric in `scoring.md`.

| Tool | Average Score |
|---|---:|
| My System Design Agent | 9400 |
| Cursor Claude | 9100 |

The custom agent scored higher overall because it consistently included explicit tradeoff reasoning and strong output structure, while Cursor scored strongly on architecture and data modeling but lower on tradeoff reasoning.

See [BENCHMARK.md](benchmark.md) for the benchmark summary.

## Usage Guide

Clone the project:

```bash
git clone <repo-url>
cd my_system_design_agent
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.2
```

Generate a system design:

```bash
python main.py "your idea" --output design.md
```

If `--output` is omitted, the app writes to `outputs/system_design_<timestamp>.md`.

## Real-World Output Examples

Sample generated output for a digital contribution app:

````md
# Digital Contribution App System Design

## 1. Problem Interpretation
The digital contribution app aims to facilitate users in making contributions to various causes, individuals, or organizations. The app should allow users to create accounts, browse through different campaigns, and make donations. It should also enable campaign creators to set up and manage their fundraising campaigns.

Assumptions:
- The app will support multiple types of campaigns.
- Users can contribute using various payment methods.
- Campaign creators can set a target amount and deadline.

## 2. High-Level Architecture
The system will follow a microservices architecture, with separate services for user management, campaign management, payment processing, and analytics.

```mermaid
graph LR
    A[User] -->|Uses|> B(Digital Contribution App)
    B -->|Interacts With|> C[User Service]
    B -->|Interacts With|> D[Campaign Service]
    B -->|Interacts With|> E[Payment Service]
    B -->|Interacts With|> F[Analytics Service]
    C -->|Stores Data In|> G[User Database]
    D -->|Stores Data In|> H[Campaign Database]
    E -->|Processes Payments Through|> I[Payment Gateway]
    F -->|Analyzes Data From|> J[Analytics Database]
```

## 3. Service Breakdown
- **User Service:** Handles authentication, account creation, and profile management.
- **Campaign Service:** Manages campaign creation, updates, and retrieval.
- **Payment Service:** Processes transactions and payment methods.
- **Analytics Service:** Provides insights for campaign creators.

## 4. Data Model
- **Users:** `id`, `email`, `password`, `name`
- **Campaigns:** `id`, `title`, `description`, `target_amount`, `deadline`, `creator_id`
- **Contributions:** `id`, `campaign_id`, `user_id`, `amount`, `payment_method`
- **Payments:** `id`, `contribution_id`, `payment_method`, `payment_status`

## 5. API Design
- `POST /users` creates a user.
- `POST /campaigns` creates a campaign.
- `GET /campaigns` lists campaigns.
- `POST /contributions` records a contribution.

## 6. Scalability Strategy
Use load balancers, autoscaling, message queues, indexing, caching, and connection pooling.

## 7. Tradeoffs
- **Security vs. Convenience:** Stronger security can add user friction.
- **Data Consistency vs. Availability:** Synchronizing distributed services can reduce availability.
- **Scalability vs. Cost:** More scalable infrastructure increases operational cost.
````
