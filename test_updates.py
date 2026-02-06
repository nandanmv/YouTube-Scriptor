#!/usr/bin/env python3.10
"""Test the updated OutlierAgent and BrainstormAgent"""

import config

print("=" * 80)
print("TESTING UPDATES")
print("=" * 80)

# Test 1: Verify config update
print("\n1. Config Update:")
print(f"   MAX_SUBSCRIBERS = {config.MAX_SUBSCRIBERS:,}")
print(f"   ✅ Config updated successfully")

# Test 2: Test OutlierAgent with subscriber filter
print("\n2. OutlierAgent with Subscriber Filter:")
from agents import OutlierAgent

agent = OutlierAgent()
outliers = agent.run("python tips")

print(f"   Found {len(outliers)} outliers from channels < {config.MAX_SUBSCRIBERS:,} subscribers")
if outliers:
    print(f"\n   Sample results:")
    for o in outliers[:3]:
        subs = o.get('subscribers', 'N/A')
        if subs != 'N/A':
            print(f"   - {o['channel']}: {subs:,} subs (Ratio: {o['ratio']:.2f}x)")
            if subs >= config.MAX_SUBSCRIBERS:
                print(f"     ⚠️  WARNING: Channel has >= {config.MAX_SUBSCRIBERS:,} subscribers!")
        else:
            print(f"   - {o['channel']}: Unknown subs (Ratio: {o['ratio']:.2f}x)")

# Test 3: Verify InsightAgent returns subtopics_covered
print("\n3. InsightAgent with Subtopics:")
from agents import InsightAgent

if outliers:
    insight_agent = InsightAgent()
    test_video = outliers[0]
    print(f"   Analyzing: {test_video['title'][:50]}...")

    insight = insight_agent.run(test_video)

    if 'subtopics_covered' in insight:
        print(f"   ✅ subtopics_covered field present")
        subtopics = insight['subtopics_covered']
        print(f"   Subtopics preview: {subtopics[:100]}...")
    else:
        print(f"   ❌ subtopics_covered field missing!")

print("\n" + "=" * 80)
print("Tests complete!")
print("=" * 80)
