
REQUIRED_SECTIONS = [
    "1. Problem Interpretation",
    "2. High-Level Architecture",
    "3. Service Breakdown",
    "4. Data Model",
    "5. API Design",
    "6. Scalability Strategy",
    "7. Tradeoffs",
]

def build_system_prompt() -> str:
      sections = "\n".join(f"- {s}" for s in REQUIRED_SECTIONS)

      return (
            "You are a senior backend system architect. "
            "Generate a production-oriented software design in markdown. "
            "Include at least one Mermaid diagram and explicit sections in this exact order:\n"
            f"{sections}\n"
            "For API Design, include representative REST endpoints with request/response examples. "
            "For Data Model, include entities/tables and relationships. "
            "Keep the output implementation-agnostic and engineering-focused."
      )

def build_user_prompt(idea: str) -> str:
      return (
        "Design a robust and scalable system for the following product idea:\n\n"
        f"{idea}\n\n"
        "Please include assumptions when requirements are ambiguous."
      )
