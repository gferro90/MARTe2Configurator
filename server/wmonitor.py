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
from flask import Response
import json
import logging
import time
import threading

##
# Project imports
##
from monitor import HieratikaMonitor

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class WMonitor(object):
    """ Provides an interface point between the specific monitor implementations (see HieratikaMonitor)
        and the webserver. In particular this class parses and transforms the web form parameters into 
        the list of the parameters that are expected by the HieratikaMonitor implementation.
        Currently this interface is very thin and is up to the HieratikaMonitor implementations to 
        decide what variables will be monitored and to trigger upon change.
    """

    def __init__(self):
        """ NOOP
        """
        self.monitorImpls = []

    def getLiveVariablesInfo(self, request):
        """ Returns the all the available information (and meta-information) for all of the live requestedVariables.

        Args:
           request.form["variables"]: identifiers of the variables to be queried.
        Returns:
            A json encoded list of variables or InvalidToken if the token is not valid.
            The following information is retrieved for any given variable:
            - name: the full variable name (containing any structure naming information, encoded as with a structure separator);
            - alias: a free format text which provides a meaningful name to the variable.
            - type as one of: uint8, int8, uint16, int16, uint32, int32, uint64, int64, string, enum, library;
            - numberOfElements: as an array where each entry contains the number of elements on any given direction; 
            - description: one-line description of the variable;
            - permissions: user groups that are allowed to change this variable;
            - value: string encoded variable value.
            - and N member variables (with the information above) if the variable being returned is structured.
        """
       
        toReturn = ""
        try: 
            requestedVariables = json.loads(request.form["variables"])
            toReturnVariables = []
            for monitorImpl in self.monitorImpls:
                monitorImplVariables = monitorImpl.getLiveVariablesInfo(requestedVariables)
                toReturnVariables = toReturnVariables + monitorImplVariables
            variablesStr = [v.asSerializableDict() for v in toReturnVariables]
            toReturn = json.dumps(variablesStr)
        except KeyError as e:
            log.critical(str(e))
            toReturn = "InvalidParameters"

        return toReturn 

    def setMonitors(self, monitorImpls):
        """ Sets the HieratikaMonitor implementations to be used.
        
        Args:
            monitorImpls ([HieratikaMonitor]): the list of HieratikaMonitor implementations to be used.
        """
        self.monitorImpls = monitorImpls 

