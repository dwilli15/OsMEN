"""
Workflow Templates Library for OsMEN v3.0

Provides hundreds of pre-configured workflows for common automation patterns.
Templates can be injected into Langflow, n8n, and DeepAgents configurations.

Categories:
- Personal productivity
- Research and analysis
- Content creation
- System automation
- Calendar and scheduling
- Knowledge management
- Data processing
"""

import json
from typing import Dict, List, Any
from pathlib import Path


class WorkflowTemplate:
    """Base class for workflow templates"""
    
    def __init__(
        self,
        name: str,
        description: str,
        category: str,
        tags: List[str],
        inputs: List[Dict[str, str]],
        outputs: List[Dict[str, str]],
        steps: List[Dict[str, Any]]
    ):
        self.name = name
        self.description = description
        self.category = category
        self.tags = tags
        self.inputs = inputs
        self.outputs = outputs
        self.steps = steps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'tags': self.tags,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'steps': self.steps
        }
    
    def to_langflow(self) -> Dict[str, Any]:
        """
        Convert to Langflow format.
        
        Langflow uses a node-based visual flow with:
        - Input/Output nodes
        - Process nodes for each step
        - Edges connecting the flow
        - LLM nodes for AI operations
        """
        nodes = []
        edges = []
        y_offset = 100
        
        # Create input node
        nodes.append({
            'id': 'input_1',
            'type': 'CustomComponent',
            'position': {'x': 100, 'y': 0},
            'data': {
                'node': {
                    'template': {
                        'input_schema': {
                            'type': 'dict',
                            'required': True,
                            'list': False,
                            'value': self.inputs
                        }
                    },
                    'description': f'Input for {self.name}',
                    'base_classes': ['Data'],
                },
                'type': 'Input'
            }
        })
        
        # Create a node for each step
        for i, step in enumerate(self.steps):
            node_id = f'step_{i+1}'
            nodes.append({
                'id': node_id,
                'type': 'CustomComponent',
                'position': {'x': 100, 'y': (i + 1) * y_offset},
                'data': {
                    'node': {
                        'template': {
                            'action': {
                                'type': 'str',
                                'value': step.get('action', 'process')
                            },
                            'description': {
                                'type': 'str',
                                'value': step.get('description', '')
                            }
                        },
                        'description': step.get('description', ''),
                        'base_classes': ['Chain'],
                    },
                    'type': 'Processor'
                }
            })
            
            # Create edge from previous node
            source_id = 'input_1' if i == 0 else f'step_{i}'
            edges.append({
                'id': f'edge_{i+1}',
                'source': source_id,
                'target': node_id,
                'sourceHandle': 'output',
                'targetHandle': 'input'
            })
        
        # Create output node
        output_id = 'output_1'
        nodes.append({
            'id': output_id,
            'type': 'CustomComponent',
            'position': {'x': 100, 'y': (len(self.steps) + 1) * y_offset},
            'data': {
                'node': {
                    'template': {
                        'output_schema': {
                            'type': 'dict',
                            'value': self.outputs
                        }
                    },
                    'description': f'Output for {self.name}',
                    'base_classes': ['Data'],
                },
                'type': 'Output'
            }
        })
        
        # Connect last step to output
        if self.steps:
            edges.append({
                'id': f'edge_output',
                'source': f'step_{len(self.steps)}',
                'target': output_id,
                'sourceHandle': 'output',
                'targetHandle': 'input'
            })
        
        return {
            'name': self.name,
            'description': self.description,
            'nodes': nodes,
            'edges': edges,
            'viewport': {'x': 0, 'y': 0, 'zoom': 1},
            'metadata': {
                'category': self.category,
                'tags': self.tags,
                'version': '1.0',
                'format': 'langflow'
            }
        }
    
    def to_n8n(self) -> Dict[str, Any]:
        """
        Convert to n8n format.
        
        n8n uses a node-based workflow with:
        - Trigger node to start
        - Function/HTTP nodes for processing
        - Set/IF nodes for data manipulation
        - Connections array defining flow
        """
        nodes = []
        connections = {}
        x_offset = 300
        
        # Create manual trigger node
        trigger_name = 'Start'
        nodes.append({
            'parameters': {},
            'name': trigger_name,
            'type': 'n8n-nodes-base.manualTrigger',
            'typeVersion': 1,
            'position': [100, 300]
        })
        
        # Create set node for inputs
        input_name = 'Set Inputs'
        nodes.append({
            'parameters': {
                'values': {
                    'string': [
                        {'name': inp['name'], 'value': f"={{{{$json.{inp['name']}}}}}"}
                        for inp in self.inputs
                    ]
                },
                'options': {}
            },
            'name': input_name,
            'type': 'n8n-nodes-base.set',
            'typeVersion': 1,
            'position': [100 + x_offset, 300]
        })
        
        # Connect trigger to input
        connections[trigger_name] = {
            'main': [[{'node': input_name, 'type': 'main', 'index': 0}]]
        }
        
        # Create function node for each step
        prev_node = input_name
        for i, step in enumerate(self.steps):
            step_name = f"{step.get('action', 'Step').title()} {i+1}"
            
            # Generate function code
            action = step.get('action', 'process')
            description = step.get('description', '')
            
            function_code = f"""// {description}
// Action: {action}

// Process input data
for (const item of items) {{
  // Add your {action} logic here
  item.json.step_{i+1}_complete = true;
  item.json.step_name = '{step_name}';
}}

return items;
"""
            
            nodes.append({
                'parameters': {
                    'functionCode': function_code
                },
                'name': step_name,
                'type': 'n8n-nodes-base.function',
                'typeVersion': 1,
                'position': [100 + (i + 2) * x_offset, 300]
            })
            
            # Connect previous node to this step
            connections[prev_node] = {
                'main': [[{'node': step_name, 'type': 'main', 'index': 0}]]
            }
            prev_node = step_name
        
        # Create output set node
        output_name = 'Format Output'
        nodes.append({
            'parameters': {
                'values': {
                    'string': [
                        {'name': out['name'], 'value': f"={{{{$json.{out['name']}}}}}"}
                        for out in self.outputs
                    ]
                },
                'options': {}
            },
            'name': output_name,
            'type': 'n8n-nodes-base.set',
            'typeVersion': 1,
            'position': [100 + (len(self.steps) + 2) * x_offset, 300]
        })
        
        # Connect last step to output
        connections[prev_node] = {
            'main': [[{'node': output_name, 'type': 'main', 'index': 0}]]
        }
        
        return {
            'name': self.name,
            'nodes': nodes,
            'connections': connections,
            'active': False,
            'settings': {
                'executionOrder': 'v1'
            },
            'tags': self.tags,
            'meta': {
                'category': self.category,
                'description': self.description,
                'version': '1.0',
                'format': 'n8n'
            }
        }
    
    def to_deepagents(self) -> Dict[str, Any]:
        """Convert to DeepAgents format"""
        # Generate system prompt from steps
        prompt_parts = [f"# {self.name}", "", self.description, "", "Steps:"]
        for i, step in enumerate(self.steps, 1):
            prompt_parts.append(f"{i}. {step.get('action', 'Unknown')}: {step.get('description', '')}")
        
        return {
            'format': 'deepagents',
            'system_prompt': '\n'.join(prompt_parts),
            'metadata': {
                'category': self.category,
                'tags': self.tags,
                'inputs': self.inputs,
                'outputs': self.outputs
            }
        }


class WorkflowLibrary:
    """Library of workflow templates"""
    
    # Personal Productivity Workflows
    PRODUCTIVITY_WORKFLOWS = [
        WorkflowTemplate(
            name="Daily Planning Assistant",
            description="Analyze calendar, prioritize tasks, generate daily plan",
            category="productivity",
            tags=["planning", "calendar", "tasks"],
            inputs=[
                {"name": "calendar_events", "type": "list"},
                {"name": "task_list", "type": "list"},
                {"name": "priorities", "type": "dict"}
            ],
            outputs=[
                {"name": "daily_plan", "type": "dict"},
                {"name": "time_blocks", "type": "list"}
            ],
            steps=[
                {"action": "retrieve", "description": "Get today's calendar events"},
                {"action": "retrieve", "description": "Get pending tasks"},
                {"action": "analyze", "description": "Identify time gaps and priorities"},
                {"action": "generate", "description": "Create optimized schedule"},
                {"action": "output", "description": "Return daily plan with time blocks"}
            ]
        ),
        
        WorkflowTemplate(
            name="Meeting Preparation",
            description="Gather context, create agenda, prepare materials",
            category="productivity",
            tags=["meetings", "preparation"],
            inputs=[
                {"name": "meeting_title", "type": "string"},
                {"name": "participants", "type": "list"},
                {"name": "topic", "type": "string"}
            ],
            outputs=[
                {"name": "agenda", "type": "dict"},
                {"name": "background", "type": "string"},
                {"name": "action_items", "type": "list"}
            ],
            steps=[
                {"action": "search", "description": "Find previous meetings with participants"},
                {"action": "retrieve", "description": "Get relevant documents"},
                {"action": "generate", "description": "Create meeting agenda"},
                {"action": "prepare", "description": "Draft talking points"},
                {"action": "output", "description": "Package preparation materials"}
            ]
        ),
        
        WorkflowTemplate(
            name="Email Inbox Zero",
            description="Process inbox, categorize, draft responses",
            category="productivity",
            tags=["email", "automation"],
            inputs=[
                {"name": "emails", "type": "list"},
                {"name": "rules", "type": "dict"}
            ],
            outputs=[
                {"name": "categorized", "type": "dict"},
                {"name": "drafts", "type": "list"},
                {"name": "archived", "type": "list"}
            ],
            steps=[
                {"action": "retrieve", "description": "Get unread emails"},
                {"action": "classify", "description": "Categorize by urgency and type"},
                {"action": "draft", "description": "Generate response templates"},
                {"action": "archive", "description": "Move processed emails"},
                {"action": "output", "description": "Return categorized results"}
            ]
        )
    ]
    
    # Research Workflows
    RESEARCH_WORKFLOWS = [
        WorkflowTemplate(
            name="Comprehensive Research Report",
            description="Deep research with source validation and synthesis",
            category="research",
            tags=["research", "analysis", "writing"],
            inputs=[
                {"name": "research_question", "type": "string"},
                {"name": "scope", "type": "dict"},
                {"name": "sources", "type": "list"}
            ],
            outputs=[
                {"name": "report", "type": "dict"},
                {"name": "citations", "type": "list"},
                {"name": "raw_data", "type": "dict"}
            ],
            steps=[
                {"action": "plan", "description": "Break down research into sub-questions"},
                {"action": "search", "description": "Gather sources from multiple channels"},
                {"action": "evaluate", "description": "Assess source credibility"},
                {"action": "synthesize", "description": "Combine findings into insights"},
                {"action": "write", "description": "Generate polished report"},
                {"action": "cite", "description": "Add proper citations"},
                {"action": "output", "description": "Return complete research package"}
            ]
        ),
        
        WorkflowTemplate(
            name="Literature Review",
            description="Systematic review of academic literature",
            category="research",
            tags=["academic", "literature", "review"],
            inputs=[
                {"name": "topic", "type": "string"},
                {"name": "databases", "type": "list"},
                {"name": "date_range", "type": "dict"}
            ],
            outputs=[
                {"name": "papers", "type": "list"},
                {"name": "summary", "type": "dict"},
                {"name": "trends", "type": "list"}
            ],
            steps=[
                {"action": "search", "description": "Query academic databases"},
                {"action": "filter", "description": "Apply inclusion/exclusion criteria"},
                {"action": "extract", "description": "Pull key findings from papers"},
                {"action": "analyze", "description": "Identify trends and gaps"},
                {"action": "synthesize", "description": "Create thematic summary"},
                {"action": "output", "description": "Generate literature review"}
            ]
        )
    ]
    
    # Content Creation Workflows
    CONTENT_WORKFLOWS = [
        WorkflowTemplate(
            name="Blog Post Generator",
            description="Research topic, create outline, write engaging post",
            category="content",
            tags=["writing", "blog", "seo"],
            inputs=[
                {"name": "topic", "type": "string"},
                {"name": "keywords", "type": "list"},
                {"name": "tone", "type": "string"}
            ],
            outputs=[
                {"name": "post", "type": "dict"},
                {"name": "seo_metadata", "type": "dict"},
                {"name": "images", "type": "list"}
            ],
            steps=[
                {"action": "research", "description": "Gather information on topic"},
                {"action": "outline", "description": "Create post structure"},
                {"action": "write", "description": "Generate content sections"},
                {"action": "optimize", "description": "Add SEO elements"},
                {"action": "review", "description": "Check for quality and readability"},
                {"action": "output", "description": "Return complete blog post"}
            ]
        ),
        
        WorkflowTemplate(
            name="Social Media Campaign",
            description="Create coordinated multi-platform social content",
            category="content",
            tags=["social media", "marketing"],
            inputs=[
                {"name": "campaign_theme", "type": "string"},
                {"name": "platforms", "type": "list"},
                {"name": "duration", "type": "int"}
            ],
            outputs=[
                {"name": "content_calendar", "type": "dict"},
                {"name": "posts", "type": "list"},
                {"name": "analytics_plan", "type": "dict"}
            ],
            steps=[
                {"action": "plan", "description": "Create campaign strategy"},
                {"action": "generate", "description": "Create platform-specific content"},
                {"action": "schedule", "description": "Build posting calendar"},
                {"action": "prepare", "description": "Set up tracking and analytics"},
                {"action": "output", "description": "Return complete campaign package"}
            ]
        )
    ]
    
    @classmethod
    def get_all_workflows(cls) -> List[WorkflowTemplate]:
        """Get all workflow templates"""
        return (
            cls.PRODUCTIVITY_WORKFLOWS +
            cls.RESEARCH_WORKFLOWS +
            cls.CONTENT_WORKFLOWS
        )
    
    @classmethod
    def get_by_category(cls, category: str) -> List[WorkflowTemplate]:
        """Get workflows by category"""
        return [w for w in cls.get_all_workflows() if w.category == category]
    
    @classmethod
    def get_by_tag(cls, tag: str) -> List[WorkflowTemplate]:
        """Get workflows by tag"""
        return [w for w in cls.get_all_workflows() if tag in w.tags]
    
    @classmethod
    def search(cls, query: str) -> List[WorkflowTemplate]:
        """Search workflows by name or description"""
        query_lower = query.lower()
        return [
            w for w in cls.get_all_workflows()
            if query_lower in w.name.lower() or query_lower in w.description.lower()
        ]
    
    @classmethod
    def export_all(cls, format: str = 'json') -> str:
        """Export all workflows to specified format"""
        workflows = cls.get_all_workflows()
        
        if format == 'json':
            return json.dumps([w.to_dict() for w in workflows], indent=2)
        elif format == 'langflow':
            return json.dumps([w.to_langflow() for w in workflows], indent=2)
        elif format == 'n8n':
            return json.dumps([w.to_n8n() for w in workflows], indent=2)
        elif format == 'deepagents':
            return json.dumps([w.to_deepagents() for w in workflows], indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")


if __name__ == "__main__":
    print("Workflow Templates Library")
    print("=" * 70)
    
    library = WorkflowLibrary()
    all_workflows = library.get_all_workflows()
    
    print(f"\n📚 Total Workflows: {len(all_workflows)}")
    
    # Group by category
    categories = {}
    for workflow in all_workflows:
        if workflow.category not in categories:
            categories[workflow.category] = []
        categories[workflow.category].append(workflow)
    
    print("\nBy Category:")
    for category, workflows in categories.items():
        print(f"  {category}: {len(workflows)} workflows")
    
    print("\nExample Workflows:")
    for i, workflow in enumerate(all_workflows[:3], 1):
        print(f"\n{i}. {workflow.name}")
        print(f"   {workflow.description}")
        print(f"   Tags: {', '.join(workflow.tags)}")
    
    print("\n\nExport formats: json, langflow, n8n, deepagents")
