"""Data preprocessing module for feature engineering."""

import pandas as pd
from sklearn.preprocessing import StandardScaler


def encode_categorical_features(df, columns, method='onehot'):
    """
    Encode categorical features.
    
    Args:
        df: Input DataFrame
        columns: List of column names to encode
        method: Encoding method ('onehot' or 'label')
        
    Returns:
        DataFrame with encoded features
    """
    df_encoded = df.copy()
    
    if method == 'onehot':
        df_encoded = pd.get_dummies(df_encoded, columns=columns, drop_first=True)
    elif method == 'label':
        for col in columns:
            df_encoded[f'{col}_encoded'] = pd.Categorical(df_encoded[col]).codes
    
    return df_encoded


def scale_numerical_features(df, columns):
    """
    Scale numerical features using StandardScaler.
    
    Args:
        df: Input DataFrame
        columns: List of column names to scale
        
    Returns:
        DataFrame with scaled features, fitted scaler
    """
    df_scaled = df.copy()
    scaler = StandardScaler()
    
    df_scaled[columns] = scaler.fit_transform(df[columns])
    
    return df_scaled, scaler


# TODO: Add data validation functions
# TODO: Add feature engineering functions
# TODO: Add pipeline class
