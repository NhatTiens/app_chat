#
# Copyright (C) 2025 pdnguyen ...
# WeApRous release
#

"""
start_chatapp
~~~~~~~~~~~~~~~~

Refactored (clean & robust) Chat Application server for Task 2 (Client–Server).
- Preserves public API surface: route paths, HTTP methods, function names.
- Rewrites internals for clarity, validation, and safer handling.
"""

import json
import socket
import threading
import argparse
import time
from datetime import datetime

from daemon.weaprous import WeApRous

PORT = 8001  # Default port for chat server

# Global data structures for chat application
# NOTE: Keep same names & shapes so other modules that import these won't break
active_peers = {}        # {peer_id: {"ip": ip, "port": port, "last_seen": timestamp}}
channels = {}            # {channel_id: {"members": [peer_ids], "messages": []}}
peer_connections = {}    # {peer_id: socket_connection}  # (optional usage)

# A small lock to protect shared maps in concurrent routes/cleanup
_PEER_LOCK = threading.Lock()
_CHAN_LOCK = threading.Lock()

app = WeApRous()

# -------------------------------------------------------------------
# Utilities (internal helpers)
# -------------------------------------------------------------------

def _json_ok(**kwargs):
    """Standard success envelope."""
    payload = {"status": "success"}
    payload.update(kwargs)
    return json.dumps(payload)

def _json_err(msg, **kwargs):
    """Standard error envelope."""
    payload = {"status": "error", "message": msg}
    if kwargs:
        payload.update(kwargs)
    return json.dumps(payload)

def _now():
    return time.time()

def _safe_get(d, key, default=None, caster=None):
    val = d.get(key, default)
    if caster and val is not None:
        try:
            return caster(val)
        except Exception:
            return default
    return val

def _ensure_channel(name):
    """Create channel record if missing."""
    with _CHAN_LOCK:
        if name not in channels:
            channels[name] = {"members": [], "messages": []}
    return channels[name]

def _append_message(channel, frm, message):
    entry = {
        "from": frm,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "channel": channel
    }
    with _CHAN_LOCK:
        channels[channel]["messages"].append(entry)
        if frm not in channels[channel]["members"]:
            channels[channel]["members"].append(frm)
    return entry

def _peer_exists(peer_id):
    with _PEER_LOCK:
        return peer_id in active_peers

def _touch_peer(peer_id):
    with _PEER_LOCK:
        if peer_id in active_peers:
            active_peers[peer_id]["last_seen"] = _now()

def _register_peer(peer_id, ip, port):
    with _PEER_LOCK:
        active_peers[peer_id] = {"ip": ip, "port": port, "last_seen": _now()}

def _get_peer(peer_id):
    with _PEER_LOCK:
        return dict(active_peers.get(peer_id, {}))  # return shallow copy

def _list_peers():
    with _PEER_LOCK:
        # copy out to avoid long lock holds
        return {k: dict(v) for k, v in active_peers.items()}

def _cleanup_expired(ttl=300):
    """Remove peers inactive for more than ttl seconds."""
    now = _now()
    expired = []
    with _PEER_LOCK:
        for pid, info in list(active_peers.items()):
            if now - info.get("last_seen", 0) > ttl:
                expired.append(pid)
        for pid in expired:
            del active_peers[pid]
    return expired

def _parse_json_body(body):
    """Parse JSON body defensively, return {} on failure/empty."""
    if not body:
        return {}
    try:
        return json.loads(body)
    except Exception:
        return {}

# -------------------------------------------------------------------
# Routes (keep names & signatures & methods)
# -------------------------------------------------------------------

@app.route('/login', methods=['POST'])
def chat_login(headers="guest", body="anonymous"):
    """
    Handle user login for chat application.
    Expected body: {"username": "user1", "password": "pass"}
    """
    try:
        data = _parse_json_body(body)
        username = data.get('username') or "anonymous"
        password = data.get('password') or ""

        print(f"[ChatApp] Login attempt: {username}")

        # Simple authentication rule preserved (truthy username & password)
        if username and password:
            resp = {
                "status": "success",
                "message": "Login successful",
                "user": {"username": username}
            }
            return json.dumps(resp)
        return _json_err("Invalid credentials")
    except Exception as e:
        print(f"[ChatApp] Login error: {e}")
        return _json_err("Login failed")


@app.route('/submit-info', methods=['POST'])
def submit_peer_info(headers="guest", body="anonymous"):
    """
    Register peer information with the tracker server.
    Expected body: {"peer_id": "user1", "ip": "192.168.1.100", "port": 9999}
    """
    try:
        data = _parse_json_body(body)
        peer_id = data.get('peer_id')
        peer_ip = data.get('ip')
        peer_port = _safe_get(data, 'port', caster=int)

        if not (peer_id and peer_ip and peer_port):
            return _json_err("Missing peer information")

        _register_peer(peer_id, peer_ip, peer_port)
        print(f"[ChatApp] Registered peer: {peer_id} @ {peer_ip}:{peer_port}")
        return _json_ok(peer_id=peer_id, ip=peer_ip, port=peer_port)
    except Exception as e:
        print(f"[ChatApp] Submit info error: {e}")
        return _json_err("Registration failed")


@app.route('/get-list', methods=['GET'])
def get_peer_list(headers="guest", body="anonymous"):
    """
    Get the list of active peers.
    Returns: {"status":"success","peers":[{"peer_id":..,"ip":..,"port":..}], "count":N}
    """
    try:
        snapshot = _list_peers()
        peers = [{"peer_id": pid, "ip": info["ip"], "port": info["port"]} for pid, info in snapshot.items()]
        print(f"[ChatApp] Returned peer list: {len(peers)} peers")
        return _json_ok(peers=peers, count=len(peers))
    except Exception as e:
        print(f"[ChatApp] Get list error: {e}")
        return _json_err("Failed to get peer list")


@app.route('/connect-peer', methods=['POST'])
def connect_peer(headers="guest", body="anonymous"):
    """
    Initiate P2P connection to another peer.
    Expected body: {"from_peer": "user1", "to_peer": "user2"}
    """
    try:
        data = _parse_json_body(body)
        from_peer = data.get('from_peer')
        to_peer = data.get('to_peer')

        if not (from_peer and to_peer):
            return _json_err("Missing from/to peer")

        target = _get_peer(to_peer)
        if not target:
            return _json_err("Target peer not found")

        # Preserve original behavior: return target address
        print(f"[ChatApp] Connect request: {from_peer} -> {to_peer} @ {target.get('ip')}:{target.get('port')}")
        return _json_ok(target={"peer_id": to_peer, "ip": target.get("ip"), "port": target.get("port")})
    except Exception as e:
        print(f"[ChatApp] Connect peer error: {e}")
        return _json_err("Connect peer failed")


@app.route('/broadcast-peer', methods=['POST'])
def broadcast_peer(headers="guest", body="anonymous"):
    """
    Broadcast a message to a channel (logical broadcast record).
    Expected body: {"from_peer":"user1","message":"Hi","channel":"general"}
    """
    try:
        data = _parse_json_body(body)
        from_peer = data.get('from_peer')
        message = data.get('message')
        channel = data.get('channel') or "general"

        if not (from_peer and message):
            return _json_err("Missing message data")

        _ensure_channel(channel)
        _append_message(channel, from_peer, message)

        # (Optional) update liveness timestamp for sender
        _touch_peer(from_peer)

        # recipients count ~ (#active - sender) as in the original idea
        recips = max(0, len(_list_peers()) - 1)
        print(f"[ChatApp] Broadcast from {from_peer} in {channel}: {message}")
        return _json_ok(message="Message broadcasted", recipients=recips)
    except Exception as e:
        print(f"[ChatApp] Broadcast error: {e}")
        return _json_err("Broadcast failed")


@app.route('/send-peer', methods=['POST'])
def send_peer(headers="guest", body="anonymous"):
    """
    Send a direct message (logically stored alongside channel for simplicity).
    Expected body: {"from_peer":"user1","to_peer":"user2","message":"Hello","channel":"dm-user2"}
    """
    try:
        data = _parse_json_body(body)
        frm = data.get('from_peer')
        to = data.get('to_peer')
        msg = data.get('message')
        channel = data.get('channel') or f"dm-{to}" if to else "dm"

        if not (frm and to and msg):
            return _json_err("Missing direct message fields")

        # Logically append message into channel record (same as original behavior)
        _ensure_channel(channel)
        _append_message(channel, frm, msg)

        _touch_peer(frm)
        print(f"[ChatApp] Direct message {frm} -> {to} via {channel}: {msg}")
        return _json_ok(message="Message sent", to=to, channel=channel)
    except Exception as e:
        print(f"[ChatApp] Send peer error: {e}")
        return _json_err("Send failed")


@app.route('/get-messages', methods=['GET'])
def get_messages(headers="guest", body="anonymous"):
    """
    Get messages from a specific channel.
    Original code defaulted channel='general' & limit=50 (no query parsing).
    We keep the same defaults; if a proxy supplies query parsing in the future,
    behavior remains backward-compatible.
    """
    try:
        channel = "general"
        limit = 50

        if channel not in channels:
            return _json_ok(channel=channel, messages=[], count=0)

        with _CHAN_LOCK:
            msgs = channels[channel]["messages"][-limit:]

        return _json_ok(channel=channel, messages=msgs, count=len(msgs))
    except Exception as e:
        print(f"[ChatApp] Get messages error: {e}")
        return _json_err("Failed to get messages")


@app.route('/channels', methods=['GET'])
def get_channels(headers="guest", body="anonymous"):
    """
    Return available channels and member counts.
    """
    try:
        with _CHAN_LOCK:
            items = [
                {
                    "channel": name,
                    "members": list(entry.get("members", [])),
                    "message_count": len(entry.get("messages", [])),
                }
                for name, entry in channels.items()
            ]
        return _json_ok(channels=items, count=len(items))
    except Exception as e:
        print(f"[ChatApp] Channels error: {e}")
        return _json_err("Failed to get channels")


# -------------------------------------------------------------------
# Background maintenance
# -------------------------------------------------------------------

def cleanup_peers():
    """
    Periodically remove peers not seen for > 5 minutes.
    """
    while True:
        try:
            expired = _cleanup_expired(ttl=300)
            for pid in expired:
                print(f"[ChatApp] Cleaned up expired peer: {pid}")
            time.sleep(60)
        except Exception as e:
            print(f"[ChatApp] Cleanup error: {e}")
            time.sleep(60)


# -------------------------------------------------------------------
# Main entry
# -------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='ChatApp',
        description='Chat Application Server',
        epilog='WeApRous Chat daemon'
    )
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)

    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    # Start background cleanup task
    cleanup_thread = threading.Thread(target=cleanup_peers, daemon=True)
    cleanup_thread.start()

    print(f"[ChatApp] Starting chat application server on {ip}:{port}")
    print("[ChatApp] Available endpoints:")
    print("  POST /login - User authentication")
    print("  POST /submit-info - Register peer")
    print("  GET  /get-list - Get active peers")
    print("  POST /connect-peer - Get peer connection info")
    print("  POST /broadcast-peer - Broadcast message")
    print("  POST /send-peer - Send direct message")
    print("  GET  /get-messages - Get channel messages")
    print("  GET  /channels - Get available channels")

    app.prepare_address(ip, port)
    app.run()
