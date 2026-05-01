import typer
from rich import print
from file_writer import save_markdown
from generator import generate


app = typer.Typer()


@app.command()
def build(idea: str):
      print("[cyan]Generating system design...[/cyan]")
    
      result = generate(idea)

      output_path = save_markdown(result)

      print(result)
      print(f"[green]\nSaved output to: {output_path}[/green]")

      return 0


if __name__ == "__main__":
    app()