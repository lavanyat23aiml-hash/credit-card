# Page 4: Model Performance

**Page Size**: 16:9 (1280x720)

## Disconnected Slicers
- **Model Name** (Dropdown, Single Select) -> `ModelPerformance[model_name]`
- **Threshold** (Dropdown, Single Select) -> `ThresholdAnalysis[threshold]`

## Explanatory Text Boxes
1. **Why accuracy alone is insufficient**: High accuracy often results from predicting the majority class. Baseline models miss actual defaulters.
2. **Why recall matters**: Missing a defaulter (false negative) represents a major financial loss.
3. **Threshold Selection**: The threshold is optimized (e.g., 0.40) to minimize the Business Cost, accepting more false positives to catch more true defaulters.
4. **Business Costs are Illustrative**: FN=5 and FP=1 are illustrative assumptions.

## Main Visuals
### 1. Model Comparison Table
- **Type**: Table
- **Columns**: `model_name`, `accuracy`, `balanced_accuracy`, `precision_class_1`, `recall_class_1`, `f1_class_1`, `roc_auc`, `average_precision`, `business_cost_illustrative`
- **Sorting**: `f1_class_1` descending

### 2. Precision / Recall / F1 / ROC-AUC / Avg Precision by Model
- **Type**: Clustered Bar Charts (5 visuals, or combined)
- **Axis**: `model_name`
- **Values**: `precision_class_1`, `recall_class_1`, `f1_class_1`, `roc_auc`, `average_precision`

### 3. False Negative & False Positive Comparison
- **Type**: Clustered Column Charts
- **Axis**: `model_name`
- **Values**: `false_negatives` (Red), `false_positives` (Orange)

### 4. Illustrative Business Cost Comparison
- **Type**: Clustered Column Chart
- **Axis**: `model_name`
- **Values**: `business_cost_illustrative`
- **Sorting**: Ascending (lowest is best)

### 5. Selected Threshold Card
- **Type**: Card
- **Value**: `Selected Model Threshold`

### 6. Threshold vs Precision / Recall / F1
- **Type**: Line Chart
- **Axis**: `threshold` (from `ThresholdAnalysis`)
- **Values**: `precision`, `recall`, `f1`

### 7. Top Feature Importance
- **Type**: Clustered Bar Chart
- **Axis**: `Feature` (from `FeatureImportance`)
- **Values**: `Importance`
- **Sorting**: `Importance` descending
- **Filter**: Top 10 by `Importance`
