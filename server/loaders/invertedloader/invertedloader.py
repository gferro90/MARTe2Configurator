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
import os
from loader import HieratikaLoader
import ctypes
from ctypes import cdll
##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class InvertedLoader(HieratikaLoader):
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
            self.basedir=config.get("server-impl", "baseDir")
            ok = True
        except (ConfigParser.Error, KeyError, IOError) as e:
            log.critical(str(e))
            ok = False
        return ok

        return True

    def loadIntoPlant(self, projectPath, fileName):
        self.projectPath = projectPath
        filePath=self.basedir+"/cfg/"+fileName
        self.lib = cdll.LoadLibrary(self.basedir+'/Lib/Build/libCdbWrapper.so')
        self.cdbWrapper1=self.lib.Create()
        self.cdbWrapper2=self.lib.Create2()

        self.lib.Open(self.cdbWrapper1, self.cdbWrapper2, ctypes.c_char_p(filePath))
        self.lib.MoveToRoot(self.cdbWrapper1, self.cdbWrapper2)

        rootComps=[]
        numberOfChildren = self.lib.GetNumberOfChildren(self.cdbWrapper1, self.cdbWrapper2)        
        log_buffer = ctypes.create_string_buffer(1024)
        for i in range(0, numberOfChildren):
            self.lib.GetChildName(self.cdbWrapper1, self.cdbWrapper2, i, log_buffer)
            nodeName = log_buffer.value
            if(nodeName[0]=='+' or nodeName[0]=='$'):
                nodeName = nodeName[1:]
                rootComps.append(nodeName)
        xmlFilePath=self.projectPath+"/plant.xml"
        self.server.updateSingleVal(xmlFilePath, "DT@ROOT@INCL", rootComps)
        return self.importFromCfg()

    def unpackRepeat(self, xmlFilePath, valueSource, myFormat, repeatIndexSource, moveChildOk):
        ret = True
        if (isinstance(valueSource,list)):
            for i in range(0,len(valueSource)):
                repeatIndexSource.append(i)
                print("pushed")
                print(repeatIndexSource)
                self.populateXml(xmlFilePath, repeatIndexSource, moveChildOk, myFormat)
                repeatIndexSource.pop()
                print("popped")
                print(repeatIndexSource)
        else:
            self.populateXml(xmlFilePath, repeatIndexSource, moveChildOk, myFormat)
        return ret

    def unpackVar(self, xmlFilePath, name, valueSource, valueDest, dimensionsDest):
        ret = True
        originValue=valueDest
        print(valueSource)
        lenDim=len(dimensionsDest)
        valueDestT=valueDest
        destLen=0
        for k in range(0, lenDim):
            if (not isinstance(valueDest,list)):
                if (k>0):
                    valueDestT[dimensionsDest[k-1]]=[]
                    valueDest=valueDestT[dimensionsDest[k-1]]
            destLen=len(valueDest)
            print(destLen, dimensionsDest[k])
            for n in range(destLen, dimensionsDest[k]+1):
                valueDest.append("")
            valueDestT=valueDest
            valueDest=valueDest[dimensionsDest[k]]
            print(valueDest)

        if (isinstance(valueSource, list)):
            if(len(valueSource)>0):
                valueDestT[dimensionsDest[lenDim-1]]=valueSource[0]
        else:
            valueDestT[dimensionsDest[lenDim-1]]=valueSource

        #clean the variable
        valueDest=originValue
        for k in range(0, lenDim):
	        destLen=len(valueDest)
	        if (destLen == 1):	            
	            if (len(valueDest[0]) == 0):
	                valueDest.pop(0)
	                break
	        valueDest=valueDest[dimensionsDest[k]]

        print(originValue)
        self.server.updateSingleVal(xmlFilePath+".xml", name, originValue)
        return ret

    def populateXml(self, xmlFilePath, repeatIndexSource, moveChildOk, formatName="invertedformat"):
        cfgFormat = self.server.getCfgFormat(xmlFilePath, formatName)
        print(cfgFormat)
        readVar = 0
        readDim = 0
        readFormat = 0
        readDest = 0
        config = ""
        dimSource = ""
        dimDest = ""
        varSource = ""
        varDest = ""
        dimensionsSource = [];
        dimensionsDest = [];
        repeat = False
        ancestor = False
        child = False
        condition = False
        skip = False
        force = False
        ret = True
        writeIfEmpty = True                
        myFormat = ""
        log_buffer = ctypes.create_string_buffer(1024)
        for i in range(0, len(cfgFormat)):
            if (not ret):
                print("ret is false!!!")
                break
            if (skip):
                if(cfgFormat[i] == '?'):
                    skip = False		
                else:
                    pass
            elif ((cfgFormat[i] == '|') and (readVar==0)):
                if (cfgFormat[i+1]=='#'):
                    repeat = True
                elif (cfgFormat[i+1]=='^'):
                    ancestor = True
                elif (cfgFormat[i+1]=='-'):
                    child = True
                elif (cfgFormat[i+1]=='?'):
                    condition = True                    
                elif (cfgFormat[i+1]=='*'):
                    force = True       
                dimensionsSource = [];
                dimensionsDest = [];
                readVar = 1
            elif ((cfgFormat[i] == '|') and (readVar==1)):
                if(child):
                    varSourceT = varSource
                    okok = True
                    childCnt = 0
                    if((varSource == 'childname') or (varSource == 'leafname')):
                        varSourceT = ""
                        #this case take the proper one
                        if (len(dimensionsSource)>0):
                            for k in range(0, len(dimensionsSource)):
                                #loop on the children
                                numberOfChildren=self.lib.GetNumberOfChildren(self.cdbWrapper1, self.cdbWrapper2)
                                nodeCnt = -1
                                for h in range(0, numberOfChildren):
                                    ctypes.memset(log_buffer, 0, 1024)
                                    self.lib.GetChildName(self.cdbWrapper1, self.cdbWrapper2, h, log_buffer)
                                    nodename=log_buffer.value
                                    if (varSource == 'childname'):
                                        if (nodename[0] == '+'):
                                            nodeCnt = nodeCnt+1
                                    else:
                                        nodeCnt = nodeCnt+1
                                    if (nodeCnt == dimensionsSource[k]):
                                        if (len(varSourceT)>0):
                                            varSourceT=varSourceT+"."
                                        varSourceT=varSourceT+nodename
                                        if (self.lib.MoveToChild(self.cdbWrapper1, self.cdbWrapper2, h)):
                                            childCnt=childCnt+1
                                        else:
                                            okok=False
                                        break
                                if (not okok):
                                    break   

                            if(childCnt>0):    
                                self.lib.MoveToAncestor(self.cdbWrapper1, self.cdbWrapper2, childCnt)        
                    if(childCnt>0):
                        for n in range(0, childCnt-1):
                            moveChildOk.append(True)

                    okok = self.lib.MoveRelative(self.cdbWrapper1, self.cdbWrapper2, varSourceT)
                    moveChildOk.append(okok)
                    print("Move to "+varSourceT+" = "+str(okok))
                elif(ancestor):
                    moveOk=moveChildOk.pop()
                    print("pop")
                    if (moveOk):
                        ret = self.lib.MoveToAncestor(self.cdbWrapper1, self.cdbWrapper2, 1)
                else:
					#not child nor ancestor: this is a variable
                    varValueSource = []
                    #if childname loop on the number of children
                    if(force):
                    	varValueSource.append(varSource)
                    else:
                        if((varSource == 'childname') or (varSource == 'leafname') or (varSource == 'fullleaf')):
                            #this case take the proper one
                            if (len(dimensionsSource)>0):
                                childCnt = 0
                                #dimensionsSource is the tree identifier
                                for k in range(0, len(dimensionsSource)):
                                    #loop on the children
                                    numberOfChildren=self.lib.GetNumberOfChildren(self.cdbWrapper1, self.cdbWrapper2)
                                    nodeCnt = -1
                                    nodename=""
                                    found=False 
                                    for h in range(0, numberOfChildren):
                                        ctypes.memset(log_buffer, 0, 1024)
                                        self.lib.GetChildName(self.cdbWrapper1, self.cdbWrapper2, h, log_buffer)
                                        if(varSource == 'fullleaf'):
                                            nodename=log_buffer.value
                                            if (nodename=='Class'):
                                                nodename=""
                                            else:
                                                ctypes.memset(log_buffer, 0, 1024)
                                                self.lib.ReadAndConvert(self.cdbWrapper1, self.cdbWrapper2, nodename, 0, log_buffer)
                                                nodename=nodename+" = "
                                                nodename=nodename+log_buffer.value
                                        else: 
                                             nodename=log_buffer.value
                                        if(varSource == 'childname'):
                                            if (nodename[0] == '+'):
                                                nodeCnt = nodeCnt+1
                                        else:
                                            nodeCnt = nodeCnt+1
                                        #found the node at that index! Go deep    
                                        if (nodeCnt == dimensionsSource[k]):
                                            if (k<len(dimensionsSource)-1):
                                                if (self.lib.MoveToChild(self.cdbWrapper1, self.cdbWrapper2, h)):
                                                    childCnt=childCnt+1
                                                    found=True
                                            else:
                                            	found=True
                                            break
                                    if (not found):
                                        print("Error at "+log_buffer.value)
                                        nodename = ""
                                        break   
                                if(len(nodename) > 0):
                                    if(varSource == 'childname'):
                                        varValueSource.append(nodename[1:])
                                    else:
                                        varValueSource.append(nodename)
                                else:
                                	varValueSource.append("")
                                if(childCnt>0):    
                                    self.lib.MoveToAncestor(self.cdbWrapper1, self.cdbWrapper2, childCnt)        
                            else:
                                #no tree selection, just append all the children
                                numberOfChildren=self.lib.GetNumberOfChildren(self.cdbWrapper1, self.cdbWrapper2)
                                for k in range(0, numberOfChildren):
                                    ctypes.memset(log_buffer, 0, 1024)
                                    if (self.lib.GetChildName(self.cdbWrapper1, self.cdbWrapper2, k, log_buffer)):
                                        nodename=log_buffer.value
                                        print(nodename)
                                        if(varSource == 'fullleaf'):
                                            nodename=log_buffer.value
                                            ctypes.memset(log_buffer, 0, 1024)
                                            self.lib.ReadAndConvert(self.cdbWrapper1, self.cdbWrapper2, nodename, 0, log_buffer)
                                            nodename=nodename+" = "
                                            nodename=nodename+log_buffer.value
                                        elif (varSource == "childname"):
                                            if(nodename[0] == '+'):
                                                varValueSource.append(nodename[1:])
                                        else:
                                             varValueSource.append(nodename)
                        else:
                            #variable with specified name
                            if (len(dimensionsSource)>0):
                                #scalar element
                                print("scalar "+varSource)
                                ctypes.memset(log_buffer, 0, 1024)
                                self.lib.ReadAndConvert(self.cdbWrapper1, self.cdbWrapper2, varSource, dimensionsSource[0], log_buffer)
                                varValueSource.append(log_buffer.value)
                            else:
                                #loop on the nElements
                                numberOfElements = self.lib.GetVarNelements(self.cdbWrapper1, self.cdbWrapper2, varSource)
                                for k in range(0, numberOfElements):
                                    ctypes.memset(log_buffer, 0, 1024)
                                    self.lib.ReadAndConvert(self.cdbWrapper1, self.cdbWrapper2, varSource, k, log_buffer)
                                    varValueSource.append(log_buffer.value) 
                    if(condition):
                    	if(varValueSource[0] != myFormat):
                    	    print("skipped "+myFormat)
                            skip = True                       
                    elif(repeat):
                        print("repeat")
                        #configure when skip or when to put empty if empty variable
                        writeVar = True
                        if(len(varValueSource)==0):
                            varValueSource = [""]
                            writeVar = writeIfEmpty
                        if(len(moveChildOk)>0):
                            if(not moveChildOk[-1]):
                                varValueSource = [""]
                                writeVar = writeIfEmpty
                        print(varValueSource)
                        #if(writeVar):
                        ret = self.unpackRepeat(xmlFilePath, varValueSource, myFormat, repeatIndexSource, moveChildOk)
                    else:
                        print("var")
                        print(varDest)
                        varValueDest = self.server.getCfgValue(xmlFilePath, varDest)
                        print(varValueSource)
                        print(varValueDest)
                        varValueDest = varValueDest[0]
                        writeVar = True
                        if(len(varValueSource)==0):
                            varValueSource = []
                            writeVar = writeIfEmpty
                        if(len(moveChildOk)>0):
                            if(not moveChildOk[-1]):
                                varValueSource = []
                                writeVar = writeIfEmpty
                        #if (writeVar):
                        self.unpackVar(xmlFilePath, varDest, varValueSource, varValueDest, dimensionsDest) 
                repeat = False
                ancestor = False
                child = False
                force = False
                condition = False
                readVar = 0
                varSource = ""
                varDest = ""
                myFormat = ""
            else:
                if (readVar == 1):
                    if ((cfgFormat[i] == '[') and (readDim == 0)):
                        readDim = 1
                        dimSource = ""
                    elif ((cfgFormat[i] == ']') and (readDim == 1)):
                        if(dimSource[0] == '#'):
                            dimNumber = repeatIndexSource[int(dimSource[1])]
                        else:
                            dimNumber = int(dimSource)
                        if(readDest == 1):
                            dimensionsDest.append(dimNumber)
                        else:
                            dimensionsSource.append(dimNumber)
                        readDim = 0
                    elif ((cfgFormat[i] == '(') and (readFormat == 0)):
                        readFormat = 1
                        myFormat = ""
                    elif ((cfgFormat[i] == ')') and (readFormat == 1)):
                        readFormat = 0

                    elif ((cfgFormat[i] == '{') and (readDest == 0)):
                        readDest = 1
                        varDest = ""
                    elif ((cfgFormat[i] == '}') and (readDest == 1)):
                        readDest = 0

                    elif ((cfgFormat[i]=='-') or (cfgFormat[i]=='^') or (cfgFormat[i]=='?') or (cfgFormat[i]=='*')):
                        pass
                    else:
                        if (readDim == 1):
                            dimSource += cfgFormat[i]
                        else:
                            if (cfgFormat[i] != '#'):
                                if (readFormat == 1):
                                    myFormat += cfgFormat[i]
                                elif (readDest == 1):
                                    varDest += cfgFormat[i]
                                else:
                                    varSource += cfgFormat[i]
                else:
                    if (cfgFormat[i] == 'C'):
                        writeIfEmpty = False
                    elif (cfgFormat[i] == 'W'):
                        writeIfEmpty = True                           
        return ret



    def searchComponentInFiles(self, className, nodeName):
        gamsDir = self.basedir+"/GAMs/"
        newFileName = ""
        suffix=""
        for rootPlantXml, dirnamesPlantXml, filenamesPlantXml in os.walk(gamsDir):
            for cgamdir in dirnamesPlantXml:
                gamDir=gamsDir+cgamdir
                for gamPlantXml, dirgamsPlantXml, filegamsPlantXml in os.walk(gamDir):
                    for f in filegamsPlantXml:
                        index=f.find("_GAM")
                        if(index == -1):
                            index=f.find("_Object")
                            if(index!=-1):
                                suffix="_Object"
                                componentName=f[0:index]
                        else:
                            suffix="_GAM"
                            componentName=f[0:index]
                        if(componentName==className):
                            newFileName=self.projectPath+"/"+nodeName+suffix
                            os.system("cp {0} {1}".format(gamDir+"/"+f, newFileName+".xml"))
        dssDir = self.basedir+"/DataSources/"
        for rootPlantXml, dirnamesPlantXml, filenamesPlantXml in os.walk(dssDir):
            for cdsdir in dirnamesPlantXml:
                dsDir=dssDir+cdsdir
                for dsPlantXml, dirdsPlantXml, filedsPlantXml in os.walk(dsDir):
                    for f in filedsPlantXml:
                        index=f.find("_DataSource")
                        if(index == -1):
                            index=f.find("_Object")
                            if(index!=-1):
                                suffix="_Object"
                                componentName=f[0:index]
                        else:
                            suffix="_DataSource"
                            componentName=f[0:index]
                        if(componentName==className):
                            newFileName=self.projectPath+"/"+nodeName+suffix
                            os.system("cp {0} {1}".format(dsDir+"/"+f, newFileName+".xml"))
        interfacesDir = self.basedir+"/Interfaces/"
        for rootPlantXml, dirnamesPlantXml, filenamesPlantXml in os.walk(interfacesDir):
            for cifacedir in dirnamesPlantXml:
                ifaceDir=interfacesDir+cifacedir
                for ifacePlantXml, dirifacePlantXml, fileifacePlantXml in os.walk(ifaceDir):
                    for f in fileifacePlantXml:
                        index=f.find("_Interface")
                        if(index == -1):
                            index=f.find("_Object")
                            if(index!=-1):
                                componentName=f[0:index]
                                suffix="_Object"
                        else:
                            suffix="_Interface"
                            componentName=f[0:index]
                        if(componentName==className):
                            newFileName=self.projectPath+"/"+nodeName+suffix
                            os.system("cp {0} {1}".format(ifaceDir+"/"+f, newFileName+".xml"))
        if(len(newFileName)>0):
            repeatIndexSource = []
            moveChildOk=[]
            return self.populateXml(newFileName, repeatIndexSource,moveChildOk, "invertedformat")
        else:
            return False

                

    def importFromCfg(self):
        numberOfChildren = self.lib.GetNumberOfChildren(self.cdbWrapper1, self.cdbWrapper2)         
        log_buffer = ctypes.create_string_buffer(1024)
        for i in range(0, numberOfChildren):
            ctypes.memset(log_buffer, 0, 1024)
            self.lib.GetChildName(self.cdbWrapper1, self.cdbWrapper2, i, log_buffer)
            nodeName = log_buffer.value
            if(nodeName[0]=='+' or nodeName[0]=='$'):
                nodeName = nodeName[1:]
                if (self.lib.MoveToChild(self.cdbWrapper1, self.cdbWrapper2, i)):
                    ctypes.memset(log_buffer, 0, 1024)
                    self.lib.ReadAndConvert(self.cdbWrapper1, self.cdbWrapper2, "Class", 0, log_buffer)
                    className = log_buffer.value
                    self.searchComponentInFiles(className, nodeName)
                    self.importFromCfg()
                    self.lib.MoveToAncestor(self.cdbWrapper1, self.cdbWrapper2, 1)
        return "true"                


        
    def isLoadable(self, pageName):
        return True

