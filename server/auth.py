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
__date__ = "27/11/2017"

##
# Standard imports
##
from abc import ABCMeta, abstractmethod
import ConfigParser
import datetime
import logging
import multiprocessing
import os
import time
import threading
import uuid

##
# Project imports
##
from util.lockpool import LockPool
from util.shareddict import SharedDictionary

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class HieratikaAuth(object):
    """ Abstract class which manages user authentication.
    """
    
    __metaclass__ = ABCMeta

    def __init__(self):
        super(HieratikaAuth, self).__init__()
        self.logListeners = []
        self.stdAloneUsername = None
        

    def addLogListener(self, listener):
        """ Registers a listener which will be notfied everytime a user logs in or out from the system.
            The listener class shall implement the functions userLoggedIn(username, token) and userLoggedOut(username, token).
        Args(listener):
            The object to notify everytime a user logs in or out from the system.
        """
        self.logListeners.append(listener)

    def loadCommon(self, config):
        """ Loads parameters that are common to all authentication implementations.
        
        Args:
            config (ConfigParser): parameters that are common to all authenticate implementations:
            - loginMonitorUpdateRate (int): the time interval in seconds at which the state of logged in users is to be checked. 
            - loginMonitorMaxInactivityTime (int): maximum time that a given user can stay logged in without interacting with the server.
            - loginMaxUsers (int): maximum number of users that can be logged in at any time.
        Returns:
            True if all the parameters are successfully loaded.
        """
        self.tokens = SharedDictionary()
        self.mux = multiprocessing.Lock()
        try:
            self.standalone = config.getboolean("hieratika", "standalone")
            #For monitoring user login state
            if (not self.standalone):
                self.loginMonitorThread = threading.Thread(target=self.loginMonitor)
                self.loginMonitorUpdateRate = config.getint("hieratika", "loginMonitorUpdateRate")
                self.loginMonitorMaxInactivityTime = config.getint("hieratika", "loginMonitorMaxInactivityTime")
                self.loginMaxUsers = config.getint("hieratika", "loginMaxUsers")
                #This allow to interrupt the sleep
                self.loginMonitorEvent = threading.Event()
            else:
                log.info("Standalone mode was set and thus no monitoring thread will be started")
        except (KeyError, ValueError, ConfigParser.Error) as e:
            log.critical("Failed to load configuration parameters {0}".format(e))
            return False
        return True

    def start(self):
        """ Starts the login monitoring thread.
        """
        #To force the killing of the threadCleaner thread with Ctrl+C
        if (not self.standalone):
            log.info("Starting login monitoring thread")
            self.loginMonitorThread.daemon = True
            self.loginMonitorThread.start()
        return True

    def stop(self):
        """ Stops the login monitoring thread.
        """
        if (not self.standalone):
            log.info("Stopping login monitoring thread")
            self.loginMonitorEvent.set()
            self.loginMonitorThread.join()
            log.info("Stopped login monitoring thread")
        return True

    def loginMonitor(self):
        """ Monitors login state of users and logsout users that have not interacted with the system for a while
        """
        while (not self.loginMonitorEvent.is_set()):
            self.loginMonitorEvent.wait(self.loginMonitorUpdateRate)
            #Logout all the users that have not interacted with the server for a while
            currentTime = int(time.time())
            #Dict proxys cannot be iterated like a normal dict
            self.mux.acquire()
            keys = self.tokens.keys()
            for k in keys:
                if ((currentTime - self.tokens[k][1])  > self.loginMonitorMaxInactivityTime):
                    log.info("User {0} was not active for the last {1} seconds. User will be logout".format(self.tokens[k][0], self.loginMonitorMaxInactivityTime))
                    self.mux.release()
                    self.logout(k) 
                    self.mux.acquire()
            self.mux.release()
            #Print current server info
            self.printInfo()

    def isTokenValid(self, tokenId):
        """ Returns true if the token is valid (i.e. if it was created against a valid login).
            If the token is valid the last time at which this token was checked is updated.
            In standalone mode always return True.

        Args:
            tokenId (str): the token to verify.           
 
        Returns:
            True if the token is valid.
        """
        log.debug(">>Checking if tokenId: {0} is in the tokens list {1}".format(tokenId, self.tokens))
        if (not self.standalone):
            log.debug(">Checking if tokenId: {0} is in the tokens list {1}".format(tokenId, self.tokens))
            self.mux.acquire()
            log.debug("Checking if tokenId: {0} is in the tokens list {1}".format(tokenId, self.tokens))
            ok = (self.tokens.has_key(tokenId))
            log.debug("--Checking if tokenId: {0} is in the tokens list {1}".format(tokenId, self.tokens))
            if (ok):
                username = self.tokens.get(tokenId)[0]
                interactionTime = time.time()
                self.tokens.update([(tokenId, (username, interactionTime))])
                log.debug("Updated: {0} ({1}) : {2}".format(username, tokenId, interactionTime))
            self.mux.release()
        return ok

    def login(self, username, password):
        """ Tries to log a new user into the system.
            If successful a token will be associated to this user and registered into the system, so a subsequent call to
            isTokenValid, with this token, will return True.

        Returns:
            A User instance associated to a token described as a 32-character hexadecimal string or None if the login fails.
        """
        user = None
        if (not self.standalone):
            self.mux.acquire()
            numberOfLoggedUsers = len(self.tokens)
            self.mux.release()
            ok = (numberOfLoggedUsers < self.loginMaxUsers)
            if (ok):
                ok = self.authenticate(username, password)
                if (ok):
                    user = self.getUser(username) 
            else:
                log.critical("Could not register {0} . No more users allowed to register into the system (max number is: {1})".format(username, self.loginMaxUsers))
                self.printInfo()
        else:
            user = self.getUser(username) 

        ok = (user is not None)
        if (ok):
            log.info("{0} logged in successfully".format(user.getUsername()))
            loginToken = uuid.uuid4().hex
            user.setToken(loginToken)
            if (not self.standalone):
                self.mux.acquire()
                self.tokens[loginToken] = (user.getUsername(), int(time.time()))
                self.mux.release()
            else:
                self.stdAloneUsername = user.getUsername()

            for l in self.logListeners:
                l.userLoggedIn(username, loginToken)
        else:
            log.warning("{0} is not registered as a valid user".format(username))
        return user

    def printInfo(self):
        """ Prints information about the server state into the log.
        """
        return
        info = "Server information\n"
        info = info + "Logged users\n"
        info = info + "{0:40}|{1:40}\n".format("user", "Last interaction")
        self.mux.acquire()
        keys = self.tokens.keys()
        for k in keys:
            user = self.tokens[k][0]
            interactionTime = str(datetime.datetime.fromtimestamp(self.tokens[k][1]))
            info = info + "{0:40}|{1:40}\n".format(user, interactionTime)
        self.mux.release()
        log.info(info)

    def getUsernameFromToken(self, token):
        """ Returns the username associated to a given token.
        """
        if (not self.standalone):
            self.mux.acquire()
            try:
                username = self.tokens[token][0]
            except KeyError as e:
                log.critical("Failed to get user with token {0}".format(token))
                username = None
            self.mux.release()
        else:
            username = self.stdAloneUsername
        return username


    def logout(self, token):
        """ Logsout the user identified with the given token from the system.

        Args:
            token (str): token that was provided to the user when was logged in
        """
        try:
            self.mux.acquire()
            user = self.tokens[token][0]
            log.info("Logging out {0} with token {1}".format(user, token))
            del(self.tokens[token])
            self.mux.release()
            for l in self.logListeners:
                l.userLoggedOut(user, token)
        except KeyError as e:
            log.critical("Failed to logout user with token {0} : {1}".format(token, e))

    @abstractmethod
    def load(self, config):
        """ Configures the authentication service against a set of parameters. This set of parameters is specific for each implementation.
        
        Args:
            config(ConfigParser): the authentication specific implementation parameters are in the "auth-impl" section.
        Returns:
            True if the authentication service is successfully configured.
        """
        pass

    @abstractmethod 
    def authenticate(self, username, password):
        """ Authenticates a user into the system.
        
        Args:
            username (str): the username.
            password (str): the user password.
        Returns:
            True if the user is successfully authenticated.
        """
        pass

    @abstractmethod
    def getUsers(self):
        """
        Returns:
            All the system users.
        """
        pass

    @abstractmethod
    def getUser(self, username):
        """ 
        Args:
            username(str): the username of the user to get.
        Returns:
            The user associated to the given username or None if not found.
        """
        pass

