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
from loader import HieratikaLoader

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class CFGLoader(HieratikaLoader):
    """ A loader for the GCC Demo.
    """
    
    def __init__(self):
        super(HieratikaLoader, self).__init__()

    def load(self, config):
        """ Loads the mapping between the hieratika variables and the EPICS records, defined in a json file whose path shall be defined in
        [loader-impl] recordVariableMappingJsonPath 
        """
        ok = False
        try:
            log.info("Tutt appost a ferragost")
            ok = True
        except (ConfigParser.Error, KeyError, IOError) as e:
            log.critical(str(e))
            ok = False
        return ok

        return True

    def loadIntoPlant(self, projectPath, fileName):
        self.fileId = open(projectPath+"/CfgFile.cfg", "w+")
        self.stream = ""
        repeatIndex = []
        return self.createCfgRecursive(projectPath, fileName, "format", repeatIndex, 0)

    def unpackNode(self, projectPath, value, myFormat, indentation):
        ret=True
        if (isinstance(value,list)):
            for i in range(0,len(value)):
                ret = self.unpackNode(projectPath, value[i], myFormat, indentation)
        else:
            newFileName = "{0}".format(value)
            inc=0
            if(len(myFormat)>0):
                print(myFormat)
                inc=int(myFormat)
            self.fileId.write("\n")
            self.stream+="\n"
            indentation=indentation+inc
            for i in range(0, indentation):
                self.fileId.write("    ")
                self.stream+="    "
            indentation=indentation+1
            self.fileId.write("+"+(str(value))+" = {")
            self.stream+="+"+(str(value))+" = {"
            ret = self.createCfgRecursive(projectPath, newFileName, "format", [], indentation)
            indentation=indentation-1
            self.fileId.write("\n")
            self.stream+="\n"
            for i in range(0, (indentation)):
                self.fileId.write("    ")
                self.stream+="    "
            self.fileId.write("}\n")
            self.stream+="}\n"
	    indentation=indentation-inc
        return ret

    def unpackVar(self, projectPath, value, indentation):
        ret = True
        if (isinstance(value,list)):
            self.fileId.write("{ ")
            self.stream+="{ "
            for i in range(0,len(value)):
                ret = self.unpackVar(projectPath, value[i], indentation)
                if (i!=(len(value)-1)):
                    self.fileId.write(", ")
                    self.stream+=", "
            self.fileId.write(" }")
            self.stream+=" }"
        else:
            self.fileId.write(str(value))
            self.stream+=str(value)
        return ret

    def unpackRepeat(self, projectPath, xmlFile, value, myFormat, repeatIndex, indentation):
        ret = True
        if (isinstance(value,list)):
            for i in range(0,len(value)):
                repeatIndex.append(i)
                self.createCfgRecursive(projectPath, xmlFile, myFormat, repeatIndex, indentation)
                repeatIndex.pop()
        else:
            self.createCfgRecursive(projectPath, xmlFile, myFormat, repeatIndex, indentation)
        return ret


    def createCfgRecursive(self, projectPath, xmlFile, formatName, repeatIndex, indentation):
        print("considering "+xmlFile+" "+formatName)
        xmlFilePath = "{0}/{1}".format(projectPath, xmlFile)
        cfgFormat = self.server.getCfgFormat(xmlFilePath, formatName)
        readVar = 0
        readDim = 0
        readFormat = 0
        config = ""
        dim = ""
        variable = ""
        dimensions = [];
        node = False
        tree = False
        repeat = False
        condition = False
        skip = False
        ret = True
        myFormat = ""
        print("INDENTATION="+str(indentation))
        for i in range(0, len(cfgFormat)):
            if (not ret):
                break
            if(skip):
                if (cfgFormat[i] == '$'):
                    skip=False
                continue
            if ((cfgFormat[i] == '|') and (readVar==0)):
                if (cfgFormat[i+1]=='+'):
                    node = True
                if (cfgFormat[i+1]=='*'):
                    tree = True
                if (cfgFormat[i+1]=='#'):
                    repeat = True
                if (cfgFormat[i+1]=='$'):
                    condition = True
                dimensions = [];
                readVar = 1
            elif ((cfgFormat[i] == '|') and (readVar==1)):
                self.fileId.write(config)
                self.stream+=config
                config = ""
                varValue = self.server.getCfgValue(xmlFilePath, variable)
                varValue=varValue[0]
                for k in range(0, len(dimensions)):
                    varValue=varValue[dimensions[k]]
                if (not isinstance(varValue, list)):
                    if (type(varValue) is not str):
                        varValue=str(varValue)
                if(condition):
                    if (len(myFormat)>0):
                        skip=(varValue!=myFormat)
                    else:
                        skip=(len(varValue)==0)
                    print(varValue, len(varValue), skip)
                elif(node):
                    ret = self.unpackNode(projectPath, varValue, myFormat, indentation)
                elif(repeat):
                    ret = self.unpackRepeat(projectPath, xmlFile, varValue, myFormat, repeatIndex, indentation)
                else:
                    self.unpackVar(projectPath, varValue, indentation) 
                node = False
                tree = False
                repeat = False
                condition = False
                readVar = 0
                child = 0
                variable = ""
                myFormat = ""
            else:
                if (readVar == 0):
                    if(cfgFormat[i] != '$'):
                        config += cfgFormat[i]
                    if(cfgFormat[i]=='\n'):
                        for i in range(0, indentation):
                            config+="    "
                else:
                    if ((cfgFormat[i] == '[') and (readDim == 0)):
                        readDim = 1
                        dim = ""
                    elif ((cfgFormat[i] == ']') and (readDim == 1)):
                        if(dim[0] == '#'):
                            dimNumber = repeatIndex[int(dim[1])]
                        else:
                            dimNumber = int(dim)
                        dimensions.append(dimNumber)
                        readDim = 0
                    elif ((cfgFormat[i] == '(') and (readFormat == 0)):
                        readFormat = 1
                        myFormat = ""
                    elif ((cfgFormat[i] == ')') and (readFormat == 1)):
                        readFormat = 0
                    elif ((cfgFormat[i]=='+') or (cfgFormat[i]=='*') or (cfgFormat[i]=='$')):
                        pass
                    else:
                        if (readDim == 1):
                            dim += cfgFormat[i]
                        else:
                            if (cfgFormat[i] != '#'):
                                if (readFormat == 1):
                                    myFormat += cfgFormat[i]
                                elif (readDim == 0):
                                    variable += cfgFormat[i]
        self.fileId.write(config)
        self.stream+=config
        self.fileId.flush()
        print("returning "+xmlFile+" "+formatName)
        if (ret):
            return self.stream
        else:
            return "False"
        
    def isLoadable(self, pageName):
        return True

