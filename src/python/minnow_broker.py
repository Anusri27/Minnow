#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import zmq

def main():

    context = zmq.Context()

    # Socket facing producers
    frontend = context.socket(zmq.XPUB)
    frontend.bind("tcp://*:5555")

    # Socket facing consumers
    backend = context.socket(zmq.XSUB)
    backend.bind("tcp://*:5556")

    zmq.proxy(frontend, backend)

    # We never get here…
    frontend.close()
    backend.close()
    context.term()

if __name__ == "__main__":
    main()