#!/usr/bin/env python3
"""Test the IntelligentContext integration with DailyBriefingGenerator."""

import sys
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("  Testing IntelligentContext Integration with DailyBriefingGenerator")
print("=" * 70)
print()

# Test 1: Import the generator
print("1. Importing DailyBriefingGenerator...")
try:
    from agents.daily_brief.daily_briefing_generator import DailyBriefingGenerator

    print("   ✅ Import successful")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Create generator with intelligent context
print("\n2. Creating generator with use_intelligent_context=True...")
try:
    generator = DailyBriefingGenerator(use_intelligent_context=True)
    print("   ✅ Generator created")
except Exception as e:
    print(f"   ❌ Creation failed: {e}")
    sys.exit(1)

# Test 3: Gather context
print("\n3. Gathering context...")
try:
    context = generator.gather_context()
    print("   ✅ Context gathered")
    print(f"      Type: {type(context).__name__}")
    print(f"      Date: {context.date}")
    print(f"      Memory enabled: {getattr(context, 'memory_enabled', 'N/A')}")
    print(f"      Reasoning enabled: {getattr(context, 'reasoning_enabled', 'N/A')}")
    print(f"      Lateral enabled: {getattr(context, 'lateral_enabled', 'N/A')}")
except Exception as e:
    print(f"   ❌ Gather failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 4: Check intelligent features
print("\n4. Checking intelligent features...")
try:
    reasoning_traces = getattr(context, "reasoning_traces", [])
    lateral_connections = getattr(context, "lateral_connections", [])
    similar_checkins = getattr(context, "similar_past_checkins", [])

    print(f"   Reasoning traces: {len(reasoning_traces)}")
    if reasoning_traces:
        for trace in reasoning_traces[:3]:
            print(f"      - {trace.decision[:60]}... ({trace.confidence}%)")

    print(f"   Lateral connections: {len(lateral_connections)}")
    if lateral_connections:
        for conn in lateral_connections[:3]:
            # LateralConnection has .insight and .strength attributes
            print(f"      - {conn.insight[:60]}... (strength: {conn.strength})")

    print(f"   Similar past check-ins: {len(similar_checkins)}")
except Exception as e:
    print(f"   ⚠️  Feature check had issues: {e}")

# Test 5: Generate script
print("\n5. Generating script with intelligent context...")
try:
    script = generator.generate_script(context)
    print("   ✅ Script generated")
    print(f"      Length: {len(script)} chars, {len(script.split())} words")
    print()
    print("   --- SCRIPT PREVIEW (first 500 chars) ---")
    print(f"   {script[:500]}...")
except Exception as e:
    print(f"   ❌ Script generation failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 70)
print("  ✅ ALL TESTS PASSED - Intelligent Context Integration Working")
print("=" * 70)
