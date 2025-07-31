# PiFi — Wi-Fi Pentesting Firmware for Raspberry Pi Zero 2 W

**PiFi** is a Wi-Fi pentesting firmware built for the Raspberry Pi Zero 2 W. It provides a one-click web interface to perform essential wireless network attacks for security testing, education, and research purposes.

---

## 🧰 Features

- ✅ Deauthentication attacks (disconnect devices from networks)
- ✅ Evil Twin AP with DNS spoofing
- ✅ ARP spoofing for MITM (Man-in-the-Middle)
- ✅ Network scanning and host discovery
- ✅ Lightweight web interface built with Flask + SocketIO

---

## ⚙️ Requirements

Before installing, ensure the following:

- 🐧 **Device**: Raspberry Pi Zero 2 W
- 💾 **OS**: Raspberry Pi OS (Bookworm or similar)
- 👤 **User**: Must be named `user`
- 🌐 **Internet**: Required during initial installation
- 📶 **Wi-Fi**: Must have `wlan1` available (e.g. external USB Wi-Fi adapter (adapter must support packet injection if you want all the features to work))

---

## 🚀 One-Line Installer

Install everything with a single command:

```bash
curl -fsSL https://raw.githubusercontent.com/greatgaga/PiFi/main/install.sh | sudo bash
```

## Usage

You need to host a network that is called: PiFi, with passkey: pifi1234. Also that network should work on frequency of 2.4GHz, 
and it will be good if network could use WPA2.
PiFi will connect to it and then it will start hosting web site on its IP address port 5000, so you should connect to it via browser
(eg http://10.0.0.2:5000)

## DISCLAIMER
**Use this for ethical purposes only!**
