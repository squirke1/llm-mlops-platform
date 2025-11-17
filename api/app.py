"""FastAPI application for churn prediction."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import ChurnPredictionRequest, ChurnPredictionResponse, HealthResponse
from src.model import ChurnModel

# Initialize FastAPI app
app = FastAPI(
    title="Customer Churn Prediction API",
    description="REST API for predicting customer churn",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model variable
model = None


@app.on_event("startup")
async def load_model():
    """Load the trained model on startup."""
    global model
    model_path = Path("models/churn_model.pkl")
    
    if not model_path.exists():
        print(f"Warning: Model file not found at {model_path}")
        print("Please train the model first by running: python src/train.py")
        model = None
    else:
        try:
            model = ChurnModel.load(model_path)
            print(f"Model loaded successfully from {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            model = None


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Customer Churn Prediction API",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
        version="1.0.0"
    )


@app.post("/api/v1/predict", response_model=ChurnPredictionResponse, tags=["Prediction"])
async def predict_churn(request: ChurnPredictionRequest):
    """
    Predict customer churn probability.
    
    Args:
        request: ChurnPredictionRequest with customer features
        
    Returns:
        ChurnPredictionResponse with prediction and probability
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please train the model first."
        )
    
    try:
        # Prepare input data
        input_data = pd.DataFrame([{
            'tenure_months': request.tenure_months,
            'monthly_charges': request.monthly_charges,
            'total_charges': request.total_charges,
            'contract_type': request.contract_type,
            'num_support_tickets': request.num_support_tickets
        }])
        
        # Encode contract type (one-hot encoding matching training)
        input_encoded = pd.get_dummies(input_data, columns=['contract_type'], drop_first=True)
        
        # Ensure all columns from training are present
        expected_cols = ['tenure_months', 'monthly_charges', 'total_charges', 
                        'num_support_tickets', 'contract_type_One year', 'contract_type_Two year']
        
        for col in expected_cols:
            if col not in input_encoded.columns:
                input_encoded[col] = 0
        
        # Reorder columns to match training data
        input_encoded = input_encoded[expected_cols]
        
        # Make prediction
        prediction = model.predict(input_encoded)[0]
        
        # Get probability (use predict_proba if available)
        if hasattr(model.model, 'predict_proba'):
            probability = float(model.model.predict_proba(input_encoded)[0][1])
        else:
            probability = float(prediction)
        
        return ChurnPredictionResponse(
            prediction=int(prediction),
            probability=round(probability, 3)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
