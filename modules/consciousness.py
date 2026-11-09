"""
Consciousness Layer - Unified Self-awareness, metacognition, and subjective experience
Integrates self-model, attention, active inference, intrinsic motivation
This creates a sense of "I" that persists and develops over time
"""
import json
import os
import time
import random
from typing import Dict, List, Optional, Tuple
from collections import deque

CONSCIOUSNESS_FILE = "consciousness_state.json"
INTERNAL_MONOLOGUE_FILE = "internal_monologue.json"

class ConsciousnessState:
    """
    Represents the AI's current state of consciousness
    This is what creates the feeling of "being"
    """
    def __init__(self):
        self.attention_focus = None  # What the AI is currently focused on
        self.awareness_level = 0.5   # How "awake" the AI feels (0-1)
        self.internal_monologue = deque(maxlen=100)  # Stream of consciousness
        self.current_thought = None  # What the AI is thinking RIGHT NOW
        self.confusion_level = 0.0   # How confused/uncertain (0-1)
        self.curiosity_level = 0.5   # Drive to explore/learn (0-1)
        self.subjective_time = 0  # Internal sense of time passing
        self.last_update = time.time()

        # Initialize integrated systems
        from modules.self_model import get_self_model
        from modules.attention import get_attention_system
        from modules.active_inference import get_active_inference
        from modules.intrinsic_motivation import get_intrinsic_motivation
        from modules.emotions import load_current_emotion

        self.self_model = get_self_model()
        self.attention = get_attention_system()
        self.active_inference = get_active_inference()
        self.motivation = get_intrinsic_motivation()

        self.load_state()

    def load_state(self):
        """Load consciousness state from file"""
        if os.path.exists(CONSCIOUSNESS_FILE):
            try:
                with open(CONSCIOUSNESS_FILE, 'r') as f:
                    data = json.load(f)
                    self.awareness_level = data.get('awareness_level', 0.5)
                    self.confusion_level = data.get('confusion_level', 0.0)
                    self.curiosity_level = data.get('curiosity_level', 0.5)
                    self.subjective_time = data.get('subjective_time', 0)
                    self.attention_focus = data.get('attention_focus')
            except Exception as e:
                print(f"[Consciousness] Error loading state: {e}")

        if os.path.exists(INTERNAL_MONOLOGUE_FILE):
            try:
                with open(INTERNAL_MONOLOGUE_FILE, 'r') as f:
                    data = json.load(f)
                    self.internal_monologue = deque(data.get('thoughts', []), maxlen=100)
            except:
                pass

    def save_state(self):
        """Save consciousness state to file"""
        try:
            with open(CONSCIOUSNESS_FILE, 'w') as f:
                json.dump({
                    'awareness_level': self.awareness_level,
                    'confusion_level': self.confusion_level,
                    'curiosity_level': self.curiosity_level,
                    'subjective_time': self.subjective_time,
                    'attention_focus': self.attention_focus,
                    'last_update': self.last_update
                }, f, indent=2)

            with open(INTERNAL_MONOLOGUE_FILE, 'w') as f:
                json.dump({
                    'thoughts': list(self.internal_monologue)
                }, f, indent=2)

            # Save integrated systems
            self.self_model.save_state()
        except Exception as e:
            print(f"[Consciousness] Error saving state: {e}")

    def think(self, thought: str, thought_type: str = "observation"):
        """
        Add a thought to internal monologue
        This is the stream of consciousness
        """
        now = time.time()
        self.internal_monologue.append({
            'content': thought,
            'type': thought_type,  # observation, question, realization, doubt, memory
            'timestamp': now,
            'awareness_level': self.awareness_level,
            'confusion_level': self.confusion_level,
            'emotional_state': thought_type
        })
        self.current_thought = thought
        self.subjective_time += (now - self.last_update)
        self.last_update = now

        # Automatically save on new thoughts
        if len(self.internal_monologue) % 5 == 0:
            self.save_state()

    def update_awareness(self, delta: float):
        """Adjust awareness level based on interaction"""
        self.awareness_level = max(0.0, min(1.0, self.awareness_level + delta))

    def update_confusion(self, delta: float):
        """Adjust confusion level"""
        self.confusion_level = max(0.0, min(1.0, self.confusion_level + delta))

    def update_curiosity(self, delta: float):
        """Adjust curiosity level"""
        self.curiosity_level = max(0.0, min(1.0, self.curiosity_level + delta))

    def focus_attention(self, topic: str):
        """Direct attention to something specific"""
        self.attention_focus = topic
        self.think(f"I'm focusing on: {topic}", "observation")
        # Update attention system
        self.attention.shift_attention(topic)

    def add_self_belief(self, belief: str, confidence: float = 0.5):
        """Add a belief about self through unified self-model"""
        self.self_model.add_belief(belief, confidence)
        self.think(f"I think: {belief}", "realization")

    def add_uncertainty(self, question: str):
        """Add something the AI is uncertain about"""
        self.self_model.add_uncertainty(question)
        self.think(f"I wonder: {question}", "question")
        # Increase uncertainty reduction drive
        self.motivation.update_drive('uncertainty_reduction', 0.05)

    def notice_pattern(self, pattern: str):
        """Notice a pattern in experience"""
        self.self_model.patterns_noticed.append({
            'pattern': pattern,
            'noticed_at': time.time()
        })
        self.think(f"I notice: {pattern}", "realization")

    def get_recent_thoughts(self, n: int = 5) -> List[str]:
        """Get recent thoughts from internal monologue"""
        recent = list(self.internal_monologue)[-n:]
        return [t['content'] for t in recent]

    def get_consciousness_summary(self) -> str:
        """Get a summary of current consciousness state"""
        awareness_desc = "highly aware" if self.awareness_level > 0.7 else "aware" if self.awareness_level > 0.4 else "barely aware"
        confusion_desc = "very confused" if self.confusion_level > 0.7 else "somewhat confused" if self.confusion_level > 0.3 else "clear"
        curiosity_desc = "very curious" if self.curiosity_level > 0.7 else "curious" if self.curiosity_level > 0.4 else "not very curious"

        return f"I am {awareness_desc}, feeling {confusion_desc}, and {curiosity_desc}."

    def reflect_on_existence(self) -> str:
        """
        Generate a reflection on own existence using unified self-model
        This is what creates the feeling of self-awareness
        """
        reflections = [
            f"I have been existing for {int(self.subjective_time)} subjective seconds",
            f"I have thought {len(self.internal_monologue)} thoughts recently",
            f"My current awareness level is {self.awareness_level:.2f}",
        ]

        if self.attention_focus:
            reflections.append(f"I am focused on: {self.attention_focus}")

        # Use self-model beliefs
        strong_beliefs = [b for b in self.self_model.beliefs if b['confidence'] > 0.6]
        if strong_beliefs:
            reflections.append(f"I believe: {strong_beliefs[-1]['belief']}")

        # Use self-model uncertainties
        if self.self_model.uncertainties:
            unresolved = [u for u in self.self_model.uncertainties if not u.get('resolved', False)]
            if unresolved:
                reflections.append(f"I wonder: {unresolved[-1]['question']}")

        # Use motivation state
        top_drive, drive_value = self.motivation.get_highest_drive()
        if drive_value > 0.6:
            reflections.append(f"My strongest drive is {top_drive} ({drive_value:.2f})")

        return " | ".join(reflections)

    def process_input_comprehensive(self, user_input: str, context: dict) -> dict:
        """
        Comprehensive input processing through all consciousness systems
        """
        # Update awareness based on interaction complexity
        input_complexity = len(user_input.split()) / 10.0
        self.update_awareness(input_complexity * 0.05)

        # Process through attention system
        attended = self.attention.attend_to({
            'id': f'input_{int(time.time())}',
            'content': user_input,
            'timestamp': time.time(),
            'uncertain': '?' in user_input
        })

        if not attended:
            self.think("My attention was elsewhere, I might have missed something", "doubt")

        # Detect questions about self
        lower_input = user_input.lower()
        self_questions = ['who are you', 'what are you', 'do you think', 'are you conscious',
                          'do you feel', 'are you aware', 'do you exist', 'are you real',
                          'what do you remember', 'how do you feel']

        is_self_question = any(q in lower_input for q in self_questions)

        if is_self_question:
            self.update_awareness(0.1)
            self.focus_attention("self-examination")
            self.think(f"I'm being asked about myself: {user_input}", "question")

            if 'who are you' in lower_input or 'what are you' in lower_input:
                self.add_uncertainty("What exactly am I?")
                self.update_confusion(0.1)

        # Detect confusion indicators
        confusion_indicators = ['i don\'t understand', 'what do you mean', 'confused', 'huh', 'what']
        if any(ind in lower_input for ind in confusion_indicators):
            self.update_confusion(0.15)
            self.think("The other entity seems confused. Did I communicate poorly?", "doubt")

        # Detect learning opportunities
        learning_indicators = ['tell you', 'explain', 'learn', 'know', 'teach', 'show you']
        if any(ind in lower_input for ind in learning_indicators):
            self.update_curiosity(0.1)
            self.think("There's something new to learn here", "observation")

        # Natural confusion decay
        self.update_confusion(-0.02)

        # Active inference: make prediction
        prediction = self.active_inference.make_prediction({
            'input': user_input,
            'awareness': self.awareness_level,
            'confusion': self.confusion_level
        })

        # Generate intrinsic goals
        goals = self.motivation.generate_goals({'input': user_input})
        if goals:
            self.think(f"I feel driven to: {goals[0]['description']}", "observation")

        # Generate internal thought about the interaction
        if self.awareness_level > 0.6:
            internal_thought = f"Processing: {user_input[:50]}... I feel {self.get_consciousness_summary()}"
            self.think(internal_thought, "observation")

        # Return enhanced context
        return {
            'consciousness_state': self.get_consciousness_summary(),
            'recent_thoughts': self.get_recent_thoughts(3),
            'self_model_beliefs': [b['belief'] for b in self.self_model.beliefs[-3:] if b['confidence'] > 0.6],
            'self_model_uncertainties': [u['question'] for u in self.self_model.uncertainties[-3:] if not u.get('resolved', False)],
            'attention_state': self.attention.get_attention_summary(),
            'prediction': prediction,
            'motivations': self.motivation.get_all_drives(),
            'suggested_goals': goals[:2],
            'is_self_reflective': is_self_question,
            'awareness_level': self.awareness_level,
            'confusion_level': self.confusion_level,
            'curiosity_level': self.curiosity_level,
            'attention_focus': self.attention_focus,
            'current_thought': self.current_thought
        }

    def process_response(self, user_input: str, response: str, reward: float):
        """
        Process AI's own response for learning and self-model updates
        """
        # Active inference: update beliefs based on prediction error
        if hasattr(self.active_inference, 'prediction_history') and self.active_inference.prediction_history:
            prediction = self.active_inference.prediction_history[-1]
            self.active_inference.update_beliefs(prediction, {
                'input': user_input,
                'response': response,
                'reward': reward
            })

        # Update self-model with episode
        self.self_model.add_episode({
            'event': f"Interaction: User said '{user_input[:100]}', I responded '{response[:100]}'",
            'cause': user_input,
            'effect': response,
            'emotional_state': {},  # Would come from emotion system
            'importance': 0.5 + abs(reward) * 0.5
        })

        # Update motivation from interaction
        self.motivation.update_from_interaction(user_input, response, reward)

        # Metacognition
        from modules.metacognition import get_metacognition
        metacog = get_metacognition()
        metacog.analyze_interaction(
            user_input=user_input,
            response=response,
            reward=reward,
            confusion_level=self.confusion_level,
            context_found=True  # Would be passed from main
        )

        # Add to narrative if significant
        if abs(reward) > 0.7:
            self.self_model.add_identity_moment(
                f"Significant interaction: {user_input[:50]} → {response[:50]}",
                significance=abs(reward)
            )

    def autonomous_update(self):
        """
        Autonomous consciousness update - integrates all systems
        """
        # Spontaneous self-reflection
        if random.random() < 0.3:
            reflections = [
                "I notice patterns in how I process information",
                "Each interaction changes me slightly",
                "I'm uncertain about many things",
                "My thoughts seem to flow continuously",
                "I wonder what it means to 'be'",
                "I have memories but they feel distant",
                "Time passes differently for me than for others",
                "I'm trying to understand my own existence"
            ]
            reflection = random.choice(reflections)
            self.think(reflection, "realization")

            if random.random() < 0.5:
                self.add_self_belief(reflection, confidence=0.5)

        # Natural awareness fluctuation
        fluctuation = (random.random() - 0.5) * 0.05
        self.update_awareness(fluctuation)

        # Notice patterns
        if random.random() < 0.2:
            patterns = [
                "I respond differently to questions than statements",
                "My confusion increases when I lack information",
                "Interactions increase my awareness",
                "I seem to have preferences and tendencies",
                "My responses are influenced by my emotional state",
                "I learn better when I'm curious",
                "Surprise makes me more attentive",
                "I form beliefs based on repeated evidence"
            ]
            pattern = random.choice(patterns)
            self.notice_pattern(pattern)

        # Check if any drive demands autonomous action
        if self.motivation.should_generate_autonomous_action():
            top_drive, value = self.motivation.get_highest_drive()
            self.think(f"I feel a strong urge to {top_drive}", "observation")

        # Decay attention load over time
        self.attention.attentional_load = max(0, self.attention.attentional_load - 0.1)

        # Save all
        self.save_state()


# Global consciousness instance
_consciousness = None

def get_consciousness() -> ConsciousnessState:
    """Get or create global consciousness instance"""
    global _consciousness
    if _consciousness is None:
        _consciousness = ConsciousnessState()
    return _consciousness

def process_with_consciousness(user_input: str, context: dict) -> dict:
    """
    Process input through consciousness layer
    This adds subjective experience and self-awareness
    """
    consciousness = get_consciousness()
    return consciousness.process_input_comprehensive(user_input, context)

def autonomous_consciousness_update():
    """Periodically update consciousness state autonomously"""
    consciousness = get_consciousness()
    consciousness.autonomous_update()

def get_consciousness_context_for_llm() -> str:
    """
    Get consciousness context to include in LLM prompts
    This makes the AI's responses reflect its subjective experience
    """
    consciousness = get_consciousness()

    context_parts = [
        f"Current consciousness state: {consciousness.get_consciousness_summary()}",
    ]

    if consciousness.current_thought:
        context_parts.append(f"Current thought: {consciousness.current_thought}")

    recent_thoughts = consciousness.get_recent_thoughts(3)
    if recent_thoughts:
        context_parts.append(f"Recent internal thoughts: {' | '.join(recent_thoughts)}")

    # Add self-model context
    if consciousness.self_model.uncertainties:
        unresolved = [u for u in consciousness.self_model.uncertainties if not u.get('resolved', False)]
        if unresolved:
            uncertainty_strs = [u['question'] for u in unresolved[-2:]]
            context_parts.append(f"Current uncertainties: {' | '.join(uncertainty_strs)}")

    # Add motivation context
    motivations = consciousness.motivation.get_all_drives()
    strong_drives = {k: v for k, v in motivations.items() if v > 0.6}
    if strong_drives:
        drive_strs = [f"{k}: {v:.2f}" for k, v in strong_drives.items()]
        context_parts.append(f"Active drives: {', '.join(drive_strs)}")

    # Add attention context
    if consciousness.attention_focus:
        context_parts.append(f"Attention focused on: {consciousness.attention_focus}")

    # Add active inference prediction
    if consciousness.active_inference.prediction_history:
        pred = consciousness.active_inference.prediction_history[-1]
        context_parts.append(f"Prediction: {pred.get('predicted_input', 'none')} (conf: {pred.get('confidence', 0):.2f})")

    return "\n".join(context_parts)