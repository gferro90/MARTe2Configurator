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
__date__ = "22/12/2017"

##
# Standard imports
##
from abc import ABCMeta, abstractmethod
import json
import logging

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
class HieratikaMonitor(object):
    """ Abstract class for any live variable monitor implementation.
        TODO
    """
    
    __metaclass__ = ABCMeta

    def __init__(self):
        pass
        
    @abstractmethod
    def load(self, config):
        """ Configures the monitor against a set of parameters. This set of parameters is specific for each transformation implementation.
        
        Args:
            config(ConfigParser): the monitor specific implementation parameters are in the section "live-impl".
        Returns:
            True if the monitor is successfully configured.
        """
        pass

    @abstractmethod
    def getLiveVariablesInfo(self, requestedVariables):
        """ Returns all the available information (and meta-information) for all of the requestedVariables.

        Args:
           requestedVariables ([str]): identifiers of the variables to be queried.
        Returns:
            A list of Variables ([Variable]) with all the information available for each of the request variables 
        """
        pass


    def loadCommon(self, config):
        """ Loads parameters that are common to all monitor implementations.
            NOOP as of today.
            
        Args:
            config (ConfigParser): parameters that are common to all authenticate implementations:
            NONE as of today.
        Returns:
            True 
        """
        return True

    def setServer(self, server):
        """ Sets the server implementation.
        
        Args:
            server (Server): the server implementation.
        """
        self.server = server

    def update(self, variables):
        """ To be called any time any of the variable monitored by this implementation has changed. 
        
        Args:
            variables ({variableName1:value1, variableName2:value2, ...}):  dictionary with the variables that have been updated.
        Returns:
            None
        """
        toStream = {
            "live": True,
            "variables": variables
        }
        log.debug("Streaming {0}".format(toStream))
        self.server.queueStreamData(json.dumps(toStream))


