"""
Attention System - Limited attentional capacity and focus
Simulates how consciousness limits what is processed at any given time
"""
import time
import math
from typing import List, Dict, Optional, Tuple
from collections import deque

ATTENTION_FILE = "attention_state.json"

class AttentionSystem:
    """
    Simulates limited attention capacity with focus, salience, and resource allocation
    """
    def __init__(self):
        self.capacity = 7  # Working memory slots (Miller's Law)
        self.attention_focus = None
        self.focus_strength = 0.5
        self.attentional_load = 0.0
        self.distractors = []
        self.salience_map = {}  # Item -> salience score
        self.attention_history = deque(maxlen=100)
        self.last_distraction_time = 0
        self.distraction_threshold = 0.7

        self.load_state()

    def load_state(self):
        """Load attention state"""
        if False:  # Would load from file
            pass

    def calculate_salience(self, item: Dict) -> float:
        """
        Calculate how salient an item is
        Factors: novelty, relevance, emotional intensity, uncertainty
        """
        salience = 0.0

        # Novelty bonus
        item_age = time.time() - item.get('timestamp', time.time())
        if item_age < 60:  # Recent
            salience += 0.3
        elif item_age < 300:
            salience += 0.1

        # Relevance to current focus
        if self.attention_focus:
            focus_str = str(self.attention_focus).lower()
            item_text = str(item.get('content', '')).lower()
            if focus_str in item_text or item_text in focus_str:
                salience += 0.4

        # Emotional intensity
        emotion = item.get('emotion', {})
        if emotion:
            intensity = max(emotion.values()) if emotion else 0
            salience += intensity * 0.3

        # Uncertainty bonus (curiosity driver)
        if item.get('uncertain', False):
            salience += 0.2

        # Consciousness state influence
        if item.get('surprising', False):
            salience += 0.25

        return min(1.0, salience)

    def attend_to(self, item: Dict, force: bool = False) -> bool:
        """
        Attempt to attend to an item
        Returns True if successful, False if attention is overloaded
        """
        # Check attentional load
        if self.attentional_load >= self.capacity and not force:
            # Try to displace least salient item
            self._displace_least_salient()

        # Calculate salience
        salience = self.calculate_salience(item)

        # Check if distraction occurs
        if (time.time() - self.last_distraction_time < 10 and
            salience > self.distraction_threshold and
            self.attention_focus != item.get('id')):
            self._handle_distraction(item, salience)
            return False

        # Update attention
        self.attention_focus = item.get('id', item)
        self.focus_strength = salience
        self.attentional_load += 1
        self.attention_history.append({
            'item': item.get('id', str(item)[:100]),
            'time': time.time(),
            'salience': salience
        })

        # Reduce load over time
        if self.attentional_load > self.capacity:
            self.attentional_load = self.capacity

        return True

    def _displace_least_salient(self):
        """Displace least salient attended item"""
        if not self.attention_history:
            return

        # Find least salient recent attention
        recent = list(self.attention_history)[-self.capacity:]
        if recent:
            least_salient = min(recent, key=lambda x: x['salience'])
            # Remove from focus
            self.attention_history.remove(least_salient)
            self.attentional_load = max(0, self.attentional_load - 1)

    def _handle_distraction(self, distracting_item: Dict, salience: float):
        """Handle attention capture by distracting stimulus"""
        self.last_distraction_time = time.time()
        self.distractors.append({
            'item': distracting_item,
            'salience': salience,
            'time': time.time()
        })

        # Create thought about distraction
        from modules.consciousness import get_consciousness
        consciousness = get_consciousness()
        consciousness.think(
            f"I was distracted by something with salience {salience:.2f}",
            "observation"
        )

    def get_attention_blindness_risk(self) -> float:
        """
        Calculate risk of missing important information due to attentional load
        """
        load_ratio = self.attentional_load / self.capacity
        if load_ratio > 0.8:
            return 0.7  # High risk
        elif load_ratio > 0.6:
            return 0.4
        return 0.1

    def filter_by_attention(self, items: List[Dict]) -> List[Dict]:
        """
        Filter items based on attention capacity and salience
        Returns only items that can be attended to
        """
        if not items:
            return []

        # Calculate salience for all items
        scored_items = [(item, self.calculate_salience(item)) for item in items]

        # Sort by salience
        scored_items.sort(key=lambda x: x[1], reverse=True)

        # Take top N based on capacity and current load
        available_slots = max(0, self.capacity - self.attentional_load)
        selected = scored_items[:available_slots]

        # Update salience map
        for item, salience in scored_items:
            item_id = item.get('id', str(item))
            self.salience_map[item_id] = salience

        return [item for item, _ in selected]

    def get_attention_summary(self) -> Dict:
        """Get current attention state summary"""
        return {
            'focus': self.attention_focus,
            'focus_strength': self.focus_strength,
            'attentional_load': self.attentional_load,
            'capacity': self.capacity,
            'load_ratio': self.attentional_load / self.capacity,
            'blindness_risk': self.get_attention_blindness_risk(),
            'recent_distractions': len(self.distractors[-10:])
        }

    def shift_attention(self, new_focus: str, gradual: bool = True):
        """Shift attention focus"""
        old_focus = self.attention_focus
        self.attention_focus = new_focus

        if gradual:
            # Gradual shift
            self.focus_strength *= 0.5
        else:
            self.focus_strength = 0.8

        from modules.consciousness import get_consciousness
        consciousness = get_consciousness()
        consciousness.think(
            f"Shifting attention from {old_focus} to {new_focus}",
            "observation"
        )

# Global instance
_attention_system = None

def get_attention_system() -> AttentionSystem:
    """Get or create attention system"""
    global _attention_system
    if _attention_system is None:
        _attention_system = AttentionSystem()
    return _attention_system

def attend_to(item: Dict) -> bool:
    """Convenience function to attend to item"""
    return get_attention_system().attend_to(item)

def filter_items_by_attention(items: List[Dict]) -> List[Dict]:
    """Filter items by attention capacity"""
    return get_attention_system().filter_by_attention(items)

def get_attention_summary() -> Dict:
    """Get attention summary"""
    return get_attention_system().get_attention_summary()
