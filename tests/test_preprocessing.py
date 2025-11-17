"""Tests for preprocessing and validation modules."""

import numpy as np
import pandas as pd
import pytest

from src.preprocessing import encode_categorical_features, scale_numerical_features
from src.validation import DataValidator, validate_churn_data


class TestPreprocessing:
    """Test preprocessing functions."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'age': [25, 30, 35, 40],
            'income': [50000, 60000, 70000, 80000],
            'category': ['A', 'B', 'A', 'C'],
            'target': [0, 1, 0, 1]
        })
    
    def test_encode_categorical_onehot(self, sample_df):
        """Test one-hot encoding of categorical features."""
        result = encode_categorical_features(sample_df, ['category'], method='onehot')
        
        # Original column should be removed
        assert 'category' not in result.columns
        
        # One-hot columns should be created (drop_first=True, so n-1 columns)
        assert 'category_B' in result.columns
        assert 'category_C' in result.columns
        assert 'category_A' not in result.columns  # First category dropped
        
        # Values should be binary
        assert result['category_B'].isin([0, 1]).all()
    
    def test_encode_categorical_label(self, sample_df):
        """Test label encoding of categorical features."""
        result = encode_categorical_features(sample_df, ['category'], method='label')
        
        # Original column should still exist
        assert 'category' in result.columns
        
        # Encoded column should be created
        assert 'category_encoded' in result.columns
        
        # Values should be integers
        assert result['category_encoded'].dtype in ['int64', 'int32', 'int8']
    
    def test_scale_numerical_features(self, sample_df):
        """Test scaling of numerical features."""
        result, scaler = scale_numerical_features(sample_df, ['age', 'income'])
        
        # Check that means are close to 0
        assert abs(result['age'].mean()) < 1e-10
        assert abs(result['income'].mean()) < 1e-10
        
        # Check that std is close to 1 (allow larger margin for small samples)
        assert abs(result['age'].std() - 1.0) < 0.2
        assert abs(result['income'].std() - 1.0) < 0.2
        
        # Check scaler is fitted
        assert scaler is not None
        assert hasattr(scaler, 'mean_')


class TestDataValidator:
    """Test DataValidator class."""
    
    @pytest.fixture
    def valid_df(self):
        """Create valid DataFrame for testing."""
        return pd.DataFrame({
            'age': [25, 30, 35],
            'income': [50000.0, 60000.0, 70000.0],
            'name': ['Alice', 'Bob', 'Charlie']
        })
    
    @pytest.fixture
    def schema(self):
        """Define test schema."""
        return {
            'age': 'int',
            'income': 'float',
            'name': 'str'
        }
    
    def test_validate_schema_success(self, valid_df, schema):
        """Test successful schema validation."""
        validator = DataValidator(schema)
        assert validator.validate_schema(valid_df) is True
        assert len(validator.get_errors()) == 0
    
    def test_validate_schema_missing_column(self, valid_df, schema):
        """Test schema validation with missing column."""
        df_missing = valid_df.drop('age', axis=1)
        validator = DataValidator(schema)
        
        assert validator.validate_schema(df_missing) is False
        assert len(validator.get_errors()) > 0
        assert 'Missing columns' in validator.get_errors()[0]
    
    def test_check_missing_values(self, valid_df, schema):
        """Test missing value detection."""
        # Add missing values
        df_with_na = valid_df.copy()
        df_with_na.loc[0, 'age'] = np.nan
        df_with_na.loc[1, 'age'] = np.nan
        
        validator = DataValidator(schema)
        missing = validator.check_missing_values(df_with_na, threshold=0.5)
        
        # Should detect age column with ~67% missing
        assert 'age' in missing
        assert missing['age'] > 0.5
    
    def test_check_outliers(self, schema):
        """Test outlier detection."""
        # Create data with obvious outlier (use more data points for stable stats)
        df = pd.DataFrame({
            'age': [25, 30, 30, 32, 33, 35, 35, 38, 40, 40, 42, 45, 10000],  # 10000 is extreme outlier
            'income': [50000.0] * 13,
            'name': ['A'] * 13
        })
        
        validator = DataValidator(schema)
        outliers = validator.check_outliers(df, ['age'], n_std=3)
        
        assert 'age' in outliers
        assert outliers['age'] >= 1
    
    def test_check_value_ranges(self, valid_df, schema):
        """Test value range validation."""
        validator = DataValidator(schema)
        ranges = {
            'age': (0, 100),
            'income': (0, 1000000)
        }
        
        violations = validator.check_value_ranges(valid_df, ranges)
        assert len(violations) == 0  # All values in range
        
        # Test with out-of-range values
        df_invalid = valid_df.copy()
        df_invalid.loc[0, 'age'] = 150  # Outside range
        
        violations = validator.check_value_ranges(df_invalid, ranges)
        assert 'age' in violations
        assert violations['age'] == 1


class TestChurnDataValidation:
    """Test churn-specific validation."""
    
    def test_validate_churn_data_valid(self):
        """Test validation of valid churn data."""
        df = pd.DataFrame({
            'tenure_months': [12, 24, 36],
            'monthly_charges': [50.0, 75.0, 100.0],
            'total_charges': [600.0, 1800.0, 3600.0],
            'contract_type': ['Month-to-month', 'One year', 'Two year'],
            'num_support_tickets': [1, 2, 3],
            'churn': [0, 1, 0]
        })
        
        assert validate_churn_data(df) is True
    
    def test_validate_churn_data_invalid_range(self):
        """Test validation fails for out-of-range values."""
        df = pd.DataFrame({
            'tenure_months': [12, 24, 200],  # 200 is out of range
            'monthly_charges': [50.0, 75.0, 100.0],
            'total_charges': [600.0, 1800.0, 3600.0],
            'contract_type': ['Month-to-month', 'One year', 'Two year'],
            'num_support_tickets': [1, 2, 3],
            'churn': [0, 1, 0]
        })
        
        assert validate_churn_data(df) is False
