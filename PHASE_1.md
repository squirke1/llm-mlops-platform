# Phase 1: Basic ML Model

##  Goal
Build a simple but functional customer churn prediction model.

## What You'll Build
- Data generation script
- Simple Random Forest model
- Training script
- Model persistence (save/load)

## Step 1: Generate Sample Data (15 min)

Create `src/data.py`:
```python
import pandas as pd
import numpy as np

def generate_churn_data(n_samples=1000, random_state=42):
    """Generate synthetic customer churn data."""
    np.random.seed(random_state)
    
    data = {
        'tenure_months': np.random.randint(1, 72, n_samples),
        'monthly_charges': np.random.uniform(20, 120, n_samples),
        'total_charges': np.random.uniform(100, 8000, n_samples),
        'contract_type': np.random.choice(['Month-to-month', 'One year', 'Two year'], n_samples),
        'num_support_tickets': np.random.poisson(2, n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Simple churn logic
    churn_prob = (
        (df['tenure_months'] < 12) * 0.3 +
        (df['contract_type'] == 'Month-to-month') * 0.3 +
        (df['monthly_charges'] > 80) * 0.2
    )
    df['churn'] = (np.random.random(n_samples) < churn_prob).astype(int)
    
    return df
```

**Test it:**
```bash
python -c "from src.data import generate_churn_data; print(generate_churn_data(100).head())"
```

**Commit:**
```bash
git add src/data.py
git commit -m "feat: add sample data generation"
```

## Step 2: Create Model Class (20 min)

Create `src/model.py`:
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import joblib

class ChurnModel:
    def __init__(self, n_estimators=100, random_state=42):
        self.model = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state)
        self.metrics = {}
    
    def train(self, X, y):
        """Train the model and evaluate."""
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)
        
        y_pred = self.model.predict(X_test)
        self.metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
        }
        return self.metrics
    
    def predict(self, X):
        """Make predictions."""
        return self.model.predict(X)
    
    def save(self, filepath):
        """Save model to disk."""
        joblib.dump(self.model, filepath)
    
    @staticmethod
    def load(filepath):
        """Load model from disk."""
        model = ChurnModel()
        model.model = joblib.load(filepath)
        return model
```

**Commit:**
```bash
git add src/model.py
git commit -m "feat: implement churn prediction model"
```

## Step 3: Training Script (15 min)

Create `src/train.py`:
```python
import pandas as pd
from pathlib import Path
from data import generate_churn_data
from model import ChurnModel

def main():
    print("Generating data...")
    df = generate_churn_data(n_samples=5000)
    
    print("Preparing features...")
    # Simple preprocessing: encode categorical
    df_encoded = pd.get_dummies(df, columns=['contract_type'], drop_first=True)
    X = df_encoded.drop('churn', axis=1)
    y = df_encoded['churn']
    
    print("Training model...")
    model = ChurnModel(n_estimators=100)
    metrics = model.train(X, y)
    
    print("\nResults:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.3f}")
    
    # Save model
    Path('models').mkdir(exist_ok=True)
    model.save('models/churn_model.pkl')
    print("\nModel saved to models/churn_model.pkl")

if __name__ == "__main__":
    main()
```

**Test it:**
```bash
python src/train.py
```

**Commit:**
```bash
git add src/train.py
git commit -m "feat: add training script"
```

## Step 4: Add Tests (15 min)

Create `tests/test_model.py`:
```python
import pytest
import pandas as pd
import numpy as np
from src.data import generate_churn_data
from src.model import ChurnModel

def test_data_generation():
    df = generate_churn_data(n_samples=100)
    assert len(df) == 100
    assert 'churn' in df.columns
    assert df['churn'].isin([0, 1]).all()

def test_model_training():
    df = generate_churn_data(n_samples=500)
    df_encoded = pd.get_dummies(df, columns=['contract_type'], drop_first=True)
    X = df_encoded.drop('churn', axis=1)
    y = df_encoded['churn']
    
    model = ChurnModel(n_estimators=10)
    metrics = model.train(X, y)
    
    assert 'accuracy' in metrics
    assert 0 <= metrics['accuracy'] <= 1

def test_model_prediction():
    df = generate_churn_data(n_samples=500)
    df_encoded = pd.get_dummies(df, columns=['contract_type'], drop_first=True)
    X = df_encoded.drop('churn', axis=1)
    y = df_encoded['churn']
    
    model = ChurnModel(n_estimators=10)
    model.train(X, y)
    
    predictions = model.predict(X.head(10))
    assert len(predictions) == 10
    assert all(p in [0, 1] for p in predictions)
```

**Test it:**
```bash
make test
```

**Commit:**
```bash
git add tests/test_model.py
git commit -m "test: add model unit tests"
```

## Step 5: Merge to Develop

```bash
# Ensure tests pass
make test

# Switch to develop and merge
git checkout develop
git merge feature/phase-1-ml-model --no-ff
```

##  Phase 1 Complete!

You now have:
-  Working ML model
-  Data generation
-  Training pipeline
-  Model persistence
-  Unit tests

**Next**: Phase 2 - Data Pipeline (preprocessing, validation)
