#!/usr/bin/env python3
"""Test enhanced Obsidian integration"""
import asyncio
import sys

sys.path.insert(0, 'D:/OsMEN')

from pathlib import Path

from integrations.obsidian_enhanced import (EnhancedObsidianIntegration,
                                            ObsidianConfig)


async def test():
    config = ObsidianConfig(vault_path=Path('D:/OsMEN/obsidian-vault'))
    obs = EnhancedObsidianIntegration(config)
    
    print('=== Enhanced Obsidian Integration ===')
    print(f'Vault exists: {obs.vault_exists}')
    
    # List notes
    notes = obs.list_notes()
    print(f'Notes found: {len(notes)}')
    
    # Read a note
    if notes:
        note = obs.read_note(notes[0]['path'])
        if note:
            print(f'\nFirst note: {note.title}')
            print(f'  Tags: {note.tags}')
            print(f'  Links: {note.links}')
            print(f'  Words: {note.word_count}')
    
    # Build backlinks
    backlinks = obs.build_backlinks()
    print(f'\nBacklinks index: {len(backlinks)} notes with incoming links')
    
    # Sync to ChromaDB
    print('\nSyncing to ChromaDB...')
    result = await obs.sync_to_chroma()
    print(f'Sync result: {result}')
    
    # Semantic search
    print('\nSemantic search for "algorithm"...')
    results = obs.search_semantic('algorithm analysis complexity', limit=3)
    for r in results:
        print(f'  - {r["title"]} (score: {r["score"]:.3f})')
    
    # Unified search
    print('\nUnified search for "course"...')
    results = obs.search_unified('course schedule assignments', limit=5)
    for r in results:
        print(f'  - {r["title"]} (score: {r.get("combined_score", 0):.3f})')

if __name__ == '__main__':
    asyncio.run(test())
        print(f'  - {r["title"]} (score: {r.get("combined_score", 0):.3f})')

if __name__ == '__main__':
    asyncio.run(test())
        print(f'  - {r["title"]} (score: {r.get("combined_score", 0):.3f})')

if __name__ == '__main__':
    asyncio.run(test())
