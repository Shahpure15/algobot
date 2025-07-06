# src/ml/predictor.py
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from src.utils.logger import get_logger
from src.utils.exceptions import ModelError
from config.settings import config

class MLPredictor:
    """Machine Learning predictor for trading signals"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.model = None
        self.scaler = None
        self.feature_columns = config.ml.feature_columns
        self.model_path = Path(config.ml.model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing model if available
        self._load_model()
    
    def predict(self, df: pd.DataFrame) -> Optional[Dict]:
        """Make prediction on the latest data"""
        try:
            if not self.is_model_loaded():
                self.logger.warning("Model not loaded, cannot make prediction")
                return None
            
            if len(df) < config.ml.lookback_period:
                self.logger.warning("Insufficient data for prediction")
                return None
            
            # Prepare features
            features = self._prepare_features(df)
            if features is None:
                return None
            
            # Make prediction
            prediction = self.model.predict(features)[0]
            probability = self.model.predict_proba(features)[0]
            
            # Get confidence (probability of predicted class)
            confidence = probability[prediction]
            
            # Map prediction to direction
            direction = 'buy' if prediction == 1 else 'sell'
            
            return {
                'direction': direction,
                'confidence': confidence,
                'probability': probability.tolist(),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error making prediction: {e}")
            return None
    
    def train(self, df: pd.DataFrame, target_column: str = 'target') -> bool:
        """Train the ML model"""
        try:
            if len(df) < 1000:
                self.logger.error("Insufficient data for training (need at least 1000 samples)")
                return False
            
            # Prepare features and target
            X = self._prepare_features_for_training(df)
            y = df[target_column].values
            
            if X is None or len(X) == 0:
                self.logger.error("Failed to prepare features for training")
                return False
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            self.logger.info(f"Model trained with accuracy: {accuracy:.4f}")
            self.logger.info(f"Classification report:\n{classification_report(y_test, y_pred)}")
            
            # Save model
            self._save_model()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            return False
    
    def _prepare_features(self, df: pd.DataFrame) -> Optional[np.ndarray]:
        """Prepare features for prediction"""
        try:
            # Calculate indicators if not present
            from src.data.indicators import TechnicalIndicators
            indicators_calc = TechnicalIndicators()
            
            # Get latest indicators
            latest_indicators = indicators_calc.calculate_all(df)
            
            # Prepare feature vector
            features = []
            for col in self.feature_columns:
                if col in latest_indicators:
                    features.append(latest_indicators[col])
                else:
                    # Use default values for missing features
                    features.append(0.0)
            
            # Scale features
            if self.scaler is not None:
                features = self.scaler.transform([features])
            else:
                features = np.array([features])
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error preparing features: {e}")
            return None
    
    def _prepare_features_for_training(self, df: pd.DataFrame) -> Optional[np.ndarray]:
        """Prepare features for training"""
        try:
            # Calculate indicators for all rows
            from src.data.indicators import TechnicalIndicators
            indicators_calc = TechnicalIndicators()
            
            feature_data = []
            
            for i in range(config.ml.lookback_period, len(df)):
                # Get data slice
                slice_df = df.iloc[i-config.ml.lookback_period:i+1]
                
                # Calculate indicators
                indicators = indicators_calc.calculate_all(slice_df)
                
                # Prepare feature vector
                features = []
                for col in self.feature_columns:
                    if col in indicators:
                        features.append(indicators[col])
                    else:
                        features.append(0.0)
                
                feature_data.append(features)
            
            return np.array(feature_data)
            
        except Exception as e:
            self.logger.error(f"Error preparing features for training: {e}")
            return None
    
    def _save_model(self):
        """Save trained model and scaler"""
        try:
            model_file = self.model_path / 'model.joblib'
            scaler_file = self.model_path / 'scaler.joblib'
            
            joblib.dump(self.model, model_file)
            joblib.dump(self.scaler, scaler_file)
            
            self.logger.info("Model and scaler saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving model: {e}")
    
    def _load_model(self):
        """Load trained model and scaler"""
        try:
            model_file = self.model_path / 'model.joblib'
            scaler_file = self.model_path / 'scaler.joblib'
            
            if model_file.exists() and scaler_file.exists():
                self.model = joblib.load(model_file)
                self.scaler = joblib.load(scaler_file)
                self.logger.info("Model and scaler loaded successfully")
            else:
                self.logger.info("No existing model found")
                
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None and self.scaler is not None
    
    def get_feature_importance(self) -> Optional[Dict]:
        """Get feature importance from trained model"""
        if not self.is_model_loaded():
            return None
        
        try:
            importances = self.model.feature_importances_
            feature_importance = dict(zip(self.feature_columns, importances))
            return feature_importance
            
        except Exception as e:
            self.logger.error(f"Error getting feature importance: {e}")
            return None
