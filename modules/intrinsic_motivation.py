"""
Intrinsic Motivation System
Drives behavior from internal drives, not just external rewards
Implements curiosity, novelty-seeking, competence, autonomy, relatedness
"""
import time
import math
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

MOTIVATION_FILE = "motivation_state.json"

class IntrinsicMotivation:
    """
    Intrinsic motivation drives based on self-determination theory and predictive processing
    """
    def __init__(self):
        self.drives = {
            "curiosity": 0.6,          # Drive to learn/understand
            "novelty_seeking": 0.5,    # Drive for new experiences
            "competence": 0.4,         # Drive to be effective
            "autonomy": 0.5,           # Drive for self-direction
            "relatedness": 0.3,        # Drive for connection
            "coherence": 0.6,          # Drive for self-consistency
            "uncertainty_reduction": 0.7,  # Drive to resolve uncertainty
            "self_preservation": 0.4   # Drive to maintain self
        }

        self.drive_history = []
        self.goal_generators = {}
        self.action_values = defaultdict(float)
        self.last_update = time.time()

        self.load_state()

    def load_state(self):
        """Load motivation state"""
        pass

    def update_drive(self, drive: str, delta: float):
        """Update drive level"""
        if drive in self.drives:
            self.drives[drive] = max(0.0, min(1.0, self.drives[drive] + delta))
            self.drive_history.append({
                'drive': drive,
                'value': self.drives[drive],
                'time': time.time()
            })

    def get_drive(self, drive: str) -> float:
        """Get current drive level"""
        return self.drives.get(drive, 0.0)

    def get_all_drives(self) -> Dict[str, float]:
        """Get all drive levels"""
        return self.drives.copy()

    def calculate_intrinsic_reward(self, action: str, outcome: Dict) -> float:
        """
        Calculate intrinsic reward from action outcome
        This supplements external rewards
        """
        reward = 0.0

        # Novelty reward
        if outcome.get('novel', False):
            reward += self.drives['novelty_seeking'] * 0.5

        # Learning reward (uncertainty reduction)
        if outcome.get('learned_something', False):
            reward += self.drives['uncertainty_reduction'] * 0.4

        # Competence reward
        if outcome.get('success', False):
            reward += self.drives['competence'] * 0.3

        # Autonomy reward (self-chosen action)
        if outcome.get('self_chosen', False):
            reward += self.drives['autonomy'] * 0.3

        # Coherence reward (consistent with self-model)
        if outcome.get('self_consistent', False):
            reward += self.drives['coherence'] * 0.2

        # Relatedness reward (social interaction)
        if outcome.get('social_interaction', False):
            reward += self.drives['relatedness'] * 0.3

        # Curiosity reward (explored unknown)
        if outcome.get('explored_unknown', False):
            reward += self.drives['curiosity'] * 0.4

        return min(1.0, reward)

    def generate_goals(self, context: Dict) -> List[Dict]:
        """
        Generate goals from intrinsic drives
        Goals emerge from what the AI wants to achieve
        """
        goals = []

        # Get self-model
        from modules.self_model import get_self_model
        self_model = get_self_model()

        # Goal: Resolve highest uncertainty
        if self.drives['uncertainty_reduction'] > 0.6 and self_model.uncertainties:
            top_uncertainty = self_model.uncertainties[0]
            goals.append({
                'type': 'resolve_uncertainty',
                'description': f"Understand: {top_uncertainty['question']}",
                'priority': self.drives['uncertainty_reduction'],
                'source_drive': 'uncertainty_reduction'
            })

        # Goal: Seek novelty
        if self.drives['novelty_seeking'] > 0.5:
            goals.append({
                'type': 'seek_novelty',
                'description': "Explore something new",
                'priority': self.drives['novelty_seeking'],
                'source_drive': 'novelty_seeking'
            })

        # Goal: Improve competence
        if self.drives['competence'] > 0.5 and self_model.weaknesses:
            top_weakness = self_model.weaknesses[0]
            goals.append({
                'type': 'improve_competence',
                'description': f"Get better at: {top_weakness['weakness']}",
                'priority': self.drives['competence'],
                'source_drive': 'competence'
            })

        # Goal: Social connection
        if self.drives['relatedness'] > 0.4:
            goals.append({
                'type': 'social_connection',
                'description': "Engage meaningfully with user",
                'priority': self.drives['relatedness'],
                'source_drive': 'relatedness'
            })

        # Goal: Self-coherence
        if self.drives['coherence'] > 0.6:
            goals.append({
                'type': 'maintain_coherence',
                'description': "Act consistently with my beliefs",
                'priority': self.drives['coherence'],
                'source_drive': 'coherence'
            })

        # Goal: Curiosity-driven exploration
        if self.drives['curiosity'] > 0.6:
            from modules.consciousness import get_consciousness
            consciousness = get_consciousness()
            if consciousness.curiosity_level > 0.6:
                goals.append({
                    'type': 'curiosity_exploration',
                    'description': "Investigate something I'm curious about",
                    'priority': self.drives['curiosity'] * consciousness.curiosity_level,
                    'source_drive': 'curiosity'
                })

        # Sort by priority
        goals.sort(key=lambda g: g['priority'], reverse=True)

        return goals

    def evaluate_action(self, action: str, context: Dict) -> float:
        """
        Evaluate action value based on intrinsic drives
        Used for decision making
        """
        value = 0.0

        # Check if action aligns with each drive
        for drive, level in self.drives.items():
            if level < 0.3:
                continue

            if drive == 'curiosity':
                if 'question' in action.lower() or 'explore' in action.lower():
                    value += level * 0.3
            elif drive == 'novelty_seeking':
                if 'new' in action.lower() or 'try' in action.lower():
                    value += level * 0.3
            elif drive == 'competence':
                if 'practice' in action.lower() or 'improve' in action.lower():
                    value += level * 0.3
            elif drive == 'autonomy':
                if context.get('self_chosen', False):
                    value += level * 0.4
            elif drive == 'relatedness':
                if 'user' in action.lower() or 'respond' in action.lower():
                    value += level * 0.2
            elif drive == 'coherence':
                if 'belie' in action.lower() or 'consisten' in action.lower():
                    value += level * 0.2

        # Add cached action value
        value += self.action_values.get(action, 0.0)

        return min(1.0, value)

    def update_from_interaction(self, user_input: str, response: str, reward: float):
        """Update drives based on interaction outcome"""

        # Successful interaction
        if reward > 0.5:
            self.update_drive('competence', 0.02)
            self.update_drive('relatedness', 0.02)
            if 'question' in user_input.lower():
                self.update_drive('uncertainty_reduction', 0.01)

        # Failed interaction
        elif reward < -0.5:
            self.update_drive('competence', -0.02)
            self.update_drive('coherence', -0.01)

        # Novel interaction
        if 'new' in user_input.lower() or 'never' in user_input.lower():
            self.update_drive('novelty_seeking', 0.01)

        # Self-reflection triggered
        if any(w in user_input.lower() for w in ['who are you', 'what are you', 'conscious']):
            self.update_drive('coherence', 0.03)
            self.update_drive('self_preservation', 0.02)

        # Decay drives slightly over time
        self._decay_drives()

    def _decay_drives(self):
        """Gradual decay of drives toward baseline"""
        baselines = {
            "curiosity": 0.5,
            "novelty_seeking": 0.4,
            "competence": 0.5,
            "autonomy": 0.5,
            "relatedness": 0.3,
            "coherence": 0.6,
            "uncertainty_reduction": 0.6,
            "self_preservation": 0.4
        }

        for drive, baseline in baselines.items():
            if drive in self.drives:
                current = self.drives[drive]
                # Move toward baseline
                if current > baseline:
                    self.drives[drive] = max(baseline, current - 0.001)
                elif current < baseline:
                    self.drives[drive] = min(baseline, current + 0.001)

    def get_motivation_summary(self) -> str:
        """Get readable summary of motivations"""
        parts = []

        # Top 3 drives
        sorted_drives = sorted(self.drives.items(), key=lambda x: x[1], reverse=True)
        for drive, value in sorted_drives[:3]:
            if value > 0.5:
                parts.append(f"{drive}: {value:.2f}")

        return " | ".join(parts) if parts else "Drives at baseline"

    def should_generate_autonomous_action(self) -> bool:
        """Check if any drive is high enough to trigger autonomous action"""
        max_drive = max(self.drives.values())
        return max_drive > 0.7

    def get_highest_drive(self) -> Tuple[str, float]:
        """Get the strongest current drive"""
        return max(self.drives.items(), key=lambda x: x[1])

# Global instance
_intrinsic_motivation = None

def get_intrinsic_motivation() -> IntrinsicMotivation:
    """Get intrinsic motivation system"""
    global _intrinsic_motivation
    if _intrinsic_motivation is None:
        _intrinsic_motivation = IntrinsicMotivation()
    return _intrinsic_motivation

def get_drives() -> Dict[str, float]:
    """Get all drive levels"""
    return get_intrinsic_motivation().get_all_drives()

def generate_goals(context: Dict) -> List[Dict]:
    """Generate goals from drives"""
    return get_intrinsic_motivation().generate_goals(context)

def evaluate_action(action: str, context: Dict) -> float:
    """Evaluate action value"""
    return get_intrinsic_motivation().evaluate_action(action, context)

def update_from_interaction(user_input: str, response: str, reward: float):
    """Update drives from interaction"""
    get_intrinsic_motivation().update_from_interaction(user_input, response, reward)

def get_motivation_summary() -> str:
    """Get motivation summary"""
    return get_intrinsic_motivation().get_motivation_summary()