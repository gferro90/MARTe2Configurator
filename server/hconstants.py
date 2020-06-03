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
__date__ = "17/11/2017"

##
# Standard imports
##
import json
import logging

##
# Project imports
##
from page import Page
from user import User
from usergroup import UserGroup

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class HieratikaConstants:
    """ List of Hieratika constant values that are used to exchange information between the client and the server.
    """
    # Invalid list of parameters was used when calling one of the Hieratika functions.
    INVALID_PARAMETERS = "InvalidParameters"

    # Invalid security token was used.
    INVALID_TOKEN = "InvalidToken"

    # Unknown error
    UNKNOWN_ERROR = "UnknownError"

    # OK
    OK = "ok"
    
    # An object is in use and cannot be changed/removed
    IN_USE = "InUse"

    # An object cannot be found
    NOT_FOUND = "NotFound" 
 
