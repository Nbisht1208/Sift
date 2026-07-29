# Sift Engine: Operational Boundaries & Failure Modes

> "All models are wrong, but some are useful." — George Box

This document outlines the known limitations of the Sift Data Quality Engine. It serves as a transparency contract for users, defining where the engine's statistical assumptions may diverge from semantic reality.

## 1. Statistical Limitations

### 1.1 Small Dataset Sensitivity
* **Condition:** Datasets with < 50 rows.
* **Failure Mode:** `IsolationForest` (Anomaly Detection) requires sufficient density to establish a "normal" baseline.
* **Result:** In ultra-small datasets, valid data points may be flagged as outliers due to sparse distribution (High False Positive rate).
* **Mitigation:** Sift allows the user to inspect the `count` metadata in the report to contextually dismiss low-volume warnings.

### 1.2 The "Startup Salary" Problem (Skewed Distributions)
* **Condition:** Data with extreme but valid power-law distributions (e.g., 99 employees earn $50k, 1 CEO earns $5M).
* **Failure Mode:** Sift detects the CEO as an "Anomaly" (Severity 0.7).
* **Reality:** The data is accurate, just skewed.
* **Impact:** Sift flags *distributional deviation*, not *factual error*. Users must verify if the deviation is expected.

## 2. Semantic Blindness

### 2.1 Contextual Validity
* **Example:** A column `Age` containing the value `150`.
* **Sift Behavior:** If the dataset range is `20-40`, Sift flags `150` as an outlier.
* **Limitation:** Sift does not know that humans *cannot* live to 150. If the entire dataset consisted of people aged 140-160, Sift would consider `150` normal.
* **Takeaway:** Sift is a **Syntax & Statistics** engine, not a **Semantics** engine.

### 2.2 Aggressive String Clustering
* **Algorithm:** Character 3-Grams + Agglomerative Clustering.
* **Failure Mode:** Short words with high character overlap.
* **Example:** "Bat" vs "Cat" (1 letter difference).
* **Result:** In small vocabularies, these might be clustered as duplicates.
* **Mitigation:** The confidence score for short-string clusters is internally damped, but false positives are possible.

## 3. Performance Boundaries
* **Memory:** Sift utilizes **Polars** (Eager execution). The entire dataset + overhead must fit in system RAM.
* **Streaming:** Sift is a batch-processing engine. It is not designed for real-time windowed data analysis.


