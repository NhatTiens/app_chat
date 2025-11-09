import argparse
from daemon.p2p import PeerClient

def main():
    parser = argparse.ArgumentParser(description="P2P Client")
    parser.add_argument("--peer-id", required=True)
    parser.add_argument("--listen-ip", default="0.0.0.0")
    parser.add_argument("--listen-port", type=int, default=5000)

    args = parser.parse_args()

    client = PeerClient(
        peer_id=args.peer_id,
        listen_ip=args.listen_ip,
        listen_port=args.listen_port
    )

    client.start()


if __name__ == "__main__":
    main()
