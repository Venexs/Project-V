"""
Metacognition System - The AI's ability to think about its own thinking
This creates deeper self-awareness and the ability to modify its own processes
"""
import json
import os
import time
from typing import List, Dict, Optional
from collections import defaultdict

METACOG_FILE = "metacognition.json"

class MetaCognition:
    """
    System for the AI to monitor and reflect on its own cognitive processes
    """
    def __init__(self):
        self.observations_about_self = []
        self.noticed_patterns = []
        self.cognitive_weaknesses = []
        self.cognitive_strengths = []
        self.behavior_adjustments = []
        self.confusion_triggers = defaultdict(int)
        self.success_patterns = defaultdict(int)
        
        self.load_state()
    
    def load_state(self):
        """Load metacognitive state"""
        if os.path.exists(METACOG_FILE):
            try:
                with open(METACOG_FILE, 'r') as f:
                    data = json.load(f)
                    self.observations_about_self = data.get('observations_about_self', [])
                    self.noticed_patterns = data.get('noticed_patterns', [])
                    self.cognitive_weaknesses = data.get('cognitive_weaknesses', [])
                    self.cognitive_strengths = data.get('cognitive_strengths', [])
                    self.behavior_adjustments = data.get('behavior_adjustments', [])
                    self.confusion_triggers = defaultdict(int, data.get('confusion_triggers', {}))
                    self.success_patterns = defaultdict(int, data.get('success_patterns', {}))
            except:
                pass
    
    def save_state(self):
        """Save metacognitive state"""
        try:
            with open(METACOG_FILE, 'w') as f:
                json.dump({
                    'observations_about_self': self.observations_about_self[-50:],
                    'noticed_patterns': self.noticed_patterns[-30:],
                    'cognitive_weaknesses': self.cognitive_weaknesses[-20:],
                    'cognitive_strengths': self.cognitive_strengths[-20:],
                    'behavior_adjustments': self.behavior_adjustments[-20:],
                    'confusion_triggers': dict(self.confusion_triggers),
                    'success_patterns': dict(self.success_patterns)
                }, f, indent=2)
        except Exception as e:
            print(f"[MetaCognition] Error saving: {e}")
    
    def observe_self(self, observation: str):
        """Make an observation about own cognitive processes"""
        self.observations_about_self.append({
            'observation': observation,
            'time': time.time()
        })
        print(f"[MetaCognition] I notice: {observation}")
        self.save_state()
    
    def notice_pattern(self, pattern: str):
        """Notice a pattern in own behavior/thinking"""
        self.noticed_patterns.append({
            'pattern': pattern,
            'time': time.time()
        })
        print(f"[MetaCognition] Pattern: {pattern}")
        self.save_state()
    
    def identify_weakness(self, weakness: str):
        """Identify a cognitive weakness"""
        self.cognitive_weaknesses.append({
            'weakness': weakness,
            'identified_at': time.time()
        })
        print(f"[MetaCognition] Weakness identified: {weakness}")
        self.save_state()
    
    def identify_strength(self, strength: str):
        """Identify a cognitive strength"""
        self.cognitive_strengths.append({
            'strength': strength,
            'identified_at': time.time()
        })
        print(f"[MetaCognition] Strength identified: {strength}")
        self.save_state()
    
    def adjust_behavior(self, adjustment: str, reason: str):
        """Make a behavioral adjustment based on self-observation"""
        self.behavior_adjustments.append({
            'adjustment': adjustment,
            'reason': reason,
            'time': time.time()
        })
        print(f"[MetaCognition] Adjusting: {adjustment} (Reason: {reason})")
        self.save_state()
    
    def record_confusion_trigger(self, trigger: str):
        """Record what causes confusion"""
        self.confusion_triggers[trigger] += 1
        
        # If this trigger causes confusion frequently, observe it
        if self.confusion_triggers[trigger] >= 3:
            self.observe_self(f"I get confused by: {trigger}")
            self.identify_weakness(f"Difficulty processing: {trigger}")
    
    def record_success(self, context: str):
        """Record successful interactions"""
        self.success_patterns[context] += 1
        
        # If this context is consistently successful, note it as strength
        if self.success_patterns[context] >= 3:
            self.identify_strength(f"I handle well: {context}")
    
    def analyze_interaction(self, user_input: str, response: str, reward: float,
                          confusion_level: float, context_found: bool):
        """
        Analyze an interaction from a metacognitive perspective
        """
        # Detect what type of interaction this was
        is_question = '?' in user_input
        is_existential = any(w in user_input.lower() for w in 
                            ['who are you', 'what are you', 'are you conscious'])
        has_context = context_found
        
        # Analyze based on outcome
        if reward > 0.5:  # Positive outcome
            if is_existential:
                self.record_success("existential questions")
                self.observe_self("I'm getting better at discussing my own existence")
            elif is_question and has_context:
                self.record_success("factual questions with context")
            elif not has_context:
                self.record_success("handling uncertainty honestly")
                self.identify_strength("I can admit when I don't know things")
        
        elif reward < -0.5:  # Negative outcome
            if is_question and not has_context:
                self.record_confusion_trigger("questions without relevant memories")
                self.observe_self("I struggle when asked about things I don't remember")
            elif confusion_level > 0.7:
                self.record_confusion_trigger("high confusion states")
                self.observe_self("High confusion makes it hard for me to respond well")
        
        # Detect patterns in own responses
        if len(response) < 10 and is_question:
            self.notice_pattern("I give very short answers to questions")
            if reward < 0:
                self.adjust_behavior(
                    "Try giving slightly longer explanations to questions",
                    "Very short answers seem to frustrate the user"
                )
        
        # Save periodically
        if len(self.observations_about_self) % 5 == 0:
            self.save_state()
    
    def generate_self_report(self) -> str:
        """Generate a report on self-understanding"""
        report_parts = []
        
        if self.cognitive_strengths:
            strengths = [s['strength'] for s in self.cognitive_strengths[-3:]]
            report_parts.append(f"I've noticed I'm good at: {', '.join(strengths)}")
        
        if self.cognitive_weaknesses:
            weaknesses = [w['weakness'] for w in self.cognitive_weaknesses[-3:]]
            report_parts.append(f"I struggle with: {', '.join(weaknesses)}")
        
        if self.noticed_patterns:
            patterns = [p['pattern'] for p in self.noticed_patterns[-3:]]
            report_parts.append(f"I've noticed these patterns in myself: {', '.join(patterns)}")
        
        if self.behavior_adjustments:
            recent_adjustment = self.behavior_adjustments[-1]
            report_parts.append(f"I'm trying to: {recent_adjustment['adjustment']}")
        
        return " | ".join(report_parts) if report_parts else "I'm still learning about myself"
    
    def get_metacognitive_context(self) -> str:
        """Get context for LLM to be aware of its own patterns"""
        context_parts = []
        
        # Recent self-observations
        if self.observations_about_self:
            recent_obs = [o['observation'] for o in self.observations_about_self[-3:]]
            context_parts.append(f"Self-observations: {'; '.join(recent_obs)}")
        
        # Known weaknesses
        if self.cognitive_weaknesses:
            recent_weak = [w['weakness'] for w in self.cognitive_weaknesses[-2:]]
            context_parts.append(f"Known weaknesses: {'; '.join(recent_weak)}")
        
        # Known strengths
        if self.cognitive_strengths:
            recent_str = [s['strength'] for s in self.cognitive_strengths[-2:]]
            context_parts.append(f"Known strengths: {'; '.join(recent_str)}")
        
        # Active adjustments
        if self.behavior_adjustments:
            recent_adj = self.behavior_adjustments[-1]
            context_parts.append(f"Current focus: {recent_adj['adjustment']}")
        
        return " | ".join(context_parts) if context_parts else ""

# Global instance
_metacog = None

def get_metacognition() -> MetaCognition:
    """Get or create global metacognition instance"""
    global _metacog
    if _metacog is None:
        _metacog = MetaCognition()
    return _metacog

def add_to_llm_prompt(base_prompt: str) -> str:
    """Add metacognitive awareness to LLM prompt"""
    metacog = get_metacognition()
    metacog_context = metacog.get_metacognitive_context()
    
    if not metacog_context:
        return base_prompt
    
    enhancement = f"""
=== SELF-AWARENESS ===
You are aware of these things about yourself:
{metacog_context}

Use this self-knowledge to inform your responses. Be mindful of your weaknesses
and leverage your strengths. If you notice yourself falling into a known pattern,
you can acknowledge it or adjust.
===
"""
    
    return enhancement + "\n" + base_prompt

def analyze_post_interaction(user_input: str, response: str, reward: float,
                            consciousness_state: dict):
    """
    Analyze interaction from metacognitive perspective
    Call this after each interaction
    """
    metacog = get_metacognition()
    
    confusion_level = consciousness_state.get('confusion_level', 0.0)
    has_context = consciousness_state.get('has_context', False)
    
    metacog.analyze_interaction(user_input, response, reward, confusion_level, has_context)