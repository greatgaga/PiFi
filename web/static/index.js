const input  = document.getElementById("input");
const output = document.getElementById("output");
const socket = io();  // connect to Flask-SocketIO
let ip = "";

socket.on("connect", () => {
  console.log("Socket.IO connected");
});

socket.on("command_output", (msg) => {
  output.textContent += msg.data;
  output.scrollTop = output.scrollHeight;
});

function init_terminal() {
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const cmd = input.value.trim();
      if      (cmd === "help")  output.textContent += "Available: airmon-ng, aircrack-ng, airodump-ng, nmap, nc. Exit to stop command\n";
      else if (cmd === "clear") output.textContent = "";
      else if (cmd === "exit") socket.emit("stop_command");
      else {
        output.textContent += `$ ${cmd}\n`;
        socket.emit("run_command", { command: cmd });
      }
      output.scrollTop = output.scrollHeight;
      input.value = "";
    }
  });
}

window.onload = init_terminal;