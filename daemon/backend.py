"""
daemon.backend
~~~~~~~~~~~~~~~~~

Refactored backend daemon — same external API, rewritten internals.
"""

import socket
import threading
import argparse

from .response import *  # keep side-effect/compat imports
from .httpadapter import HttpAdapter
from .dictionary import CaseInsensitiveDict  # noqa: F401


def handle_client(ip, port, conn, addr, routes):
    """
    Instantiate HttpAdapter and delegate the whole request lifecycle.
    """
    adapter = HttpAdapter(ip, port, conn, addr, routes)
    adapter.handle_client(conn, addr, routes)


def run_backend(ip, port, routes):
    """
    Bind a TCP socket and accept clients concurrently via threads.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((ip, port))
        server.listen(50)

        print("[Backend] Listening on port {}".format(port))
        if routes:
            print("[Backend] route settings {}".format(routes))

        while True:
            conn, addr = server.accept()
            t = threading.Thread(
                target=handle_client,
                args=(ip, port, conn, addr, routes),
                daemon=True,
            )
            t.start()
    except socket.error as e:
        print("Socket error: {}".format(e))


def create_backend(ip, port, routes={}):
    """
    Public entrypoint kept for compatibility with start scripts.
    """
    run_backend(ip, port, routes)
