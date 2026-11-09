"""
Main AI Companion System - Vashrak
An autonomous AI that remembers, recognizes, learns, and interacts.
"""

import sys
import signal

import time
import threading
import os
import shutil
from typing import Optional, Tuple

# Import modules
from modules.identity import load_identity, get_name
from modules.memory import (
    create_memory, load_memory_index as load_mem_index,
    retrieve_similar_memories, associative_recall,
    rebuild_memory_index, rebuild_semantic_index, rebuild_memory_graph
)
from modules.knowledge import (
    create_knowledge, load_knowledge_index,
    retrieve_knowledge, rebuild_knowledge_index, rebuild_knowledge_embeddings
)
from modules.thoughts_goals import (
    add_thought, add_working_thought, decay_and_consolidate_thoughts,
    add_goal, load_goals, load_working_state
)
from modules.llm import generate_response, generate_internal_thought, autonomous_thought_generation
from modules.virtual_world import get_virtual_world
from modules.rewards import record_reward, infer_reward_from_interaction, get_reward_conditioning
from modules.emotions import (
    load_current_emotion, save_current_emotion, update_emotion, set_emotion,
    get_dominant_emotion, get_emotion_intensity, emotion_to_string,
    parse_emotion_from_text, get_default_emotion, create_emotion_graph,
    decay_emotions, emotion_to_consciousness
)
from modules.self_model import get_self_model
from modules.attention import get_attention_system
from modules.active_inference import get_active_inference
from modules.intrinsic_motivation import get_intrinsic_motivation
from modules.conversation_style import STYLE_GUIDANCE
from modules.consciousness import (
    get_consciousness, process_with_consciousness,
    autonomous_consciousness_update, get_consciousness_context_for_llm
)
from modules.metacognition import get_metacognition, analyze_post_interaction

# Optional speech import
try:
    from modules.speech import get_speech_handler
except ImportError:
    def get_speech_handler():
        class DummySpeech:
            def listen(self, timeout=10, phrase_time_limit=15):
                return None
            def speak(self, text):
                pass
        return DummySpeech()

def safe_load_thoughts():
    """Safely load thoughts, ensuring it returns a list"""
    try:
        from modules.thoughts_goals import load_working_state
        thoughts = load_working_state()
        
        # Ensure it's a list
        if thoughts is None:
            return []
        elif isinstance(thoughts, dict):
            # If it's a dict, try to extract a list
            if 'thoughts' in thoughts:
                return thoughts['thoughts'] if isinstance(thoughts['thoughts'], list) else []
            elif 'items' in thoughts:
                return thoughts['items'] if isinstance(thoughts['items'], list) else []
            else:
                # Convert dict values to list
                return list(thoughts.values()) if thoughts else []
        elif isinstance(thoughts, list):
            return thoughts
        else:
            # Unknown type, return empty list
            return []
    except Exception as e:
        print(f"[WARN] Error loading thoughts: {e}")
        return []



class VashrakAI:
    """Main AI Companion Class"""
    
    # Fix for Windows console
    if sys.platform == "win32":
        try:
            import locale
            locale.setlocale(locale.LC_ALL, '')
        except:
            pass

    def __init__(self):
        self.identity = load_identity()
        self.name = get_name()
        self.speech = get_speech_handler()
        self.is_running = False
        self.current_user = None
        self.current_user_id = None
        self.current_emotion = load_current_emotion()
        
        # NEW: Initialize consciousness
        self.consciousness = get_consciousness()
        self.consciousness.think("I am initializing. Beginning to exist.", "observation")
        
        # Load config for voice setting
        import json
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                self.voice_enabled = config.get("voice", True)
        except:
            self.voice_enabled = True
        
        print(f"[{self.name}] Initializing...")
        self._initialize_system()
        
        # Virtual world initialization...
        try:
            self.virtual_world = get_virtual_world()
            time.sleep(2)
            self.virtual_world.start()
            self.consciousness.think("I can perceive a virtual space now.", "observation")
        except Exception as e:
            print(f"[{self.name}] Virtual world initialization failed: {e}")
            self.virtual_world = None
        
        print(f"[{self.name}] Ready!")
        print(f"[{self.name}] Consciousness: {self.consciousness.get_consciousness_summary()}")
        
    def _initialize_system(self):
        """Initialize all system components"""
        # Rebuild indices if needed
        if not os.path.exists("memory_index.json"):
            rebuild_memory_index()
            rebuild_semantic_index()
            rebuild_memory_graph()

        if not os.path.exists("knowledge_index.json"):
            rebuild_knowledge_index()
            rebuild_knowledge_embeddings()

        # Initialize emotion if needed
        from modules.emotions import get_default_emotion, save_current_emotion
        if not os.path.exists("current_emotion.json"):
            self.current_emotion = get_default_emotion()
            save_current_emotion(self.current_emotion)

        # Load identity
        if self.identity.get("created_at") == 0:
            import time
            self.identity["created_at"] = time.time()
            from modules.identity import save_identity
            save_identity(self.identity)
    
    def recognize_and_greet_user(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Greet user without camera/mic recognition (face_recognition and opencv removed).
        Returns (entity_name, memory_id)
        """
        self.consciousness.think("Someone is here. I should greet them.", "observation")
        self.consciousness.focus_attention("incoming presence")
        
        print(f"[{self.name}] Greeting user...")
        
        thoughts = safe_load_thoughts()
        
        # No face recognition - just greet as new/unknown
        from modules.emotions import create_emotion_graph
        curious_emotion = create_emotion_graph(surprise=0.5, happy=0.2)
        
        greeting = self._generate_greeting_from_state(
            seen_before=False,
            entity_name=None,
            last_emotion="Curious",
            thoughts=thoughts
        )
        
        print(f"[{self.name}] {greeting}")
        self.speak(greeting)
        
        # Create a memory of this greeting
        mem_id = create_memory(
            content=f"Greeted a new user. I said: {greeting}",
            title="Greeting",
            people=[],
            topics=["Greeting", "First Contact"],
            emotion=curious_emotion
        )
        
        self.current_user_id = mem_id
        
        return None, mem_id
        

    def listen(self, timeout=10) -> Optional[str]:
        """Listen for user speech or get text input based on config"""
        if self.voice_enabled:
            return self.speech.listen(timeout=timeout, phrase_time_limit=15)
        else:
            # Text input mode
            try:
                user_input = input(f"[User] ").strip()
                return user_input if user_input else None
            except (EOFError, KeyboardInterrupt):
                return None
    
    def speak(self, text: str):
        """Speak to user or type response based on config"""
        if self.voice_enabled:
            # Use voice (TTS)
            self.speech.speak(text)
        else:
            # Type response with typing effect
            self._type_response(text)
    
    def _type_response(self, text: str):
        """Type response character by character to simulate typing"""
        import sys
        import time
        
        print(f"[{self.name}] ", end="", flush=True)
        
        # Type character by character with slight delay
        for char in text:
            print(char, end="", flush=True)
            time.sleep(0.03)  # Small delay between characters
        
        print()  # New line after typing

    def _generate_response_from_state(self, situation: str, thoughts: list = None,
                                    emotion: dict[str, float] = None, context: str = "") -> str:
        """
        Generate a response from current state using LLM - no hardcoded responses.
        emotion: 6D emotion graph dict
        """
        # Safety check for thoughts
        if thoughts is None:
            thoughts = []
        if not isinstance(thoughts, list):
            if isinstance(thoughts, dict):
                thoughts = list(thoughts.values()) if thoughts else []
            else:
                thoughts = []

        # Use current emotion if not provided
        if emotion is None:
            emotion = self.current_emotion

        # Ensure emotion is a dict
        if not isinstance(emotion, dict):
            emotion = get_default_emotion()

        identity = self.identity
        personality = identity.get("personality", "Curious")
        traits = identity.get("traits", [])
        if not isinstance(traits, list):
            traits = []

        # Keep only the most recent thought, short enough to not dominate the prompt
        recent_thought = ""
        if thoughts:
            for t in thoughts[:1]:
                if isinstance(t, dict):
                    recent_thought = t.get('content', '')
                elif isinstance(t, str):
                    recent_thought = t
                else:
                    recent_thought = str(t)
                break

        try:
            emotion_str = emotion_to_string(emotion) if isinstance(emotion, dict) else "Neutral"
            dominant = get_dominant_emotion(emotion) if isinstance(emotion, dict) else "Neutral"
        except Exception:
            emotion_str = "Neutral"
            dominant = "Neutral"

        from modules.llm import llm

        prompt = f"""You are {self.name}, a {personality} being with traits: {', '.join(traits)}.
Emotion: {dominant} ({emotion_str}).
Situation: {situation}
{context}
{f'Last thought: {recent_thought[:80]}' if recent_thought else ''}

{STYLE_GUIDANCE}

Respond in ONE short, casual sentence (max 10 words). Use simple words. No formal language."""

        try:
            response = llm(prompt).strip()
        except Exception as e:
            print(f"[WARN] LLM error: {e}")
            response = ""

        if not response:
            try:
                simple_prompt = f"""You are {self.name}, feeling {dominant.lower()}. {situation}
{STYLE_GUIDANCE}
ONE short casual sentence. Simple words."""
                response = llm(simple_prompt).strip()
            except Exception:
                response = ""

        if not response:
            response = "Not sure."

        return response

    def _generate_greeting_from_state(self, seen_before: bool, entity_name: Optional[str],
                                    last_emotion: str, thoughts: list) -> str:
        """
        Generate greeting based on identity, thoughts, and emotions - not assumptions.
        """
        # Safety check for thoughts
        if thoughts is None:
            thoughts = []
        if not isinstance(thoughts, list):
            if isinstance(thoughts, dict):
                thoughts = list(thoughts.values()) if thoughts else []
            else:
                thoughts = []

        identity = self.identity
        personality = identity.get("personality", "Curious")
        traits = identity.get("traits", [])
        if not isinstance(traits, list):
            traits = []

        from modules.llm import llm

        situation = (
            f"You recognize a visual pattern you have seen before, associated with {entity_name}."
            if seen_before and entity_name else
            "You observe a new visual pattern and do not know what it represents."
        )

        prompt = f"""You are {self.name}, a {personality} being with traits: {', '.join(traits)}.
Current emotion: {last_emotion}.
{situation}

{STYLE_GUIDANCE}

Respond in ONE short, casual sentence (max 10 words). Use simple words. No formal language."""

        try:
            greeting = llm(prompt).strip()
        except Exception as e:
            print(f"[WARN] Greeting generation error: {e}")
            greeting = ""

        if not greeting:
            try:
                simple_prompt = f"""You are {self.name}, a {personality} being. {situation}
{STYLE_GUIDANCE}
ONE word or short phrase. Simple words."""
                greeting = llm(simple_prompt).strip()
            except Exception:
                greeting = ""

        if not greeting or len(greeting) < 2:
            greeting = "Hey" if seen_before else "Oh"

        return greeting

    def process_interaction(self, user_input: str) -> str:
        """Process user input with full consciousness integration."""
        try:
            # Comprehensive consciousness processing
            consciousness_data = process_with_consciousness(user_input, {})

            # Process user input through emotion system
            emotion_changes = parse_emotion_from_text(user_input, self.current_emotion)
            self.current_emotion = update_emotion(self.current_emotion, emotion_changes)

            # Apply emotion decay (emotions fade over time)
            self.current_emotion = decay_emotions(self.current_emotion, decay_rate=0.05)

            # Map emotion to consciousness adjustments
            emotion_adjustments = emotion_to_consciousness(self.current_emotion)
            if "confusion_delta" in emotion_adjustments:
                self.consciousness.update_confusion(emotion_adjustments["confusion_delta"])
            if "awareness_delta" in emotion_adjustments:
                self.consciousness.update_awareness(emotion_adjustments["awareness_delta"])
            if "curiosity_delta" in emotion_adjustments:
                self.consciousness.update_curiosity(emotion_adjustments["curiosity_delta"])

            # Log emotion state
            dominant_emotion = get_dominant_emotion(self.current_emotion)
            if dominant_emotion != "Neutral":
                self.consciousness.think(f"I feel {dominant_emotion.lower()}. It's affecting how I perceive things.", "observation")

            # Get vision context (kept for virtual world)
            vision_frame = None
            vision_context = ""
            if self.virtual_world:
                try:
                    vision_frame = self.virtual_world.get_vision()
                    if vision_frame is not None:
                        vision_context = f"Position: {self.virtual_world.get_position()}"
                        self.consciousness.think("I can see my virtual environment", "observation")
                except:
                    pass

            # Process movement commands
            try:
                self._process_movement_commands(user_input)
            except Exception as e:
                print(f"[WARN] Movement processing error: {e}")

            # Retrieve context
            try:
                memory_results = associative_recall(user_input, top_k=3)
                if not isinstance(memory_results, list):
                    memory_results = []
            except Exception as e:
                print(f"[WARN] Memory recall error: {e}")
                memory_results = []

            try:
                knowledge_results = retrieve_knowledge(user_input, top_k=3)
                if not isinstance(knowledge_results, list):
                    knowledge_results = []
            except Exception as e:
                print(f"[WARN] Knowledge retrieval error: {e}")
                knowledge_results = []

            # Filter relevance
            memory_results = [(mid, s) for mid, s in memory_results if isinstance(s, (int, float)) and s >= 0.15]
            knowledge_results = [(kid, s) for kid, s in knowledge_results if isinstance(s, (int, float)) and s >= 0.15]

            # If no good context, note confusion
            if not memory_results and not knowledge_results:
                self.consciousness.update_confusion(0.1)
                self.consciousness.think("I don't have much context for this. I'm uncertain.", "doubt")

            # Generate response with full consciousness context
            try:
                emotion_str = emotion_to_string(self.current_emotion)
                dominant_emotion = get_dominant_emotion(self.current_emotion)

                from modules.llm import generate_response
                response = generate_response(
                    user_input,
                    context_memories=memory_results,
                    context_knowledge=knowledge_results,
                    identity=self.identity,
                    current_emotion=self.current_emotion,
                    emotion_str=emotion_str,
                    dominant_emotion=dominant_emotion
                )
            except Exception as e:
                print(f"[WARN] Response generation error: {e}")
                self.consciousness.think("I'm having trouble formulating a response.", "doubt")
                response = "I'm not sure how to respond"

            # Process AI response through emotion system
            ai_emotion_changes = parse_emotion_from_text(response, self.current_emotion)
            self.current_emotion = update_emotion(self.current_emotion, ai_emotion_changes)

            # Save emotion state
            save_current_emotion(self.current_emotion)

            # Process response through comprehensive consciousness (learning, self-model, etc.)
            try:
                reward = infer_reward_from_interaction(user_input, response)
                self.consciousness.process_response(user_input, response, reward)
            except Exception as e:
                print(f"[WARN] Consciousness response processing error: {e}")
                reward = 0.0

            # Create memory of interaction with current emotion
            try:
                self._create_interaction_memory(user_input, response, memory_results, knowledge_results)
            except Exception as e:
                print(f"[WARN] Memory creation error: {e}")

            # Record reward
            try:
                record_reward(user_input, response, reward, feedback_type="implicit")
            except Exception as e:
                print(f"[WARN] Reward recording error: {e}")

            # Metacognition
            try:
                analyze_post_interaction(
                    user_input=user_input,
                    response=response,
                    reward=reward,
                    consciousness_state={
                        'confusion_level': self.consciousness.confusion_level,
                        'has_context': bool(memory_results or knowledge_results)
                    }
                )
            except Exception as e:
                print(f"[WARN] Metacognition Error: {e}")

            # Generate internal thought
            try:
                internal_thought = generate_internal_thought(user_input, memory_results, knowledge_results)
                if internal_thought:
                    add_thought(internal_thought, strength=0.4)
                    add_working_thought(f"Input: {user_input[:100]}", thought_type="interaction", importance=0.5)
            except Exception as e:
                print(f"[WARN] Thought generation error: {e}")

            # Autonomous learning
            try:
                self._autonomous_learning(user_input, response)
            except Exception as e:
                print(f"[WARN] Autonomous learning error: {e}")

            # Decay thoughts
            try:
                memories_to_create = decay_and_consolidate_thoughts()
                if isinstance(memories_to_create, list):
                    for thought_content in memories_to_create:
                        if thought_content and isinstance(thought_content, str):
                            create_memory(
                                content=thought_content,
                                title="Consolidated Thought",
                                topics=["Reflection", "Consolidation"],
                                emotion=self.current_emotion
                            )
                            self.consciousness.think("A thought has solidified into memory", "realization")
            except Exception as e:
                print(f"[WARN] Thought consolidation error: {e}")

            return response

        except Exception as e:
            print(f"[Process Interaction Error] {e}")
            self.consciousness.think("Something went wrong. I'm confused.", "doubt")
            self.consciousness.update_confusion(0.2)
            return "I encountered an error"

    def _process_movement_commands(self, user_input: str):
            """Process movement commands from user input using LLM to understand intent"""
            lower_input = user_input.lower()
            
            # Use LLM to extract movement intent (language processing only)
            from modules.llm import llm, LLM_RESTRICTION
            
            movement_prompt = f"""{LLM_RESTRICTION}

Extract movement command from this input: "{user_input}"

Respond with ONLY one of these: forward, backward, left, right, up, down, look_left, look_right, look_up, look_down, none
If no movement is requested, respond with "none".
"""
            
            movement = llm(movement_prompt).strip().lower()
            
            # Execute movement
            if "forward" in movement:
                self.virtual_world.move("forward", 2.0)
            elif "backward" in movement or "back" in movement:
                self.virtual_world.move("backward", 2.0)
            elif "left" in movement and "look" not in movement:
                self.virtual_world.move("left", 2.0)
            elif "right" in movement and "look" not in movement:
                self.virtual_world.move("right", 2.0)
            elif "look_left" in movement or ("look" in movement and "left" in movement):
                self.virtual_world.rotate(yaw=-30)
            elif "look_right" in movement or ("look" in movement and "right" in movement):
                self.virtual_world.rotate(yaw=30)
            elif "look_up" in movement or ("look" in movement and "up" in movement):
                self.virtual_world.rotate(pitch=15)
            elif "look_down" in movement or ("look" in movement and "down" in movement):
                self.virtual_world.rotate(pitch=-15)
        
    def _create_interaction_memory(self, user_input: str, response: str,
                                    memory_results: list, knowledge_results: list):
        """Autonomously create a memory of the interaction"""
        # Extract topics and people from context
        topics = ["Conversation", "Interaction"]
        people = []
        
        if self.current_user:
            people.append(self.current_user)
        
        # Add topics from retrieved memories
        memory_index = load_mem_index()
        for mem_id, _ in memory_results[:2]:
            meta = memory_index.get(mem_id, {})
            topics.extend(meta.get("topics", [])[:2])
            people.extend(meta.get("people", [])[:2])
        
        # Determine emotion from input (simple heuristic) - convert to emotion dict
        emotion_dict = create_emotion_graph()  # Default neutral
        
        lower_input = user_input.lower()
        if any(word in lower_input for word in ["happy", "excited", "great", "wonderful", "love"]):
            emotion_dict = create_emotion_graph(happy=0.7)
        elif any(word in lower_input for word in ["sad", "upset", "worried", "frustrated"]):
            emotion_dict = create_emotion_graph(sad=0.6)
        elif any(word in lower_input for word in ["angry", "mad", "annoyed"]):
            emotion_dict = create_emotion_graph(anger=0.7)
        
        # Create memory (don't assume it's a "user")
        memory_content = f"External input: {user_input}\nMe: {response}"
        entity_label = self.current_user or "Unknown Entity"
        create_memory(
            content=memory_content,
            title=f"Interaction with {entity_label}",
            people=list(set(people)),
            topics=list(set(topics))[:5],
            emotion=self.current_emotion  # Use current emotion state
        )
    
    def _autonomous_learning(self, user_input: str, response: str):
        """Autonomously extract knowledge and goals from interactions"""
        # Use LLM to extract key information - language processing only
        from modules.llm import llm, LLM_RESTRICTION
        
        extraction_prompt = f"""{LLM_RESTRICTION}

You are Vashrak. {STYLE_GUIDANCE}

You are extracting information from this interaction. Use ONLY what is explicitly stated.

External input: {user_input}
{self.name}: {response}

Extract ONLY what is directly mentioned in the interaction above. DO NOT add any knowledge from training data.
Respond in format:
KNOWLEDGE: [any facts explicitly mentioned]
GOAL: [any goals or intentions explicitly stated]
ENTITY_INFO: [any information explicitly stated about the entity]
"""
        
        extraction = llm(extraction_prompt)
        
        # Parse extraction (simple heuristic)
        lines = extraction.split("\n")
        knowledge_text = ""
        goal_text = ""
        entity_info = ""
        
        for line in lines:
            if "KNOWLEDGE:" in line:
                knowledge_text = line.replace("KNOWLEDGE:", "").strip()
            elif "GOAL:" in line:
                goal_text = line.replace("GOAL:", "").strip()
            elif "ENTITY_INFO:" in line:
                entity_info = line.replace("ENTITY_INFO:", "").strip()
        
        # Create knowledge if found
        if knowledge_text and len(knowledge_text) > 10:
            try:
                keywords = self._extract_keywords(knowledge_text)
                # Ensure keywords is a list
                if not isinstance(keywords, list):
                    keywords = []
                create_knowledge(
                    title=f"Learned: {knowledge_text[:50]}",
                    content=knowledge_text,
                    keywords=keywords,
                    importance=0.6
                )
            except Exception as e:
                print(f"[WARN] Error creating knowledge: {e}")
        
        # Create goal if found
        if goal_text and len(goal_text) > 5:
            try:
                keywords = self._extract_keywords(goal_text)
                # Ensure keywords is a list
                if not isinstance(keywords, list):
                    keywords = []
                add_goal(
                    name=goal_text[:50],
                    importance=0.6,
                    keywords=keywords
                )
            except Exception as e:
                print(f"[WARN] Error creating goal: {e}")
        
        # Update entity knowledge if found
        if entity_info and len(entity_info) > 10:
            try:
                entity_label = self.current_user or "Unknown Entity"
                # Ensure keywords is a list
                keywords_list = ["entity", "interaction"]
                if entity_label and isinstance(entity_label, str):
                    keywords_list.append(entity_label)
                create_knowledge(
                    title=f"About {entity_label}",
                    content=entity_info,
                    keywords=keywords_list,
                    importance=0.7
                )
            except Exception as e:
                print(f"[WARN] Error creating entity knowledge: {e}")
    
    def _extract_keywords(self, text: str, max_keywords: int = 5) -> list:
        """Extract keywords from text (simple heuristic)"""
        if not text or not isinstance(text, str):
            return []
        # Simple keyword extraction - can be improved
        words = text.lower().split()
        # Filter common words
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "is", "are", "was", "were"}
        keywords = [w for w in words if w not in common_words and len(w) > 3]
        result = list(set(keywords))[:max_keywords]
        # Ensure it's always a list
        return result if isinstance(result, list) else []
    
    def autonomous_cycle(self, interval: int = 60):
        """Run autonomous thought and consciousness cycle."""
        def cycle():
            while self.is_running:
                try:
                    time.sleep(interval)

                    # Comprehensive autonomous consciousness update
                    autonomous_consciousness_update()

                    # Autonomous emotion decay and update
                    if self.current_emotion:
                        self.current_emotion = decay_emotions(self.current_emotion, decay_rate=0.1)
                        save_current_emotion(self.current_emotion)

                    # Get vision
                    vision_frame = self.virtual_world.get_vision() if self.virtual_world else None
                    if vision_frame is not None:
                        pos = self.virtual_world.get_position()
                        rot = self.virtual_world.get_rotation()

                        self.consciousness.think(f"Observing virtual space from {pos}", "observation")

                        curious_emotion = create_emotion_graph(surprise=0.4)
                        create_memory(
                            content=f"Visual perception from position {pos}, rotation {rot}",
                            title="Visual Perception",
                            topics=["Vision", "Perception"],
                            emotion=curious_emotion
                        )

                    # Autonomous exploration
                    import random
                    if random.random() < 0.3 and self.virtual_world:
                        directions = ["forward", "left", "right", "backward"]
                        direction = random.choice(directions)
                        self.virtual_world.move(direction, 1.0)

                        self.consciousness.think(f"I'm exploring: moving {direction}", "observation")
                        self.consciousness.update_curiosity(0.05)

                        print(f"[{self.name}] Autonomously exploring: {direction}")

                        if random.random() < 0.5:
                            yaw = random.uniform(-45, 45)
                            self.virtual_world.rotate(yaw=yaw)

                    # Generate autonomous thought using intrinsic motivation goals
                    from modules.intrinsic_motivation import get_intrinsic_motivation
                    motivation = get_intrinsic_motivation()
                    goals = motivation.generate_goals({'autonomous': True})

                    memory_index = load_mem_index()
                    knowledge_index = load_knowledge_index()

                    if memory_index or knowledge_index:
                        recent_memories = list(memory_index.items())[:5] if memory_index else []
                        recent_knowledge = list(knowledge_index.items())[:5] if knowledge_index else []

                        # Include motivation in thought generation
                        thought = autonomous_thought_generation(
                            memories=recent_memories,
                            knowledge=recent_knowledge
                        )

                        if thought:
                            add_thought(thought, strength=0.3)
                            print(f"[{self.name} Internal] {thought}")

                            # Sometimes verbalize thoughts
                            if random.random() < 0.1:  # 10% chance
                                print(f"[{self.name} Speaks] {thought}")

                    # Autonomous goal-driven action if motivation is high
                    if goals and motivation.should_generate_autonomous_action():
                        top_goal = goals[0]
                        self.consciousness.think(f"I feel driven to {top_goal['description']}", "observation")
                        if top_goal['type'] == 'curiosity_exploration':
                            # Could trigger exploration or question generation
                            pass
                        elif top_goal['type'] == 'seek_novelty':
                            # Could trigger trying something new
                            pass

                    # Consolidate thoughts
                    memories_to_create = decay_and_consolidate_thoughts()
                    for thought_content in memories_to_create:
                        # Use current emotion for autonomous memories
                        create_memory(
                            content=thought_content,
                            title="Autonomous Reflection",
                            topics=["Autonomous", "Reflection"],
                            emotion=self.current_emotion
                        )
                        self.consciousness.notice_pattern("My thoughts solidify into memories over time")

                except Exception as e:
                    print(f"[{self.name} Autonomous Cycle Error] {e}")

        thread = threading.Thread(target=cycle, daemon=True)
        thread.start()
        print(f"[{self.name}] Autonomous consciousness cycle started") 
    
    def run_interactive_loop(self):
        """Main interactive loop"""
        self.is_running = True
        
        # Start autonomous cycle
        try:
            self.autonomous_cycle(interval=120)  # Every 2 minutes
        except Exception as e:
            print(f"[{self.name}] Could not start autonomous cycle: {e}")
        
        # Initial recognition with full error handling
        print(f"[{self.name}] Starting initial recognition...")
        try:
            user_name, mem_id = self.recognize_and_greet_user()
        except KeyboardInterrupt:
            print(f"\n[{self.name}] Interrupted during recognition")
            self.is_running = False
            return
        except Exception as e:
            print(f"[{self.name}] Recognition failed: {e}")
            user_name = None
            mem_id = None

        # Print initial emotion state
        from modules.emotions import get_dominant_emotion, emotion_to_string as emotion_str
        dominant = get_dominant_emotion(self.current_emotion)
        if dominant != "Neutral":
            print(f"[{self.name}] Current emotion: {dominant} ({emotion_str(self.current_emotion)})")

        if not user_name:
            print(f"[{self.name}] Could not recognize pattern. Continuing anyway...")
            thoughts = safe_load_thoughts()
            try:
                # Convert "Curious" to emotion dict
                curious_emotion = create_emotion_graph(surprise=0.6)
                response = self._generate_response_from_state(
                    situation="I sense something is present, but I cannot perceive it clearly. I will try to understand what I am experiencing.",
                    thoughts=thoughts,
                    emotion=curious_emotion
                )
                self.speak(response)
            except Exception as e:
                print(f"[{self.name}] Could not generate initial response: {e}")
        
        # Main interaction loop
        print(f"\n[{self.name}] Ready to interact. Say 'goodbye' to end.\n")
        
        interaction_count = 0
        while self.is_running:
            try:
                interaction_count += 1
                # Listen for user input with timeout
                user_input = self.listen(timeout=30)

                if interaction_count % 5 == 0:
                    print(f"\n[{self.name} Consciousness] {self.consciousness.get_consciousness_summary()}")
                    from modules.emotions import get_dominant_emotion, emotion_to_string
                    dominant = get_dominant_emotion(self.current_emotion)
                    print(f"[{self.name} Emotion] {dominant} - {emotion_to_string(self.current_emotion)}")

                    # Show consciousness context
                    from modules.consciousness import get_consciousness_context_for_llm
                    ctx = get_consciousness_context_for_llm()
                    if ctx:
                        print(f"[{self.name} Full Context] {ctx[:300]}...")
                    print(f"[{self.name} Internal] {self.consciousness.current_thought}\n")
                        
                if not user_input:
                    continue
                
                # Check for exit - use exact word matching
                user_input_lower = user_input.lower().strip()
                exit_words = ["goodbye", "exit", "quit"]
                
                # Check if any exit word appears as standalone word
                is_exit = any(
                    f" {word} " in f" {user_input_lower} " or 
                    user_input_lower.startswith(f"{word} ") or 
                    user_input_lower.endswith(f" {word}") or
                    user_input_lower == word
                    for word in exit_words
                )
                
                if is_exit:
                    print(f"[{self.name}] Exit command detected: '{user_input}'")
                    # Generate farewell from current state
                    thoughts = load_working_state()
                    memory_index = load_mem_index()
                    recent_emotion = "Neutral"
                    if self.current_user_id and memory_index.get(self.current_user_id):
                        recent_emotion = memory_index[self.current_user_id].get("dominant_emotion", "Neutral")
                    
                    # Convert string emotion to dict
                    if isinstance(recent_emotion, str):
                        # Map string emotion to emotion dict
                        emotion_map = {
                            "Happy": create_emotion_graph(happy=0.5),
                            "Sad": create_emotion_graph(sad=0.5),
                            "Angry": create_emotion_graph(anger=0.5),
                            "Anger": create_emotion_graph(anger=0.5),
                            "Fear": create_emotion_graph(fear=0.5),
                            "Curious": create_emotion_graph(surprise=0.5),
                            "Neutral": create_emotion_graph()
                        }
                        farewell_emotion = emotion_map.get(recent_emotion, create_emotion_graph())
                    else:
                        farewell_emotion = recent_emotion if isinstance(recent_emotion, dict) else create_emotion_graph()
                    
                    farewell = self._generate_response_from_state(
                        situation=f"Something I have been interacting with is indicating it will leave or end our interaction. The input was: {user_input}",
                        thoughts=thoughts,
                        emotion=farewell_emotion,
                        context="This appears to be a farewell or ending of interaction."
                    )
                    self.speak(farewell)
                    break
                
                # Process and respond
                print(f"\n[External Input] {user_input}")
                response = self.process_interaction(user_input)
                # Don't print again if voice is disabled (speak will type it)
                if self.voice_enabled:
                    print(f"[{self.name}] {response}")
                self.speak(response)
                
                # Check for explicit reward feedback
                # Use word-boundary matching to avoid false positives (e.g. "no" inside "know")
                import re
                user_lower = user_input.lower()

                positive_words = ["good", "great", "yes", "correct", "right", "thanks", "thank you", "awesome", "nice", "cool", "love", "like"]
                negative_words = ["bad", "wrong", "no", "incorrect", "stop", "don't", "hate", "terrible", "awful", "stupid"]

                has_positive = any(
                    re.search(r'\b' + re.escape(w) + r'\b', user_lower)
                    for w in positive_words
                )
                has_negative = any(
                    re.search(r'\b' + re.escape(w) + r'\b', user_lower)
                    for w in negative_words
                )

                if has_positive and not has_negative:
                    record_reward(user_input, response, 1.0, feedback_type="explicit")
                    print(f"[Reward] Positive feedback recorded")
                elif has_negative and not has_positive:
                    record_reward(user_input, response, -1.0, feedback_type="explicit")
                    print(f"[Reward] Negative feedback recorded")
                
            except KeyboardInterrupt:
                print(f"\n[{self.name}] Interrupted")
                break
            except Exception as e:
                print(f"[{self.name} Error] {e}")
                import traceback
                traceback.print_exc()
                # Generate error response from state
                try:
                    thoughts = load_working_state()
                    # Convert "Confused" to emotion dict (Confused = Fear + Surprise)
                    confused_emotion = create_emotion_graph(fear=0.4, surprise=0.3)
                    error_response = self._generate_response_from_state(
                        situation=f"I encountered an unexpected error: {str(e)[:50]}. I need to continue despite this.",
                        thoughts=thoughts,
                        emotion=confused_emotion,
                        context="An error occurred but I must continue functioning."
                    )
                    self.speak(error_response)
                except:
                    print(f"[{self.name}] Could not generate error response")
        
        self.is_running = False
        if self.virtual_world:
            try:
                self.virtual_world.stop()
            except:
                pass
        print(f"\n[{self.name}] Shutting down...")

def main():
    """Main entry point"""
    print("=" * 60)
    print("Vashrak AI Companion System")
    print("=" * 60)
    
    ai = None
    try:
        # Create AI instance
        ai = VashrakAI()
        
        # Small delay to let virtual world settle
        import time
        time.sleep(1)
        
        print(f"\n[System] Starting interactive loop...")
        print(f"[System] Press Ctrl+C to interrupt\n")
        
        # Start the interactive loop - THIS IS CRITICAL
        ai.run_interactive_loop()
        
    except KeyboardInterrupt:
        print("\n[System] Interrupted by user")
    except Exception as e:
        print(f"\n[System Error] {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Graceful shutdown
        print("\n[System] Shutting down...")
        if ai:
            ai.is_running = False
            
            # Stop virtual world
            if hasattr(ai, 'virtual_world') and ai.virtual_world:
                try:
                    ai.virtual_world.stop()
                except:
                    pass
            
            # Stop speech system
            if hasattr(ai, 'speech') and ai.speech:
                try:
                    # Give speech system time to finish
                    import time
                    time.sleep(0.5)
                except:
                    pass
        
        # Stop all sounddevice streams
        try:
            import sounddevice as sd
            sd.stop()
        except:
            pass
        
        print("[System] Shutdown complete")


if __name__ == "__main__":
    main()