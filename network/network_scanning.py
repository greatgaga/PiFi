import nmap
import socket
import netifaces

scanner = nmap.PortScanner()

def get_rpi_ip():
    try:
        ip = netifaces.ifaddresses("wlan0")[netifaces.AF_INET][0]["addr"]
    except (ValueError, KeyError):
        return None
    return ip

# host discovery via netifaces
def host_discovery():
    # getting our IP so we can setup the scan to scan only for our specific subnet 
    ip = get_rpi_ip()
    scanner.scan(hosts = ip + "/24", arguments = "-sP")
    return scanner.all_hosts()

def host_port_scan(host):
    result = scanner.scan(hosts = host, arguments = "-p- -sS -Pn")
    return result

def host_version_scan(host):
    result = scanner.scan(hosts = host, arguments= "-sV -sS --host-timeout 60s -Pn")
    return result

def host_vuln_scanner(host):
    result = scanner.scan(hosts = host, arguments = "-sS -sV --host-timeout 60s --script vuln -Pn")
    return result