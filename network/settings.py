import subprocess

def get_old_connection():
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
                if device == "wlan1":
                    connections.append([device, dev_type, state, connection])

        return connections

    except Exception as e:
        print(f"Error: {e}")
        return []

def remove_connections(connections):
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

def change_connection_wlan1(SSID, password):
    try:
        # Get current wlan0 connections
        old_connections = get_old_connection()

        # Remove old connections
        remove_connections(old_connections)

        # connecting to new network
        subprocess.run(["sudo", "nmcli", "device", "wifi", "rescan", "ifname", "wlan1"], check=True)
        subprocess.run(["sudo", "nmcli", "device", "wifi", "list", "ifname", "wlan1"], check=True)
        if len(password):
            for i in range(3):
                try:
                    subprocess.run(["nmcli", "device", "wifi", "connect", SSID, "password", password, "ifname", "wlan1"], check=True)
                    break
                except Exception as e:
                    continue
        else:
            for i in range(3):
                try:
                    subprocess.run(["nmcli", "device", "wifi", "connect", SSID, "ifname", "wlan1"], check=True)
                    break
                except Exception as e:
                    continue
        return "done\n"
    except Exception as e:
        return f"Error: {e}\n"