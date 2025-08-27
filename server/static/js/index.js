// Define WebSocket const
const ws = new WebSocket(`${location.protocol !== "https:" ? "ws" : "wss"}://${location.host}/ws/browser/`)
ws.addEventListener("message", function(event) {
    // When you receive a message, parse the json
    const message = JSON.parse(JSON.parse(event.data).message)

    // If message is from client and not browser (c)
    if (message.sender == "c") {
        // If the message contains a client id
        if (message.hasOwnProperty("client_id")) {
            const client_id = message.client_id

            // Go through possible types of messages
            switch (message.type) {
                case "ping":
                    // Ping message, get ping in ms
                    const ping = message.ping
                    updatePing(ping, client_id)
                    break
                case "cpu_percent":
                    // Cpu percent message, update cpu chart
                    const cpuPercent = message.percent
                    updateCpuChart(cpuPercent, client_id)
                    break
                case "ram_usage":
                    // Ram usage message, update ram chart
                    const ramUsage = message.usage_gb
                    const ramTotal = message.total_gb
                    updateRamChart(ramUsage, ramTotal, client_id)
                    break
                case "bandwidth":
                    // Bandwidth message, update bandwidth chart
                    const bandwidthReceived = message.received
                    const bandwidthTransmitted = message.transmitted
                    const bandwidthInterval = message.bandwidth_interval
                    updateBandwidthChart(bandwidthReceived, bandwidthTransmitted, bandwidthInterval, client_id)
                    break
                case "download_upload":
                    // Download upload speed message, update download upload chart
                    const uploadSpeed = message.upload_speed
                    const downloadSpeed = message.download_speed
                    const downloadUploadInterval = message.bandwidth_interval
                    updateDownloadUploadChart(uploadSpeed, downloadSpeed, downloadUploadInterval, client_id)
                    break
                case "read_write":
                    // Read write speed message, update read write chart
                    const readWriteData = message.data
                    updateReadWriteChart(readWriteData, client_id)
                    break
                case "storage":
                    // Storage usage message, update storage chart
                    const storageData = message.data
                    updateStorageChart(storageData, client_id)
                    break
                case "uptime":
                    // Uptime message, update uptime chart
                    const uptimeSeconds = message.seconds
                    updateUptimeChart(uptimeSeconds, client_id)
                    break
                case "processes":
                    // Processes message, update processes chart
                    const processesData = message.processes
                    updateProcessesData(processesData, client_id)
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
})

// Add startup data to charts
page_load_data.forEach(element => {
    const data = JSON.parse(element)
    console.log(data)
});