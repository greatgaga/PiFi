function run_host_discovery() {
  fetch("/get_rpi_ip")
    .then(res => res.json())
    .then(d => {
      const ip = d.ip || "";
      output.textContent += `$ nmap ${ip}/24 -sP\n`;
      return fetch("/network_scanning/host_discovery");
    }) 
    .then(res => res.json())
    .then(hosts => {
      if (Array.isArray(hosts) && hosts.length) {
        hosts.forEach(h => {
          output.textContent += `\u2022 ${h}\n`;
        });
      } else {
        output.textContent += "No hosts found.\n";
      }
    })
    .catch(err => {
      output.textContent += "Error during host discovery.\n";
      console.error("Host discovery error:", err);
    })
    .finally(() => {
      // Scroll to bottom in all cases
      output.scrollTop = output.scrollHeight;
    });
}

function run_host_port_scan(){
    const target = prompt("Target's IP:");
    if (!target) {
        output.textContent += "Scan canceled or no IP provided.\n";
        return;
    }

    output.textContent += `$ nmap ${target} -p- -sS -Pn\n`;
    output.textContent += `This will take a while to complete\n`;

    fetch("/network_scanning/host_port_scan", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ host: target })
    })
    .then(response => response.json())
    .then(data => {
        if (data && data.open_ports?.length) {
            output.textContent += `Open ports on ${target}:\n`;
            data.open_ports.forEach(port => {
                output.textContent += `\u2022 Port ${port}\n`;
            });
        } else {
            output.textContent += `No open ports found on ${target}.\n`;
        }
    })
    .catch(err => {
        output.textContent += "Error during host port scan.\n";
        console.error("Host port scan error:", err);
    })
    .finally(() => {
        output.scrollTop = output.scrollHeight;
    });
}

function run_host_version_scan(){
    const target = prompt("Target's IP:");
    if (!target) {
        output.textContent += "Scan canceled or no IP provided.\n";
        return;
    }

    output.textContent += `$ nmap ${target} -sV -sS -Pn\n`;
    output.textContent += `This will take a while to complete\n`;

    fetch("/network_scanning/host_version_scan", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ host: target })
    })
    .then(response => response.json())
    .then(data => {
        if (data && data.services?.length) {
            output.textContent += `Versions of software on ${target}:\n`;
            data.services.forEach(version => {
                output.textContent += `     \u2022 Port ${version.port}\n`;
                output.textContent += `         \u2022 State ${version.state}\n`;
                output.textContent += `         \u2022 Service ${version.service}\n`;
                output.textContent += `         \u2022 Product ${version.product}\n`;
                output.textContent += `         \u2022 Version ${version.version}\n`;
            });
        } else {
            output.textContent += `No open ports found on ${target}.\n`;
        }
    })
    .catch(err => {
        output.textContent += "Error during host port scan.\n";
        console.error("Host port scan error:", err);
    })
    .finally(() => {
        output.scrollTop = output.scrollHeight;
    });
}

function run_host_vulns_scan(){
    const target = prompt("Target's IP:");
    if (!target) {
        output.textContent += "Scan canceled or no IP provided.\n";
        return;
    }

    output.textContent += `$ nmap ${target} -sS -sV --host-timeout 60s --script vuln -Pn\n`;
    output.textContent += `This will take a while to complete\n`;

    fetch("/network_scanning/host_vuln_scan", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ host: target })
    })
    .then(response => response.json())
    .then(data => {
        if (data && data.vulnerabilities?.length) {
            output.textContent += `Vulns on ${target}:\n`;
            data.vulnerabilities.forEach(vuln => {
                output.textContent += `     \u2022 Port ${vuln.port}\n`;
                output.textContent += `         \u2022 State ${vuln.state}\n`;
                output.textContent += `         \u2022 Service ${vuln.service}\n`;
                output.textContent += `         \u2022 Product ${vuln.product}\n`;
                output.textContent += `         \u2022 Version ${vuln.version}\n`;
                output.textContent += `         \u2022 Vulnerabilities ${vuln.vulnerabilities}\n`;
            });
        } else {
            output.textContent += `No vulns found on ${target}.\n`;
        }
    })
    .catch(err => {
        output.textContent += "Error during host port scan.\n";
        console.error("Host port scan error:", err);
    })
    .finally(() => {
        output.scrollTop = output.scrollHeight;
    });
}

function run_hosts_vulns_scans() {
    fetch("/get_rpi_ip")
        .then(res => res.json())
        .then(d => {
            const ip = d.ip || "";
            output.textContent += `$ nmap ${ip}/24 -sP -Pn\n`;
            return fetch("/network_scanning/host_discovery");
        })
        .then(res => res.json())
        .then(hosts => {
            if (!Array.isArray(hosts) || !hosts.length) {
                output.textContent += "No hosts found.\n";
                return;
            }

            const scanPromises = hosts.map(target => {
                output.textContent += `$ nmap ${target} -sS -sV --host-timeout 60s --script vuln -Pn\n`;
                output.textContent += `This will take a while to complete\n`;

                return fetch("/network_scanning/host_vuln_scan", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ host: target })
                })
                .then(response => response.json())
                .then(data => {
                    if (data && data.vulnerabilities?.length) {
                        output.textContent += `Vulns on ${target}:\n`;
                        data.vulnerabilities.forEach(vuln => {
                            output.textContent += `     \u2022 Port ${vuln.port}\n`;
                            output.textContent += `         \u2022 State ${vuln.state}\n`;
                            output.textContent += `         \u2022 Service ${vuln.service}\n`;
                            output.textContent += `         \u2022 Product ${vuln.product}\n`;
                            output.textContent += `         \u2022 Version ${vuln.version}\n`;
                            output.textContent += `         \u2022 Vulnerabilities ${vuln.vulnerabilities}\n`;
                        });
                    } else {
                        output.textContent += `No vulns found on ${target}.\n`;
                    }
                })
                .catch(err => {
                    output.textContent += "Error during host port scan.\n";
                    console.error("Host port scan error:", err);
                })
                .finally(() => {
                    output.scrollTop = output.scrollHeight;
                });
            });

            return Promise.all(scanPromises);
        })
        .then(() => {
            output.textContent += "Hosts vulns scan completed\n";
            output.scrollTop = output.scrollHeight;
        })
        .catch(err => {
            output.textContent += "Error during host discovery or version scanning.\n";
            console.error("Error:", err);
        });
}

function run_hosts_versions_scans() {
    fetch("/get_rpi_ip")
        .then(res => res.json())
        .then(d => {
            const ip = d.ip || "";
            output.textContent += `$ nmap ${ip}/24 -sP -Pn\n`;
            return fetch("/network_scanning/host_discovery");
        })
        .then(res => res.json())
        .then(hosts => {
            if (!Array.isArray(hosts) || !hosts.length) {
                output.textContent += "No hosts found.\n";
                return;
            }

            const scanPromises = hosts.map(target => {
                output.textContent += `$ nmap ${target} -sV -sS\n`;
                output.textContent += `This will take a while to complete\n`;

                return fetch("/network_scanning/host_version_scan", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ host: target })
                })
                .then(response => response.json())
                .then(data => {
                    if (data && data.services?.length) {
                        output.textContent += `Versions of software on ${target}:\n`;
                        data.services.forEach(version => {
                            output.textContent += `     \u2022 Port ${version.port}\n`;
                            output.textContent += `         \u2022 State ${version.state}\n`;
                            output.textContent += `         \u2022 Service ${version.service}\n`;
                            output.textContent += `         \u2022 Product ${version.product}\n`;
                            output.textContent += `         \u2022 Version ${version.version}\n`;
                        });
                    } else {
                        output.textContent += `No open ports found on ${target}.\n`;
                    }
                })
                .catch(err => {
                    output.textContent += `Error during version scan on ${target}\n`;
                    console.error("Version scan error:", err);
                })
                .finally(() => {
                    output.scrollTop = output.scrollHeight;
                });
            });

            return Promise.all(scanPromises);
        })
        .then(() => {
            output.textContent += "Hosts version scan completed\n";
            output.scrollTop = output.scrollHeight;
        })
        .catch(err => {
            output.textContent += "Error during host discovery or version scanning.\n";
            console.error("Error:", err);
        });
}

function run_hosts_ports_scans() {
    fetch("/get_rpi_ip")
        .then(res => res.json())
        .then(d => {
            const ip = d.ip || "";
            output.textContent += `$ nmap ${ip}/24 -sP -Pn\n`;
            return fetch("/network_scanning/host_discovery");
        })
        .then(res => res.json())
        .then(hosts => {
            if (!Array.isArray(hosts) || !hosts.length) {
                output.textContent += "No hosts found.\n";
                return;
            }

            const scanPromises = hosts.map(target => {
                output.textContent += `$ nmap ${target} -p- -sS\n`;

                return fetch("/network_scanning/host_port_scan", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ host: target })
                })
                .then(response => response.json())
                .then(data => {
                    if (data && data.open_ports?.length) {
                        output.textContent += `Open ports on ${target}:\n`;
                        data.open_ports.forEach(port => {
                            output.textContent += `\u2022 Port ${port}\n`;
                        });
                    } else {
                        output.textContent += `No open ports found on ${target}.\n`;
                    }
                })
                .catch(err => {
                    output.textContent += `Error during port scan on ${target}\n`;
                    console.error("Host port scan error:", err);
                })
                .finally(() => {
                    output.scrollTop = output.scrollHeight;
                });
            });

            // Wait for all scan promises to finish
            return Promise.all(scanPromises);
        })
        .then(() => {
            output.textContent += "Hosts ports scan completed\n";
            output.scrollTop = output.scrollHeight;
        })
        .catch(err => {
            output.textContent += "Error during host discovery or port scanning.\n";
            console.error("Error:", err);
        });
}