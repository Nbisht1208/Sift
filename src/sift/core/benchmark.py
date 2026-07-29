import polars as pl
from rich.console import Console
from rich.table import Table
from sift.chaos_monkey.polluter import ChaosMonkey
from sift.core.profiler import Profiler
from sift.core.inference import InferenceEngine

class Benchmark:
    def __init__(self, iterations: int = 10):
        self.iterations = iterations
        self.console = Console()

    def run(self):
        self.console.print(f"[bold cyan]🚀 Running Sift Benchmark ({self.iterations} iterations)...[/bold cyan]")
        
        results = {
            "nulls_injected": 0,
            "nulls_detected": 0,
            "outliers_injected": 0,
            "outliers_detected": 0,
        }

        for i in range(self.iterations):
            # 1. Setup Ground Truth
            df_clean = pl.DataFrame({
                "age": [25, 30, 35, 40, 20] * 100,
                "salary": [50000.0, 60000.0, 75000.0, 100000.0, 45000.0] * 100,
            })
            monkey = ChaosMonkey(seed=i) # diff seed each time
            
            # 2. Inject & Track
            df_dirty = monkey.inject_nulls(df_clean, ["age"], fraction=0.1)
            results["nulls_injected"] += 1
            
            df_dirty = monkey.inject_outliers(df_dirty, ["salary"], scale=100.0)
            results["outliers_injected"] += 1

            # 3. Run Engine
            profiler = Profiler(df_dirty)
            profile = profiler.run()
            
            inference = InferenceEngine(df_dirty)
            outliers = inference.detect_outliers("salary")

            # 4. Score
            # Did we find the missing values in Age?
            if profile.columns["age"].missing_count > 0:
                results["nulls_detected"] += 1
            
            # Did we find the outliers in Salary?
            if len(outliers) > 0:
                results["outliers_detected"] += 1

        self._print_report(results)

    def _print_report(self, results):
        table = Table(title="Reliability Scorecard")
        table.add_column("Test Case", style="cyan")
        table.add_column("Injected", justify="right")
        table.add_column("Detected", justify="right")
        table.add_column("Recall Rate", justify="right", style="bold green")

        # Nulls Stats
        null_rate = (results['nulls_detected'] / results['nulls_injected']) * 100
        table.add_row("Missing Value Injection", str(results['nulls_injected']), str(results['nulls_detected']), f"{null_rate:.1f}%")

        # Outlier Stats
        outlier_rate = (results['outliers_detected'] / results['outliers_injected']) * 100
        table.add_row("Extreme Outlier Injection", str(results['outliers_injected']), str(results['outliers_detected']), f"{outlier_rate:.1f}%")

        self.console.print("\n")
        self.console.print(table)
        
        overall = (null_rate + outlier_rate) / 2
        self.console.print(f"\n[bold]⭐ Overall Engine Reliability Score:[/bold] [green]{overall:.1f}%[/green]")