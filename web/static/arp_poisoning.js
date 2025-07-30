function run_arp_poison(){
    const targetInput = document.getElementById("target"); 
    const target = targetInput.value.trim();

    console.log(target);

    output.textContent += "$ echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward\n";
    output.textContent += "$ sudo python3 /networking_tools/arp_poison.py\n";

    fetch("/arp_poisoning/arp_poison", {
        method: "POST", 
        headers: {
            "Content-Type": "application/json"
        },
        // make this use acctuall gateway ip
        body: JSON.stringify({ host: target, attacker: "192.168.50.1" })
    })
    .then(data => data.json())
    .then(data => {
        output.textContent += data.status + "\n";
    })
    .catch(err => {
        output.textContent += "Error: " + err;
    })
    .finally(() => {
        output.scrollTop = output.scrollHeight;
    });
}

function run_undo_arp_poison(){
    const targetInput = document.getElementById("target"); 
    const target = targetInput.value.trim();

    output.textContent += "$ echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward\n";
    output.textContent += "$ sudo python3 /networking_tools/undo_arp_poison.py\n";

    fetch("/arp_poisoning/undo_arp_poison", {
        method: "POST", 
        headers: {
            "Content-Type": "application/json"
        },
        // make this use acctuall gateway ip
        body: JSON.stringify({ host: target, attacker: "192.168.50.1" })
    })
    .then(data => data.json())
    .then(data => {
        output.textContent += data.status + "\n";
    })
    .catch(err => {
        output.textContent += "Error: " + err;
    })
    .finally(() => {
        output.scrollTop = output.scrollHeight;
    });
}