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

    class Config:
        json_schema_extra = {"example": {"prediction": 1, "probability": 0.73}}


class HealthResponse(BaseModel):
    """Response schema for health check."""

    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    version: str = Field(..., description="API version")

    class Config:
        json_schema_extra = {
            "example": {"status": "healthy", "model_loaded": True, "version": "1.0.0"}
        }
