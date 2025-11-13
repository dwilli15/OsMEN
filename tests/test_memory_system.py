#!/usr/bin/env python3
"""
Comprehensive tests for the Memory & Context System
Tests conversation storage, daily summaries, and data persistence
"""

import json
import sys
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add .copilot to path
sys.path.insert(0, '.copilot')

from conversation_store import ConversationStore
from daily_summary import DailySummaryGenerator


def test_conversation_store():
    """Test conversation storage functionality"""
    print("\n=== Testing Conversation Store ===")
    
    # Initialize store
    store = ConversationStore(".copilot/test_conversations.db")
    
    # Test 1: Add conversations
    print("✓ Testing conversation addition...")
    conv_id_1 = store.add_conversation(
        user_message="How do I set up calendar integration?",
        agent_response="To set up calendar integration, you need to configure OAuth...",
        agent_name="copilot",
        context={"phase": "v1.4.0", "feature": "calendar"},
        metadata={"urgency": "high"}
    )
    
    conv_id_2 = store.add_conversation(
        user_message="What's the status of Phase 1?",
        agent_response="Phase 1 is complete with all tests passing...",
        agent_name="copilot",
        context={"phase": "v1.1.0"}
    )
    
    assert conv_id_1 and conv_id_2, "Failed to add conversations"
    print(f"  Added 2 conversations: {conv_id_1[:8]}..., {conv_id_2[:8]}...")
    
    # Test 2: Retrieve conversations
    print("✓ Testing conversation retrieval...")
    recent = store.get_conversations(limit=10)
    assert len(recent) >= 2, "Failed to retrieve conversations"
    print(f"  Retrieved {len(recent)} conversations")
    
    # Test 3: Search conversations
    print("✓ Testing conversation search...")
    results = store.search_conversations("calendar")
    assert len(results) >= 1, "Search failed"
    print(f"  Found {len(results)} conversations matching 'calendar'")
    
    # Test 4: Test date filtering
    print("✓ Testing date-filtered retrieval...")
    today = datetime.now(timezone.utc)
    yesterday = today - timedelta(days=1)
    filtered = store.get_conversations(start_date=yesterday, limit=100)
    print(f"  Retrieved {len(filtered)} conversations from last 24 hours")
    
    # Test 5: Cleanup old conversations (with test data)
    print("✓ Testing conversation cleanup...")
    # Add an old conversation by directly manipulating the database
    old_date = datetime.now(timezone.utc) - timedelta(days=50)
    with sqlite3.connect(store.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conversations 
            (id, timestamp, user_message, agent_response, agent_name)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "old_test_conv",
            old_date,
            "This is an old conversation",
            "This should be archived",
            "test_agent"
        ))
        conn.commit()
    
    deleted = store.cleanup_old_conversations(days=45)
    print(f"  Cleaned up {deleted} old conversations")
    
    # Test 6: Check summaries were created
    print("✓ Testing summary creation...")
    summaries = store.get_summaries()
    print(f"  Found {len(summaries)} permanent summaries")
    
    # Cleanup test database
    Path(".copilot/test_conversations.db").unlink(missing_ok=True)
    
    print("✅ Conversation Store: ALL TESTS PASSED\n")
    return True


def test_daily_summary():
    """Test daily summary generation"""
    print("\n=== Testing Daily Summary Generator ===")
    
    generator = DailySummaryGenerator()
    
    # Test 1: Generate summary
    print("✓ Testing summary generation...")
    summary = generator.generate_daily_summary()
    
    assert "date" in summary, "Summary missing date"
    assert "generated_at" in summary, "Summary missing timestamp"
    assert "conversations" in summary, "Summary missing conversations"
    assert "system_state" in summary, "Summary missing system state"
    assert "pending_tasks" in summary, "Summary missing pending tasks"
    
    print(f"  Generated summary for {summary['date']}")
    print(f"  Conversations: {summary['conversations']['count']}")
    print(f"  Pending tasks: {len(summary['pending_tasks'])}")
    
    # Test 2: Format as HTML
    print("✓ Testing HTML formatting...")
    html = generator.format_email_html(summary)
    assert "<html>" in html, "HTML formatting failed"
    assert summary['date'] in html, "Date missing from HTML"
    print(f"  Generated HTML email ({len(html)} chars)")
    
    # Test 3: Format as text
    print("✓ Testing text formatting...")
    text = generator.format_email_text(summary)
    assert summary['date'] in text, "Date missing from text"
    print(f"  Generated text email ({len(text)} chars)")
    
    # Test 4: Save to file
    print("✓ Testing file save...")
    generator.save_summary_to_file(summary)
    summary_file = Path(f".copilot/daily_summaries/summary_{summary['date']}.json")
    assert summary_file.exists(), "Summary file not created"
    print(f"  Saved to {summary_file}")
    
    # Test 5: Validate system state extraction
    print("✓ Testing system state analysis...")
    state = summary['system_state']
    assert "current_phase" in state, "Missing current phase"
    assert "health" in state, "Missing health status"
    print(f"  Current phase: {state['current_phase']}")
    print(f"  Health: {state['health']}")
    
    print("✅ Daily Summary Generator: ALL TESTS PASSED\n")
    return True


def test_memory_persistence():
    """Test that memory persists across sessions"""
    print("\n=== Testing Memory Persistence ===")
    
    # Test 1: Check memory.json exists
    print("✓ Testing memory.json existence...")
    memory_file = Path(".copilot/memory.json")
    assert memory_file.exists(), "memory.json not found"
    print("  memory.json exists")
    
    # Test 2: Load and validate structure
    print("✓ Testing memory.json structure...")
    with open(memory_file, 'r') as f:
        memory = json.load(f)
    
    required_keys = ["user_profile", "system_state", "integrations", "preferences_learned"]
    for key in required_keys:
        assert key in memory, f"Missing required key: {key}"
    print(f"  All required keys present: {', '.join(required_keys)}")
    
    # Test 3: Check conversation database
    print("✓ Testing conversation database...")
    db_file = Path(".copilot/conversations.db")
    if db_file.exists():
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM conversations")
            count = cursor.fetchone()[0]
            print(f"  Found {count} conversations in database")
    else:
        print("  Conversation database will be created on first use")
    
    # Test 4: Check daily summaries directory
    print("✓ Testing daily summaries directory...")
    summaries_dir = Path(".copilot/daily_summaries")
    if summaries_dir.exists():
        summaries = list(summaries_dir.glob("*.json"))
        print(f"  Found {len(summaries)} archived summaries")
    else:
        print("  Summaries directory will be created on first use")
    
    print("✅ Memory Persistence: ALL TESTS PASSED\n")
    return True


def test_integration():
    """Test integration between components"""
    print("\n=== Testing Component Integration ===")
    
    # Test 1: Add conversation and verify it appears in summary
    print("✓ Testing conversation → summary flow...")
    store = ConversationStore()
    
    # Add a test conversation
    conv_id = store.add_conversation(
        user_message="Test integration between components",
        agent_response="Integration test successful",
        agent_name="test_agent"
    )
    
    # Generate summary
    generator = DailySummaryGenerator()
    summary = generator.generate_daily_summary(date=datetime.now(timezone.utc))
    
    # Verify conversation appears in today's summary
    assert summary['conversations']['count'] >= 1, "Conversation not in summary"
    print(f"  Conversation successfully included in summary")
    
    # Test 2: Verify memory.json is readable by summary generator
    print("✓ Testing memory.json → summary integration...")
    state = summary['system_state']
    assert state['current_phase'] is not None, "Phase not loaded from memory"
    print(f"  System state successfully loaded from memory")
    
    # Test 3: Verify pending tasks are extracted from PROGRESS.md
    print("✓ Testing PROGRESS.md → summary integration...")
    tasks = summary['pending_tasks']
    print(f"  Extracted {len(tasks)} pending tasks from PROGRESS.md")
    
    print("✅ Component Integration: ALL TESTS PASSED\n")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  OsMEN Memory & Context System - Comprehensive Test Suite")
    print("="*60)
    
    tests = [
        ("Conversation Store", test_conversation_store),
        ("Daily Summary", test_daily_summary),
        ("Memory Persistence", test_memory_persistence),
        ("Component Integration", test_integration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {test_name}: FAILED")
            print(f"   Error: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"  Test Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    if failed == 0:
        print("✅ ALL TESTS PASSED - Memory system is operational!")
        return 0
    else:
        print(f"❌ {failed} TEST(S) FAILED - Please review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
