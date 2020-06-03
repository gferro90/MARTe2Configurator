#!/usr/bin/env python

""" A list which can be safely shared between processes.
"""
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
__date__ = "3/1/2018"

##
# Standard imports
##
import logging
import multiprocessing
import multiprocessing.managers
import os
import time
import threading

##
# Project imports
##
from util.shareddict import SharedDictionary

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class SharedList(object):
    """ A multiprocessing, multithreading, list which can be safely shared between processes.
        This is to address the myriad of problems that have been found while trying to share state between different processes using the multiprocessing module:
        - Issues with sharing access to dictionary with forked processes (see https://stackoverflow.com/questions/68645/static-class-variables-in-python)
        - Issues related to using gevent and multiprocessing
        Only the methods which are currently needed by hieratika are proxied.
    """

    def __init__(self):
        """ Creates the shared list.
        """
        super(SharedList, self).__init__()
        self.mux = SharedDictionary.globalMux
        self.mux.acquire()
        self.listImpl = SharedDictionary.globalManager.list()
        self.mux.release()

    def append (self, item):
        """ See list.append ()
        """
        self.mux.acquire()
        self.listImpl.append(item)
        self.mux.release()

    def index (self, item):
        """ See list.index ()
        """
        self.mux.acquire()
        ret = self.listImpl.index(item)
        self.mux.release()
        return ret

    def pop(self, i):
        """ See list.pop
        """
        self.mux.acquire()
        ret = self.listImpl.pop(i)
        self.mux.release()
        return ret

    def __getitem__(self, index):
        """ See list.__getitem__()
        """
        self.mux.acquire()
        try:
            ret = self.listImpl.__getitem__(index)
        #This has to stay since otherwise accessing an invalid index will trigger a infinite loop (as __getitem__ will be called again and will lock forever in mux.acquire)
        except Exception:
            self.mux.release()
            raise
        self.mux.release()
        return ret

    def __setitem__(self, key, item):
        """ See list.__setitem__()
        """
        self.mux.acquire()
        ret = self.listImpl.__setitem__(key, item)
        self.mux.release()
        return ret

    def __len__(self):
        """ See list.__len__()
        """
        self.mux.acquire()
        ret = self.listImpl.__len__()
        self.mux.release()
        return ret

    def __contains__(self, item):
        """ See list.__contains__()
        """
        self.mux.acquire()
        ret = self.listImpl.__contains__(item)
        self.mux.release()
        return ret

    def __str__(self):
        """ See list.__str__
        """
        self.mux.acquire()
        ret = self.listImpl.__str__()
        log.debug("here ret {0}".format(ret))
        self.mux.release()
        return ret


