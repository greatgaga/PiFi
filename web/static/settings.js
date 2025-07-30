function run_change_connection_wlan1(){
    const ssid = document.getElementById("SSID");
    const password = document.getElementById("password");

    ssid_value = ssid.value.trim();
    password_value = password.value.trim();

    if (!ssid_value){
        output.textContent += "SSID or password not provided";
        return;
    }

    output.textContent += "$ sudo python3 networking_tools/change_wlan1_connection.py\n";

    fetch("/settings/change_connection_wlan1", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ SSID: ssid_value, password: password_value })
    })
    .then(data => data.json())
    .then(data => 
        output.textContent += data.status
    )
    .finally(() => {
        output.scrollTop = output.scrollHeight;
        update_wlan1_status()
    });
}

function update_wlan1_status(){
    fetch("/settings/wlan1_status")
    .then(data => data.json())
    .then(data => {
        if (!data.status.length){
            document.getElementById("wlan1_status").textContent = "wlan1 is currently connected to: no APs"
        }
        else {
            document.getElementById("wlan1_status").textContent = "wlan1 is currently connected to: "
            for (let i = 0; i < data.status.length; i++){
                if (i > 0){
                    document.getElementById("wlan1_status").textContent += ", " + data.status[i][3]
                }
                document.getElementById("wlan1_status").textContent += data.status[i][3]
            }
        }
    })
    .catch(err => {
        console.error(`Error: ${err}`)
    });
}

window.onload = () => {
    update_wlan1_status()
}