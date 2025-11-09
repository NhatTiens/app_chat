#
# p2p.py – Clean P2P client built from your original
#

import socket
import threading
import json
import time


class PeerClient:
    def __init__(self, peer_id, listen_ip="0.0.0.0", listen_port=5000):
        self.peer_id = peer_id
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.running = True

        # Storage for received messages
        self.messages = []

    # --------------------------
    # Start listener thread
    # --------------------------
    def start_listener(self):
        def listen():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((self.listen_ip, self.listen_port))
            sock.listen(5)

            print(f"[P2P] Listening on {self.listen_ip}:{self.listen_port}")

            while self.running:
                try:
                    conn, addr = sock.accept()
                    data = conn.recv(4096).decode()
                    if data:
                        try:
                            msg = json.loads(data)
                            print(f"[P2P] Message from {msg.get('from')}: {msg.get('message')}")
                            self.messages.append(msg)
                        except:
                            print("[P2P] Invalid JSON received")
                    conn.close()
                except:
                    pass

        t = threading.Thread(target=listen, daemon=True)
        t.start()

    # --------------------------
    # Send message to peer
    # --------------------------
    def send_to_peer(self, target_ip, target_port, message):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((target_ip, target_port))

            payload = {
                "from": self.peer_id,
                "message": message,
                "timestamp": time.time()
            }
            sock.sendall(json.dumps(payload).encode())
            sock.close()

            print(f"[P2P] Sent to {target_ip}:{target_port} → {message}")
        except Exception as e:
            print(f"[P2P] Send failed: {e}")

    # --------------------------
    # Main start entry
    # --------------------------
    def start(self):
        print(f"[P2P] Peer {self.peer_id} running at {self.listen_ip}:{self.listen_port}")
        self.start_listener()

        # Simple REPL
        while self.running:
            try:
                raw = input("> ").strip()
                if not raw:
                    continue

                if raw == "exit":
                    self.running = False
                    break

                parts = raw.split(" ")
                if len(parts) < 3:
                    print("Usage: send <ip> <port> <message>")
                    continue

                cmd = parts[0]

                if cmd == "send":
                    ip = parts[1]
                    port = int(parts[2])
                    msg = " ".join(parts[3:])
                    self.send_to_peer(ip, port, msg)
                else:
                    print("Unknown command")

            except KeyboardInterrupt:
                self.running = False
                break
