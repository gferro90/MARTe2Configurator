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
import getpass
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
class HieratikaStdAloneAuth(HieratikaAuth):
    """ An authentication service implementation which provides access only to the user which has launched the service.
        Note that the password is not used to validate the user.
    """
    
    def __init__(self):
        super(HieratikaStdAloneAuth, self).__init__()
        self.user = None
        

    def load(self, config):
        """ Loads the list of groups that are to be associated with this user.
        
        Returns:
            True 
        """
        try:
            groups = config.get("auth-impl", "groups").split(",")
        except Exception as e:
            log.critical("Could not read the groups parameter {0}".format(e))
            return False
        self.user = User(getpass.getuser(), groups)
        return True

    def authenticate(self, username, password):
        """ NOOP
        """
        return True 

    def getUsers(self):
        """
        Returns:
            The user which has started the hieratika service.
        """
        return [self.user]

    def getUser(self, username):
        return self.user


