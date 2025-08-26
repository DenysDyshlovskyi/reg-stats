Chart.register({
    id: 'centerText',
    beforeDraw(chart) {
        if (chart.config.type !== 'doughnut') return;
        const {
            ctx,
            chartArea: {
                width,
                height
            }
        } = chart;
        const value = chart.config.data.datasets[0].data.reduce((a, b) => a + b, 0);
        ctx.save();
        ctx.font = `${Math.min(width, height) / 6}px Segoe UI`;
        ctx.fillStyle = '#facc15';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(value, width / 2, height / 2);
        ctx.restore();
    }
});

const charts = {};

function createDoughnut(id, colors, labels, data) {
    return new Chart(document.getElementById(id), {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors
            }]
        },
        options: {
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function createLine(id, label, color, data, max = 100) {
    const ctx = document.getElementById(id).getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
    gradient.addColorStop(0, color + '77');
    gradient.addColorStop(1, color + '11');
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map((_, i) => i + 1),
            datasets: [{
                label,
                data,
                borderColor: color,
                backgroundColor: gradient,
                fill: true,
                tension: 0.4,
                pointRadius: 6,
                pointBackgroundColor: color
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                y: {
                    min: 0,
                    max
                },
                x: {
                    grid: {
                        display: true
                    }
                }
            }
        }
    });
}

function createBar(id, labels, data, colors) {
    return new Chart(document.getElementById(id), {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function initCharts() {
    charts.totalClientsChart = createDoughnut('totalClientsChart', ['#3b82f6', '#22c55e'], ['Servers', 'PCs'], [0, 0]);
    charts.statusChart = createDoughnut('statusChart', ['#22c55e', '#ef4444'], ['Online', 'Offline'], [0, 0]);
    charts.fleetCpuChart = createLine('fleetCpuChart', 'Avg CPU %', '#38bdf8', [0, 0, 0, 0, 0]);
    charts.cpuTrendChart = createLine('cpuTrendChart', 'CPU %', '#3b82f6', [0, 0, 0, 0, 0, 0, 0]);
    charts.memTrendChart = createLine('memTrendChart', 'Memory %', '#f97316', [0, 0, 0, 0, 0, 0, 0]);
    charts.diskIOChart = createBar('diskIOChart', ['Read', 'Write'], [0, 0], ['#22c55e', '#3b82f6']);
    charts.netChart = createLine('netChart', 'Network Mbps', '#ec4899', [0, 0, 0, 0, 0], 200);
    charts.latencyChart = createLine('latencyChart', 'Latency ms', '#facc15', [0, 0, 0, 0, 0], 100);
    charts.trafficChart = createLine('trafficChart', 'Traffic Mbps', '#22c55e', [0, 0, 0, 0, 0], 200);
}

function populateLogs(logs) {
    const tbody = document.getElementById('logTableBody');
    tbody.innerHTML = '';
    logs.forEach(l => {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${l.time}</td><td><span class="tag ${l.level.toUpperCase()}">${l.level}</span></td><td>${l.message}</td>`;
        tbody.appendChild(row);
    });
}

function populateClients(clients) {
    const container = document.getElementById('clientsOverview');
    container.innerHTML = '';
    clients.forEach(client => {
        const card = document.createElement('div');
        card.classList.add('client-card');

        card.innerHTML = `
            <h4>${client.name}</h4>
            <div class="client-info">OS: ${client.os}</div>
            <div class="client-info">Version: ${client.version}</div>
            <div class="client-info">CPU Usage</div>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width:${client.cpu}%;background:#38bdf8;"></div>
            </div>
            <div class="client-info">RAM Usage</div>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width:${client.ram}%;background:#f97316;"></div>
            </div>
            <div class="client-info">Disk Usage</div>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width:${client.disk}%;background:#22c55e;"></div>
            </div>
        `;
        container.appendChild(card);
    });
}

const exampleClients = [
    { id: 1, name: 'Server01', os: 'Windows Server 2022', version: 'v1.0', cpu: 45, ram: 65, disk: 70 },
    { id: 2, name: 'Server02', os: 'Ubuntu 22.04', version: 'v1.1', cpu: 25, ram: 40, disk: 50 },
    { id: 3, name: 'Server03', os: 'Windows 10', version: 'v2.3', cpu: 70, ram: 80, disk: 60 },
];

function updateData() {
    const data = {
        totalClients: {
            servers: 3,
            pcs: 3
        },
        status: {
            Online: 28,
            Offline: 4
        },
        fleetCpu: [35, 45, 50, 42, 60],
        client: {
            cpu: 62,
            ram: 70,
            disk: 55,
            net: [12, 30, 18, 40, 28],
            uptime: '12d 4h 36m'
        },
        network: {
            latency: [20, 25, 22, 18, 30],
            traffic: [50, 80, 60, 90, 70]
        },
        logs: [{
            time: '2025-08-26 10:00:01',
            level: 'INFO',
            message: 'System started.'
        },
        {
            time: '2025-08-26 10:05:22',
            level: 'DEBUG',
            message: 'CPU check passed.'
        },
        {
            time: '2025-08-26 10:07:11',
            level: 'WARN',
            message: 'High memory usage.'
        },
        {
            time: '2025-08-26 10:15:43',
            level: 'ERROR',
            message: 'Disk write failed.'
        }
        ]
    };
    charts.totalClientsChart.data.datasets[0].data = [data.totalClients.servers, data.totalClients.pcs];
    charts.totalClientsChart.update();
    charts.statusChart.data.datasets[0].data = [data.status.Online, data.status.Offline];
    charts.statusChart.update();
    charts.fleetCpuChart.data.datasets[0].data = data.fleetCpu;
    charts.fleetCpuChart.update();
    charts.cpuTrendChart.data.datasets[0].data = Array(7).fill(data.client.cpu);
    charts.cpuTrendChart.update();
    charts.memTrendChart.data.datasets[0].data = Array(7).fill(data.client.ram);
    charts.memTrendChart.update();
    charts.diskIOChart.data.datasets[0].data = [data.client.disk, data.client.disk];
    charts.diskIOChart.update();
    charts.netChart.data.datasets[0].data = data.client.net;
    charts.netChart.update();
    charts.latencyChart.data.datasets[0].data = data.network.latency;
    charts.latencyChart.update();
    charts.trafficChart.data.datasets[0].data = data.network.traffic;
    charts.trafficChart.update();
    document.getElementById('uptime').textContent = data.client.uptime;
    document.getElementById('totalServers').textContent = data.totalClients.servers;
    document.getElementById('totalPCs').textContent = data.totalClients.pcs;
    populateLogs(data.logs);
}




initCharts();
updateData();
populateClients(exampleClients);

// Add slide5 to the slides array automatically in your cycling logic
const slides = document.querySelectorAll('section');
let currentSlide = 0;
function showSlide(i) {
    slides.forEach((s, idx) => s.style.display = (idx === i ? 'flex' : 'none'));
}
showSlide(currentSlide);
setInterval(() => {
    currentSlide = (currentSlide + 1) % slides.length;
    showSlide(currentSlide);
}, 5000);