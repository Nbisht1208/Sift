import polars as pl
import polars.selectors as cs  # This handles the types for us
import numpy as np
from typing import Optional, List

class ChaosMonkey:
    def __init__(self, seed: Optional[int] = None):
        
        self.rng = np.random.default_rng(seed) # Master RNG: controls all randomness in the class

    def inject_nulls(self, df: pl.DataFrame, columns: List[str], fraction: float = 0.05) -> pl.DataFrame:
        df_dirty = df.clone()
        
        for col in columns:
            if col not in df.columns:
                continue
                
            n_rows = df.height
            n_nulls = int(n_rows * fraction)
            
            # Use the master RNG, don't re-seed
            indices = self.rng.choice(n_rows, size=n_nulls, replace=False)
            
            mask = np.zeros(n_rows, dtype=bool)
            mask[indices] = True
            
            df_dirty = df_dirty.with_columns(
                pl.when(pl.Series(mask))
                .then(None)
                .otherwise(pl.col(col))
                .alias(col)
            )
            
        return df_dirty

    def inject_outliers(self, df: pl.DataFrame, columns: List[str], scale: float = 5.0, outlier_fraction: float = 0.02) -> pl.DataFrame:
        # multiply random values by a scale to create anomalies, Numeric columns only.

        df_dirty = df.clone()
        
        valid_cols = [c for c in columns if c in df.select(cs.numeric()).columns] # validate that columns numeric using Polars Selectors, better that checking dtypes manually
        
        for col in valid_cols:
            n_rows = df.height
            n_outliers = max(1, int(n_rows * outlier_fraction)) 
            
            indices = self.rng.choice(n_rows, size=n_outliers, replace=False)
            
            data = df_dirty[col].to_numpy().copy()
            
            # Generic outlier logic: works for int and float
            if 'Float' in str(df[col].dtype):
                data[indices] = data[indices] * scale
            else:
                offset = np.max(data) * scale
                data[indices] = data[indices] + offset
                
            df_dirty = df_dirty.with_columns(pl.Series(name=col, values=data))
            
        return df_dirty

    def inject_duplicates(self, df: pl.DataFrame, n_dupes: int = 5) -> pl.DataFrame:
        if n_dupes <= 0:
            return df
            
        indices = self.rng.integers(0, df.height, size=n_dupes) # master RNG, no internal re-seeding.
        duplicates = df[indices]
        
        return pl.concat([df, duplicates])        