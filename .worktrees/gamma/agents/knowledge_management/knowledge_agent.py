#!/usr/bin/env python3
"""
Knowledge Management Agent
Manages knowledge base using Obsidian integration
"""

import os
import json
import logging
from typing import Dict, List
from datetime import datetime
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from tools.obsidian.obsidian_integration import ObsidianIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeAgent:
    """Agent for knowledge management with Obsidian"""
    
    def __init__(self):
        try:
            self.obsidian = ObsidianIntegration()
            logger.info("KnowledgeAgent initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing KnowledgeAgent: {e}")
            raise
        
    def capture_note(self, title: str, content: str, tags: List[str] = None, 
                    folder: str = '') -> Dict:
        """Capture a new note to the knowledge base"""
        try:
            result = self.obsidian.create_note(
                title=title,
                content=content,
                tags=tags or [],
                folder=folder,
                frontmatter={
                    'created': datetime.now().isoformat(),
                    'source': 'osmen'
                }
            )
            logger.info(f"Note '{title}' created successfully")
            return result
        except Exception as e:
            logger.error(f"Error capturing note '{title}': {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': f'Failed to create note: {title}'
            }
    
    def search_knowledge(self, query: str) -> List[Dict]:
        """Search the knowledge base"""
        try:
            results = self.obsidian.search_notes(query)
            logger.info(f"Search for '{query}' returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error searching knowledge base for '{query}': {e}")
            return []
    
    def get_note(self, note_path: str) -> Dict:
        """Retrieve a specific note"""
        try:
            note = self.obsidian.read_note(note_path)
            logger.debug(f"Retrieved note: {note_path}")
            return note
        except Exception as e:
            logger.error(f"Error retrieving note '{note_path}': {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': f'Failed to retrieve note: {note_path}'
            }
    
    def update_knowledge(self, note_path: str, new_content: str, append: bool = True) -> Dict:
        """Update existing knowledge"""
        try:
            result = self.obsidian.update_note(note_path, new_content, append=append)
            logger.info(f"Note '{note_path}' updated successfully")
            return result
        except Exception as e:
            logger.error(f"Error updating note '{note_path}': {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': f'Failed to update note: {note_path}'
            }
    
    def find_related(self, note_path: str) -> Dict:
        """Find notes related to the given note"""
        try:
            # Get backlinks
            backlinks = self.obsidian.get_backlinks(note_path)
            
            # Get forward links
            note = self.obsidian.read_note(note_path)
            forward_links = note.get('links', [])
            
            logger.info(f"Found {len(backlinks)} backlinks and {len(forward_links)} forward links for '{note_path}'")
            return {
                'backlinks': backlinks,
                'forward_links': forward_links,
                'note': note_path
            }
        except Exception as e:
            logger.error(f"Error finding related notes for '{note_path}': {e}")
            return {
                'backlinks': [],
                'forward_links': [],
                'note': note_path,
                'error': str(e)
            }
    
    def get_knowledge_graph(self) -> Dict:
        """Export the complete knowledge graph"""
        try:
            graph = self.obsidian.export_graph()
            logger.info("Knowledge graph exported successfully")
            return graph
        except Exception as e:
            logger.error(f"Error exporting knowledge graph: {e}")
            return {
                'nodes': [],
                'edges': [],
                'error': str(e)
            }
    
    def create_daily_note(self, content: str = '') -> Dict:
        """Create a daily note for today"""
        try:
            today = datetime.now()
            title = today.strftime('%Y-%m-%d')
            folder = 'Daily Notes'
            
            daily_content = f"""## Tasks
- [ ] Review daily brief
- [ ] Check system status

## Notes
{content}

## Links
- [[{(today.replace(day=today.day-1)).strftime('%Y-%m-%d')}|Yesterday]]
- [[{(today.replace(day=today.day+1)).strftime('%Y-%m-%d')}|Tomorrow]]
"""
        
        return self.obsidian.create_note(
            title=title,
            content=daily_content,
            folder=folder,
            tags=['daily-note'],
            frontmatter={
                'date': title,
                'type': 'daily-note'
            }
        )
    
    def organize_notes(self) -> Dict:
        """Analyze and suggest organization improvements"""
        notes = self.obsidian.list_notes()
        graph = self.obsidian.export_graph()
        
        # Find orphan notes (no links in or out)
        linked_notes = set()
        for edge in graph['edges']:
            linked_notes.add(edge['source'])
            linked_notes.add(edge['target'])
        
        all_notes = {node['id'] for node in graph['nodes']}
        orphans = all_notes - linked_notes
        
        return {
            'total_notes': len(notes),
            'linked_notes': len(linked_notes),
            'orphan_notes': list(orphans),
            'graph_density': len(graph['edges']) / max(len(notes), 1)
        }
    
    def generate_summary(self, folder: str = '') -> Dict:
        """Generate a summary of knowledge base"""
        notes = self.obsidian.list_notes(folder)
        
        summary = {
            'total_notes': len(notes),
            'folder': folder or 'all',
            'recent_notes': sorted(notes, key=lambda x: x['modified'], reverse=True)[:10]
        }
        
        return summary


def main():
    """Test the knowledge agent"""
    agent = KnowledgeAgent()
    
    # Example: Create a note
    result = agent.capture_note(
        title="OsMEN Knowledge Base",
        content="This is the main entry point for OsMEN knowledge management.",
        tags=["osmen", "knowledge-base"]
    )
    print("Created note:")
    print(json.dumps(result, indent=2))
    
    # Example: Get summary
    summary = agent.generate_summary()
    print("\nKnowledge base summary:")
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
