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
import logging

##
# Project imports
##
from loader import HieratikaLoader

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class NOOPLoader(HieratikaLoader):
    """ An empty Loader implementation which just logs the loader requests. To be used in demos and tests.
    """
    
    def __init__(self):
        super(HieratikaLoader, self).__init__()
        
    def load(self, config):
        return True

    def loadIntoPlant(self, pageName):
        log.info("Loading {0}".format(pageName)) 
        return True

    def isLoadable(self, pageName):
        return True

