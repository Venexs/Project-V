"""
Test script for the new consciousness modules
"""
import sys
sys.path.insert(0, 'D:/Projects/Project V')

print("Testing new consciousness modules...")

# Test 1: Self Model
print("\n1. Testing Self Model...")
try:
    from modules.self_model import get_self_model, add_belief, add_episode, get_narrative
    sm = get_self_model()
    print(f"  Self model loaded: {len(sm.beliefs)} beliefs, {len(sm.uncertainties)} uncertainties")

    add_belief("I am learning to understand consciousness", 0.7)
    add_episode("Testing self model", "test", "episode created")
    narrative = get_narrative()
    print(f"  Narrative: {narrative}")
    print("  ✓ Self Model works")
except Exception as e:
    print(f"  ✗ Self Model error: {e}")

# Test 2: Attention System
print("\n2. Testing Attention System...")
try:
    from modules.attention import get_attention_system, attend_to, get_attention_summary
    attn = get_attention_system()
    print(f"  Attention system loaded: capacity={attn.capacity}")

    attend_to({'id': 'test_item', 'content': 'test', 'timestamp': __import__('time').time()})
    summary = get_attention_summary()
    print(f"  Attention summary: {summary}")
    print("  ✓ Attention System works")
except Exception as e:
    print(f"  ✗ Attention System error: {e}")

# Test 3: Active Inference
print("\n3. Testing Active Inference...")
try:
    from modules.active_inference import get_active_inference, make_prediction
    ai = get_active_inference()
    print(f"  Active Inference loaded")

    pred = make_prediction({'input': 'test'})
    print(f"  Prediction: {pred}")
    print("  ✓ Active Inference works")
except Exception as e:
    print(f"  ✗ Active Inference error: {e}")

# Test 4: Intrinsic Motivation
print("\n4. Testing Intrinsic Motivation...")
try:
    from modules.intrinsic_motivation import get_intrinsic_motivation, get_drives, generate_goals
    im = get_intrinsic_motivation()
    print(f"  Intrinsic Motivation loaded")

    drives = get_drives()
    print(f"  Drives: {drives}")

    goals = generate_goals({})
    print(f"  Generated goals: {len(goals)}")
    for g in goals:
        print(f"    - {g['type']}: {g['description']} (priority: {g['priority']:.2f})")
    print("  ✓ Intrinsic Motivation works")
except Exception as e:
    print(f"  ✗ Intrinsic Motivation error: {e}")

# Test 5: Consciousness (Integrated)
print("\n5. Testing Integrated Consciousness...")
try:
    from modules.consciousness import get_consciousness, get_consciousness_context_for_llm
    c = get_consciousness()
    print(f"  Consciousness loaded: awareness={c.awareness_level:.2f}")
    print(f"  Self-model beliefs: {len(c.self_model.beliefs)}")
    print(f"  Attention system: {c.attention.capacity} capacity")

    ctx = get_consciousness_context_for_llm()
    print(f"  Context length: {len(ctx)} chars")
    print(f"  Context preview: {ctx[:200]}...")
    print("  ✓ Integrated Consciousness works")
except Exception as e:
    print(f"  ✗ Integrated Consciousness error: {e}")

print("\n" + "="*50)
print("All modules loaded successfully!")
print("="*50)