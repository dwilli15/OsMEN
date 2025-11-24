// OsMEN v3.0 - Agent Status Dashboard JavaScript

// Agent data
const agentsData = {
    backend: {
        name: 'BackendAgent',
        icon: '🔧',
        domain: 'Integration & API Domain',
        color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        completed: 7,
        total: 10,
        status: 'active',
        tasks: [
            { id: 'BE-001', text: 'Quantum retrieval implementation', priority: 'high', completed: true },
            { id: 'BE-002', text: 'Interference scoring', priority: 'high', completed: true },
            { id: 'BE-003', text: 'Context-based collapse', priority: 'medium', completed: true },
            { id: 'BE-004', text: 'Langflow conversion', priority: 'medium', completed: true },
            { id: 'BE-005', text: 'n8n conversion', priority: 'medium', completed: true },
            { id: 'BE-006', text: 'Token refresh daemon', priority: 'high', completed: true },
            { id: 'BE-007', text: 'OAuth webhook server', priority: 'medium', completed: true },
            { id: 'BE-009', text: 'Integration test suite', priority: 'high', completed: false },
            { id: 'BE-010', text: 'Semantic embedding model', priority: 'medium', completed: false },
            { id: 'BE-008', text: 'Zoom OAuth integration', priority: 'low', completed: false }
        ]
    },
    frontend: {
        name: 'FrontendAgent',
        icon: '🎨',
        domain: 'Web Dashboard Domain',
        color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        completed: 1,
        total: 10,
        status: 'active',
        tasks: [
            { id: 'FE-001', text: 'Agent status dashboard', priority: 'high', completed: true },
            { id: 'FE-002', text: 'Workflow builder UI', priority: 'high', completed: false },
            { id: 'FE-005', text: 'OAuth setup wizard', priority: 'high', completed: false },
            { id: 'FE-003', text: 'Calendar view component', priority: 'medium', completed: false },
            { id: 'FE-004', text: 'Task kanban board', priority: 'medium', completed: false },
            { id: 'FE-006', text: 'Real-time updates (WebSocket)', priority: 'medium', completed: false },
            { id: 'FE-008', text: 'Mobile-responsive design', priority: 'medium', completed: false },
            { id: 'FE-010', text: 'Settings page', priority: 'medium', completed: false },
            { id: 'FE-007', text: 'Analytics dashboard', priority: 'low', completed: false },
            { id: 'FE-009', text: 'Dark mode support', priority: 'low', completed: false }
        ]
    },
    devops: {
        name: 'DevOpsAgent',
        icon: '🚀',
        domain: 'Infrastructure Domain',
        color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        completed: 1,
        total: 10,
        status: 'active',
        tasks: [
            { id: 'DO-008', text: 'CI/CD pipeline setup', priority: 'high', completed: true },
            { id: 'DO-001', text: 'SSL/TLS automation', priority: 'high', completed: false },
            { id: 'DO-002', text: 'Prometheus monitoring', priority: 'high', completed: false },
            { id: 'DO-004', text: 'Automated backups', priority: 'high', completed: false },
            { id: 'DO-005', text: 'Secrets manager integration', priority: 'high', completed: false },
            { id: 'DO-006', text: 'Production Docker compose', priority: 'high', completed: false },
            { id: 'DO-003', text: 'Grafana dashboards', priority: 'medium', completed: false },
            { id: 'DO-007', text: 'Health check endpoints', priority: 'medium', completed: false },
            { id: 'DO-009', text: 'Terraform templates', priority: 'medium', completed: false },
            { id: 'DO-010', text: 'Rate limiting middleware', priority: 'medium', completed: false }
        ]
    }
};

// Workflow templates
const workflows = [
    { name: 'Daily Planning', description: 'Automated morning routine', category: 'Productivity', tags: ['Scheduling'] },
    { name: 'Research Report', description: 'Comprehensive research synthesis', category: 'Research', tags: ['Analysis'] },
    { name: 'Email Management', description: 'Inbox zero automation', category: 'Productivity', tags: ['Communication'] },
    { name: 'Blog Generation', description: 'Content creation pipeline', category: 'Content', tags: ['Writing'] },
    { name: 'Social Media Campaign', description: 'Multi-platform content', category: 'Marketing', tags: ['Social'] },
    { name: 'Meeting Preparation', description: 'Pre-meeting automation', category: 'Productivity', tags: ['Meetings'] },
    { name: 'Literature Review', description: 'Academic paper synthesis', category: 'Research', tags: ['Academic'] },
    { name: 'Podcast Generation', description: 'Audio content pipeline', category: 'Content', tags: ['Audio'] }
];

// Render agent cards
function renderAgents() {
    const container = document.getElementById('agentsContainer');
    container.innerHTML = '';
    
    Object.values(agentsData).forEach(agent => {
        const progress = (agent.completed / agent.total * 100).toFixed(0);
        const remaining = agent.total - agent.completed;
        
        const statusBadge = agent.status === 'active' 
            ? '<span class="badge badge-success">Active</span>'
            : '<span class="badge badge-warning">Queued</span>';
        
        const tasksHTML = agent.tasks.map(task => `
            <div class="task-item ${task.completed ? 'completed' : ''}">
                <div class="task-checkbox">${task.completed ? '✓' : ''}</div>
                <div class="task-text">${task.text}</div>
                <div class="task-priority priority-${task.priority}">${task.priority}</div>
            </div>
        `).join('');
        
        const cardHTML = `
            <div class="agent-card">
                <div class="agent-header" style="background: ${agent.color}">
                    <h2>${agent.icon} ${agent.name}</h2>
                    <div class="agent-domain">${agent.domain}</div>
                </div>
                <div class="agent-body">
                    <div class="agent-stats">
                        <div class="agent-stat">
                            <div class="agent-stat-value">${agent.completed}</div>
                            <div class="agent-stat-label">Completed</div>
                        </div>
                        <div class="agent-stat">
                            <div class="agent-stat-value">${remaining}</div>
                            <div class="agent-stat-label">Remaining</div>
                        </div>
                        <div class="agent-stat">
                            <div class="agent-stat-value">${progress}%</div>
                            <div class="agent-stat-label">Progress</div>
                        </div>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progress}%"></div>
                    </div>
                    <div style="margin-top: 20px;">
                        ${statusBadge}
                    </div>
                    <div class="task-list" style="margin-top: 20px;">
                        ${tasksHTML}
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML += cardHTML;
    });
}

// Render workflows
function renderWorkflows() {
    const container = document.getElementById('workflowsContainer');
    container.innerHTML = '';
    
    workflows.forEach(workflow => {
        const tagsHTML = workflow.tags.map(tag => 
            `<span class="workflow-tag">${tag}</span>`
        ).join('');
        
        const cardHTML = `
            <div class="workflow-card">
                <h4>${workflow.name}</h4>
                <p>${workflow.description}</p>
                <div class="workflow-tags">
                    <span class="workflow-tag">${workflow.category}</span>
                    ${tagsHTML}
                </div>
            </div>
        `;
        
        container.innerHTML += cardHTML;
    });
}

// Update overall stats
function updateStats() {
    const totalTasks = Object.values(agentsData).reduce((sum, agent) => sum + agent.total, 0);
    const completedTasks = Object.values(agentsData).reduce((sum, agent) => sum + agent.completed, 0);
    const progress = (completedTasks / totalTasks * 100).toFixed(1);
    
    document.getElementById('overallProgress').textContent = `${progress}%`;
    document.getElementById('overallProgressBar').style.width = `${progress}%`;
    document.querySelector('.stat-label').textContent = `${completedTasks}/${totalTasks} tasks complete`;
}

// Refresh data
function refreshData() {
    const btn = document.querySelector('.btn-primary');
    const lastUpdated = document.getElementById('lastUpdated');
    
    btn.classList.add('updating');
    btn.disabled = true;
    btn.textContent = '⏳ Updating...';
    
    // Simulate API call
    setTimeout(() => {
        const now = new Date().toLocaleTimeString();
        lastUpdated.textContent = `Last updated: ${now}`;
        btn.classList.remove('updating');
        btn.disabled = false;
        btn.textContent = '🔄 Refresh Data';
        
        // Re-render
        renderAgents();
        renderWorkflows();
        updateStats();
    }, 1000);
}

// Initialize dashboard
window.addEventListener('load', () => {
    renderAgents();
    renderWorkflows();
    updateStats();
    
    const now = new Date().toLocaleTimeString();
    document.getElementById('lastUpdated').textContent = `Last updated: ${now}`;
});

// Auto-refresh every 30 seconds
setInterval(refreshData, 30000);
