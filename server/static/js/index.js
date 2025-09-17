// Define global variables
const pingDataMaxLenght = 10
const cpuDataMaxLenght = 10
const ramDataMaxLenght = 10
const ioDiskDataMaxLenght = 1
const uploadDownloadMaxLenght = 3
const bandwidthMaxLenght = 12

const slideChangeInterval = 20000

// Define WebSocket const
const ws = new WebSocket(`${location.protocol !== "https:" ? "ws" : "wss"}://${location.host}/ws/browser/`)
ws.addEventListener("message", function(event) {
    try {
        // When you receive a message, parse the json
        const message = JSON.parse(JSON.parse(event.data).message)
        handleMessage(message)
    } catch {
        return
    }
})

// Handles a standard websocket message
function handleMessage(message) {
    // If message is from client and not browser (c)
    if (message.sender == "c") {
        // If the message contains a client id
        if (message.hasOwnProperty("client_id")) {
            const client_id = message.client_id

            // Go through possible types of messages
            const timestamp = message.timestamp
            switch (message.type) {
                case "ping":
                    // Ping message, get ping in ms
                    const ping = message.ping
                    updatePing(ping, timestamp, client_id)
                    break
                case "cpu_percent":
                    // Cpu percent message, update cpu chart
                    const cpuPercent = message.percent
                    updateCpuChart(cpuPercent, timestamp, client_id)
                    break
                case "ram_usage":
                    // Ram usage message, update ram chart
                    const ramUsage = message.usage_gb
                    const ramTotal = message.total_gb
                    updateRamChart(ramUsage, ramTotal, timestamp, client_id)
                    break
                case "bandwidth":
                    // Bandwidth message, update bandwidth chart
                    const bandwidthReceived = message.received
                    const bandwidthTransmitted = message.transmitted
                    const bandwidthInterval = message.bandwidth_interval
                    updateBandwidthChart(bandwidthReceived, bandwidthTransmitted, bandwidthInterval, timestamp, client_id)
                    break
                case "download_upload":
                    // Download upload speed message, update download upload chart
                    const uploadSpeed = message.upload_speed
                    const downloadSpeed = message.download_speed
                    const downloadUploadInterval = message.bandwidth_interval
                    updateDownloadUploadChart(uploadSpeed, downloadSpeed, downloadUploadInterval, timestamp, client_id)
                    break
                case "read_write":
                    // Read write speed message, update read write chart
                    const readWriteData = message.data
                    updateReadWriteChart(readWriteData, timestamp, client_id)
                    break
                case "storage":
                    // Storage usage message, update storage chart
                    const storageData = message.data
                    updateStorageChart(storageData, timestamp, client_id)
                    break
                case "uptime":
                    break
                case "processes":
                    // Processes message, update processes chart
                    const processesData = message.processes
                    updateProcessesData(processesData, timestamp, client_id)
                    break
                case "connect":
                    // Connect message, update status
                    updateConnectionStatus("online", client_id)
                    break
                case "disconnect":
                    // Disconnect message, update status
                    updateConnectionStatus("offline", client_id)
                    break
            }
        }
    }
}

// Updates the ping chart
function updatePing(ping, timestamp, client_id) {
    // Check if chart exists, make it if it doesnt
    if (!Chart.getChart(`${client_id}-ping`)) {
        const ctx = document.getElementById(`${client_id}-ping`).getContext('2d')
        new Chart(ctx, {
            type: "line",
            data: {
                labels: [],
                datasets: [{
                    label: "Milliseconds",
                    data: [],
                    borderColor: "#facc15",
                    backgroundColor: "#facc1546",
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: "Timestamp",
                            color: "white",
                            font: {
                                size: 16,
                                weight: "bold"
                            }
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: "Milliseconds",
                            color: "white",
                            font: {
                                size: 16,
                                weight: "bold"
                            }
                        }
                    }
                }
            }
        });
    }

    const chart = Chart.getChart(`${client_id}-ping`)

    // Update the data
    chart.data.labels.push(timestamp);
    chart.data.datasets[0].data.push(Number(ping.replace("ms", "")));

    // Keep only last 10 points
    if (chart.data.labels.length > pingDataMaxLenght) {
        chart.data.labels.shift();
        chart.data.datasets.forEach(dataset => {
            dataset.data.shift();
        });
    }

    chart.update();
}

function updateCpuChart(cpuPercent, timestamp, client_id) {
    // Check if chart exists, make it if it doesnt
    if (!Chart.getChart(`${client_id}-cpu`)) {
        const ctx = document.getElementById(`${client_id}-cpu`).getContext('2d')
        new Chart(ctx, {
            type: "line",
            data: {
                labels: [],
                datasets: [{
                    label: "Percent",
                    data: [],
                    borderColor: "#facc15",
                    backgroundColor: "#facc1546",
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: "Timestamp",
                            color: "white",
                            font: {
                                size: 16,
                                weight: "bold"
                            }
                        }
                    },
                    y: {
                        min: 0,
                        max: 100,
                        title: {
                            display: true,
                            text: "Percent",
                            color: "white",
                            font: {
                                size: 16,
                                weight: "bold"
                            }
                        }
                    }
                }
            }
        });
    }

    const chart = Chart.getChart(`${client_id}-cpu`)

    // Update the data
    chart.data.labels.push(timestamp);
    chart.data.datasets[0].data.push(Number(cpuPercent));

    // Keep only last 10 points
    if (chart.data.labels.length > cpuDataMaxLenght) {
        chart.data.labels.shift();
        chart.data.datasets.forEach(dataset => {
            dataset.data.shift();
        });
    }

    chart.update();
}

function updateRamChart(ramUsage, ramTotal, timestamp, client_id) {
    // Check if chart exists, make it if it doesnt
    if (!Chart.getChart(`${client_id}-memory`)) {
        const ctx = document.getElementById(`${client_id}-memory`).getContext('2d')
        new Chart(ctx, {
            type: "line",
            data: {
                labels: [],
                datasets: [{
                    label: "GB",
                    data: [],
                    borderColor: "#facc15",
                    backgroundColor: "#facc1546",
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: "Timestamp",
                            color: "white",
                            font: {
                                size: 16,
                                weight: "bold"
                            }
                        }
                    },
                    y: {
                        min: 0,
                        max: ramTotal,
                        title: {
                            display: true,
                            text: "GB",
                            color: "white",
                            font: {
                                size: 16,
                                weight: "bold"
                            }
                        }
                    }
                }
            }
        });
    }

    const chart = Chart.getChart(`${client_id}-memory`)

    // Update the data
    chart.data.labels.push(timestamp);
    chart.data.datasets[0].data.push(Number(ramUsage));

    // Keep only last 10 points
    if (chart.data.labels.length > ramDataMaxLenght) {
        chart.data.labels.shift();
        chart.data.datasets.forEach(dataset => {
            dataset.data.shift();
        });
    }

    chart.update();
}

function updateBandwidthChart(bandwidthReceived, bandwidthTransmitted, bandwidthInterval, timestamp, client_id) {
    // Check if chart exists, make it if it doesnt
    function getBackgroundColor(hsl_value) {
        const array = hsl_value.split("(")
        array[0] = "hsla("
        const hsla = array.join('')
        const final = `${hsla.slice(0, -1)}, 0.5)`
        return final
    }
    var datasets = []
    const colors = [getRandomColor(), getRandomColor()]
    datasets.push({
        label: `Received`,
        data: [],
        borderColor: colors[0],
        backgroundColor: getBackgroundColor(colors[0]),
        fill: true,
        yAxisID: "y"
    })
    datasets.push({
        label: `Transmitted`,
        data: [],
        borderColor: colors[1],
        backgroundColor: getBackgroundColor(colors[1]),
        fill: true,
        yAxisID: "y1"
    })
    if (!Chart.getChart(`${client_id}-bandwidth`)) {
        const ctx = document.getElementById(`${client_id}-bandwidth`).getContext('2d')
        new Chart(ctx, {
            type: "line",
            data: {
                labels: [],
                datasets: datasets
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: 'false'
                },
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "top"
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: "Timestamp",
                            color: "white",
                            font: {
                                size: 16,
                                weight: "bold"
                            }
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        min: 0,
                        title: {
                            display: true,
                            text: "Bytes",
                            color: "white",
                            font: {
                                size: 16,
                                weight: "bold"
                            }
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: 'true',
                        position: 'right'
                    }
                }
            }
        });
    }

    const chart = Chart.getChart(`${client_id}-bandwidth`)

    // Update the data
    chart.data.labels.push(timestamp);
    chart.data.datasets[0].data.push(Number(bandwidthReceived))
    chart.data.datasets[1].data.push(Number(bandwidthTransmitted))
    if (chart.data.labels.length > bandwidthMaxLenght) {
        chart.data.labels.shift();
        chart.data.datasets.forEach(dataset => {
            dataset.data.shift();
        });
    }

    chart.update();
}

function updateDownloadUploadChart(uploadSpeed, downloadSpeed, downloadUploadInterval, timestamp, client_id) {
    // Check if chart exists, make it if it doesnt
    var datasets = []
    datasets.push({
            label: `Upload`,
            data: [],
            backgroundColor: getRandomColor(),
            fill: "false",
    })
    datasets.push({
        label: `Download`,
        data: [],
        backgroundColor: getRandomColor(),
        fill: "false",
    })
    if (!Chart.getChart(`${client_id}-uploadDownload`)) {
        const ctx = document.getElementById(`${client_id}-uploadDownload`).getContext('2d')
        new Chart(ctx, {
            type: "bar",
            data: {
                labels: [],
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "top"
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: "Timestamp",
                            color: "white",
                            font: {
                                size: 16,
                                weight: "bold"
                            }
                        }
                    },
                    y: {
                        min: 0,
                        title: {
                            display: true,
                            text: "Mbps",
                            color: "white",
                            font: {
                                size: 16,
                                weight: "bold"
                            }
                        }
                    }
                }
            }
        });
    }

    const chart = Chart.getChart(`${client_id}-uploadDownload`)

    // Update the data
    chart.data.labels.push(timestamp);
    chart.data.datasets[0].data.push(Number(uploadSpeed))
    chart.data.datasets[1].data.push(Number(downloadSpeed))
    if (chart.data.labels.length > uploadDownloadMaxLenght) {
        chart.data.labels.shift();
        chart.data.datasets.forEach(dataset => {
            dataset.data.shift();
        });
    }

    chart.update();
}

function getRandomColor() {
    const hue = Math.floor(Math.random() * 360);
    const saturation = Math.floor(Math.random() * 30) + 70;
    const lightness = Math.floor(Math.random() * 20) + 50;
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

function updateReadWriteChart(readWriteData, timestamp, client_id) {
    // Parse read write data
    var datasets = []
    for (key in readWriteData) { // Each key is a drive
        datasets.push({
            label: `${key} Read`,
            data: [],
            backgroundColor: getRandomColor(),
            fill: "false",
            driveLetter: key,
            driveType: "read"
        })
        datasets.push({
            label: `${key} Write`,
            data: [],
            backgroundColor: getRandomColor(),
            fill: "false",
            driveLetter: key,
            driveType: "write"
        })
    }

    // Check if chart exists, make it if it doesnt
    if (!Chart.getChart(`${client_id}-diskIo`)) {
        const ctx = document.getElementById(`${client_id}-diskIo`).getContext('2d')
        new Chart(ctx, {
            type: "bar",
            data: {
                labels: [],
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "top"
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: "Timestamp",
                            color: "white",
                            font: {
                                size: 16,
                                weight: "bold"
                            }
                        }
                    },
                    y: {
                        min: 0,
                        title: {
                            display: true,
                            text: "Mbps",
                            color: "white",
                            font: {
                                size: 16,
                                weight: "bold"
                            }
                        }
                    }
                }
            }
        });
    }

    const chart = Chart.getChart(`${client_id}-diskIo`)

    // Update the data
    chart.data.labels.push(timestamp);
    chart.data.datasets.forEach(dataset => {
        const readSpeed = readWriteData[dataset.driveLetter].read.mbps
        const writeSpeed = readWriteData[dataset.driveLetter].write.mbps
        if (dataset.driveType == "read") {
            dataset.data.push(Number(readSpeed))
        } else {
            dataset.data.push(Number(writeSpeed))
        }
    });

    if (chart.data.labels.length > ioDiskDataMaxLenght) {
        chart.data.labels.shift();
        chart.data.datasets.forEach(dataset => {
            dataset.data.shift();
        });
    }

    chart.update();
}

function updateStorageChart(storageData, timestamp, client_id) {
    return
}

function formatSeconds(seconds) {
    const days = Math.floor(seconds / (24 * 3600));
    seconds %= 24 * 3600; // remaining seconds after days

    const hours = Math.floor(seconds / 3600);
    seconds %= 3600;      // remaining seconds after hours

    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);

    return { days, hours, minutes, seconds: secs };
}

function updateProcessesData(processesData, timestamp, client_id) {
    // Parse cpu data
    var cpuTotal = 0
    for (key in processesData) {
        const cpuAmount = processesData[key].cpu
        cpuTotal += cpuAmount
    }
    const divisionNumber = cpuTotal / 100

    const legendData = []
    var otherData = 0
    for (key in processesData) {
        if (Number(processesData[key].cpu / divisionNumber) > 1) {
            legendData.push({
                label: key,
                value: processesData[key].cpu / divisionNumber,
                color: getRandomColor()
            })
        } else {
            otherData += (Number(processesData[key].cpu / divisionNumber))
        }
    }

    legendData.push({
        label: "Other",
        value: otherData,
        color: "grey"
    })

    // Sort legend data
    legendData.sort((a, b) => b.value - a.value)

    const labels = []
    const data = []
    const backgroundColors = []
    legendData.forEach(item => {
        labels.push(item.label)
        data.push(item.value)
        backgroundColors.push(item.color)
    })

    // Check if chart exists, make it if it doesnt
    if (!Chart.getChart(`${client_id}-processes`)) {
        const ctx = document.getElementById(`${client_id}-processes`).getContext('2d')
        new Chart(ctx, {
            type: "pie",
            data: {
                labels: labels,
                datasets: [{
                    data: [],
                    backgroundColor: [],
                    borderColor: 'var(--panel-bg)',
                    borderWidth: 2,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    const chart = Chart.getChart(`${client_id}-processes`)
    chart.data.labels = labels
    chart.data.datasets[0].data = data
    chart.data.datasets[0].backgroundColor = backgroundColors
    const legendInner = document.getElementById(`${client_id}-legendContainer`)
    legendInner.innerHTML = ""

    // Put all legends in the scrollable container
    legendData.forEach(itemData => {
        const item = document.createElement('div');
        item.className = 'legend-item';

        const colorBox = document.createElement('div');
        colorBox.className = 'legend-color';
        colorBox.style.backgroundColor = itemData.color
        const labelText = document.createElement('span');
        labelText.className = "legend-span"
        labelText.innerHTML = `<span class='processes-legend-label'>${itemData.label}</span> - ${Number(itemData.value).toFixed(2)}%`;

        item.appendChild(colorBox);
        item.appendChild(labelText);
        legendInner.appendChild(item);
    });

    chart.update()
}

var uptimeIntervals = {}
function updateConnectionStatus(status, client_id, seconds_or_timestamp) {
    clearInterval(uptimeIntervals[client_id])

    // Set online or offline
    const connectionStatusText = document.getElementById(`${client_id}-connection-status`)
    const uptimeContainer = document.getElementById(`${client_id}-uptime`)
    if (status == "online") {
        connectionStatusText.innerHTML = 'Status: <span class="online-span">ONLINE</span>'
        const formatted = formatSeconds(seconds_or_timestamp)
        uptimeContainer.innerHTML = `${formatted.days}d ${formatted.hours}h ${formatted.minutes}m ${formatted.seconds}s`
        uptimeIntervals[client_id] = setInterval(function() {
            seconds_or_timestamp += 1
            const uptimeContainer = document.getElementById(`${client_id}-uptime`)
            const formatted = formatSeconds(seconds_or_timestamp)
            uptimeContainer.innerHTML = `${formatted.days}d ${formatted.hours}h ${formatted.minutes}m ${formatted.seconds}s`
        }, 1000)
        availablePanel(client_id)
    } else if (status == "offline") {
        connectionStatusText.innerHTML = 'Status: <span class="offline-span">OFFLINE</span>'
        uptimeContainer.innerHTML = `OFFLINE - Last online: ${seconds_or_timestamp}`
        unavailablePanel(client_id)
    }
}

// Add startup data to charts
page_load_data.forEach(element => {
    const message = JSON.parse(element)
    handleMessage(message)
});

// Scroll up and down legend containers
var currentScrollIntervals = []
var currentScrollTimeouts = []
function startScrollLoop(client_id) {
    currentScrollIntervals = []
    currentScrollTimeouts = []
    const container = document.getElementById(`${client_id}-legendContainer`);

    // Define variables for animation
    const waitTime = slideChangeInterval * 0.2
    const scrollTime = slideChangeInterval * 0.4

    let maxScroll = container.scrollHeight - container.clientHeight

    // If the container isnt scrollable
    if (maxScroll <= 0) {
        return
    }

    // Start at top of container and wait the waiting time
    container.scrollTop = 0
    const startTimeout = setTimeout(function() {
        const framerate = 60
        const intervalTime = 1000 / framerate
        const totalSteps = scrollTime / intervalTime
        const scrollStep = maxScroll / totalSteps

        var scrollTop = 0
        var currentStep = 0
        const scrollInterval = setInterval(function() {
            scrollTop += scrollStep
            container.scrollTop = scrollTop
            currentStep += 1

            if (currentStep >= totalSteps) {
                clearInterval(scrollInterval)
            }
        }, intervalTime)
        currentScrollIntervals.push(scrollInterval)
    }, waitTime)
    currentScrollTimeouts.push(startTimeout)
}

// Clears intervals and timeouts for scrolling
function clearScrollIntervals() {
    currentScrollIntervals.forEach(interval => {
        clearInterval(interval)
    })
    currentScrollTimeouts.forEach(timeout => {
        clearTimeout(timeout)
    })
}

// Says unavailable for all panels for client id
function unavailablePanel(client_id) {
    const section = document.getElementById(`${client_id}-slide`)
    const section_two = document.getElementById(`${client_id}-slide2`)

    // Get every panel div in the section
    function getPanels(section) {
        const panels = section.querySelectorAll('div')
        panels.forEach(panel => {
            const classList = []
            panel.classList.forEach(function (value, key, listObj) {
                classList.push(value)
            })
            if (classList.includes("panel") && !classList.includes("client-info")) {
                const cover = document.createElement("div")
                cover.style.width = "100%"
                cover.style.height = "100%"
                cover.style.position = "absolute"
                cover.style.background = "var(--panel-bg)"
                cover.style.top = "0"
                cover.style.left = "0"
                cover.style.display = "flex"
                cover.style.alignItems = "center"
                cover.style.justifyContent = "center"
                cover.style.color = "Red"
                cover.innerHTML = "UNAVAILABLE - CLIENT OFFLINE"
                cover.style.borderRadius = "var(--radius)"
                cover.className = "unavailable-cover"
                cover.style.fontSize = "3rem"
                panel.appendChild(cover)
            }
        })
    }

    getPanels(section)
    getPanels(section_two)
}

// Removes unavailable for all panels for client id
function availablePanel(client_id) {
    const section = document.getElementById(`${client_id}-slide`)
    const section_two = document.getElementById(`${client_id}-slide2`)

    // Get every panel div in the section
    function getPanels(section) {
        const panels = section.querySelectorAll('div')
        panels.forEach(panel => {
            const classList = []
            panel.classList.forEach(function (value, key, listObj) {
                classList.push(value)
            })
            if (classList.includes("unavailable-cover")) {
                panel.remove()
            }
        })
    }

    getPanels(section)
    getPanels(section_two)
}

// Checks if a client is online
function isOnline(client_id) {
    fetch("/api/is_online", {
        method: "POST",
        body: JSON.stringify({
            client_id: client_id
        }),
        credentials: "include"
    })

    .then(response => response.json())

    .then(response => {
        if (response.success) {
            if (response.success.online) {
                const uptime_seconds = response.success.uptime_seconds
                updateConnectionStatus("online", client_id, uptime_seconds)
            } else {
                const offline_since = response.success.last_ping_timestamp
                updateConnectionStatus("offline", client_id, offline_since)
            }
        }
    })

    .catch(error => {
        console.error(error)
    })
}

var count = 0
// Shows a slide
function selectSlide(currentSectionId) {
    // Hide every section except the current one
    section_ids.forEach(sectionId => {
        if (sectionId !== currentSectionId) {
            document.getElementById(sectionId).style.display = "none"
        } else {
            document.getElementById(sectionId).style.display = "block"
        }
    })
    // Get client id from section to start scroll loop
    const sectionElement = document.getElementById(currentSectionId)
    const client_id = sectionElement.dataset.clientid
    isOnline(client_id)

    if (sectionElement.dataset.isslidetwo == "true" || sectionElement.dataset.isslidetwo == true) {
        startScrollLoop(client_id)
    }
    if (count >= section_ids.length - 1) {
        count = 0
    } else {
        count++;
    }
}

var slideChangeIntervalLoop = null
function startLoop() {
    selectSlide(section_ids[count])
    slideChangeIntervalLoop = setInterval(function() {
        clearScrollIntervals()
        selectSlide(section_ids[count])
    }, slideChangeInterval)
}

// Make slides change with arrow keys
document.addEventListener("keydown", function(e) {
    if (e.code == "Space") {
        clearScrollIntervals()
        clearInterval(slideChangeIntervalLoop)
        startLoop()
    }
})

document.addEventListener("DOMContentLoaded", function() {
    startLoop()
})

let cursorTimeout;

function showCursorTemporarily() {
    document.body.classList.remove('hide-cursor');
    
    clearTimeout(cursorTimeout);
    cursorTimeout = setTimeout(() => {
        document.body.classList.add('hide-cursor');
    }, 2000); // 2 seconds of inactivity
}

document.addEventListener('mousemove', showCursorTemporarily);

// Start timer immediately in case user is idle
showCursorTemporarily();

// Auto refresh every hour
setInterval(function() {
    window.location.reload()
}, 3600000)