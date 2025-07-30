from scapy.all import *
import time
import subprocess

iface = "wlan1mon"

def start_wifi_adapter():
    subprocess.run(["bash", "./network/wifi_adapter_start.sh"], check = True)

def stop_wifi_adapter():
    subprocess.run(["bash", "./network/wifi_adapter_stop.sh"], check = True)

seen_macs = []

def handle_frame_for_mac(pkt):
    if pkt.haslayer(Dot11):
        mac = pkt.addr2
        if mac and not (mac in seen_macs):
            seen_macs.append(mac)
            print(f"{mac} found")

ssids = []
seen = []

def handle_frame_for_AP(pkt):
    if pkt.haslayer(Dot11Beacon):
        ssid = pkt[Dot11Elt].info.decode()
        bssid = pkt[Dot11].addr2
        channel = None

        elt = pkt[Dot11Elt]

        while isinstance(elt, Dot11Elt):
            if elt.ID == 3:
                channel = elt.info[0]
                break
            elt = elt.payload.getlayer(Dot11Elt)

        rssi = pkt.dBm_AntSignal if hasattr(pkt, 'dBm_AntSignal') else "N/A"

        enc_type = "Open"

        if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp):
            cap = pkt.sprintf("{Dot11Beacon:%Dot11Beacon.cap%}{Dot11ProbeResp:%Dot11ProbeResp.cap%}")
            if ("privacy" in cap.lower()):
                enc_type = "WEP"
                ssid = pkt[Dot11Elt].info.decode(errors = "ignore")
                raw = pkt[Dot11Elt:][1]

                while isinstance(raw, Dot11Elt):
                    if raw.ID == 48:
                        enc_type = "WPA2"
                    elif raw.ID == 221 and raw.info.startswith(b"\x00P\xf2\x01\x01\x00"):
                        enc_type = "WPA1"
                    raw = raw.payload

        if ssid and bssid and rssi and channel and enc_type and not ([ssid, bssid] in seen):
            ssids.append([ssid, bssid, str(channel), str(rssi), enc_type])
            seen.append([ssid, bssid])
            print(f"SSID: {ssid}, BSSID: {bssid}, channel: {channel}, RSSI: {rssi}, Encription type: {enc_type}")

def get_AP_mac():
    start_wifi_adapter()
    sniff(iface = iface, prn = handle_frame_for_AP, timeout = 30)
    stop_wifi_adapter()
    return ssids

def get_hosts_mac():
    start_wifi_adapter()
    sniff(iface = iface, prn = handle_frame_for_mac, timeout = 30)
    stop_wifi_adapter()
    return seen_macs