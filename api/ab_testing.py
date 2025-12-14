"""A/B testing module for model version routing and experiment management."""

import hashlib
import os
import random
from dataclasses import dataclass
from typing import Dict, Optional

from prometheus_client import Counter, Histogram

# Module-level Prometheus metrics (singleton pattern)
try:
    variant_requests = Counter(
        "ab_test_requests_total",
        "Total requests per model variant",
        ["variant_name", "variant_version"],
    )
    variant_latency = Histogram(
        "ab_test_prediction_duration_seconds",
        "Prediction duration per variant",
        ["variant_name", "variant_version"],
    )
    variant_errors = Counter(
        "ab_test_errors_total",
        "Total errors per model variant",
        ["variant_name", "variant_version"],
    )
except ValueError:
    # Metrics already registered (e.g., in tests)
    from prometheus_client import REGISTRY

    variant_requests = REGISTRY._collector_to_names.get("ab_test_requests_total")
    variant_latency = REGISTRY._collector_to_names.get("ab_test_prediction_duration_seconds")
    variant_errors = REGISTRY._collector_to_names.get("ab_test_errors_total")


@dataclass
class ModelVariant:
    """Represents a model variant in an A/B test."""

    name: str
    model: object
    traffic_percentage: float
    version: str
    stage: str  # 'control', 'treatment', 'champion', 'challenger'


class ABTestManager:
    """Manages A/B testing for model versions."""

    def __init__(self):
        self.variants: Dict[str, ModelVariant] = {}
        self.active_test: Optional[str] = None
        self.routing_strategy: str = "random"  # 'random', 'hash', 'sticky'
        self.enabled: bool = False

    def add_variant(
        self,
        name: str,
        model: object,
        traffic_percentage: float,
        version: str = "unknown",
        stage: str = "control",
    ):
        """
        Add a model variant to the A/B test.

        Args:
            name: Variant identifier (e.g., 'model_v1', 'model_v2')
            model: The model object
            traffic_percentage: Percentage of traffic (0-100)
            version: Model version string
            stage: Stage identifier (control, treatment, champion, challenger)
        """
        if traffic_percentage < 0 or traffic_percentage > 100:
            raise ValueError("traffic_percentage must be between 0 and 100")

        self.variants[name] = ModelVariant(
            name=name,
            model=model,
            traffic_percentage=traffic_percentage,
            version=version,
            stage=stage,
        )
        print(
            f"Added variant '{name}' (version: {version}, stage: {stage}, "
            f"traffic: {traffic_percentage}%)"
        )

    def remove_variant(self, name: str):
        """Remove a variant from the test."""
        if name in self.variants:
            del self.variants[name]
            print(f"Removed variant '{name}'")

    def set_routing_strategy(self, strategy: str):
        """
        Set the routing strategy for A/B tests.

        Args:
            strategy: 'random', 'hash', or 'sticky'
                - random: Random distribution based on traffic percentage
                - hash: Hash-based routing using user/request ID
                - sticky: Session-based routing (requires session ID)
        """
        if strategy not in ["random", "hash", "sticky"]:
            print(f"Invalid strategy '{strategy}', defaulting to 'random'")
            strategy = "random"
        self.routing_strategy = strategy
        print(f"Routing strategy set to: {strategy}")

    def select_variant(
        self, user_id: Optional[str] = None, session_id: Optional[str] = None
    ) -> Optional[ModelVariant]:
        """
        Select a model variant based on routing strategy.

        Args:
            user_id: User identifier for hash-based routing
            session_id: Session identifier for sticky routing

        Returns:
            Selected ModelVariant or None if no variants available
        """
        if not self.variants:
            return None

        # Normalize traffic percentages
        total_traffic = sum(v.traffic_percentage for v in self.variants.values())
        if total_traffic == 0:
            return None

        # Random routing
        if self.routing_strategy == "random":
            rand_value = random.uniform(0, total_traffic)
            cumulative = 0
            for variant in self.variants.values():
                cumulative += variant.traffic_percentage
                if rand_value <= cumulative:
                    return variant
            return list(self.variants.values())[-1]

        # Hash-based routing
        elif self.routing_strategy == "hash":
            if not user_id:
                # Fallback to random if no user_id
                return self.select_variant()

            # Hash user_id to get consistent routing
            hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            bucket = (hash_value % 100) + 1  # 1-100

            cumulative = 0
            for variant in self.variants.values():
                cumulative += variant.traffic_percentage
                if bucket <= cumulative:
                    return variant
            return list(self.variants.values())[-1]

        # Sticky routing (session-based)
        elif self.routing_strategy == "sticky":
            if not session_id:
                # Fallback to random if no session_id
                return self.select_variant()

            # Hash session_id for consistent routing within session
            hash_value = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
            bucket = (hash_value % 100) + 1

            cumulative = 0
            for variant in self.variants.values():
                cumulative += variant.traffic_percentage
                if bucket <= cumulative:
                    return variant
            return list(self.variants.values())[-1]

        return None

    def get_variant_stats(self) -> Dict:
        """Get statistics about current variants."""
        return {
            "enabled": self.enabled,
            "active_variants": len(self.variants),
            "routing_strategy": self.routing_strategy,
            "variants": [
                {
                    "name": v.name,
                    "version": v.version,
                    "stage": v.stage,
                    "traffic_percentage": v.traffic_percentage,
                }
                for v in self.variants.values()
            ],
        }

    def update_traffic_split(self, traffic_config: Dict[str, float]):
        """
        Update traffic split for variants.

        Args:
            traffic_config: Dict mapping variant names to traffic percentages
                Example: {'model_v1': 90, 'model_v2': 10}
        """
        total = sum(traffic_config.values())
        if abs(total - 100) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Traffic percentages must sum to 100, got {total}")

        for name, percentage in traffic_config.items():
            if name in self.variants:
                self.variants[name].traffic_percentage = percentage
                print(f"Updated '{name}' traffic to {percentage}%")
            else:
                print(f"Warning: Variant '{name}' not found")

    def enable_test(self, test_name: str):
        """Enable an A/B test."""
        self.active_test = test_name
        print(f"Enabled A/B test: {test_name}")

    def disable_test(self):
        """Disable the active A/B test."""
        if self.active_test:
            print(f"Disabled A/B test: {self.active_test}")
            self.active_test = None

    def is_test_active(self) -> bool:
        """Check if an A/B test is currently active."""
        return self.active_test is not None and len(self.variants) > 0


# Global A/B test manager instance
ab_test_manager = ABTestManager()


def configure_ab_test_from_env():
    """Configure A/B testing from environment variables."""
    # Check if A/B testing is enabled
    ab_testing_enabled = os.getenv("AB_TESTING_ENABLED", "false").lower() == "true"

    if not ab_testing_enabled:
        print("A/B testing is disabled")
        return

    # Get routing strategy
    strategy = os.getenv("AB_ROUTING_STRATEGY", "random")
    ab_test_manager.set_routing_strategy(strategy)

    # Get traffic split configuration
    # Format: VARIANT_NAME:PERCENTAGE,VARIANT_NAME:PERCENTAGE
    # Example: model_v1:90,model_v2:10
    traffic_config_str = os.getenv("AB_TRAFFIC_CONFIG", "")

    if traffic_config_str:
        try:
            traffic_config = {}
            for pair in traffic_config_str.split(","):
                name, percentage = pair.split(":")
                traffic_config[name.strip()] = float(percentage.strip())

            print(f"Configured A/B test traffic split: {traffic_config}")
            return traffic_config
        except Exception as e:
            print(f"Error parsing AB_TRAFFIC_CONFIG: {e}")
            return None

    return None
