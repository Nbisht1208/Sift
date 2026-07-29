import polars as pl
import polars.selectors as cs 
from sift.core.models import DatasetProfile, ColumnProfile

class Profiler:
    def __init__(self, df: pl.DataFrame):
        self.df = df

    def _map_dtype(self, dtype: pl.DataType) -> str:
        
        # map technical polars types to normal names.
        
        dtype_str = str(dtype)
        if dtype in [pl.Int64, pl.Int32, pl.Float64, pl.Float32]:
            return "Numeric"
        elif dtype == pl.Boolean:
            return "Boolean"
        elif dtype == pl.Date or dtype == pl.Datetime:
            return "DateTime"
        elif dtype == pl.String:
            return "Text"
        else:
            return "Unknown" # Objects/Structs

    def run(self) -> DatasetProfile:
        row_count = self.df.height
        col_profiles = {}

        for col_name in self.df.columns:
            series = self.df[col_name]
            
            missing_count = series.null_count()
            unique_count = series.n_unique()
            
            friendly_type = self._map_dtype(series.dtype)
            
            stats = {}
            
            # --- NUMERIC STATS ---
            if friendly_type == "Numeric":
                stats = {
                    "mean": float(series.mean()) if series.mean() is not None else None, # type: ignore
                    "min": series.min(), # Polars min() usually returns scalar
                    "max": series.max(),
                    "std": float(series.std()) if series.std() is not None else None # type: ignore
                }
            
            # --- TEXT STATS ---
            elif friendly_type == "Text":
                # get most common value - mode

                clean_series = series.drop_nulls()
                if not clean_series.is_empty():

                    top_values_df = (
                        clean_series.value_counts()
                        .sort("count", descending=True)
                        .head(5)
                    )
                    
                    top_dicts = top_values_df.to_dicts()
                    stats["top_values"] = top_dicts
                    
                    if top_dicts:
                        stats["mode"] = top_dicts[0][col_name]

            col_profiles[col_name] = ColumnProfile(
                name=col_name,
                inferred_type=friendly_type, # friendly type
                total_rows=row_count,
                missing_count=missing_count,
                missing_ratio=missing_count / row_count if row_count > 0 else 0,
                unique_count=unique_count,
                unique_ratio=unique_count / row_count if row_count > 0 else 0,
                stats=stats
            )

        dup_rows = int(self.df.is_duplicated().sum())

        return DatasetProfile(
            row_count=row_count,
            column_count=len(self.df.columns),
            columns=col_profiles,
            duplicate_rows=dup_rows,
            issues=[]
        )