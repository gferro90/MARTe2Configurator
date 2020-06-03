#!/usr/bin/env python

""" A multiprocessing, multithreading, pool of named semaphores.
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
__date__ = "17/11/2017"

##
# Standard imports
##
import logging
import multiprocessing
import os
import time
import threading

##
# Project imports
##
from util.shareddict import SharedDictionary
from util.sharedlist import SharedList

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class LockPool(object):
    """ A multiprocessing, multithreading, pool of named semaphores.

        Semaphores are identified by a key at the time of acquire and release.
        A semaphore associated to a given key will guarantee both multiprocessing and multithreading locking.
        It should be noted that the same process is allowed to acquire different named semaphores (using multithreading).

        The first time a key is acquired a multiprocessing.Lock is retrieved from a pool of semaphores. Subsequent acquires
        will either lock the process (if it is first time the caller process is acquiring this key) or the thread
        (after the second time the same caller process is acquiring the same key).

        When a key is released, if no more threads or processes are waiting on that key, the semaphore is returned to the pool.

    Args:
        numberOfLocks (int): the maximum number of simultaneous locks (i.e. different keys) that are allowed to lock on this pool.
    """

    def __init__(self, numberOfLocks):
        super(LockPool, self).__init__()
        #Global mux to protect access to shared counter (I have tested that this also protects against multi-threading in the scope of the same process)
        self.mux = multiprocessing.Lock()
        #Counts the number of locks that were allocated to a given key. Note that this has to be done this way as no multiprocessing semaphores nor multiprocessing dicts can be created after the child processes are forked (given that these will have a local copy of all the variables)
        self.allocatedLocksC = SharedDictionary()
        #Stores the self.sharedLocks array index that is assigned to a given key
        self.allocatedLocksI = SharedDictionary()
        #The pool of semaphores. One different semaphore will be allocated for each key
        self.sharedLocks = []
        #Stores the indexes of the semaphores which are ready to be used
        self.sharedLocksFreeState = SharedList()
        for i in range(numberOfLocks):
            self.sharedLocks.append(multiprocessing.Lock())
            self.sharedLocksFreeState.append(True)

    def acquire(self, key):
        """ Acquires a lock against a given key.
        
            Args:
                key (str): a unique identifier for the semaphore to be locked.
        """
        self.mux.acquire()
        pid = str(os.getpid())
        #Check if there is already a key with this lock
        if (key in self.allocatedLocksC):
            #Since this key was already locked, it can have been locked by another process or by this same process using
            #another thread
            self.allocatedLocksC[key] = self.allocatedLocksC[key] + 1
            idx = self.allocatedLocksI[key]
            log.debug("The process with pid: {0} had already locked the key (with another thread): {1}. Thread: {2}. Number of locks for this key:{3} idx:{4} L:{5} @ {6}".format(pid, key, threading.current_thread().ident, self.allocatedLocksC[key], id(idx), self.sharedLocks[idx], id(self.sharedLocks[idx])))
            lock = self.sharedLocks[idx]
            self.mux.release()
            lock.acquire()
        else:
            #Get a free lock
            try:
                #No one has ever requested to lock on this key, so just lock the process and prepare a shared lock
                idx = int(self.sharedLocksFreeState.index(True))
                #Get a multiprocessing semaphore which in not being used now. If this fails the exception below will be raised
                self.allocatedLocksC[key] = 1
                self.allocatedLocksI[key] = idx
                self.sharedLocksFreeState[idx] = False
                #Lock on the process
                log.debug("The process with pid: {0} is the first to lock key: {1}. Thread: {2} {3} L:{4} @ {5}".format(pid, key, threading.current_thread().ident, id(idx), self.sharedLocks[idx], id(self.sharedLocks[idx])))
                #Note that this will block the calling thread from this process but not other threads from the same process
                self.sharedLocks[idx].acquire()
                self.mux.release()
            except ValueError:
                #No locks available on the shared pool. Poll for resources to be available...
                self.mux.release()
                warned = False
                while(True not in self.sharedLocksFreeState):
                    if (not warned):
                        log.critical("No locks available on the shared pool. Sleeping while waiting for available resources.")
                        warned = True
                    time.sleep(1e-2)
                return self.acquire(key)

    def release(self, key):
        """ Releases a lock that was acquired against a given key.
        
            Args:
                key (str): the unique identifier that was used to lock the semaphore.
        """
        self.mux.acquire()
        pid = str(os.getpid())
        idx = int(self.allocatedLocksI[key])
        log.debug("Releasing process with pid: {0} for key: {1}. Thread: {2} {3} L:{4} @ {5}".format(pid, key, threading.current_thread().ident, id(idx), self.sharedLocks[idx], id(self.sharedLocks[idx]))) 
        lock = self.sharedLocks[idx]
        self.allocatedLocksC[key] = self.allocatedLocksC[key] - 1
        if (self.allocatedLocksC[key] == 0):
            log.debug("The process with pid: {0} was the last locking the key: {1} so that the semaphore will be returned to the pool. Thread: {2}".format(pid, key, threading.current_thread().ident)) 
            # If there are no more processes interested give it back to the pool 
            self.sharedLocksFreeState[idx] = True 
            self.allocatedLocksC.pop(key) 
            self.allocatedLocksI.pop(key)
        else: 
            log.debug("The process with pid: {0} is releasing the key: {1}. Thread: {2}. Number of locks: {3}".format(pid, key, threading.current_thread().ident, self.allocatedLocksC[key]))
        lock.release()
        self.mux.release()
               
    def isKeyInUse(self, key): 
        """ Checks if a given key is currently being used.
        
        Returns:
            True if the key currently being used to lock a semaphore in the pool.
        """
        self.mux.acquire()
        ret = (key in self.allocatedLocksC)
        self.mux.release()
        return ret

