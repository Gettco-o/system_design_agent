from pathlib import Path
from datetime import datetime

DEFAULT_OUTPUT_DIR = "outputs"
DEFAULT_OUTPUT_PREFIX = "system_design"

def build_default_filename() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{DEFAULT_OUTPUT_PREFIX}_{stamp}.md"

def save_markdown(markdown: str, output_path: str | None = None) -> str:
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = Path(DEFAULT_OUTPUT_DIR)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / build_default_filename()

    path.write_text(markdown, encoding="utf-8")
    return str(path)
