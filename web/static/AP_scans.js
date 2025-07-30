function run_hosts_scans() {
    output.textContent += "$ sudo airodump-ng start wlan1mon\n";
    fetch("/AP_scans/hosts_scan")
        .then(data => data.json())
        .then(data => {
            if (data.hosts.length) {      
                data.hosts.forEach(host => {
                    output.textContent += `Found new host: ${host}\n`;
                });
            }
        })
        .catch(err => {
            output.textContent += "Error during hosts scan.\n";
            console.error("Hosts scan error:", err);
        });
}

function run_AP_scans(){
    output.textContent += "$ sudo airodump-ng start wlan1mon\n";
    fetch("/AP_scans/AP_scan")
        .then(data => data.json())
        .then(data => {
            console.log(data)
            if (data.ssids.length) {      
                data.ssids.forEach(info => {
                    output.textContent += `Found new AP:\n`;
                    output.textContent += `     SSID: ${info[0]}\n`;
                    output.textContent += `     BSSID: ${info[1]}\n`;
                    output.textContent += `     channel: ${info[2]}\n`;
                    output.textContent += `     RSSI: ${info[3]}\n`;
                    output.textContent += `     Encription type: ${info[4]}\n`;
                });
            }
        })
        .catch(err => {
            output.textContent += "Error during AP scan.\n";
            console.error("AP scan error:", err);
        });
}