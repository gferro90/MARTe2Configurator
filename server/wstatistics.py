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
__date__ = "22/01/2018"

##
# Standard imports
##
import logging
import math
import os
import threading
import time
import timeit

##
# Project imports
##
from util.lockpool import LockPool
from util.shareddict import SharedDictionary
from util.sharedlist import SharedList

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class WStatistics:
    """ Statistics information about the webserver interface.
        Before and after calling the actual function whose performance is to be tracked, the functions startUpdate and endUpdate must be called.
    """

    def __init__(self):
        """ NOOP
        """
        #An instance of the updatedTimesLocal will be created for every forked process
        self.updatedTimesLocal = {}
        self.updatedTimes = SharedList()
        self.statistics = SharedDictionary()

    def load(self, config):
        """ TODO
        """
        ok = True
        try:
            numberOfLocks = config.getint("hieratika", "numberOfLocks")
            statisticsUpdatePeriod = config.getint("hieratika", "statisticsUpdatePeriod")
            self.lockPool = LockPool(numberOfLocks)
        except (ConfigParser.Error, KeyError) as e:
            log.critical(str(e))
            ok = False 
   
        if (ok):
            statisticsThread= threading.Thread(target=self.updateStatistics, args=(statisticsUpdatePeriod, ))
            statisticsThread.daemon = True
            statisticsThread.start()

        return ok

    def getTid(self):
        """
        Returns:
            A keyword which univocally identifies both the process and the thread.
        """
        tid = str(os.getpid())
        tid += "_"
        tid += str(threading.current_thread().ident) 
        return tid

    def startUpdate(self, key):
        """ Stores the current time against a given key. To be called before the key against which the statistics are to be updated has started its function.

        """
        keyTidPid = "{0}.{1}".format(self.getTid(), key)
        self.lockPool.acquire(key)
        now = timeit.default_timer()
        self.updatedTimesLocal[keyTidPid] = now
        self.lockPool.release(key)
        
    def endUpdate(self, key):
        """ To be called after the key against which the statistics are to be updated has finished its function.
        """
        now = timeit.default_timer()
        keyTidPid = "{0}.{1}".format(self.getTid(), key)
        self.lockPool.acquire(key)
        self.updatedTimes.append((key, now - self.updatedTimesLocal[keyTidPid]))
        self.lockPool.release(key)
       
    def updateStatistics(self, statisticsUpdatePeriod):
        """ Updates the available statistics for all the keys used so far. It shall be called in the background by a single process (i.e. it is not multi-process/multi-thread safe)
        
        Args:
            statisticsUpdatePeriod(int): update rate of the statistics loop.
        """
        while (True):
            while (len(self.updatedTimes) > 0):
                update = self.updatedTimes.pop()
                key = update[0]
                timeu = update[1]
                if (key in self.statistics):
                    stats = self.statistics[key]
                    cnt = stats["cnt"]
                    cnt = cnt + 1
                    stats["cnt"] = cnt 
                    stats["min"] = min(stats["min"], timeu)
                    stats["max"] = max(stats["max"], timeu)
                    acc = stats["acc"] + timeu
                    acc2 = stats["acc2"] + timeu * timeu
                    stats["acc"] = acc
                    stats["acc2"] = acc2
                    stats["mean"] = acc / cnt
                    stats["var"] = ((acc2 - acc) / cnt)
                else:
                    stats = {}
                    stats["cnt"] = 1
                    stats["min"] = timeu
                    stats["max"] = timeu
                    stats["acc"] = timeu
                    stats["acc2"] = timeu * timeu
                    stats["mean"] = timeu
                    stats["var"] = 0
                stats["last"] = timeu
                self.statistics[key] = stats
            time.sleep(statisticsUpdatePeriod)
           
    def getStatistics(self):
        stats = {}
        keys = self.statistics.keys()
        for k in keys:
            stats[k] = self.statistics[k]
        return stats
