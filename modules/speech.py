"""Speech-to-text and text-to-speech functionality"""
import speech_recognition as sr
import pyttsx3
import threading
import queue
from typing import Optional

class SpeechHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        self.audio_queue = queue.Queue()
        self.is_listening = False
        
        # Configure TTS
        voices = self.tts_engine.getProperty('voices')
        if voices:
            self.tts_engine.setProperty('voice', voices[0].id)
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 0.8)
        
        # Calibrate microphone
        print("[Speech] Calibrating microphone...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("[Speech] Microphone calibrated")
    
    def listen(self, timeout=5, phrase_time_limit=10) -> Optional[str]:
        """
        Listen for speech and convert to text.
        Returns transcribed text or None if no speech detected.
        """
        try:
            with self.microphone as source:
                print("[Listening] Speak now...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            
            try:
                text = self.recognizer.recognize_google(audio)
                print(f"[Heard] {text}")
                return text
            except sr.UnknownValueError:
                print("[Speech] Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"[Speech] Error with speech recognition service: {e}")
                return None
        except sr.WaitTimeoutError:
            print("[Speech] No speech detected")
            return None
        except Exception as e:
            print(f"[Speech] Error: {e}")
            return None
    
    def speak(self, text: str):
        """Convert text to speech"""
        print(f"[Speaking] {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
    
    def speak_async(self, text: str):
        """Speak asynchronously in a separate thread"""
        thread = threading.Thread(target=self.speak, args=(text,))
        thread.daemon = True
        thread.start()

# Global instance
_speech_handler = None

def get_speech_handler():
    """Get or create global speech handler"""
    global _speech_handler
    if _speech_handler is None:
        _speech_handler = SpeechHandler()
    return _speech_handler

