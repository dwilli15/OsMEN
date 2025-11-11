// OsMEN Dashboard JavaScript

let ws = null;
let productivityChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    initializeWebSocket();
    loadDashboardData();
    initializeChart();
    
    // Refresh data every 30 seconds
    setInterval(loadDashboardData, 30000);
});

// WebSocket Connection
function initializeWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = function() {
        console.log('WebSocket connected');
        updateConnectionStatus(true);
    };
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === 'status_update') {
            updateSystemStatus(data.data);
        }
    };
    
    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
        updateConnectionStatus(false);
    };
    
    ws.onclose = function() {
        console.log('WebSocket disconnected');
        updateConnectionStatus(false);
        
        // Reconnect after 5 seconds
        setTimeout(initializeWebSocket, 5000);
    };
}

function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');
    if (connected) {
        statusEl.innerHTML = '<span class="dot"></span> Connected';
        statusEl.style.color = 'var(--accent-success)';
    } else {
        statusEl.innerHTML = '<span class="dot" style="background: var(--accent-error);"></span> Disconnected';
        statusEl.style.color = 'var(--accent-error)';
    }
}

// Load Dashboard Data
async function loadDashboardData() {
    try {
        await Promise.all([
            loadSystemStatus(),
            loadProductivityMetrics(),
            loadInnovationBacklog(),
            loadAgents()
        ]);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

async function loadSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        updateSystemStatus(data);
    } catch (error) {
        console.error('Error loading system status:', error);
    }
}

function updateSystemStatus(data) {
    document.getElementById('system-status').textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
    document.getElementById('tools-count').textContent = `${data.services.mcp_server.tools} Tools`;
    document.getElementById('last-update').textContent = formatTime(data.timestamp);
}

async function loadProductivityMetrics() {
    try {
        const response = await fetch('/api/productivity');
        const data = await response.json();
        
        if (data.status === 'success') {
            updateProductivityMetrics(data.daily, data.weekly);
        }
    } catch (error) {
        console.error('Error loading productivity metrics:', error);
    }
}

function updateProductivityMetrics(daily, weekly) {
    document.getElementById('sessions-today').textContent = daily.sessions_completed;
    document.getElementById('focus-time').textContent = `${daily.focus_time_minutes} min`;
    document.getElementById('avg-score').textContent = daily.average_productivity_score.toFixed(1);
    document.getElementById('weekly-sessions').textContent = weekly.total_sessions;
    
    // Update chart
    if (productivityChart && weekly.daily_breakdown) {
        const labels = weekly.daily_breakdown.map(d => d.date);
        const sessions = weekly.daily_breakdown.map(d => d.sessions);
        const scores = weekly.daily_breakdown.map(d => d.avg_score);
        
        productivityChart.data.labels = labels;
        productivityChart.data.datasets[0].data = sessions;
        productivityChart.data.datasets[1].data = scores;
        productivityChart.update();
    }
}

async function loadInnovationBacklog() {
    try {
        const response = await fetch('/api/innovations');
        const data = await response.json();
        
        if (data.status === 'success') {
            updateInnovationBacklog(data.innovations, data.total);
        }
    } catch (error) {
        console.error('Error loading innovation backlog:', error);
    }
}

function updateInnovationBacklog(innovations, total) {
    document.getElementById('innovation-count').textContent = `${total} discoveries`;
    
    const listEl = document.getElementById('innovation-list');
    listEl.innerHTML = '';
    
    if (innovations.length === 0) {
        listEl.innerHTML = '<p style="color: var(--text-secondary);">No innovations discovered yet. Run a scan to get started.</p>';
        return;
    }
    
    innovations.forEach(innovation => {
        const itemEl = document.createElement('div');
        itemEl.className = 'innovation-item';
        itemEl.innerHTML = `
            <div class="innovation-name">${innovation.name}</div>
            <div class="innovation-details">${innovation.details.slice(0, 2).join(' ')}</div>
        `;
        listEl.appendChild(itemEl);
    });
}

async function loadAgents() {
    try {
        const response = await fetch('/api/agents');
        const data = await response.json();
        
        if (data.status === 'success') {
            updateAgents(data.agents);
        }
    } catch (error) {
        console.error('Error loading agents:', error);
    }
}

function updateAgents(agents) {
    const gridEl = document.getElementById('agents-grid');
    gridEl.innerHTML = '';
    
    Object.entries(agents).forEach(([name, info]) => {
        const agentEl = document.createElement('div');
        agentEl.className = 'agent-card';
        agentEl.innerHTML = `
            <div class="agent-name">${formatAgentName(name)}</div>
            <div class="agent-status ${info.status}">${info.status}</div>
        `;
        gridEl.appendChild(agentEl);
    });
    
    document.getElementById('agents-count').textContent = `${Object.keys(agents).length} Active`;
}

// Initialize Chart
function initializeChart() {
    const ctx = document.getElementById('productivity-chart');
    if (!ctx) return;
    
    productivityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Sessions',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Avg Score',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#f1f5f9'
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    ticks: {
                        color: '#94a3b8'
                    },
                    grid: {
                        color: '#334155'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    ticks: {
                        color: '#94a3b8'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                },
                x: {
                    ticks: {
                        color: '#94a3b8'
                    },
                    grid: {
                        color: '#334155'
                    }
                }
            }
        }
    });
}

// Helper Functions
function formatAgentName(name) {
    return name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
    return date.toLocaleDateString();
}

// Action Functions
async function startSession() {
    const type = prompt('Session type (pomodoro/deep_work):', 'pomodoro');
    if (!type) return;
    
    const duration = parseInt(prompt('Duration (minutes):', '25'));
    if (!duration) return;
    
    try {
        const response = await fetch(`/api/productivity/session/start?session_type=${type}&duration=${duration}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            alert(`Session started! ID: ${data.data.session_id}`);
            loadProductivityMetrics();
        } else {
            alert('Error starting session');
        }
    } catch (error) {
        console.error('Error starting session:', error);
        alert('Error starting session');
    }
}

function runScan() {
    alert('Innovation scan will run in the background. Check the backlog in a few minutes.');
}

function viewLogs() {
    window.open('/api/agents/innovation_agent/logs', '_blank');
}

function refreshData() {
    loadDashboardData();
}
