"""
Web server to connect the React GUI with your AI system
Run this to enable the GUI interface
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import time
import os

# Import your AI modules
from modules.identity import get_name
from modules.llm import generate_response
from modules.memory import associative_recall
from modules.knowledge import retrieve_knowledge
from modules.consciousness import get_consciousness, process_with_consciousness
from modules.metacognition import get_metacognition

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for React frontend

@app.route('/')
def index():
    """Serve the GUI HTML"""
    return send_from_directory('.', 'gui.html')

# Global state
consciousness = get_consciousness()
metacog = get_metacognition()
ai_name = get_name()

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages from GUI"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Process through consciousness
        consciousness_data = process_with_consciousness(user_message, {})
        
        # Get context
        try:
            memory_results = associative_recall(user_message, top_k=3)
        except:
            memory_results = []
        
        try:
            knowledge_results = retrieve_knowledge(user_message, top_k=3)
        except:
            knowledge_results = []
        
        # Generate response
        from modules.identity import load_identity
        identity = load_identity()
        
        response = generate_response(
            user_message,
            context_memories=memory_results,
            context_knowledge=knowledge_results,
            identity=identity
        )
        
        # Get updated consciousness state
        state_data = {
            'awareness': consciousness.awareness_level,
            'confusion': consciousness.confusion_level,
            'curiosity': consciousness.curiosity_level,
            'state': _determine_state(consciousness_data, user_message),
            'response': response,
            'current_thought': consciousness.current_thought or ''
        }
        
        return jsonify(state_data)
        
    except Exception as e:
        print(f"[GUI Server Error] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'response': "I encountered an error",
            'awareness': 0.5,
            'confusion': 0.8,
            'curiosity': 0.3,
            'state': 'confused'
        }), 500

@app.route('/api/state', methods=['GET'])
def get_state():
    """Get current AI state without sending a message"""
    try:
        return jsonify({
            'awareness': consciousness.awareness_level,
            'confusion': consciousness.confusion_level,
            'curiosity': consciousness.curiosity_level,
            'state': 'idle',
            'current_thought': consciousness.current_thought or ''
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'awareness': 0.5,
            'confusion': 0.3,
            'curiosity': 0.5,
            'state': 'idle'
        }), 500

@app.route('/api/autonomous', methods=['POST'])
def trigger_autonomous():
    """Trigger autonomous thought generation"""
    try:
        from modules.llm import autonomous_thought_generation
        from modules.memory import load_memory_index
        from modules.knowledge import load_knowledge_index
        
        memory_index = load_memory_index()
        knowledge_index = load_knowledge_index()
        
        recent_memories = list(memory_index.items())[:5] if memory_index else []
        recent_knowledge = list(knowledge_index.items())[:5] if knowledge_index else []
        
        thought = autonomous_thought_generation(
            memories=recent_memories,
            knowledge=recent_knowledge
        )
        
        return jsonify({
            'thought': thought,
            'awareness': consciousness.awareness_level,
            'confusion': consciousness.confusion_level,
            'curiosity': consciousness.curiosity_level
        })
        
    except Exception as e:
        print(f"[Autonomous Error] {e}")
        return jsonify({'error': str(e)}), 500

def _determine_state(consciousness_data, user_input):
    """Determine current AI state based on consciousness and input"""
    lower_input = user_input.lower()
    
    # Check for existential questions
    if consciousness_data.get('is_self_reflective'):
        return 'thinking'
    
    # Check consciousness levels
    if consciousness_data.get('confusion_level', 0) > 0.6:
        return 'confused'
    
    if consciousness_data.get('curiosity_level', 0) > 0.7:
        return 'curious'
    
    # Check input type
    if '?' in user_input:
        return 'thinking'
    
    return 'responding'

def run_server():
    """Run the Flask server"""
    print(f"[GUI Server] Starting server for {ai_name}...")
    print("[GUI Server] Access at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    run_server()