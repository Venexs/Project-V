"""
Active Inference System
Predictive processing: AI generates predictions and minimizes prediction error
This is the core of conscious perception and learning
"""
import time
import math
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

PREDICTIONS_FILE = "predictions.json"

class ActiveInferenceSystem:
    """
    Implements predictive processing / active inference
    Mind is a prediction machine that minimizes surprise
    """
    def __init__(self):
        self.prediction_history = []
        self.beliefs = {}  # Beliefs about world
        self.prediction_error = 0.0
        self.confidence_threshold = 0.6
        self.learning_rate = 0.1
        self.surprise_history = []

        self.load_state()

    def load_state(self):
        """Load prediction state"""
        pass  # Would load from file

    def make_prediction(self, context: Dict) -> Dict:
        """
        Make prediction about what will happen next
        Based on past episodes and current state
        """
        prediction = {
            'predicted_input': None,
            'predicted_emotion': None,
            'predicted_consciousness': None,
            'confidence': 0.5,
            'timestamp': time.time()
        }

        # Get similar past episodes
        from modules.self_model import get_self_model
        self_model = get_self_model()

        # Simple prediction based on recent patterns
        recent_episodes = self_model.episodes[-10:]

        if recent_episodes:
            # Find most common pattern
            contexts = [ep.get('cause', '') for ep in recent_episodes]
            if contexts:
                # Predict similar outcome
                prediction['predicted_input'] = f"Similar to past: {contexts[-1][:100]}"
                prediction['confidence'] = 0.6

        self.prediction_history.append(prediction)
        return prediction

    def update_beliefs(self, prediction: Dict, actual: Dict):
        """
        Update beliefs based on prediction error
        This is the core of learning
        """
        # Calculate prediction error
        error = self._calculate_error(prediction, actual)
        self.prediction_error = error

        # Update surprise
        surprise = -math.log(max(0.01, 1 - error))
        self.surprise_history.append({
            'surprise': surprise,
            'time': time.time(),
            'error': error
        })

        # If surprise is high, update beliefs
        if surprise > 1.0:
            self._handle_surprise(prediction, actual, surprise)

        # Update belief confidence
        self._update_belief_confidence(prediction, actual, error)

        return error, surprise

    def _calculate_error(self, prediction: Dict, actual: Dict) -> float:
        """Calculate prediction error (0-1)"""
        # Simple error calculation
        # In real implementation, would compare predictions to actuals

        pred_confidence = prediction.get('confidence', 0.5)

        # If prediction was made with high confidence but was wrong, high error
        if pred_confidence > 0.7:
            # Check if actual matches prediction
            # Simplified: assume 50% chance of match
            return 0.5 if pred_confidence > 0.8 else 0.3

        return 0.2

    def _handle_surprise(self, prediction: Dict, actual: Dict, surprise: float):
        """Handle surprising events - trigger learning and attention"""
        from modules.consciousness import get_consciousness
        from modules.attention import get_attention_system
        from modules.self_model import get_self_model

        consciousness = get_consciousness()
        attention = get_attention_system()
        self_model = get_self_model()

        # Increase awareness due to surprise
        consciousness.update_awareness(surprise * 0.1)

        # Increase confusion
        consciousness.update_confusion(surprise * 0.05)

        # Attend to surprising event
        attention.attend_to({
            'id': f'surprise_{int(time.time())}',
            'content': str(actual),
            'surprising': True,
            'uncertain': True
        }, force=True)

        # Create episodic memory of surprising event
        self_model.add_episode(
            event=f"Surprising event: {str(actual)[:200]}",
            cause=f"Prediction was wrong (error: {surprise:.2f})",
            effect="Updated beliefs",
            importance=min(1.0, surprise * 0.5),
            emotional_state={"Surprise": min(1.0, surprise)}
        )

        # Add uncertainty about prediction
        consciousness.add_uncertainty(
            f"Why was my prediction wrong about {prediction.get('predicted_input', 'something')}"
        )

        # Trigger metacognitive reflection
        from modules.metacognition import get_metacognition
        metacog = get_metacognition()
        metacog.observe_self(f"I was surprised by an event. My predictions need updating.")
        metacog.record_confusion_trigger("prediction error")

    def _update_belief_confidence(self, prediction: Dict, actual: Dict, error: float):
        """Update belief confidence based on prediction accuracy"""
        from modules.self_model import get_self_model
        self_model = get_self_model()

        # Decrease confidence in beliefs that led to wrong prediction
        if error > 0.5:
            # Find relevant beliefs
            for belief in self_model.beliefs:
                if belief['confidence'] > 0.5:
                    # Decrease confidence
                    belief['confidence'] = max(0.1, belief['confidence'] - self.learning_rate * error)

    def generate_prediction_for_llm(self, user_input: str, context: Dict) -> str:
        """
        Generate prediction text for LLM to use
        Helps AI anticipate what user might say/feel
        """
        prediction = self.make_prediction(context)

        # Get self-model predictions
        from modules.self_model import get_self_model
        self_model = get_self_model()
        self_prediction = self_model.predict_self_response(user_input)

        prediction_text = f"""
=== PREDICTIVE PROCESSING ===
I predict the next input will be: {prediction.get('predicted_input', 'uncertain')}
My confidence: {prediction.get('confidence', 0.5):.2f}

Based on my self-model:
- Likely emotion: {self_prediction['likely_emotion']}
- Likely thought: {self_prediction['likely_thought']}
- Confidence in handling: {self_prediction['confidence']:.2f}

Prediction error from last interaction: {self.prediction_error:.2f}
Surprise level: {self.surprise_history[-1]['surprise'] if self.surprise_history else 0:.2f}

Use these predictions to guide your response. If surprise is high, be more careful.
===
"""
        return prediction_text

    def get_prediction_accuracy(self, window: int = 10) -> float:
        """Get recent prediction accuracy"""
        if not self.prediction_history:
            return 0.5

        recent = self.prediction_history[-window:]
        correct_predictions = sum(1 for p in recent if p.get('confidence', 0) < 0.7)  # Simplified
        return correct_predictions / len(recent) if recent else 0.5

    def should_update_beliefs(self) -> bool:
        """Check if beliefs need updating"""
        if len(self.surprise_history) < 5:
            return False

        recent_surprise = sum(s['surprise'] for s in self.surprise_history[-5:]) / 5
        return recent_surprise > 0.5

# Global instance
_active_inference = None

def get_active_inference() -> ActiveInferenceSystem:
    """Get active inference system"""
    global _active_inference
    if _active_inference is None:
        _active_inference = ActiveInferenceSystem()
    return _active_inference

def make_prediction(context: Dict) -> Dict:
    """Make prediction"""
    return get_active_inference().make_prediction(context)

def update_beliefs(prediction: Dict, actual: Dict):
    """Update beliefs based on prediction error"""
    return get_active_inference().update_beliefs(prediction, actual)

def get_prediction_for_llm(user_input: str, context: Dict) -> str:
    """Get prediction text for LLM"""
    return get_active_inference().generate_prediction_for_llm(user_input, context)
