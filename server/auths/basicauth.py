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
import ConfigParser
import logging

##
# Project imports
##
from auth import HieratikaAuth
from user import User
from usergroup import UserGroup 

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class HieratikaBasicAuth(HieratikaAuth):
    """ An authentication service implementation which reads the list of authorised users from the ini file.
        Note that the password is not used to validate the user.
    """
    
    def __init__(self):
        super(HieratikaBasicAuth, self).__init__()
        self.allowedUsers = []

    def load(self, config):
        """ Loads the list of usernames that are allowed to login into the system.
        
        Args:
            config(ConfigParser): shall contain the usernames and user groups in the "auth-impl" section inside a parameter named users.
            The format shall be users:username1;usergroup1;usergroup2,username2;usergroup1,... (i.e. users are separated by , and each user groups separated by ;)
        Returns:
            True if at least one user is specified.
        """
        try:
            users = config.get("auth-impl", "users").split(",")
            for u in users:
                groups = []
                gs = u.split(";")
                username = gs[0]
                for g in gs[1:]:
                    groups.append(UserGroup(g))
                user = User(username, groups) 
                self.allowedUsers.append(user)
                log.info("Registering user {0}".format(user))
            return True
        except Exception as e:
            log.critical("Could not read the users parameter {0}".format(e))
            return False
        return (len(self.allowedUsers) > 0)

    def authenticate(self, username, password):
        """ 
        Returns:
        	True if the username was specified in the list of allowed usernames.
        """
        return (username in self.allowedUsers)

    def getUsers(self):
        """
        Returns:
            All the users specified in the users configuration parameter.
        """
        return self.allowedUsers

    def getUser(self, username):
        user = None
        try:
            idx = self.allowedUsers.index(username)
        except ValueError as e:
            log.critical(e)
            idx = -1
        if (idx >= 0):
            user = self.allowedUsers[idx]
        return user


