"""Customer churn prediction model."""

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split


class ChurnModel:
    """Random Forest model for customer churn prediction."""

    def __init__(self, n_estimators=100, random_state=42):
        """
        Initialize the model.

        Args:
            n_estimators: Number of trees in the forest
            random_state: Random seed for reproducibility
        """
        self.model = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state)
        self.metrics = {}

    def train(self, X, y):
        """
        Train the model and evaluate performance.

        Args:
            X: Features DataFrame
            y: Target labels

        Returns:
            Dictionary of evaluation metrics
        """
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        self.metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
        }
        return self.metrics

    def predict(self, X):
        """
        Make predictions.

        Args:
            X: Features to predict on

        Returns:
            Predicted labels
        """
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
