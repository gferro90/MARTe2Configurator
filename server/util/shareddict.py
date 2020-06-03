#!/usr/bin/env python

""" A dictionary which can be safely shared between processes.
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

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class SharedDictionary(object):
    """ A multiprocessing, multithreading, dictionary which can be safely shared between processes.
        This is to address the myriad of problems that have been found while trying to share state between different processes using the multiprocessing module:
        - Issues with sharing access to dictionary with forked processes (see https://stackoverflow.com/questions/68645/static-class-variables-in-python)
        - Issues related to using gevent and multiprocessing
        Only the methods which are currently needed by hieratika are proxied.
    """

    globalMux = multiprocessing.Lock()
    globalManager = multiprocessing.managers.SyncManager()
    globalManager.start()

    def __init__(self):
        """ Creates the shared dictionary.
        """
        super(SharedDictionary, self).__init__()
        self.mux = SharedDictionary.globalMux
        self.mux.acquire()
        self.dictImpl = SharedDictionary.globalManager.dict()
        self.mux.release()

    def get (self, key):
        """ See dict.get()
        """
        self.mux.acquire()
        try:
            ret = self.dictImpl.get(key)
        except Exception:
            self.mux.release()
            raise
        self.mux.release()
        return ret

    def update (self, keyitem):
        """ See dict.update()
        """
        self.mux.acquire()
        try:
            ret = self.dictImpl.update(keyitem)
        except Exception:
            self.mux.release()
            raise
        self.mux.release()
        return ret

    def has_key (self, key):
        """ See dict.has_key()
        """
        self.mux.acquire()
        ret = self.dictImpl.has_key(key)
        self.mux.release()
        return ret

    def __getitem__(self, key):
        """ See dict.__getitem__()
        """
        self.mux.acquire()
        try:
            ret = self.dictImpl.__getitem__(key)
        #This has to stay since otherwise accessing an invalid index will trigger a infinite loop (as __getitem__ will be called again and will lock forever in mux.acquire)
        except Exception:
            self.mux.release()
            raise

        self.mux.release()
        return ret

    def __setitem__(self, key, item):
        """ See dict.__setitem__()
        """
        self.mux.acquire()
        ret = self.dictImpl.__setitem__(key, item)
        self.mux.release()
        return ret

    def pop(self, key):
        """ See dict.pop()
        """
        self.mux.acquire()
        try:
            ret = self.dictImpl.pop(key)
        #This has to stay since otherwise accessing an invalid index will trigger a infinite loop (as __getitem__ will be called again and will lock forever in mux.acquire)
        except Exception:
            self.mux.release()
            raise

        self.mux.release()
        return ret

    def __len__(self):
        """ See dict.__len__()
        """
        self.mux.acquire()
        ret = self.dictImpl.__len__()
        self.mux.release()
        return ret

    def __contains__(self, item):
        """ See dict.__contains__()
        """
        self.mux.acquire()
        ret = self.dictImpl.__contains__(item)
        self.mux.release()
        return ret

    def __delitem__(self, item):
        """ See dict.__delitem__()
        """
        self.mux.acquire()
        ret = self.dictImpl.__delitem__(item)
        self.mux.release()
        return ret

    def keys(self):
        """ See dict.keys()
        """
        self.mux.acquire()
        ret = self.dictImpl.keys()
        self.mux.release()
        return ret

    def __str__(self):
        """ See dict.__str__
        """
        self.mux.acquire()
        ret = self.dictImpl.__str__()
        self.mux.release()
        return ret

