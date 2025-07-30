let dns_spoof = false;
let socket2;

function run_create_evil_twin() {
    const AP_name = document.getElementById("AP_name");
    const AP_password = document.getElementById("AP_password");
    const DNS_spoffing = document.getElementById("dns_spoof_checkbox");

    const DNS_spoffing_value = DNS_spoffing.checked;
    const AP_name_value = AP_name.value.trim();
    const AP_password_value = AP_password.value.trim();

    if (!AP_name_value) {
        output.textContent += "Evil twin AP needs a name\n";
    }

    if (DNS_spoffing_value === true) {
        output.textContent += "$ sudo python3 networking_tools/create_evil_twin.py --dns_spoof\n";

        create_evil_twin_with_dns_spoof()
    }

    else {
        output.textContent += "$ sudo python3 networking_tools/create_evil_twin.py\n";

        fetch("/evil_twin/create_evil_twin", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ AP_name: AP_name_value, AP_password: AP_password_value })
        })
            .then(data => data.json())
            .then(data => {
                output.textContent += data.status;
            })
            .catch(err => {
                console.error(`Error: ${err}`)
                output.textContent += ("Error: " + err)
            })
            .finally(() => {
                output.scrollTop = output.scrollHeight;
            });
    }
}

function create_evil_twin_with_dns_spoof() {
    socket2 = io()

    dns_spoof = true

    socket2.on("connect", () => {
        console.log("Socket.IO for dns spoof is connected")
    });

    socket2.on("output", (msg) => {
        output.textContent += msg.data;
        output.scrollTop = output.scrollHeight;
    });

    socket2.emit("create_evil_twin_with_dns_spoof", {
        SSID: document.getElementById("AP_name").value.trim(),
        passkey: document.getElementById("AP_password").value.trim()
    })
}

function run_remove_evil_twin() {
    output.textContent += "$ sudo python3 networking_tools/remove_evil_twin.py\n";

    if (dns_spoof === false) {
        fetch("/evil_twin/remove_evil_twin")
            .then(data => data.json())
            .then(data => {
                output.textContent += data.status;
            })
            .catch(err => {
                console.log(`Error: ${err}`)
                output.textContent += ("Error: " + err)
            })
            .finally(() => {
                output.scrollTop = output.scrollHeight;
            });
    }
    else {
        socket2.emit("stop_evil_twin_dns_spoof")
        output.scrollTop = output.scrollHeight;
    }
}