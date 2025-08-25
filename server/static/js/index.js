// JavaScript file for index page

const ws = new WebSocket(`${location.protocol !== "https:" ? "ws" : "wss"}://${location.host}/ws/browser/`)
ws.addEventListener("message", function(event) {
    const message = JSON.parse(JSON.parse(event.data).message)
    if (message.sender == "c") {
        if (!document.getElementById(message.type)) {
            const typeDiv = document.createElement("div")
            typeDiv.id = message.type
            typeDiv.style.border = "solid 1px black"
            typeDiv.style.margin = "10px"
            typeDiv.style.padding = "10px"
            document.body.appendChild(typeDiv)
        }
        document.getElementById(message.type).innerHTML = JSON.stringify(message)
        if (message.type == "cpu_percent") {
            console.log(message.percent)
        }
    }
})