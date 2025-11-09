#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#

"""
start_sampleapp
~~~~~~~~~~~~~~~~~

This module provides a sample RESTful web application using the WeApRous framework.

It defines basic route handlers and launches a TCP-based backend server to serve
HTTP requests. The application includes a login endpoint and a greeting endpoint,
and can be configured via command-line arguments.
"""

import json
import socket
import argparse

from daemon.weaprous import WeApRous

PORT = 8000  # Default port

# Create the WeApRous application instance
app = WeApRous()

# ----------------------------------------------------------
# Route 1: login_post
# ----------------------------------------------------------
@app.route("/login_post", methods=["POST"])
def login_post(req):
    """
    Handle a login request.
    This receives the full Request object from the HTTP adapter.
    """
    print("[SampleApp] Received login POST: {} {}".format(req.parameters.get("username"),
                                                          req.parameters.get("password")))

    username = req.parameters.get("username", "")
    password = req.parameters.get("password", "")

    # Check simple credentials (example only)
    if username == "admin" and password == "123":
        return {"status": "success", "message": "Login successful!"}
    else:
        return {"status": "fail", "message": "Invalid username/password!"}


# ----------------------------------------------------------
# Route 2: echo
# ----------------------------------------------------------
@app.route("/echo", methods=["POST"])
def echo(body):
    """
    This route echos back JSON content sent by clients.
    """
    try:
        data = json.loads(body)
        return {"echo": data}
    except:
        return {"error": "Invalid JSON in /echo"}


# ----------------------------------------------------------
# Route 3: hello
# ----------------------------------------------------------
@app.route("/hello", methods=["GET"])
def hello(headers=None, body=None):
    """
    Simple hello route
    """
    return {"message": "Hello from SampleApp!"}


# ----------------------------------------------------------
# Main: run application
# ----------------------------------------------------------
if __name__ == "__main__":
    print(">>> RUNNING start_sampleapp.py FROM THIS FILE <<<")
    parser = argparse.ArgumentParser(prog="SampleApp", description="RESTful Sample App", epilog="")
    parser.add_argument("--server-ip", default="0.0.0.0")
    parser.add_argument("--server-port", type=int, default=PORT)

    args = parser.parse_args()

    ip = args.server_ip
    port = args.server_port

    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()
