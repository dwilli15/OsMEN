#!/usr/bin/env python3
"""
Workflow Conversion and Utilization Scripts

Provides scripts to convert workflows between different formats:
- OsMEN native → Langflow
- OsMEN native → n8n
- OsMEN native → DeepAgents
- Langflow → OsMEN
- n8n → OsMEN

Also includes utilities for workflow deployment and execution.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from integrations.workflow_templates import WorkflowLibrary, WorkflowTemplate


class WorkflowConverter:
    """Convert workflows between different formats"""
    
    @staticmethod
    def to_langflow(workflow: WorkflowTemplate) -> Dict[str, Any]:
        """
        Convert OsMEN workflow to Langflow format.
        
        Langflow uses a node-based visual flow with:
        - Nodes for each step
        - Edges connecting nodes
        - Data schemas for inputs/outputs
        """
        nodes = []
        edges = []
        
        # Create input node
        nodes.append({
            'id': 'input_node',
            'type': 'InputNode',
            'position': {'x': 0, 'y': 0},
            'data': {
                'inputs': workflow.inputs,
                'label': 'Input'
            }
        })
        
        # Create step nodes
        for i, step in enumerate(workflow.steps):
            node_id = f"step_{i}"
            nodes.append({
                'id': node_id,
                'type': 'ProcessNode',
                'position': {'x': 0, 'y': (i + 1) * 100},
                'data': {
                    'action': step.get('action', 'process'),
                    'description': step.get('description', ''),
                    'label': f"Step {i + 1}: {step.get('action', 'process')}"
                }
            })
            
            # Create edge from previous node
            prev_id = 'input_node' if i == 0 else f"step_{i-1}"
            edges.append({
                'id': f"edge_{i}",
                'source': prev_id,
                'target': node_id
            })
        
        # Create output node
        nodes.append({
            'id': 'output_node',
            'type': 'OutputNode',
            'position': {'x': 0, 'y': (len(workflow.steps) + 1) * 100},
            'data': {
                'outputs': workflow.outputs,
                'label': 'Output'
            }
        })
        
        # Connect last step to output
        if workflow.steps:
            edges.append({
                'id': f"edge_final",
                'source': f"step_{len(workflow.steps)-1}",
                'target': 'output_node'
            })
        
        return {
            'name': workflow.name,
            'description': workflow.description,
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'category': workflow.category,
                'tags': workflow.tags,
                'format': 'langflow'
            }
        }
    
    @staticmethod
    def to_n8n(workflow: WorkflowTemplate) -> Dict[str, Any]:
        """
        Convert OsMEN workflow to n8n format.
        
        n8n uses a node-based workflow with:
        - Trigger nodes
        - Function nodes
        - Output nodes
        """
        nodes = []
        connections = {}
        
        # Create trigger node
        nodes.append({
            'parameters': {
                'mode': 'manual'
            },
            'name': 'Manual Trigger',
            'type': 'n8n-nodes-base.manualTrigger',
            'typeVersion': 1,
            'position': [250, 300],
            'id': 'trigger_node'
        })
        
        connections['Manual Trigger'] = {
            'main': [[{'node': workflow.steps[0].get('action', 'Step 1') if workflow.steps else 'Output', 'type': 'main', 'index': 0}]]
        }
        
        # Create step nodes
        for i, step in enumerate(workflow.steps):
            node_name = f"{step.get('action', 'Step')} {i + 1}"
            nodes.append({
                'parameters': {
                    'functionCode': f"// {step.get('description', '')}\nreturn items;"
                },
                'name': node_name,
                'type': 'n8n-nodes-base.function',
                'typeVersion': 1,
                'position': [250 + (i + 1) * 200, 300],
                'id': f"step_{i}"
            })
            
            # Create connection to next node
            next_node = f"{workflow.steps[i+1].get('action', 'Step')} {i + 2}" if i < len(workflow.steps) - 1 else 'Output'
            connections[node_name] = {
                'main': [[{'node': next_node, 'type': 'main', 'index': 0}]]
            }
        
        # Create output node
        nodes.append({
            'parameters': {},
            'name': 'Output',
            'type': 'n8n-nodes-base.noOp',
            'typeVersion': 1,
            'position': [250 + (len(workflow.steps) + 1) * 200, 300],
            'id': 'output_node'
        })
        
        return {
            'name': workflow.name,
            'nodes': nodes,
            'connections': connections,
            'active': False,
            'settings': {
                'executionOrder': 'v1'
            },
            'metadata': {
                'description': workflow.description,
                'category': workflow.category,
                'tags': workflow.tags,
                'format': 'n8n'
            }
        }
    
    @staticmethod
    def to_deepagents(workflow: WorkflowTemplate) -> Dict[str, Any]:
        """
        Convert OsMEN workflow to DeepAgents system prompt.
        
        DeepAgents uses natural language prompts to guide agent behavior.
        """
        prompt_sections = [
            f"# {workflow.name}",
            "",
            workflow.description,
            "",
            "## Inputs",
        ]
        
        for inp in workflow.inputs:
            prompt_sections.append(f"- {inp['name']} ({inp['type']})")
        
        prompt_sections.extend([
            "",
            "## Workflow Steps",
        ])
        
        for i, step in enumerate(workflow.steps, 1):
            action = step.get('action', 'process').upper()
            desc = step.get('description', '')
            prompt_sections.append(f"{i}. **{action}**: {desc}")
        
        prompt_sections.extend([
            "",
            "## Expected Outputs",
        ])
        
        for out in workflow.outputs:
            prompt_sections.append(f"- {out['name']} ({out['type']})")
        
        prompt_sections.extend([
            "",
            "## Best Practices",
            "- Follow each step in sequence",
            "- Validate inputs before processing",
            "- Handle errors gracefully",
            "- Provide clear progress updates",
            "- Ensure all outputs are generated",
        ])
        
        return {
            'format': 'deepagents',
            'system_prompt': '\n'.join(prompt_sections),
            'metadata': {
                'name': workflow.name,
                'description': workflow.description,
                'category': workflow.category,
                'tags': workflow.tags,
                'inputs': workflow.inputs,
                'outputs': workflow.outputs
            }
        }


class WorkflowDeployer:
    """Deploy workflows to different platforms"""
    
    def __init__(self, config_dir: str = None):
        self.config_dir = config_dir or Path.home() / '.osmen' / 'workflows'
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def deploy_to_langflow(self, workflow: WorkflowTemplate, output_path: str = None):
        """Deploy workflow to Langflow"""
        converted = WorkflowConverter.to_langflow(workflow)
        
        if output_path is None:
            output_path = self.config_dir / 'langflow' / f"{workflow.name.replace(' ', '_').lower()}.json"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(converted, f, indent=2)
        
        print(f"✅ Deployed to Langflow: {output_path}")
        return output_path
    
    def deploy_to_n8n(self, workflow: WorkflowTemplate, output_path: str = None):
        """Deploy workflow to n8n"""
        converted = WorkflowConverter.to_n8n(workflow)
        
        if output_path is None:
            output_path = self.config_dir / 'n8n' / f"{workflow.name.replace(' ', '_').lower()}.json"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(converted, f, indent=2)
        
        print(f"✅ Deployed to n8n: {output_path}")
        return output_path
    
    def deploy_to_deepagents(self, workflow: WorkflowTemplate, output_path: str = None):
        """Deploy workflow to DeepAgents"""
        converted = WorkflowConverter.to_deepagents(workflow)
        
        if output_path is None:
            output_path = self.config_dir / 'deepagents' / f"{workflow.name.replace(' ', '_').lower()}.json"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(converted, f, indent=2)
        
        print(f"✅ Deployed to DeepAgents: {output_path}")
        return output_path
    
    def deploy_all(self, workflow: WorkflowTemplate, platforms: List[str] = None):
        """Deploy workflow to multiple platforms"""
        if platforms is None:
            platforms = ['langflow', 'n8n', 'deepagents']
        
        results = {}
        for platform in platforms:
            if platform == 'langflow':
                results['langflow'] = self.deploy_to_langflow(workflow)
            elif platform == 'n8n':
                results['n8n'] = self.deploy_to_n8n(workflow)
            elif platform == 'deepagents':
                results['deepagents'] = self.deploy_to_deepagents(workflow)
        
        return results


def main():
    """CLI for workflow conversion and deployment"""
    parser = argparse.ArgumentParser(
        description='Convert and deploy OsMEN workflows'
    )
    parser.add_argument(
        'action',
        choices=['list', 'convert', 'deploy'],
        help='Action to perform'
    )
    parser.add_argument(
        '--workflow',
        help='Workflow name to convert/deploy'
    )
    parser.add_argument(
        '--format',
        choices=['langflow', 'n8n', 'deepagents', 'all'],
        default='all',
        help='Target format'
    )
    parser.add_argument(
        '--output',
        help='Output file path'
    )
    parser.add_argument(
        '--category',
        help='Filter workflows by category'
    )
    
    args = parser.parse_args()
    
    library = WorkflowLibrary()
    
    if args.action == 'list':
        # List all workflows
        workflows = library.get_all_workflows()
        if args.category:
            workflows = [w for w in workflows if w.category == args.category]
        
        print(f"\n📚 Available Workflows ({len(workflows)}):\n")
        for i, workflow in enumerate(workflows, 1):
            print(f"{i}. {workflow.name}")
            print(f"   Category: {workflow.category}")
            print(f"   Tags: {', '.join(workflow.tags)}")
            print(f"   {workflow.description}")
            print()
    
    elif args.action == 'convert':
        if not args.workflow:
            print("❌ --workflow required for convert action")
            return
        
        # Find workflow
        workflows = library.search(args.workflow)
        if not workflows:
            print(f"❌ Workflow not found: {args.workflow}")
            return
        
        workflow = workflows[0]
        converter = WorkflowConverter()
        
        if args.format == 'langflow':
            result = converter.to_langflow(workflow)
        elif args.format == 'n8n':
            result = converter.to_n8n(workflow)
        elif args.format == 'deepagents':
            result = converter.to_deepagents(workflow)
        else:  # all
            result = {
                'langflow': converter.to_langflow(workflow),
                'n8n': converter.to_n8n(workflow),
                'deepagents': converter.to_deepagents(workflow)
            }
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"✅ Converted workflow saved to: {args.output}")
        else:
            print(json.dumps(result, indent=2))
    
    elif args.action == 'deploy':
        if not args.workflow:
            print("❌ --workflow required for deploy action")
            return
        
        # Find workflow
        workflows = library.search(args.workflow)
        if not workflows:
            print(f"❌ Workflow not found: {args.workflow}")
            return
        
        workflow = workflows[0]
        deployer = WorkflowDeployer()
        
        if args.format == 'all':
            results = deployer.deploy_all(workflow)
            print(f"\n✅ Deployed to all platforms")
            for platform, path in results.items():
                print(f"   {platform}: {path}")
        elif args.format == 'langflow':
            deployer.deploy_to_langflow(workflow, args.output)
        elif args.format == 'n8n':
            deployer.deploy_to_n8n(workflow, args.output)
        elif args.format == 'deepagents':
            deployer.deploy_to_deepagents(workflow, args.output)


if __name__ == '__main__':
    main()
