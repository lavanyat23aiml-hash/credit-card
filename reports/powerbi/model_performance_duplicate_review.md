# Model Performance Duplicate Review

## Issue Observed
The file `data/processed/powerbi/ModelPerformance.csv` contains identical metrics for two differently named models:
- `M2_LR_Weighted`
- `Tuned_LR_Weighted`

Both models yield identical values across all evaluation metrics, including accuracy (0.7408), balanced accuracy, precision, recall, F1-score, ROC-AUC, True Positives (TP), True Negatives (TN), False Positives (FP), False Negatives (FN), and illustrative business cost.

## Analysis
Because both rows have exactly identical metrics at 4 decimal places, this implies that the hyperparameters selected during the GridSearch/RandomSearch tuning phase for the Logistic Regression (`Tuned_LR_Weighted`) naturally converged back to the exact same baseline parameters configured in the original weighted model (`M2_LR_Weighted`), or the tuning grid did not offer combinations that improved upon the default parameters.

## Recommendation for Power BI Dashboard
Do not silently delete either row.
Power BI will plot them both. To prevent confusion from viewers thinking there is a bug displaying "tied" bars:
1. Present both models as they exist in the raw CSV.
2. In the `04_model_performance.md` explanatory text boxes, add a footnote explaining:
   *"Note: Tuned_LR_Weighted and M2_LR_Weighted present identical scores because the hyperparameter tuning process concluded that the baseline weighted parameters were already optimal."*

This maintains the integrity of the data pipeline while solving the visualization ambiguity.
