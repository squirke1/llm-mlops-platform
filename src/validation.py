"""Data validation module for ensuring data quality."""

import pandas as pd
import numpy as np


class DataValidator:
    """Validate data schema and quality."""
    
    def __init__(self, schema):
        """
        Initialize validator with expected schema.
        
        Args:
            schema: Dictionary defining expected columns and types
                    Example: {'tenure_months': 'int', 'monthly_charges': 'float'}
        """
        self.schema = schema
        self.validation_errors = []
    
    def validate_schema(self, df):
        """
        Validate that DataFrame has expected columns and types.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        self.validation_errors = []
        
        # Check for missing columns
        expected_cols = set(self.schema.keys())
        actual_cols = set(df.columns)
        missing_cols = expected_cols - actual_cols
        
        if missing_cols:
            self.validation_errors.append(f"Missing columns: {missing_cols}")
            return False
        
        # Check data types
        for col, expected_type in self.schema.items():
            actual_type = df[col].dtype
            if not self._is_compatible_type(actual_type, expected_type):
                self.validation_errors.append(
                    f"Column '{col}' has type {actual_type}, expected {expected_type}"
                )
        
        return len(self.validation_errors) == 0
    
    def _is_compatible_type(self, actual, expected):
        """Check if actual dtype is compatible with expected type."""
        type_map = {
            'int': ['int64', 'int32', 'int16', 'int8'],
            'float': ['float64', 'float32'],
            'str': ['object'],
            'bool': ['bool']
        }
        
        return str(actual) in type_map.get(expected, [expected])
    
    def check_missing_values(self, df, threshold=0.5):
        """
        Check for excessive missing values.
        
        Args:
            df: DataFrame to check
            threshold: Maximum allowed fraction of missing values (0-1)
            
        Returns:
            dict: Columns with missing values and their proportions
        """
        missing = df.isnull().sum() / len(df)
        problematic = missing[missing > threshold]
        
        if len(problematic) > 0:
            self.validation_errors.append(
                f"Columns with >{threshold*100}% missing: {problematic.to_dict()}"
            )
        
        return problematic.to_dict()
    
    def check_outliers(self, df, columns, n_std=3):
        """
        Detect outliers using standard deviation method.
        
        Args:
            df: DataFrame to check
            columns: List of numerical columns to check
            n_std: Number of standard deviations for outlier threshold
            
        Returns:
            dict: Outlier counts per column
        """
        outliers = {}
        
        for col in columns:
            if col not in df.columns:
                continue
                
            mean = df[col].mean()
            std = df[col].std()
            outlier_mask = (df[col] < mean - n_std * std) | (df[col] > mean + n_std * std)
            outlier_count = outlier_mask.sum()
            
            if outlier_count > 0:
                outliers[col] = outlier_count
        
        return outliers
    
    def check_value_ranges(self, df, ranges):
        """
        Check if values are within expected ranges.
        
        Args:
            df: DataFrame to check
            ranges: Dict of column: (min, max) tuples
            
        Returns:
            dict: Columns with values outside expected ranges
        """
        violations = {}
        
        for col, (min_val, max_val) in ranges.items():
            if col not in df.columns:
                continue
                
            out_of_range = ((df[col] < min_val) | (df[col] > max_val)).sum()
            if out_of_range > 0:
                violations[col] = out_of_range
                self.validation_errors.append(
                    f"Column '{col}': {out_of_range} values outside range [{min_val}, {max_val}]"
                )
        
        return violations
    
    def get_errors(self):
        """Return list of validation errors."""
        return self.validation_errors


def validate_churn_data(df):
    """
    Validate customer churn dataset.
    
    Args:
        df: DataFrame with churn data
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Define expected schema
    schema = {
        'tenure_months': 'int',
        'monthly_charges': 'float',
        'total_charges': 'float',
        'contract_type': 'str',
        'num_support_tickets': 'int',
        'churn': 'int'
    }
    
    # Define expected value ranges
    ranges = {
        'tenure_months': (0, 100),
        'monthly_charges': (0, 500),
        'total_charges': (0, 20000),
        'num_support_tickets': (0, 50),
        'churn': (0, 1)
    }
    
    validator = DataValidator(schema)
    
    # Run validations
    schema_valid = validator.validate_schema(df)
    missing = validator.check_missing_values(df, threshold=0.3)
    outliers = validator.check_outliers(
        df, 
        ['tenure_months', 'monthly_charges', 'total_charges', 'num_support_tickets']
    )
    range_violations = validator.check_value_ranges(df, ranges)
    
    # Report results
    is_valid = schema_valid and len(missing) == 0 and len(range_violations) == 0
    
    if not is_valid:
        print("Validation errors:")
        for error in validator.get_errors():
            print(f"  - {error}")
    
    if outliers:
        print(f"Warning: Outliers detected: {outliers}")
    
    return is_valid
