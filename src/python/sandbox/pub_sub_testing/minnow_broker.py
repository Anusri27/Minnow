#!/usr/bin/python
# -*- coding: UTF-8 -*-

import zmq

def main():

    context = zmq.Context.instance()


    # Socket facing producers
    frontend = context.socket(zmq.DISH)
    frontend.rcvtimeo = 1000
    frontend.bind("udp://127.0.0.1:5556")
    frontend.join('numbers')

    # Socket facing consumers
    backend = context.socket(zmq.RADIO)
    backend.connect("udp://127.0.0.1:5555")

    #frontend.setsockopt(zmq.SUBSCRIBE, b'')

    # Shunt messages out to our own subscribers
    while True:
        print('test')
        # Process all parts of the message
        try:
            message = frontend.recv(copy=False)
            print(message)
            backend.send(message)
        except:
            pass

if __name__ == "__main__":
    main()
