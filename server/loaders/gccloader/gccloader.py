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
__date__ = "22/02/2018"

##
# Standard imports
##
import bitstring
import ConfigParser
import epics
import json
import logging
import time

##
# Project imports
##
from hieratika.loader import HieratikaLoader

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class GCCLoader(HieratikaLoader):
    """ A loader for the GCC Demo.
    """
    
    def __init__(self):
        super(HieratikaLoader, self).__init__()
        self.variableMap = {}
        self.variables = []
        self.pvLoadDigestName = ""
        self.pvLoadCounter = ""
        self.pvLoadCommand = ""
        self.pageName = "GCC"

    def load(self, config):
        """ Loads the mapping between the hieratika variables and the EPICS records, defined in a json file whose path shall be defined in
        [loader-impl] recordVariableMappingJsonPath 
        """
        ok = False
        try:
            jsonFileName = config.get("loader-impl", "pvVariableMappingJsonPath")
            with open(jsonFileName) as jsonFile:
                self.variableMap = json.load(jsonFile)
            self.pvLoadDigestName = config.get("loader-impl", "pvLoadDigestName")
            self.pvLoadCounter = config.get("loader-impl", "pvLoadCounter")
            self.pvLoadCommand = config.get("loader-impl", "pvLoadCommand")

            for pv in self.variableMap:
                self.variables.append(pv)

            log.info("Going to be capable of loading the following variables: {0}".format(self.variables))

            ok = True
        except (ConfigParser.Error, KeyError, IOError) as e:
            log.critical(str(e))
            ok = False
        return ok

        return True

    def loadIntoPlant(self, pageName):
        log.info("Loading {0}".format(pageName)) 

        variablesPlantInfo = self.server.getVariablesInfo(self.pageName, self.variables)
        counterValue = epics.caget(self.pvLoadCounter)
        log.info("Counter value {0}:{1}".format(self.pvLoadCounter, counterValue))
        digest = int(counterValue)

        for var in variablesPlantInfo:
            varname = var.getName()
            if varname in self.variableMap:
                pvname = self.variableMap[varname][0]
                isLock = (self.variableMap[varname][1] == 1)
                value = var.getValue()
                if type(value) is list:
                    value = value[0]
                if (isLock):
                    value = abs(int(value))
                epics.caput(pvname, value)
                log.info("Updated {0} ({1}:{2})".format(var.getName(), pvname, value))

                if (var.getType() == "float32"):
                    value = float(value)
                    value = bitstring.BitArray(float=value, length=32)
                    value = value.int
                    log.info("Float value to be updated {0}:{1}".format(var.getName(), value))
                else:
                    value = int(value)
                digest = digest ^ value
            else:
                log.critical("{0} not found in the variable map!".format(var)) 

        time.sleep(1)            
        log.info("Setting digest: {0}".format(digest))
        epics.caput(self.pvLoadDigestName, digest)
        time.sleep(1)            
        log.info("Setting load command: {0}".format(digest))
        epics.caput(self.pvLoadCommand, 1)
        return True

    def isLoadable(self, pageName):
        return pageName == "GCC"

