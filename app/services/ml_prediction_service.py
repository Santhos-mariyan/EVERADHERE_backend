"""
Machine Learning Service for Patient Recovery Prediction
========================================================

This module provides ML models for predicting patient recovery progress
based on medication adherence, test scores, and other health metrics.
"""

import logging
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import numpy as np
import pickle
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Model storage directory
MODELS_DIR = Path("ml_models")
MODELS_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODELS_DIR / "recovery_model.pkl"
SCALER_PATH = MODELS_DIR / "recovery_scaler.pkl"


class RecoveryPredictionModel:
    """
    ML Model for predicting patient recovery progress.
    
    Features used:
    - medication_adherence_rate: Percentage of medications taken on time (0-100)
    - avg_test_score: Average score from all patient tests (0-100)
    - test_score_trend: Trend in recent test scores (upward=positive, downward=negative)
    - days_in_treatment: Number of days patient has been in treatment
    - medication_count: Number of active medications
    
    IMPORTANT: Always expects exactly 5 features in this order!
    """
    
    # Fixed number of features
    N_FEATURES = 5
    FEATURE_NAMES = [
        'medication_adherence',
        'avg_test_score', 
        'test_score_trend',
        'days_in_treatment',
        'medication_count'
    ]
    
    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self._load_model_if_exists()
    
    def _load_model_if_exists(self):
        """Load pre-trained model if it exists"""
        try:
            if MODEL_PATH.exists() and SCALER_PATH.exists():
                try:
                    with open(MODEL_PATH, 'rb') as f:
                        loaded_model = pickle.load(f)
                    with open(SCALER_PATH, 'rb') as f:
                        loaded_scaler = pickle.load(f)
                    
                    # Verify loaded model and scaler have matching features
                    # Create dummy data to test
                    test_data = np.array([[0, 0, 0, 0, 0]])
                    test_scaled = loaded_scaler.transform(test_data)
                    
                    if test_scaled.shape[1] == self.N_FEATURES:
                        self.model = loaded_model
                        self.scaler = loaded_scaler
                        self.is_trained = True
                        logger.info("✅ Loaded pre-trained recovery prediction model")
                    else:
                        logger.warning(f"⚠️ Loaded model has {test_scaled.shape[1]} features, expected {self.N_FEATURES}. Rebuilding...")
                        self._delete_corrupted_model()
                        self._initialize_default_model()
                except Exception as load_error:
                    logger.warning(f"⚠️ Could not load corrupted model: {load_error}. Rebuilding...")
                    self._delete_corrupted_model()
                    self._initialize_default_model()
            else:
                logger.info("📊 No pre-trained model found, using default model")
                self._initialize_default_model()
        except Exception as e:
            logger.error(f"Error in _load_model_if_exists: {e}")
            self._initialize_default_model()
    
    def _delete_corrupted_model(self):
        """Delete corrupted model files"""
        try:
            if MODEL_PATH.exists():
                MODEL_PATH.unlink()
                logger.info(f"🗑️ Deleted corrupted model file: {MODEL_PATH}")
            if SCALER_PATH.exists():
                SCALER_PATH.unlink()
                logger.info(f"🗑️ Deleted corrupted scaler file: {SCALER_PATH}")
        except Exception as e:
            logger.error(f"Error deleting corrupted model files: {e}")
    
    def _initialize_default_model(self):
        """Initialize model with default training data if not trained"""
        try:
            # Generate synthetic training data for initial model
            X_train, y_train = self._generate_synthetic_training_data()
            self.train(X_train, y_train)
            logger.info("✅ Initialized default recovery prediction model with synthetic data")
        except Exception as e:
            logger.error(f"Error initializing default model: {e}")
    
    def _generate_synthetic_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic training data for initial model training.
        This helps the model start with reasonable predictions.
        """
        n_samples = 200
        
        # Feature ranges based on realistic scenarios
        medication_adherence = np.random.uniform(30, 100, n_samples)
        avg_test_score = np.random.uniform(20, 95, n_samples)
        test_score_trend = np.random.uniform(-10, 20, n_samples)  # Score change per month
        days_in_treatment = np.random.uniform(30, 365, n_samples)
        medication_count = np.random.randint(1, 6, n_samples)
        
        X_train = np.column_stack([
            medication_adherence,
            avg_test_score,
            test_score_trend,
            days_in_treatment,
            medication_count
        ])
        
        # Recovery score is calculated based on features
        # Higher adherence + higher test scores + positive trend = higher recovery
        y_train = (
            medication_adherence * 0.35 +  # Adherence weight
            avg_test_score * 0.35 +        # Test score weight
            test_score_trend * 2 +         # Trend weight (amplified)
            (np.minimum(days_in_treatment, 180) / 180 * 20) +  # Time in treatment (cap at 180 days)
            (5 - medication_count) * 2    # Fewer medications = better (recovery goal)
        )
        
        # Normalize to 0-100 scale
        y_train = np.clip(y_train, 0, 100)
        
        return X_train, y_train
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray):
        """Train the recovery prediction model"""
        try:
            X_scaled = self.scaler.fit_transform(X_train)
            self.model.fit(X_scaled, y_train)
            self.is_trained = True
            self._save_model()
            logger.info("✅ Recovery prediction model trained successfully")
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    def _save_model(self):
        """Save trained model to disk"""
        try:
            with open(MODEL_PATH, 'wb') as f:
                pickle.dump(self.model, f)
            with open(SCALER_PATH, 'wb') as f:
                pickle.dump(self.scaler, f)
            logger.info("💾 Recovery prediction model saved to disk")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def predict_recovery_score(
        self,
        medication_adherence_rate: float,
        avg_test_score: float,
        test_score_trend: float,
        days_in_treatment: int,
        medication_count: int,
        has_medications: bool = False,
        has_test_results: bool = False
    ) -> Dict:
        """
        Predict recovery score for a patient.
        
        Args:
            medication_adherence_rate: Percentage of medications taken (0-100)
            avg_test_score: Average test score (0-100)
            test_score_trend: Trend in scores - positive means improving
            days_in_treatment: Days since patient started treatment
            medication_count: Number of active medications
            has_medications: Whether patient has medication data
            has_test_results: Whether patient has test result data
        
        Returns:
            Dictionary with recovery score and interpretation
            
        CRITICAL: Always uses exactly 5 features!
        """
        try:
            # Validate and normalize inputs to proper ranges
            medication_adherence_rate = float(max(0, min(100, medication_adherence_rate)))
            avg_test_score = float(max(0, min(100, avg_test_score)))
            test_score_trend = float(test_score_trend)  # Can be negative or positive
            days_in_treatment = int(max(1, days_in_treatment))
            medication_count = int(max(1, medication_count))
            
            # Prepare features - EXACTLY 5 features in this specific order
            X = np.array([[
                medication_adherence_rate,    # Feature 1
                avg_test_score,                # Feature 2
                test_score_trend,              # Feature 3
                days_in_treatment,             # Feature 4
                medication_count               # Feature 5
            ]], dtype=np.float64)
            
            # Verify we have exactly 5 features
            if X.shape[1] != self.N_FEATURES:
                logger.error(f"Feature mismatch: Expected {self.N_FEATURES} features, got {X.shape[1]}")
                raise ValueError(f"Expected {self.N_FEATURES} features, got {X.shape[1]}")
            
            # Transform using scaler
            X_scaled = self.scaler.transform(X)
            
            # Make prediction
            recovery_score = self.model.predict(X_scaled)[0]
            recovery_score = float(np.clip(recovery_score, 0, 100))
            
            # Get feature importance
            importances = self.model.feature_importances_
            
            # Calculate interpretation
            interpretation = self._get_recovery_interpretation(recovery_score)
            
            # Get recommendations (only for available data)
            recommendations = self._get_recommendations(
                medication_adherence_rate,
                avg_test_score,
                test_score_trend,
                has_medications=has_medications,
                has_test_results=has_test_results
            )
            
            # Calculate confidence level based on data quality and availability
            confidence_level = self._calculate_confidence_level(
                days_in_treatment,
                has_medications,
                has_test_results,
                medication_adherence_rate
            )
            
            return {
                'recovery_score': round(recovery_score, 2),
                'score_percentage': f"{round(recovery_score, 1)}%",
                'status': interpretation['status'],
                'message': interpretation['message'],
                'recommendations': recommendations,
                'confidence_level': confidence_level,
                'data_points': {
                    'medication_adherence': round(medication_adherence_rate, 1),
                    'avg_test_score': round(avg_test_score, 1),
                    'test_score_trend': round(test_score_trend, 2),
                    'days_in_treatment': int(days_in_treatment),
                    'medication_count': int(medication_count)
                },
                'feature_importance': {
                    name: round(float(importance), 4)
                    for name, importance in zip(self.FEATURE_NAMES, importances)
                }
            }
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            raise
    
    def _calculate_confidence_level(
        self,
        days_in_treatment: int,
        has_medications: bool,
        has_test_results: bool,
        medication_adherence: float
    ) -> str:
        """
        Calculate confidence level based on:
        - Data availability (medications + tests)
        - Duration in treatment
        - Data quality (adherence level)
        """
        # Check data availability
        data_points = 0
        if has_medications:
            data_points += 1
        if has_test_results:
            data_points += 1
        
        # If missing any data type, confidence is lower
        if data_points < 2:
            return 'LOW'
        
        # Good data, check duration and quality
        if days_in_treatment >= 60:
            # Long-term data = HIGH confidence
            return 'HIGH'
        elif days_in_treatment >= 30:
            # Medium-term data
            # Consider adherence quality
            if medication_adherence >= 80:
                return 'HIGH'  # Good data quality
            else:
                return 'MEDIUM'
        else:
            # Short-term data = MEDIUM at best
            return 'MEDIUM' if medication_adherence >= 75 else 'LOW'
    
    def _get_recovery_interpretation(self, score: float) -> Dict[str, str]:
        """Get interpretation text based on recovery score"""
        if score >= 80:
            return {
                'status': 'EXCELLENT',
                'message': '✅ Excellent recovery progress! Patient is responding very well to treatment.'
            }
        elif score >= 60:
            return {
                'status': 'GOOD',
                'message': '👍 Good recovery progress. Patient is on track with treatment.'
            }
        elif score >= 40:
            return {
                'status': 'MODERATE',
                'message': '⚠️ Moderate progress. Patient needs additional support or medication adjustments.'
            }
        elif score >= 20:
            return {
                'status': 'POOR',
                'message': '⚠️ Poor progress. Recommend doctor review and treatment plan adjustment.'
            }
        else:
            return {
                'status': 'CRITICAL',
                'message': '🚨 Critical concern. Immediate doctor consultation recommended.'
            }
    
    def _get_recommendations(
        self,
        adherence: float,
        avg_score: float,
        trend: float,
        has_medications: bool = False,
        has_test_results: bool = False
    ) -> list:
        """Generate personalized recommendations based on patient data
        
        IMPORTANT: Only shows recommendations for data that actually exists:
        - Medication recommendations ONLY if patient has medications
        - Test score recommendations ONLY if patient has test results
        - Trend recommendations ONLY if patient has test results
        """
        recommendations = []
        
        # ============================================
        # MEDICATION RECOMMENDATIONS (if has meds)
        # ============================================
        if has_medications:
            if adherence < 60:
                # CRITICAL: Very low adherence
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Medication Adherence',
                    'recommendation': f'Critical: Adherence only at {adherence:.1f}%. Set up automated reminders and follow-up calls immediately.',
                    'impact': 'Low adherence severely impacts recovery',
                    'show_background': True
                })
            elif adherence < 80:
                # NEEDS IMPROVEMENT: Moderate adherence
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Medication Adherence',
                    'recommendation': f'Good progress: Adherence at {adherence:.1f}%. Work towards 90%+ for optimal results.',
                    'impact': 'Improving adherence can significantly boost recovery',
                    'show_background': True
                })
            else:
                # EXCELLENT: High adherence (80-100%)
                recommendations.append({
                    'priority': 'EXCELLENT',
                    'category': 'Medication Adherence',
                    'recommendation': f'Excellent! Adherence at {adherence:.1f}%. Keep up this outstanding commitment to treatment.',
                    'impact': 'Your dedication to medication compliance is driving recovery',
                    'show_background': False  # No background color for excellent
                })
        
        # ============================================
        # TEST SCORE RECOMMENDATIONS (if has tests)
        # ============================================
        if has_test_results:
            # Depression severity levels (Hamilton Depression Scale):
            # 0-7: Normal, 8-13: Mild, 14-18: Moderate, 19-22: Severe, 23-30: Very Severe
            if avg_score >= 23:
                # VERY SEVERE DEPRESSION
                recommendations.append({
                    'priority': 'CRITICAL',
                    'category': 'Test Performance',
                    'recommendation': f'Critical: Very severe depression (score: {avg_score:.1f}/30). Immediate psychiatric intervention required.',
                    'impact': 'Urgent medical attention needed - risk of severe complications',
                    'show_background': True
                })
            elif avg_score >= 19:
                # SEVERE DEPRESSION
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Test Performance',
                    'recommendation': f'Severe depression (score: {avg_score:.1f}/30). Intensive treatment and close monitoring required.',
                    'impact': 'Immediate intervention needed to prevent further deterioration',
                    'show_background': True
                })
            elif avg_score >= 14:
                # MODERATE DEPRESSION
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Test Performance',
                    'recommendation': f'Moderate depression (score: {avg_score:.1f}/30). Consider therapy and medication adjustment.',
                    'impact': 'Enhanced treatment can significantly improve quality of life',
                    'show_background': True
                })
            elif avg_score >= 8:
                # MILD DEPRESSION
                recommendations.append({
                    'priority': 'LOW',
                    'category': 'Test Performance',
                    'recommendation': f'Mild depression (score: {avg_score:.1f}/30). Monitor closely and consider supportive interventions.',
                    'impact': 'Early intervention can prevent progression',
                    'show_background': False
                })
            else:
                # NORMAL (0-7)
                recommendations.append({
                    'priority': 'EXCELLENT',
                    'category': 'Test Performance',
                    'recommendation': f'Normal range (score: {avg_score:.1f}/30). Excellent mental health status - maintain current wellness practices.',
                    'impact': 'Strong mental health foundation - continue positive habits',
                    'show_background': False
                })
            
            # ============================================
            # TREND RECOMMENDATIONS (only if has tests)
            # ============================================
            if trend > 2:
                # SCORES INCREASING: Depression worsening
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Recovery Trend',
                    'recommendation': f'Alert: Depression symptoms worsening (trend: +{trend:.2f}). Immediate intervention needed.',
                    'impact': 'Early intervention prevents further deterioration',
                    'show_background': True
                })
            elif trend > 0:
                # SCORES SLIGHTLY INCREASING: Mild worsening
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Recovery Trend',
                    'recommendation': f'Caution: Slight increase in symptoms (trend: +{trend:.2f}). Monitor closely.',
                    'impact': 'Close monitoring can prevent progression',
                    'show_background': False
                })
            elif trend < -2:
                # SCORES DECREASING: Significant improvement
                recommendations.append({
                    'priority': 'EXCELLENT',
                    'category': 'Recovery Trend',
                    'recommendation': f'Outstanding! Significant improvement in symptoms (trend: {trend:.2f}). Continue current treatment.',
                    'impact': 'Strong positive trajectory - patient is making excellent progress',
                    'show_background': False
                })
            elif trend < 0:
                # SCORES SLIGHTLY DECREASING: Mild improvement
                recommendations.append({
                    'priority': 'GOOD',
                    'category': 'Recovery Trend',
                    'recommendation': f'Good progress: Symptoms improving (trend: {trend:.2f}). Maintain current approach.',
                    'impact': 'Positive direction - continue supportive care',
                    'show_background': False
                })
            else:
                # STABLE
                recommendations.append({
                    'priority': 'INFO',
                    'category': 'Recovery Trend',
                    'recommendation': f'Stable symptoms (trend: {trend:.2f}). Continue monitoring and current treatment.',
                    'impact': 'Stability is positive - no immediate changes needed',
                    'show_background': False
                })
        
        # ============================================
        # INFO MESSAGES FOR MISSING DATA
        # ============================================
        if not has_medications and not has_test_results:
            # Brand new patient
            recommendations.append({
                'priority': 'INFO',
                'category': 'Data Collection',
                'recommendation': 'Patient is new. Start recording medications and test results to enable tracking.',
                'impact': 'Data collection is essential for generating insights',
                'show_background': False  # No background for info
            })
        elif not has_medications:
            # Has tests but no medications
            recommendations.append({
                'priority': 'INFO',
                'category': 'Data Collection',
                'recommendation': 'Start recording patient medications to enable adherence tracking.',
                'impact': 'Medication data will provide adherence-based recommendations',
                'show_background': False  # No background for info
            })
        elif not has_test_results:
            # Has medications but no tests
            recommendations.append({
                'priority': 'INFO',
                'category': 'Data Collection',
                'recommendation': 'Patient test results not yet recorded. Schedule first test to enable performance tracking.',
                'impact': 'Test data will provide performance and trend recommendations',
                'show_background': False  # No background for info
            })
        
        # If we have data but no recommendations generated, add general message
        if not recommendations:
            recommendations.append({
                'priority': 'LOW',
                'category': 'General',
                'recommendation': 'Patient is progressing well. Maintain current treatment plan.',
                'impact': 'Consistency is key to sustained recovery',
                'show_background': False  # No background for general info
            })
        
        return recommendations


# Global prediction model instance
_recovery_model: Optional[RecoveryPredictionModel] = None


def get_recovery_model() -> RecoveryPredictionModel:
    """Get or create the recovery prediction model"""
    global _recovery_model
    if _recovery_model is None:
        _recovery_model = RecoveryPredictionModel()
    return _recovery_model


def predict_patient_recovery(
    patient_id: int,
    medication_data: list,
    test_results: list
) -> Dict:
    """
    Predict patient recovery based on historical data.
    NEW PATIENTS: Shows all 0s until they have data.
    EXISTING PATIENTS: Shows ML predictions based on available data.
    
    Args:
        patient_id: Patient ID
        medication_data: List of medication objects with dates and taken status
        test_results: List of test result objects with scores and dates
    
    Returns:
        Dictionary with recovery prediction and recommendations
    """
    try:
        # Check if patient has ANY data
        has_medications = medication_data and len(medication_data) > 0
        has_test_results = test_results and len(test_results) > 0
        
        # If NEW PATIENT with no data - return default zero values
        if not has_medications and not has_test_results:
            logger.info(f"📊 New patient {patient_id}: No historical data, returning default zeros")
            return {
                'patient_id': patient_id,
                'recovery_score': 0.0,
                'score_percentage': '0%',
                'status': 'NOT_STARTED',
                'message': '⏳ Patient is new. Recovery prediction will be available once treatment data is recorded.',
                'confidence_level': 'LOW',
                'data_points': {
                    'medication_adherence': 0.0,
                    'avg_test_score': 0.0,
                    'test_score_trend': 0.0,
                    'days_in_treatment': 0,
                    'medication_count': 0
                },
                'feature_importance': {
                    'medication_adherence': 0.0,
                    'avg_test_score': 0.0,
                    'test_score_trend': 0.0,
                    'days_in_treatment': 0.0,
                    'medication_count': 0.0
                },
                'recommendations': [
                    {
                        'priority': 'INFO',
                        'category': 'Getting Started',
                        'recommendation': 'Patient is new. Start recording medications and test results to enable recovery predictions.',
                        'impact': 'Data collection is essential for tracking progress'
                    }
                ],
                'predicted_at': datetime.utcnow().isoformat()
            }
        
        # Calculate medication adherence
        medication_adherence = calculate_medication_adherence(medication_data)
        
        # Calculate test score metrics
        avg_test_score, test_score_trend = calculate_test_score_metrics(test_results)
        
        # Calculate days in treatment
        days_in_treatment = calculate_days_in_treatment(medication_data, test_results)
        
        # Count active medications
        medication_count = len(medication_data) if medication_data else 0
        
        # Get prediction from ML model
        model = get_recovery_model()
        prediction = model.predict_recovery_score(
            medication_adherence_rate=medication_adherence,
            avg_test_score=avg_test_score,
            test_score_trend=test_score_trend,
            days_in_treatment=days_in_treatment,
            medication_count=medication_count,
            has_medications=has_medications,
            has_test_results=has_test_results
        )
        
        prediction['patient_id'] = patient_id
        prediction['predicted_at'] = datetime.utcnow().isoformat()
        
        return prediction
    except Exception as e:
        logger.error(f"Error predicting recovery for patient {patient_id}: {e}")
        raise


def calculate_medication_adherence(medication_data: list) -> float:
    """
    Calculate medication adherence percentage.
    
    Adherence = (Medications taken / Total medications) * 100
    """
    if not medication_data:
        return 0.0
    
    try:
        taken_count = sum(1 for med in medication_data if med.is_taken)
        total_count = len(medication_data)
        adherence = (taken_count / total_count) * 100 if total_count > 0 else 0.0
        return float(adherence)
    except Exception as e:
        logger.error(f"Error calculating medication adherence: {e}")
        return 0.0


def calculate_test_score_metrics(test_results: list) -> Tuple[float, float]:
    """
    Calculate average test score and trend.
    
    Returns:
        Tuple of (average_score, trend)
        Trend = recent score - older score (positive means improving)
    """
    if not test_results:
        return 0.0, 0.0
    
    try:
        # Sort by date
        sorted_results = sorted(test_results, key=lambda x: x.date)
        scores = [result.score for result in sorted_results]
        
        # Average score
        avg_score = float(sum(scores) / len(scores)) if scores else 0.0
        
        # Trend calculation (slope of recent vs older)
        if len(scores) >= 2:
            # Compare last test with average of older tests
            recent_score = scores[-1]
            older_avg = sum(scores[:-1]) / (len(scores) - 1)
            trend = float(recent_score - older_avg)
        else:
            trend = 0.0
        
        return avg_score, trend
    except Exception as e:
        logger.error(f"Error calculating test score metrics: {e}")
        return 0.0, 0.0


def calculate_days_in_treatment(medication_data: list, test_results: list) -> int:
    """
    Calculate number of days patient has been in treatment.
    Based on the earliest date from medications or test results.
    """
    try:
        earliest_date = None
        
        # Check medications
        if medication_data:
            med_dates = [med.prescribed_date for med in medication_data if med.prescribed_date]
            if med_dates:
                earliest_date = min(med_dates)
        
        # Check test results
        if test_results:
            test_dates = [test.date for test in test_results if test.date]
            if test_dates:
                test_earliest = min(test_dates)
                if earliest_date is None:
                    earliest_date = test_earliest
                else:
                    earliest_date = min(earliest_date, test_earliest)
        
        if earliest_date:
            days = (datetime.utcnow() - earliest_date).days
            return max(1, int(days))  # At least 1 day
        
        return 0
    except Exception as e:
        logger.error(f"Error calculating days in treatment: {e}")
        return 0


# Initialize model on module load
try:
    _recovery_model = RecoveryPredictionModel()
    logger.info("✅ ML Prediction service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ML Prediction service: {e}")
