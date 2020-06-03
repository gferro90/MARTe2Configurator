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
__date__ = "17/11/2017"

##
# Standard imports
##
from abc import ABCMeta, abstractmethod
import ConfigParser
import datetime
import json
import logging
import multiprocessing
import multiprocessing.managers
import os
import time
import threading

##
# Project imports
##
from util.broadcastqueue import BroadcastQueue
from util.shareddict import SharedDictionary

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class HieratikaServer(object):
    """ Abstract class for any server implementation.
        It implements the inter-client SSE streaming mechanism which allows to notify all the registered clients
        about changes in the schedule or in the plant.
    """
    
    __metaclass__ = ABCMeta

    def __init__(self):
        super(HieratikaServer, self).__init__()
        
    def loadCommon(self, config):
        """ Loads parameters that are common to all server implementations.
        
        Args:
            config (ConfigParser): parameters that are common to all server implementations:
            - udpBroadcastPort (int): the port that is used by the broadcastqueue.
        Returns:
            True if all the parameters are successfully loaded.
        """
        self.streamUsers = SharedDictionary() 
        try:
            #IPC using UDP sockets
            udpPort = config.getint("hieratika", "udpBroadcastQueuePort")
            self.standalone = config.getboolean("hieratika", "standalone")
            self.udpQueue = BroadcastQueue(udpPort)
        except (KeyError, ValueError, ConfigParser.Error) as e:
            log.critical("Failed to load configuration parameters {0}".format(e))
            return False
        return True

    def getTid(self):
        """
        Returns:
            A keyword which univocally identifies both the process and the thread.
        """
        tid = str(os.getpid())
        tid += "_"
        tid += str(threading.current_thread().ident) 
        return tid
 
    def streamData(self, username, token):
        """ Streams data back to the client using SSE.
            The inferface is provided by a broadcastqueue.
         
        Args:
            username (str): user requesting for data to be streamed.
            token (str): login token of the user requesting for data to be streamed.
        """
        #TODO This implementation has a design choice that has to be discussed in the future: all the variables are always streamed, even if the client might 
        #have no interest on them (because e.g. the page he is browsing has none the variables that have been updated). This design choice makes the server
        #processing lighter at the expense of increased bandwidth and more processing on the client (which has to decide if the updated variables are relevant to him or not).
        #An alternative would be to use a registrar at the server side and to filter before sending to the client. Given that the current architecture is multi process and multi threading
        #this might also have a performance impact which is not negligible, as the registrar would have to be implemented using multi process safe components (e.g. multiprocessing.Manager()) or 
        #to use a local mechanism which allows to register variables using the UDP queue. This strategy would allow to have the registrar structures local to the streamData thread and would potentially
        #increase performance.
        tid = None
        try:
            log.info("Streaming data for user {0} ({1})".format(username, token))
            while True:
                if (tid == None):
                    # The first time just register the Queue and send back the TID so that updates from this client are not sent back to itself (see updateschedule)
                    tid = self.getTid()
                    encodedPy = {"reset": True, "tid": tid}
                    encodedJson = json.dumps(encodedPy)
                else:
                    # Monitor on change
                    encodedJson = self.udpQueue.get()
                    if (encodedJson == None):
                        encodedJson = ""
                        time.sleep(0.01)
                    else:
                        log.debug("Streaming {0}".format(encodedJson))
                        encodedPy = json.loads(encodedJson)
                        if ("logout" in encodedPy):
                            if (encodedPy["logout"] == token):
                                log.info("Stopping streamData as user {0} in instance ({1}) logged out".format(username, token))
                                break
                            else:
                                encodedJson = ""
                                time.sleep(0.01)
                yield "data: {0}\n\n".format(encodedJson)
        except Exception as e:
            log.critical("streamData failed for user {0} in instance ({1}) {2}".format(username, token, e))
            self.streamData(username, token)
        log.info("Stopped streamData for user {0} in instance ({1})".format(username, token))

    def queueStreamData(self, jSonData):
        """ Streams the input jSonData to all the SSE registered clients. This data contains the id of the client thread (received the first time the client registered in streamData), the scheduleUID related to the update and a dictionary with the list of variables that were update. If the update is from the plant the tid and scheduleUID parameters are ignored.
        
        Args 
            jSonData (json): the data to be streamed in the format {tid: threadIdWhichTriggeredTheUpdate, scheduleUID:idOfScheduleWhichTriggeredTheUpdate, variables:{varibleName1:variableValue1, ...}}
        """
        self.udpQueue.put(jSonData)

    def userLoggedIn(self, username, token):
        """ Called everytime a user is logged in into the system.
        
        Args:
            username (str): the username of the user.
        """
        pass

    def userLoggedOut(self, username, token):
        """ Called everytime a user is logged in into the system.
        
        Args:
            username (str): the username of the user.
        """
        self.udpQueue.put(json.dumps({"logout": token}))

    def isStandalone(self):
        """
        Returns:
            True if the server is configured to run standalone (i.e. not distributed and not multi-user).
        """
        return self.standalone
