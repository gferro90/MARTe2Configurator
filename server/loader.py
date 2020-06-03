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
__date__ = "21/12/2017"

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
class HieratikaLoader(object):
    """ Abstract class for any loader implementation.
        TODO
    """
    
    __metaclass__ = ABCMeta

    def __init__(self):
        pass
        
    @abstractmethod
    def load(self, config):
        """ Configures the loader against a set of parameters. This set of parameters is specific for each loader implementation.
        
        Args:
            config(ConfigParser): the loader specific implementation parameters are in the section "loader-impl".
        Returns:
            True if the loader is successfully configured.
        """
        pass

    def loadCommon(self, config):
        """ Loads parameters that are common to all loader implementations.
            NOOP as of today.
            
        Args:
            config (ConfigParser): parameters that are common to all authenticate implementations:
            NONE as of today.
        Returns:
            True 
        """
        return True

    @abstractmethod
    def loadIntoPlant(self, pageName):
        """ Loads the configuration model idenfied by the page.
        
        Args:
            pageName (str): unique identifier of the configuration to be loaded.
        Returns:
            True if the configuration is successfully loaded.
        """
        pass

    @abstractmethod
    def isLoadable(self, pageName):
        """ Returns True if the configuration identified by the page name can be loaded by this loader.
        
        Args:
            pageName (str): unique identifier of the configuration to be loaded.
        Returns:
            True if the configuration can be loaded by this loader.
        """
        pass

    def setServer(self, server):
        """ Sets the server implementation.
        
        Args:
            server (Server): the server implementation.
        """
        self.server = server

