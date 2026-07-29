import polars as pl
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import CountVectorizer
from typing import List, Dict, Any

class InferenceEngine:
    def __init__(self, df: pl.DataFrame):
        self.df = df

    def detect_outliers(self, col_name: str, contamination: float = 0.01) -> List[int]:
        """
        use Isolation Forest to find anomalies in numeric data
        Returns a list of row indices that are outliers
        """
        series = self.df[col_name]
        
        data = series.drop_nulls().to_numpy().reshape(-1, 1)# sklearn can't handle nulls
        
        if len(data) < 50:
            return [] # Too small for ML

        # Train Model
        iso = IsolationForest(contamination=contamination, random_state=42)
        preds = iso.fit_predict(data) # -1 is outlier, 1 is normal
        
        # Map back to original indices
        outlier_values = data[preds == -1].flatten()
        
        # Return indices where value is in the outlier set
        return self.df.with_row_index().filter(
            pl.col(col_name).is_in(outlier_values)
        ).select("index").to_series().to_list()

    def detect_string_clusters(self, col_name: str, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Uses N-Grams + Clustering to find fuzzy duplicates.
        """
        vocab = self.df[col_name].drop_nulls().unique().to_list()
        if len(vocab) < 5: 
            return []

        # Vectorize (Character 3-grams)
        vectorizer = CountVectorizer(analyzer='char', ngram_range=(2, 3))
        try:
            X = vectorizer.fit_transform(vocab)
        except ValueError:
            return [] 

        # Cluster
        clustering = AgglomerativeClustering(
            n_clusters=None, 
            metric='cosine', 
            linkage='average',
            distance_threshold=1 - threshold
        )
        labels = clustering.fit_predict(X.toarray()) # type: ignore

        # Group results
        clusters = {}
        for word, label in zip(vocab, labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(word)

        # Filter for interesting clusters (size > 1)
        results = []
        for _, group in clusters.items():
            if len(group) > 1:
                results.append({
                    "issue": "String Inconsistency",
                    "values": group,
                    "suggestion": f"Map all to '{max(group, key=len)}'" 
                })
        
        return results
    