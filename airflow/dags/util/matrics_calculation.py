import pandas as pd
import numpy as np
import math

def get_metric_json(data):
    metrics = {}
    metrics['row_count'] = len(data)
    metrics['col_count'] = len(data.columns)

    for col in data.columns:
        nulls_count = data[col].isnull().sum()
        unique_values = data[col].nunique()
        duplicates_value = int(data[col].duplicated().sum().sum())
        if np.issubdtype(data[col].dtype, np.number):
            mean_value = data[col].mean() 
            median_value = data[col].median()

            std_value = data[col].std()
            percentiles_values = data[col].describe(percentiles=[.25, .5, .75])
            skewness_value = data[col].skew()

            kurtosis_value = data[col].kurtosis()

            correlation_values = {}
            if np.issubdtype(data[col].dtype, np.number):
                for other_col in data.columns:
                    if other_col != col and np.issubdtype(data[other_col].dtype, np.number):
                        correlation_values[other_col] = data[col].corr(data[other_col])

            outliers = None
            if np.issubdtype(data[col].dtype, np.number):
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = data[(data[col] < (Q1 - 1.5 * IQR)) | (data[col] > (Q3 + 1.5 * IQR))].index.tolist()

            metrics[col] = {
                "nulls_count": int(nulls_count),
                "unique_values": int(unique_values),
                "mean": float(mean_value) if mean_value is not None else None,
                "median": float(median_value) if median_value is not None else None,
                "duplicates": duplicates_value,
                "std": float(std_value) if std_value is not None else None,
                "percentiles": percentiles_values.to_dict() if percentiles_values is not None else None,
                "skewness": float(skewness_value) if skewness_value is not None else None,
                "kurtosis": float(kurtosis_value) if kurtosis_value is not None else None,
                "correlation": correlation_values,
                "outliers": outliers
            }
            
        else :
            metrics[col] = {
                "nulls_count": int(nulls_count),
                "unique_values": int(unique_values),
                "duplicates": duplicates_value
            }

    for col in data.columns:
        if np.issubdtype(data[col].dtype, np.number):
            if np.isnan(metrics[col]["std"]):
                metrics[col]["std"] = 0
            if np.isnan(metrics[col]["skewness"]):
                metrics[col]["skewness"] = 0
            if np.isnan(metrics[col]["kurtosis"]):
                metrics[col]["kurtosis"] = 0

    return metrics
