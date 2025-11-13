#!/usr/bin/env python3
"""
Start OsMEN Web Dashboard
Simple script to run the web interface without Docker
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables
os.environ.setdefault('WEB_PORT', '8000')
os.environ.setdefault('WEB_HOST', '0.0.0.0')
os.environ.setdefault('LANGFLOW_URL', 'http://localhost:7860')
os.environ.setdefault('N8N_URL', 'http://localhost:5678')
os.environ.setdefault('QDRANT_URL', 'http://localhost:6333')

if __name__ == "__main__":
    import uvicorn
    
    print("="*70)
    print("OsMEN Agent Hub Starting...")
    print("="*70)
    print(f"Dashboard: http://localhost:8000")
    print(f"Langflow:  http://localhost:7860")
    print(f"n8n:       http://localhost:5678")
    print(f"Qdrant:    http://localhost:6333")
    print("="*70)
    print()
    
    try:
        uvicorn.run(
            "web.main:app",
            host=os.getenv('WEB_HOST', '0.0.0.0'),
            port=int(os.getenv('WEB_PORT', '8000')),
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nShutting down OsMEN Agent Hub...")
    except Exception as e:
        print(f"\nError starting web dashboard: {e}")
        print("\nMake sure you have installed dependencies:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
