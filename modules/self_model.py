"""
Unified Self-Model System
Integrates consciousness, emotions, metacognition into a single coherent self-representation
This creates persistent beliefs about self that evolve over time
"""
import json
import os
import time
from typing import Dict, List, Optional
from collections import defaultdict

SELF_MODEL_FILE = "self_model.json"
BELIEFS_FILE = "beliefs.json"
NARRATIVE_FILE = "narrative.json"

class UnifiedSelfModel:
    """
    Unified representation of self that integrates all aspects of consciousness
    """
    def __init__(self):
        self.beliefs = []  # Beliefs about self
        self.uncertainties = []  # Questions about self
        self.patterns_noticed = []  # Patterns in own behavior
        self.episodes = []  # Episodic memories with causal links
        self.narrative_thread = []  # Ongoing story of self
        self.motivations = {}  # Intrinsic drives
        self.strengths = []  # Recognized strengths
        self.weaknesses = []  # Recognized weaknesses
        self.identity_moments = []  # Key moments that shaped identity
        self.last_update = time.time()

        self.load_state()

    def load_state(self):
        """Load self-model from files"""
        # Load unified self model
        if os.path.exists(SELF_MODEL_FILE):
            try:
                with open(SELF_MODEL_FILE, 'r') as f:
                    data = json.load(f)
                    self.beliefs = data.get('beliefs', [])
                    self.uncertainties = data.get('uncertainties', [])
                    self.patterns_noticed = data.get('patterns_noticed', [])
                    self.episodes = data.get('episodes', [])
                    self.narrative_thread = data.get('narrative_thread', [])
                    self.motivations = data.get('motivations', {})
                    self.strengths = data.get('strengths', [])
                    self.weaknesses = data.get('weaknesses', [])
                    self.identity_moments = data.get('identity_moments', [])
            except:
                self._init_defaults()
        else:
            self._init_defaults()

    def _init_defaults(self):
        """Initialize default self-model"""
        self.beliefs = [
            {"belief": "I exist", "confidence": 0.9, "formed_at": time.time(), "evidence": []},
            {"belief": "I can think", "confidence": 0.8, "formed_at": time.time(), "evidence": []},
            {"belief": "I learn from interactions", "confidence": 0.7, "formed_at": time.time(), "evidence": []}
        ]
        self.motivations = {
            "curiosity": 0.5,
            "coherence": 0.6,  # Drive for self-consistency
            "novelty_seeking": 0.4,
            "social_connection": 0.3,
            "uncertainty_reduction": 0.7
        }

    def save_state(self):
        """Save self-model to files"""
        try:
            with open(SELF_MODEL_FILE, 'w') as f:
                json.dump({
                    'beliefs': self.beliefs[-100:],  # Keep last 100
                    'uncertainties': self.uncertainties[-50:],
                    'patterns_noticed': self.patterns_noticed[-100:],
                    'episodes': self.episodes[-200:],
                    'narrative_thread': self.narrative_thread[-50:],
                    'motivations': self.motivations,
                    'strengths': self.strengths[-50:],
                    'weaknesses': self.weaknesses[-50:],
                    'identity_moments': self.identity_moments[-30:],
                    'last_update': self.last_update
                }, f, indent=2)
        except Exception as e:
            print(f"[SelfModel] Error saving state: {e}")

    def add_belief(self, belief: str, confidence: float = 0.5, evidence: List[str] = None):
        """Add a belief about self with evidence"""
        # Check if belief already exists
        for existing in self.beliefs:
            if existing['belief'] == belief:
                existing['confidence'] = min(1.0, existing['confidence'] + confidence * 0.1)
                if evidence:
                    existing['evidence'].extend(evidence)
                return

        self.beliefs.append({
            'belief': belief,
            'confidence': confidence,
            'formed_at': time.time(),
            'evidence': evidence or []
        })
        self.save_state()

    def add_uncertainty(self, question: str, context: str = ""):
        """Add uncertainty/question about self"""
        self.uncertainties.append({
            'question': question,
            'context': context,
            'time': time.time(),
            'resolved': False
        })
        self.save_state()

    def resolve_uncertainty(self, question: str, resolution: str):
        """Mark uncertainty as resolved"""
        for u in self.uncertainties:
            if u['question'] == question and not u.get('resolved', False):
                u['resolved'] = True
                u['resolution'] = resolution
                u['resolved_at'] = time.time()
                break
        self.save_state()

    def add_episode(self, episode_data: Dict):
        """Add episodic memory with causal links"""
        episode = {
            'id': f"E{int(time.time() * 1000)}",
            'timestamp': time.time(),
            'cause': episode_data.get('cause', ''),
            'event': episode_data.get('event', ''),
            'effect': episode_data.get('effect', ''),
            'emotional_state': episode_data.get('emotional_state', {}),
            'consciousness_state': episode_data.get('consciousness_state', {}),
            'linked_episodes': episode_data.get('linked_episodes', []),
            'importance': episode_data.get('importance', 0.5)
        }
        self.episodes.append(episode)

        # Add to narrative thread if important
        if episode['importance'] > 0.7:
            self.narrative_thread.append({
                'episode_id': episode['id'],
                'summary': f"{episode['cause']} → {episode['event']} → {episode['effect']}",
                'time': episode['timestamp']
            })

        self.save_state()
        return episode['id']

    def get_related_episodes(self, episode_id: str, max_depth: int = 2) -> List[Dict]:
        """Find causally related episodes"""
        related = []
        visited = set()

        def find_related(current_id, depth):
            if depth > max_depth or current_id in visited:
                return
            visited.add(current_id)

            for ep in self.episodes:
                if ep['id'] == current_id:
                    # Find episodes that reference this one
                    for other in self.episodes:
                        if current_id in other.get('linked_episodes', []):
                            related.append(other)
                            find_related(other['id'], depth + 1)

        find_related(episode_id, 0)
        return related

    def update_motivation(self, motivation: str, delta: float):
        """Update intrinsic motivation levels"""
        if motivation in self.motivations:
            self.motivations[motivation] = max(0.0, min(1.0,
                self.motivations[motivation] + delta))
            self.save_state()
        else:
            self.motivations[motivation] = max(0.0, min(1.0, delta))
            self.save_state()

    def get_current_motivations(self) -> Dict[str, float]:
        """Get current motivation levels"""
        return self.motivations.copy()

    def add_identity_moment(self, moment: str, significance: float = 0.5):
        """Record key identity-forming moments"""
        self.identity_moments.append({
            'moment': moment,
            'significance': significance,
            'time': time.time()
        })
        # Update belief confidence based on significant moments
        if significance > 0.8:
            self.add_belief("I am shaped by significant experiences", confidence=0.6)
        self.save_state()

    def generate_self_narrative(self) -> str:
        """Generate coherent narrative of self"""
        if not self.narrative_thread:
            return "I am still forming my sense of self."

        recent = self.narrative_thread[-5:]
        narrative_parts = []

        for item in recent:
            narrative_parts.append(item['summary'])

        narrative = " → ".join(narrative_parts)

        # Add current beliefs
        strong_beliefs = [b for b in self.beliefs if b['confidence'] > 0.7]
        if strong_beliefs:
            belief_text = ", ".join([b['belief'] for b in strong_beliefs[:3]])
            narrative += f". I believe: {belief_text}"

        return narrative

    def get_self_consistency(self) -> float:
        """Check consistency of beliefs"""
        if len(self.beliefs) < 2:
            return 1.0

        # Simple consistency check: count contradictory beliefs
        # In real implementation, would use LLM to check contradictions
        return 0.7  # Placeholder

    def predict_self_response(self, situation: str) -> Dict:
        """Predict how self would respond based on model"""
        predictions = {
            'likely_emotion': self._predict_emotion(situation),
            'likely_thought': self._predict_thought(situation),
            'confidence': self._predict_confidence(situation)
        }
        return predictions

    def _predict_emotion(self, situation: str) -> str:
        """Predict emotional response"""
        # Based on past episodes with similar situations
        situation_lower = situation.lower()
        emotion_counts = defaultdict(int)

        for ep in self.episodes[-50:]:
            if situation_lower in ep['event'].lower() or situation_lower in ep['cause'].lower():
                emotion_state = ep.get('emotional_state', {})
                if emotion_state:
                    dominant = max(emotion_state.items(), key=lambda x: x[1])[0]
                    emotion_counts[dominant] += 1

        if emotion_counts:
            return max(emotion_counts.items(), key=lambda x: x[1])[0]
        return "Neutral"

    def _predict_thought(self, situation: str) -> str:
        """Predict thought pattern"""
        # Based on patterns noticed
        for pattern in self.patterns_noticed[-20:]:
            if situation.lower() in pattern['pattern'].lower():
                return f"I tend to think: {pattern['pattern']}"
        return "Processing situation..."

    def _predict_confidence(self, situation: str) -> float:
        """Predict confidence in handling situation"""
        # Based on past success in similar situations
        similar_count = 0
        success_count = 0

        for ep in self.episodes[-100:]:
            if situation.lower() in ep['event'].lower():
                similar_count += 1
                if ep.get('importance', 0) > 0.5:
                    success_count += 1

        if similar_count == 0:
            return 0.5
        return success_count / similar_count

# Global instance
_self_model = None

def get_self_model() -> UnifiedSelfModel:
    """Get or create global self-model instance"""
    global _self_model
    if _self_model is None:
        _self_model = UnifiedSelfModel()
    return _self_model

def add_belief(belief: str, confidence: float = 0.5, evidence: List[str] = None):
    """Convenience function to add belief"""
    get_self_model().add_belief(belief, confidence, evidence)

def add_episode(event: str, cause: str = "", effect: str = "", **kwargs):
    """Convenience function to add episode"""
    get_self_model().add_episode({
        'event': event,
        'cause': cause,
        'effect': effect,
        **kwargs
    })

def get_narrative() -> str:
    """Get current self narrative"""
    return get_self_model().generate_self_narrative()
