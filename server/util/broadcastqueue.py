#!/usr/bin/env python
__copyright__ = """
    Copyright 2017 F4E | European Joint Undertaking for ITER and
    the Development of Fusion Energy ('Fusion for Energy').
    Licensed under the EUPL, Version 1.1 or - as soon they will be approved
    by the European Commission - subsequent versions of the EUPL (the "Licence")
    You may not use this work except in compliance with the Licence.
    You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
 
    Unless required by applicable law or agreed to in writing, 
    software distributed under the Licence is distributed on an "AS IS"
    basis, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
    or implied. See the Licence permissions and limitations under the Licence.
"""
__license__ = "EUPL"
__author__ = "Andre' Neto"
__date__ = "07/11/2017"


##
# Standard imports
##
import logging
import multiprocessing 
import os
import threading
import time
import zmq

##
# Project imports
##

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class BroadcastQueue:
    """ A one to many queue which allows to share objects between one and many processes.
        The implementation is based on a zmq published subscriber pattern.
    """
    
    def __init__(self, port, timeout = 100, address = "127.0.0.1"):
        """ Constructor.
        Args:
            port (int): the zmq port.
            timeout (int): maximum timeout in ms to wait for an item to arrive. If no item arrives in this time the queue will return None.
            address (str): the zmq address.
        """
        self.port = port
        self.timeout = timeout
        self.address = address
        self.proxyUrl = 'ipc://broadcastqueue-proxy-internal'
        self.sockets = {}
        #The proxy provides an ipc interface for the publishers that live in different processes
        p = multiprocessing.Process(target=self.proxy)
        p.start()

    def __del__(self):
        """ Destructor.
            Closes all the queue sockets.
        """
        for k,  sock in self.sockets.iteritems():
             sock.close()

    def proxy(self):
        """ Required to share the context between different processes. Heavily based on https://github.com/zeromq/pyzmq/issues/710
        """
        ctx = zmq.Context()
        sub = ctx.socket(zmq.ROUTER)
        #sub.setsockopt(zmq.SUBSCRIBE, "")
        sub.bind(self.proxyUrl)
        pub = ctx.socket(zmq.PUB)
        pub.bind("tcp://{0}:{1}".format(self.address, self.port))
        try:
            log.info("Starting zmq proxy and binding to ({0}) {1}:{2}".format(self.proxyUrl, self.address, self.port))
            zmq.proxy(sub, pub) 
        except Exception as e:
            log.critical("zmq proxy terminated {0}".format(e))
        log.critical("Exiting zmq proxy callback")
        
    def getSocket(self, receiver):
        """ Gets a socket. A socket will be cached for every pid/tid pair.
   
        Args:
            receiver (bool): True if the socket is for a subscriber. 
        Returns:
            A zmq socket.
        """
        uid = str(os.getpid()) + "_" + str(threading.current_thread().ident)
        if (receiver):
            uid = uid + "_rec"
        if (uid not in self.sockets):
            context = zmq.Context()
            if (receiver):
                sock = context.socket(zmq.SUB)
                sock.connect("tcp://{0}:{1}".format(self.address, self.port))
                log.info("Creating new subscriber socket @ {0}:{1}".format(self.address, self.port))
                sock.setsockopt(zmq.RCVTIMEO, self.timeout)
                sock.setsockopt(zmq.SUBSCRIBE, "")
            else:
                log.info("Creating new publisher socket {0} @ {1}:{2}".format(self.proxyUrl, self.address, self.port))
                sock = context.socket(zmq.DEALER)
                sock.sndhwm = 1100000
                sock.connect(self.proxyUrl)

            self.sockets[uid] = sock 
        return self.sockets[uid]

    def put(self, item):
        """ Puts an item in the queue and warns all the registered receivers.
        
        Args:
            item (str): the item to be sent.
        """
        sock = self.getSocket(False)
        sock.send_pyobj(item)
            
    def get(self):
        """ Gets an item from queue.
        
        Returns:
            The received item or None if a timeout occurs.
        """

        sock = self.getSocket(True)
        try:
            item = sock.recv_pyobj()
        except Exception as e:
            item = None 
        return item

