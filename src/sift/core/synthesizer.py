from typing import List, Dict, Any
from sift.core.models import DataIssue

class IssueSynthesizer:
    def __init__(self):
        self.issues: List[DataIssue] = []

    def add_anomaly_issue(self, column: str, count: int, total_rows: int):
        """
        Logic: Outliers are bad, but if EVERYTHING is an outlier, it's just a messy column.
        """
        ratio = count / total_rows
        severity = 0.5  # Default medium
        
        if ratio < 0.05:
            severity = 0.7  # Small % of outliers is usually a high-value finding
        elif ratio > 0.5:
            severity = 0.3  # If 50% are outliers, the data is just noise (low priority to fix)

        self.issues.append(DataIssue(
            type="Anomaly",
            column=column,
            severity=severity,
            detail=f"Found {count} ({ratio:.1%}) outliers using Isolation Forest.",
            action="Investigate rows. If valid, ignore. If errors, cap or drop.",
            metadata={"count": count}
        ))

    def add_string_cluster_issue(self, column: str, clusters: List[Dict[str, Any]]):
        """
        Logic: String inconsistency is HIGH severity because it breaks GROUP BY operations.
        """
        for cluster in clusters:
            self.issues.append(DataIssue(
                type="String Inconsistency",
                column=column,
                severity=0.85,  # High priority
                detail=f"Found confusing variations: {cluster['values']}",
                action=cluster['suggestion'],
                metadata={"values": cluster['values']}
            ))

    def add_null_issue(self, column: str, missing_count: int, total_rows: int):
        ratio = missing_count / total_rows
        severity = 0.1
        
        if ratio == 1.0:
            severity = 0.9 # Dead column
        elif ratio > 0.1:
            severity = 0.6 # Significant missing data
            
        self.issues.append(DataIssue(
            type="Missing Values",
            column=column,
            severity=severity,
            detail=f"Column is missing {missing_count} values ({ratio:.1%}).",
            action="Impute with median/mode or drop column if >50% missing."
        ))

    def get_ranked_issues(self) -> List[DataIssue]:
        """
        Returns issues sorted by Severity (Highest first).
        """
        # Sort descending by severity
        return sorted(self.issues, key=lambda x: x.severity, reverse=True)