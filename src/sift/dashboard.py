import time
import os
import typer
import polars as pl
from typing_extensions import Annotated
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box

from sift.chaos_monkey.polluter import ChaosMonkey
from sift.core.profiler import Profiler
from sift.core.inference import InferenceEngine
from sift.core.synthesizer import IssueSynthesizer

def main(
    filepath: Annotated[Optional[str], typer.Argument(help="Path to a CSV or Parquet file to analyze.")] = None
):
    console = Console()
    console.print(Panel.fit("[bold cyan] SIFT: Adaptive Data Quality Engine[/bold cyan]", border_style="cyan"))

    mode = "FILE" if filepath else "DEMO"
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        
        # --- LOAD DATA ---
        task1 = progress.add_task("[green]Initializing...", total=None)
        time.sleep(0.5)

        if mode == "FILE":
            assert filepath is not None
            if not os.path.exists(filepath):
                console.print(f"[bold red]❌ Error: File not found: {filepath}[/bold red]")
                raise typer.Exit(code=1)
            
            progress.update(task1, description=f"[green]Loading {filepath}...")
            
            if filepath.endswith(".csv"):
                df_target = pl.read_csv(filepath, ignore_errors=True) 
            elif filepath.endswith(".parquet"):
                df_target = pl.read_parquet(filepath)
            else:
                console.print("[red]Unsupported file type. Use .csv or .parquet[/red]")
                raise typer.Exit(code=1)
                
        else:
            # DEMO MODE (Generate Dummy Data)
            progress.update(task1, description="[green]Generating Synthetic Data...")
            df_raw = pl.DataFrame({
                "id": range(1000),
                "age": [25, 30, 35, 40, 20] * 200,
                "salary": [50000.0, 60000.0, 75000.0, 100000.0, 45000.0] * 200,
                "city": ["NY", "New York", "new york", "SF", "San Fran"] * 200 
            })
            # Only run Chaos Monkey in Demo mode 
            monkey = ChaosMonkey(seed=42)
            df_target = monkey.inject_nulls(df_raw, ["age"], fraction=0.15)
            df_target = monkey.inject_outliers(df_target, ["salary"], scale=100.0)

        # --- ANALYZE  ---
        progress.update(task1, description="[green]Profiling Structure (Layer 1)...")
        time.sleep(0.5) 
        profiler = Profiler(df_target)
        profile = profiler.run()

        progress.update(task1, description="[green]Running Inference (Layer 2)...")
        time.sleep(0.5)
        inference = InferenceEngine(df_target)
        synthesizer = IssueSynthesizer()

        for col_name, col_stats in profile.columns.items():
            if col_stats.missing_count > 0:
                synthesizer.add_null_issue(col_name, col_stats.missing_count, profile.row_count)


        numeric_cols = [col for col, data in profile.columns.items() if data.inferred_type == "Numeric" and col != "id"]
        for col in numeric_cols:
            outliers = inference.detect_outliers(col)
            if outliers:
                synthesizer.add_anomaly_issue(col, len(outliers), profile.row_count)

        text_cols = [col for col, data in profile.columns.items() if data.inferred_type == "Text"]
        for col in text_cols:
            clusters = inference.detect_string_clusters(col)
            synthesizer.add_string_cluster_issue(col, clusters)

        ranked_issues = synthesizer.get_ranked_issues()

    summary_text = (
        f"[bold]Source:[/bold] {filepath if filepath else 'Synthetic Demo'}\n"
        f"[bold]Rows:[/bold] {profile.row_count}\n"
        f"[bold]Columns:[/bold] {profile.column_count}"
    )
    console.print(Panel(summary_text, title="Dataset Context", expand=False))

    console.print("\n[bold underline]🚨 Detected Quality Issues[/bold underline]")
    if not ranked_issues:
        console.print("[green]No critical issues detected![/green]")
    else:
        table = Table(box=box.SIMPLE_HEAD)
        table.add_column("Sev", justify="center", style="bold")
        table.add_column("Type", style="cyan")
        table.add_column("Column", style="magenta")
        table.add_column("Detail")
        table.add_column("Action", style="italic green")

        for issue in ranked_issues:
            sev_color = "red" if issue.severity > 0.7 else "yellow"
            sev_display = f"[{sev_color}]{issue.severity}[/{sev_color}]"
            table.add_row(sev_display, issue.type, issue.column, issue.detail, issue.action)
        console.print(table)

    console.print("\n(✅ Analysis Complete)")

if __name__ == "__main__":
    typer.run(main)