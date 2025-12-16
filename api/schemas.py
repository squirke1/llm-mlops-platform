"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field, field_validator


class ChurnPredictionRequest(BaseModel):
    """Request schema for churn prediction."""

    tenure_months: int = Field(..., ge=0, le=100, description="Customer tenure in months")
    monthly_charges: float = Field(..., ge=0, le=500, description="Monthly charges in dollars")
    total_charges: float = Field(..., ge=0, le=20000, description="Total charges in dollars")
    contract_type: str = Field(
        ..., description="Contract type (Month-to-month, One year, Two year)"
    )
    num_support_tickets: int = Field(..., ge=0, le=50, description="Number of support tickets")

    @field_validator("contract_type")
    @classmethod
    def validate_contract_type(cls, v):
        """Validate contract type is one of allowed values."""
        allowed = ["Month-to-month", "One year", "Two year"]
        if v not in allowed:
            raise ValueError(f"contract_type must be one of {allowed}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tenure_months": 24,
                "monthly_charges": 79.99,
                "total_charges": 1919.76,
                "contract_type": "Month-to-month",
                "num_support_tickets": 3,
            }
        }


class ChurnPredictionResponse(BaseModel):
    """Response schema for churn prediction."""

    prediction: int = Field(..., description="Churn prediction (0=No, 1=Yes)")
    probability: float = Field(..., ge=0, le=1, description="Churn probability")
    model_variant: str = Field(default="default", description="Model variant used for prediction")
    model_version: str = Field(default="unknown", description="Model version")

    class Config:
        json_schema_extra = {
            "example": {
                "prediction": 1,
                "probability": 0.73,
                "model_variant": "production",
                "model_version": "production",
            }
        }


class HealthResponse(BaseModel):
    """Response schema for health check."""

    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    version: str = Field(..., description="API version")
    ab_testing_enabled: bool = Field(default=False, description="Whether A/B testing is active")
    feature_store_available: bool = Field(
        default=False, description="Whether feature store is available"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "model_loaded": True,
                "version": "1.0.0",
                "ab_testing_enabled": True,
                "feature_store_available": True,
            }
        }


class CustomerIdRequest(BaseModel):
    """Request schema for feature store-based prediction."""

    customer_id: str = Field(..., description="Customer ID for feature retrieval")

    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "CUST_000123",
            }
        }


class FeatureStoreHealthResponse(BaseModel):
    """Response schema for feature store health check."""

    available: bool = Field(..., description="Whether feature store is available")
    online_store_healthy: bool = Field(
        default=False, description="Whether online store is accessible"
    )
    feature_views_count: int = Field(default=0, description="Number of registered feature views")
    feature_services_count: int = Field(
        default=0, description="Number of registered feature services"
    )
    error: str = Field(default=None, description="Error message if unhealthy")

    class Config:
        json_schema_extra = {
            "example": {
                "available": True,
                "online_store_healthy": True,
                "feature_views_count": 3,
                "feature_services_count": 2,
                "error": None,
            }
        }
