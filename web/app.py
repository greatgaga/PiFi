import sys, os
from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO
import subprocess
import threading
from collections import defaultdict
import signal, os
import time

# make sure your project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from network import network_scanning
from network import AP_attacks
from network import AP_scans
from network import network_attacks
from network import arp_poisoning
from network import evil_twin
from network import settings

current_procs = defaultdict(lambda: None)

def get_old_connection_wlan0():
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "dev"],
            capture_output=True,
            text=True,
            check=True
        )

        connections = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.strip().split(":", maxsplit=3)
            if len(parts) == 4:
                device, dev_type, state, connection = parts
                if device == "wlan0":
                    connections.append([device, dev_type, state, connection])

        return connections

    except Exception as e:
        print(f"Error: {e}")
        return []

def remove_connections_wlan0(connections):
    try:
        for connection in connections:
            conn_name = connection[3]
            if (conn_name == ''):
                pass
            else:
                subprocess.run(["nmcli", "connection", "delete", conn_name], check=True)
                print(f"Connection '{conn_name}' deleted.")
    except subprocess.CalledProcessError as e:
        print(f"Error deleting connection: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def change_connection_wlan0(SSID = "PiFi", password = "pifi1234"):
    try:
        # Get current wlan0 connections
        old_connections = get_old_connection_wlan0()

        # Remove old connections
        remove_connections_wlan0(old_connections)

        # connecting to new network
        subprocess.run(["sudo", "nmcli", "device", "wifi", "rescan", "ifname", "wlan0"], check=True)
        subprocess.run(["sudo", "nmcli", "device", "wifi", "list", "ifname", "wlan0"], check=True)
        if len(password):
            for i in range(3):
                try:
                    subprocess.run(["nmcli", "device", "wifi", "connect", SSID, "password", password, "ifname", "wlan0"], check=True)
                    break
                except Exception as e:
                    continue
        else:
            for i in range(3):
                try:
                    subprocess.run(["nmcli", "device", "wifi", "connect", SSID, "ifname", "wlan0"], check=True)
                    break
                except Exception as e:
                    continue
        return "done\n"
    except Exception as e:
        return f"Error: {e}\n"
    
try:
    connections = get_old_connection_wlan0()
    change_connection_wlan0()
    print(connections)
    while len(connections) == 0:
        print("No wlan0 connection found, trying to connect...")
        change_connection_wlan0()
        subprocess.run(["sudo", "nmcli", "device", "wifi", "rescan", "ifname", "wlan0"], check=True)
        subprocess.run(["sudo", "nmcli", "device", "wifi", "list", "ifname", "wlan0"], check=True)
        time.sleep(1)
except Exception as e:
    print(f"Error while connecting to wlan0: {e}")
    sys.exit(1)

print("wlan0 connected succesfuly successfully.")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading", logger=True, engineio_logger=True)

# --- HTTP routes ---
@app.route("/", methods=["GET"])
def root():
    return render_template("root.html")

@app.route("/network_scanning", methods=["GET"])
def network_scanning_page():
    return render_template("network_scanning.html")

@app.route("/network_attacks", methods=["GET"])
def network_attacks_page():
    return render_template("network_attacks.html")

@app.route("/AP_attacks", methods=["GET"])
def AP_attacks_page():
    return render_template("AP_attacks.html")

@app.route("/AP_scanning", methods=["GET"])
def AP_scanning_page():
    return render_template("AP_scans.html")

@app.route("/ARP_poisoning", methods=["GET", "POST"])
def ARP_poisoning_page():
    return render_template("ARP_poisoning.html")

@app.route("/evil_twin", methods=["GET", "POST"])
def evil_twin_page():
    return render_template("Evil_twin.html")

@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    return render_template("settings.html")

# --- API ---
@app.route("/network_scanning/host_discovery", methods=["GET", "POST"])
def handle_host_discovery():
    return jsonify(network_scanning.host_discovery())

@app.route("/get_rpi_ip", methods=["GET"])
def get_rpi_ip():
    ip = network_scanning.get_rpi_ip() or ""
    return jsonify({"ip": ip})

@app.route("/network_scanning/host_port_scan", methods=["POST"])
def port_scan():
    print("Port scanner running")
    data = request.get_json()
    if not data or "host" not in data:
        return jsonify({"error": "No host provided"}), 400

    host = data["host"]
    result = network_scanning.host_port_scan(host)
    print(result)
    
    open_ports = []
    try:
        for port, info in result['scan'][host]['tcp'].items():
            if info['state'] == 'open':
                open_ports.append(port)
    except KeyError:
        pass

    print(open_ports)

    return jsonify({
        "host": host,
        "open_ports": open_ports
    })

@app.route("/network_scanning/host_version_scan", methods=["POST"])
def version_scan():
    print("Version scanner running")
    data = request.get_json()
    if not data or "host" not in data:
        return jsonify({"error": "No host provided"}), 400

    host = data["host"]
    result = network_scanning.host_version_scan(host) 

    version_info = []
    try:
        tcp_ports = result['scan'][host]['tcp']
        for port, info in tcp_ports.items():
            if info['state'] == 'open':
                service = info.get('name', 'unknown')
                version = info.get('version', '')
                product = info.get('product', '')
                extra_info = info.get('extrainfo', '')
                
                version_info.append({
                    "port": port,
                    "state": info['state'],
                    "service": service,
                    "product": product,
                    "version": version,
                })
    except KeyError:
        pass

    return jsonify({
        "host": host,
        "services": version_info
    })

@app.route("/network_scanning/host_vuln_scan", methods=["POST"])
def vuln_scan():
    print("Vuln scanner running")
    data = request.get_json()
    if not data or "host" not in data:
        return jsonify({"error": "No host provided"}), 400

    host = data["host"]
    result = network_scanning.host_vuln_scanner(host)  

    vuln_info = []
    try:
        print(result['scan'])
        tcp_ports = result['scan'][host]['tcp']
        for port, info in tcp_ports.items():
            if info['state'] == 'open':
                scripts = info.get('script', {}) 

                vuln_info.append({
                    "port": port,
                    "state": info['state'],
                    "service": info.get('name', 'unknown'),
                    "product": info.get('product', ''),
                    "version": info.get('version', ''),
                    "extrainfo": info.get('extrainfo', ''),
                    "vulnerabilities": scripts
                })
    except KeyError:
        pass

    return jsonify({
        "host": host,
        "vulnerabilities": vuln_info
    })

@app.route("/AP_attacks/deauth_host", methods=["POST"])
def deauth_host():
    print("Deauth host running")
    data = request.get_json()
    if not data or "host" not in data:
        return jsonify({"error": "No host provided"}), 400
    
    host = data["host"]
    bssid = data["bssid"]
    AP_attacks.deauth_host(host, bssid)

    return '', 204

@app.route("/AP_attacks/deauth_AP", methods=["POST", "GET"])
def deauth_AP():
    print("Death AP started")
    data = request.get_json()
    bssid = data["AP"]

    AP_attacks.deauth_AP(bssid)

    return '', 204

@app.route("/AP_attacks/deauth_all", methods=["POST", "GET"])
def deauth_all():
    print("Deauth all started")
    
    AP_attacks.deauth_all()

    return '', 204

@app.route("/AP_scans/hosts_scan", methods=["POST", "GET"])
def hosts_scan():
    print("Hosts scan running")

    hosts = AP_scans.get_hosts_mac()

    return jsonify({
        "hosts": hosts 
    }) 

@app.route("/AP_scans/AP_scan", methods=["POST", "GET"])
def AP_scan():
    print("AP scan running")

    ssids = AP_scans.get_AP_mac()

    print(ssids)

    return jsonify({
        "ssids": ssids
    })

@app.route("/arp_poisoning/arp_poison", methods=["POST"])
def ARP_poison():
    print("ARP poison running")
    data = request.get_json()

    host = data.get("host")
    attacker = data.get("attacker")

    result = arp_poisoning.arp_poison(host, attacker)

    if (result == False):
        return jsonify({"status": "error"})
    else:
        return jsonify({"status": "completed"})
    
@app.route("/arp_poisoning/undo_arp_poison", methods=["POST"])
def undo_ARP_poison():
    print("Undo ARP poison running")
    data = request.get_json()

    host = data.get("host")
    attacker = data.get("attacker")

    result = arp_poisoning.undo_arp_poison(host, attacker)

    if (result == True):
        return jsonify({"status": "completed"})
    else:
        return jsonify({"status": "error"})
    
@app.route("/evil_twin/create_evil_twin", methods=["POST", "GET"])
def start_evil_twin():
    print("Start evil twin running")    
    data = request.get_json()

    evil_twin_name = data.get("AP_name")
    evil_twin_password = data.get("AP_password")
    connect_to_wlan0 = data.get("connect_to_wlan0")

    result = evil_twin.create_evil_twin(evil_twin_name, evil_twin_password, connect_to_wlan0)

    return jsonify({"status": result})

@app.route("/evil_twin/remove_evil_twin", methods=["POST", "GET"])
def remove_evil_twin():
    print("Remove evil twin running")

    result = evil_twin.remove_evil_twin()

    return jsonify({"status": result})

@app.route("/settings/change_connection_wlan1", methods=["POST", "GET"])
def change_connection_wlan1():
    print("Change connection wlan running")
    data = request.get_json()

    SSID = data["SSID"]
    password = data["password"]

    result = settings.change_connection_wlan1(SSID, password)

    return jsonify({"status": result})

@app.route("/settings/wlan1_status", methods=["POST", "GET"])
def wlan1_status():
    print("wlan1 status is running")
    
    result = settings.get_old_connection()

    return jsonify({"status": result})

# --- WebSocket handler for evil twin with dns spoofing ---
@socketio.on("create_evil_twin_with_dns_spoof")
def run_create_ewil_twin_dns_spoof(data):
    ssid = data.get("SSID", "").strip()
    passkey = data.get("passkey", "").strip()
    connect_to_wlan0 = data.get("connect_to_wlan0", False)
    sid = request.sid

    if not ssid or (len(passkey) < 8 and len(passkey) > 0):
        socketio.emit("output", {"data": "No SSID provided or password isnt long enough.\n"}, to=sid)
        return
    
    def worker():
        try:
            # Emit a status message
            socketio.emit("output", {"data": "Starting Evil Twin with DNS spoofing...\n"}, to=sid)

            # Run the function directly
            result = evil_twin.create_evil_twin_with_dns_spoof(ssid, passkey, connect_to_wlan0, sid, socketio)

            # Emit the result string
            socketio.emit("output", {"data": result}, to=sid)
        except Exception as e:
            socketio.emit("output", {"data": f"Error: {e}\n"}, to=sid)
        finally:
            current_procs[sid] = None

    threading.Thread(target=worker, daemon=True).start()

# stop evil twin handler
@socketio.on("stop_evil_twin_dns_spoof")
def stop_dns_spoof():
    sid = request.sid
    proc = current_procs.get(sid)

    if proc and proc.poll() is None:
        # Send SIGINT to the entire process group (like Ctrl+C)
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
        socketio.emit("output", {"data": "\n^C\n"}, to=sid)
    else:
        socketio.emit("output", {"data": "No process running.\n"}, to=sid)

# --- WebSocket handler ---
@socketio.on("run_command")
def run_command_ws(data):
    cmd = data.get("command", "").strip()
    sid = request.sid

    if not cmd:
        socketio.emit("command_output", {"data": "No command provided.\n"}, to=sid)
        return

    def worker():
        try:
            # Start the process in its own process group
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                preexec_fn=os.setsid
            )
            # Save it so stop_command can find it
            current_procs[sid] = proc

            # Stream output back to the client
            for line in proc.stdout:
                socketio.emit("command_output", {"data": line}, to=sid)
            proc.wait()

        except Exception as e:
            socketio.emit("command_output", {"data": f"Error: {e}\n"}, to=sid)
        finally:
            current_procs[sid] = None

    threading.Thread(target=worker, daemon=True).start()

# stop_command handler
@socketio.on("stop_command")
def stop_command():
    sid = request.sid
    proc = current_procs.get(sid)

    if proc and proc.poll() is None:
        # Send SIGINT to the entire process group (like Ctrl+C)
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
        socketio.emit("command_output", {"data": "\n^C\n"}, to=sid)
    else:
        socketio.emit("command_output", {"data": "No process running.\n"}, to=sid)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)