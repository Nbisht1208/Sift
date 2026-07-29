import typer
from sift import dashboard, scorecard

app = typer.Typer(
    name="sift",
    help="Sift: Adaptive Data Quality Engine",
    add_completion=False,
    no_args_is_help=True
)

@app.command()
def analyze(
    filepath: str = typer.Argument(..., help="Path to the CSV/Parquet file to analyze.")
):
 
    dashboard.main(filepath)

@app.command()
def demo():

    dashboard.main(None)

@app.command()
def benchmark():

    scorecard.main()

def start():
    app()

if __name__ == "__main__":
    start()