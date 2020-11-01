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


#from gevent import monkey
#monkey.patch_all(thread=False, socket=False)
#import socket
#socket.setdefaulttimeout(None)

##
# Standard imports
##
import argparse
import ast
import ConfigParser
import importlib
import json
import logging
import multiprocessing
import os
import timeit
from flask import Flask, Response, request, send_from_directory

##
# Project imports
##
from hconstants import HieratikaConstants
from wloader import WLoader
from wmonitor import WMonitor
from wserver import WServer
from wstatistics import WStatistics


##
# Logger configuration
##
#TODO change to fileConfig (see https://docs.python.org/2/howto/logging.html). This can be input to gunicorn using --log-config (TBC)
logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] [%(levelname)s] [%(process)d] [%(thread)d] [%(filename)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##

# The Flask application
application = Flask(__name__, static_url_path="")

# The WServer implementation
wserver = WServer()

# The WLoader implementation
wloader = WLoader()
winverseloader = WLoader()

# The WMonitor implementation
wmonitor = WMonitor()

# The WStatistics implementation
wstatistics = WStatistics()


def load(config):
    try:
        serverModuleName = config.get("hieratika", "serverModule")
        log.info("Server module is {0}".format(serverModuleName))
        serverModule = importlib.import_module(serverModuleName)

        serverClassName = config.get("hieratika", "serverClass")
        log.info("Server class is {0}".format(serverClassName))
        serverClass = getattr(serverModule, serverClassName)

        authModuleName = config.get("hieratika", "authModule")
        log.info("Auth module is {0}".format(authModuleName))
        authModule = importlib.import_module(authModuleName)

        authClassName = config.get("hieratika", "authClass")
        log.info("Auth class is {0}".format(authClassName))
        authClass = getattr(authModule, authClassName)

        transformationModuleNames = []
        transformationClassNames = []
        if (config.has_option("hieratika", "transformationModules")):
            transformationModuleNames = config.get("hieratika", "transformationModules")
            log.info("Transformation modules are {0}".format(transformationModuleNames))
            transformationModuleNames = ast.literal_eval(transformationModuleNames)

            transformationClassNames = config.get("hieratika", "transformationClasses")
            log.info("Transformation classes are {0}".format(transformationClassNames))
            transformationClassNames = ast.literal_eval(transformationClassNames)

        loaderModuleNames = []
        loaderClassNames = []
        if (config.has_option("hieratika", "loaderModules")):
            loaderModuleNames = config.get("hieratika", "loaderModules")
            log.info("Loader modules are {0}".format(loaderModuleNames))
            loaderModuleNames = ast.literal_eval(loaderModuleNames)

            loaderClassNames = config.get("hieratika", "loaderClasses")
            log.info("Loader classes are {0}".format(loaderClassNames))
            loaderClassNames = ast.literal_eval(loaderClassNames)

        monitorModuleNames = []
        monitorClassNames = []
        if (config.has_option("hieratika", "monitorModules")):
            monitorModuleNames = config.get("hieratika", "monitorModules")
            log.info("Monitor modules are {0}".format(monitorModuleNames))
            monitorModuleNames = ast.literal_eval(monitorModuleNames)

            monitorClassNames = config.get("hieratika", "monitorClasses")
            log.info("Monitor classes are {0}".format(monitorClassNames))
            monitorClassNames = ast.literal_eval(monitorClassNames)


        pagesFolder = config.get("hieratika", "pagesFolder")
        #Translate into absolute path so that it can be used by other modules (which belong to other directories) as well.
        pagesFolder = os.path.abspath(pagesFolder)
        config.set("hieratika", "pagesFolder", pagesFolder)
        application.static_folder = config.get("hieratika", "staticFolder")
        application.debug = True
        application.logger.setLevel(logging.DEBUG)
        server = serverClass()
        auth = authClass()

        log.info("Loading server common configuration")
        ok = server.loadCommon(config)
        if (ok):
            log.info("Loading server configuration")
            ok = server.load(config)
        else:
            log.critical("Failed to load common server configuration")

        if (ok):
            log.info("Loading auth configuration")
            ok = auth.loadCommon(config)
        else:
            log.critical("Failed to load server configuration")
        if (ok):
            ok = auth.load(config)
        if (ok):
            auth.addLogListener(server)
            ok = auth.start()
        else:
            log.critical("Failed to load auth configuration")

        if (ok):
            ok = wstatistics.load(config)
            if (not ok):
                log.critical("Failed to load wstatistics")


        loaders = []
        if (ok):
            for loaderModuleName, loaderClassName in zip(loaderModuleNames, loaderClassNames):
                loaderModule = importlib.import_module(loaderModuleName) 
                loaderClass = getattr(loaderModule, loaderClassName)
                loaderInstance = loaderClass()
                loaders.append(loaderInstance)
                log.info("Loading loader {0}.{1} common configuration".format(loaderModuleName, loaderClassName))
                ok = loaderInstance.loadCommon(config)
                if (ok):
                    log.info("Loading loader {0}.{1} configuration".format(loaderModuleName, loaderClassName))
                    ok = loaderInstance.load(config)
                else:
                    log.info("Failed Loading loader {0}.{1} common configuration".format(loaderModuleName, loaderClassName))

                if (ok):
                    loaderInstance.setServer(server)
                else:
                    log.info("Failed Loading loader {0}.{1} configuration".format(loaderModuleName, loaderClassName))
                    break

        if (ok):
            baseDir = config.get("server-impl", "baseDir")
            wloader.setLoaders(loaders, baseDir)
            inverseLoaderModuleName = config.get("hieratika", "inverseLoaderModule")
            inverseLoaderClassName = config.get("hieratika", "inverseLoaderClass")
            inverseLoaderModuleName = ast.literal_eval(inverseLoaderModuleName)
            inverseLoaderClassName = ast.literal_eval(inverseLoaderClassName)

            log.info("Inverted Loader modules are {0}".format(inverseLoaderModuleName))
            log.info("Inverted Loader classes are {0}".format(inverseLoaderClassName))
            inverseLoaderModule = importlib.import_module(inverseLoaderModuleName)
            inverseLoaderClass = getattr(inverseLoaderModule, inverseLoaderClassName)
            inverseLoaderInstance = inverseLoaderClass()
            ok=inverseLoaderInstance.load(config)
            if(ok):
                inverseLoaderInstance.setServer(server)
                winverseloader.setLoaders([inverseLoaderInstance], baseDir)
            else:
                log.info("Failed Loading inverse loader {0}.{1} common configuration".format(inverseLoaderModuleName, inverseLoaderClassName))

        monitors = []
        if (ok):
            for monitorModuleName, monitorClassName in zip(monitorModuleNames, monitorClassNames):
                monitorModule = importlib.import_module(monitorModuleName) 
                monitorClass = getattr(monitorModule, monitorClassName)
                monitorInstance = monitorClass()
                monitors.append(monitorInstance)
                log.info("Loading monitor {0}.{1} common configuration".format(monitorModuleName, monitorClassName))
                ok = monitorInstance.loadCommon(config)
                if (ok):
                    log.info("Loading monitor {0}.{1} configuration".format(monitorModuleName, monitorClassName))
                    ok = monitorInstance.load(config)
                else:
                    log.info("Failed Loading monitor {0}.{1} common configuration".format(monitorModuleName, monitorClassName))

                if (ok):
                    monitorInstance.setServer(server)
                else:
                    log.info("Failed Loading monitor {0}.{1} configuration".format(monitorModuleName, monitorClassName))
                    break

        if (ok):
            wmonitor.setMonitors(monitors)            

        if (ok):
            #The web app which is a Flask standard application
            wserver.setServer(server)
            wserver.setAuth(auth)
            wserver.setPagesFolder(pagesFolder)
            #monkey.patch_socket()
            return application
        else:
            log.critical("Failed to load either the server or the auth service") 
    except (KeyError, ValueError, ConfigParser.Error) as e:
        #Trap both IOError 
        log.critical("Failed to load configuration: {0}".format(e))
        exit()

def start(*args, **kwargs):
    configFilePath = kwargs["config"]
    try:
        with open(configFilePath, "r") as configFile:
            config = ConfigParser.ConfigParser()
            config.readfp(configFile)
            return load(config)
    except (IOError, ConfigParser.Error) as e:
        #Trap both IOError 
        log.critical("Failed to load configuration file {0} : {1}".format(configFile, e))
        exit()

#Gets all the variables information for a given configuration
@application.route("/getvariablesinfo", methods=["POST", "GET"])
def getvariablesinfo():
    log.debug("/getvariablesinfo")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getvariablesinfo")
        wstatistics.startUpdate("getvariablesinfo")
        ret = wserver.getVariablesInfo(request)
        wstatistics.endUpdate("getvariablesinfo")
        log.debug("/OUT getvariablesinfo")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Gets information about a set of live variables
@application.route("/getlivevariablesinfo", methods=["POST", "GET"])
def getlivevariablesinfo():
    log.debug("/getlivevariablesinfo")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getlivevariablesinfo")
        wstatistics.startUpdate("getlivevariablesinfo")
        ret = wmonitor.getLiveVariablesInfo(request)
        wstatistics.endUpdate("getlivevariablesinfo")
        log.debug("/OUT getlivevariablesinfo")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

  
#Gets all the variables information for a given library
@application.route("/getlibraryvariablesinfo", methods=["POST", "GET"])
def getlibraryvariablesinfo():
    log.debug("/getlibraryvariablesinfo")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getlibraryvariablesinfo")
        wstatistics.startUpdate("getlibraryvariablesinfo")
        ret = wserver.getLibraryVariablesInfo(request)
        wstatistics.endUpdate("getlibraryvariablesinfo")
        log.debug("/OUT getlibraryvariablesinfo")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Gets all the available transformations
@application.route("/gettransformationsinfo", methods=["POST", "GET"])
def gettransformationsinfo():
    log.debug("/gettransformationsinfo")
    if (wserver.isTokenValid(request)):
        log.debug("/IN gettransformationsinfo")
        wstatistics.startUpdate("gettransformationsinfo")
        ret = wserver.getTransformationsInfo(request)
        wstatistics.endUpdate("gettransformationsinfo")
        log.debug("/OUT gettransformationsinfo")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Try to update the values in the plant
@application.route("/updateplant", methods=["POST", "GET"])
def updateplant():
    log.debug("/updateplant")
    if (wserver.isTokenValid(request)):
        log.debug("/IN updateplant")
        wstatistics.startUpdate("updateplant")
        ret = wserver.updatePlant(request)
        wstatistics.endUpdate("updateplant")
        log.debug("/OUT updateplant")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Try to update the values in the plant against the values stored in a schedule
@application.route("/updateplantfromschedule", methods=["POST", "GET"])
def updateplantfromschedule():
    log.debug("/updateplantfromschedule")
    if (wserver.isTokenValid(request)):
        log.debug("/IN updateplantfromschedule")
        wstatistics.startUpdate("updateplantfromschedule")
        ret = wserver.updatePlantFromSchedule(request)
        wstatistics.endUpdate("updateplantfromschedule")
        log.debug("/OUT updateplantfromschedule")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Try to load the values into the plant
@application.route("/loadintoplant", methods=["POST", "GET"])
def loadintoplant():
    log.debug("/loadintoplant")
    if (wserver.isTokenValid(request)):
        log.debug("/IN loadintoplant")
        wstatistics.startUpdate("loadintoplant")
        ret = wloader.loadIntoPlant(request)
        wstatistics.endUpdate("loadintoplant")
        log.debug("/OUT loadintoplant")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Try to load the values into the plant
@application.route("/loadfromcfg", methods=["POST", "GET"])
def loadfromcfg():
    log.debug("/loadfromcfg")
    if (wserver.isTokenValid(request)):
        log.debug("/IN loadfromcfg")
        wstatistics.startUpdate("loadfromcfg")
        ret = winverseloader.loadIntoPlant(request)
        wstatistics.endUpdate("loadfromcfg")
        log.debug("/OUT loadfromcfg")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN



#Return the available libraries (for a given user and a given library type)
@application.route("/getlibraries", methods=["POST", "GET"])
def getlibraries():
    log.debug("/getlibraries")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getlibraries")
        wstatistics.startUpdate("getlibraries")
        ret = wserver.getLibraries(request) 
        wstatistics.endUpdate("getlibraries")
        log.debug("/OUT getlibraries")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Saves/creates a library with new values
@application.route("/savelibrary", methods=["POST", "GET"])
def savelibrary():
    log.debug("/savelibrary")
    if (wserver.isTokenValid(request)):
        log.debug("/IN savelibrary")
        ret = wserver.saveLibrary(request) 
        log.debug("/OUT savelibrary")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Deletes an existent library 
@application.route("/deletelibrary", methods=["POST", "GET"])
def deletelibrary():
    log.debug("/deletelibrary")
    if (wserver.isTokenValid(request)):
        log.debug("/IN deletelibrary")
        wstatistics.startUpdate("deletelibrary")
        ret = wserver.deleteLibrary(request)
        wstatistics.endUpdate("deletelibrary")
        log.debug("/OUT deletelibrary")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Obsoletes an existent library
@application.route("/obsoletelibrary", methods=["POST", "GET"])
def obsoletelibrary():
    log.debug("/obsoletelibrary")
    if (wserver.isTokenValid(request)):
        log.debug("/IN obsoletelibrary")
        wstatistics.startUpdate("obsoletelibrary")
        ret = wserver.obsoleteLibrary(request)
        wstatistics.endUpdate("obsoletelibrary")
        log.debug("/OUT obsoletelibrary")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN
    
#Return the available schedules
@application.route("/getschedules", methods=["POST", "GET"])
def getschedules():
    log.debug("/getschedules")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getschedules")
        wstatistics.startUpdate("getschedules")
        ret = wserver.getSchedules(request) 
        wstatistics.endUpdate("getschedules")
        log.debug("/OUT getschedules")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Return the available schedule folders
@application.route("/getschedulefolders", methods=["POST", "GET"])
def getschedulefolders():
    log.debug("/getschedulefolders")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getschedulefolders")
        wstatistics.startUpdate("getschedulefolders")
        ret = wserver.getScheduleFolders(request) 
        wstatistics.endUpdate("getschedulefolders")
        log.debug("/OUT getschedulefolders")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Return the available users
@application.route("/getusers", methods=["POST", "GET"])
def getusers():
    log.debug("/getusers")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getusers")
        wstatistics.startUpdate("getusers")
        ret = wserver.getUsers(request) 
        wstatistics.endUpdate("getusers")
        log.debug("/OUT getusers")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Returns the information about a given user
@application.route("/getuser", methods=["POST", "GET"])
def getuser():
    log.debug("/getuser")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getuser")
        wstatistics.startUpdate("getuser")
        ret = wserver.getUser(request) 
        wstatistics.endUpdate("getuser")
        log.debug("/OUT getuser")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Return the available pages
@application.route("/getconfigurations", methods=["POST", "GET"])
def getconfigurations():
    log.debug("/getconfigurations")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getconfigurations")
        wstatistics.startUpdate("getconfigurations")
        ret = wserver.getConfigurations(request) 
        wstatistics.endUpdate("getconfigurations")
        log.debug("/OUT getconfigurations")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Return the available pages
@application.route("/copycomponent", methods=["POST", "GET"])
def copycomponent():
    log.debug("/copycomponent")
    if (wserver.isTokenValid(request)):
        log.debug("/IN copycomponent")
        wstatistics.startUpdate("copycomponent")
        ret = wserver.copyComponent(request) 
        wstatistics.endUpdate("copycomponent")
        log.debug("/OUT copycomponent")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Return the available pages
@application.route("/getconfiguration", methods=["POST", "GET"])
def getconfiguration():
    log.debug("/getconfiguration")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getconfiguration")
        wstatistics.startUpdate("getconfiguration")
        ret = wserver.getConfiguration(request) 
        wstatistics.endUpdate("getconfiguration")
        log.debug("/OUT getconfiguration")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Create a new project
@application.route("/createproject", methods=["POST", "GET"])
def createproject():
    log.debug("/createproject")
    if (wserver.isTokenValid(request)):
        log.debug("/IN createproject")
        wstatistics.startUpdate("createproject")
        ret = wserver.createProject(request) 
        wstatistics.endUpdate("createproject")
        log.debug("/OUT createproject")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Delete a project
@application.route("/deleteproject", methods=["POST", "GET"])
def deleteproject():
    log.debug("/deleteproject")
    if (wserver.isTokenValid(request)):
        log.debug("/IN deleteproject")
        wstatistics.startUpdate("deleteproject")
        ret = wserver.deleteProject(request) 
        wstatistics.endUpdate("deleteproject")
        log.debug("/OUT deleteproject")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#copy a project
@application.route("/copyproject", methods=["POST", "GET"])
def copyproject():
    log.debug("/copyproject")
    if (wserver.isTokenValid(request)):
        log.debug("/IN copyproject")
        wstatistics.startUpdate("copyproject")
        ret = wserver.copyProject(request) 
        wstatistics.endUpdate("copyproject")
        log.debug("/OUT copyproject")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Return the available datasources
@application.route("/getdatasources", methods=["POST", "GET"])
def getdatasources():
    log.debug("/getdatasources")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getdatasources")
        wstatistics.startUpdate("getdatasources")
        ret = wserver.getDatasources(request) 
        wstatistics.endUpdate("getdatasources")
        log.debug("/OUT getdatasources")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Return the available config files
@application.route("/getcfgfiles", methods=["POST", "GET"])
def getcfgfiles():
    log.debug("/getcfgfiles")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getcfgfiles")
        wstatistics.startUpdate("getcfgfiles")
        ret = wserver.getCfgFiles(request) 
        wstatistics.endUpdate("getcfgfiles")
        log.debug("/OUT getcfgfiles")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Return the available gams
@application.route("/getgams", methods=["POST", "GET"])
def getgams():
    log.debug("/getgams")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getgams")
        wstatistics.startUpdate("getgams")
        ret = wserver.getGams(request) 
        wstatistics.endUpdate("getgams")
        log.debug("/OUT getgams")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Return the available interfaces
@application.route("/getinterfaces", methods=["POST", "GET"])
def getinterfaces():
    log.debug("/getinterfaces")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getinterfaces")
        wstatistics.startUpdate("getinterfaces")
        ret = wserver.getInterfaces(request)
        wstatistics.endUpdate("getinterfaces")
        log.debug("/OUT getinterfaces")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Return the available objects in datasource
@application.route("/getdatasourceobjects", methods=["POST", "GET"])
def getdatasourceobjects():
    log.debug("/getdatasourceobjects")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getdatasourceobjects")
        wstatistics.startUpdate("getdatasourceobjects")
        ret = wserver.getDatasourceObjects(request) 
        wstatistics.endUpdate("getdatasourceobjects")
        log.debug("/OUT getdatasourceobjects")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Return the available objects in gam
@application.route("/getgamobjects", methods=["POST", "GET"])
def getgamobjects():
    log.debug("/getgamobjects")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getgamobjects")
        wstatistics.startUpdate("getgamobjects")
        ret = wserver.getGamObjects(request) 
        wstatistics.endUpdate("getgamobjects")
        log.debug("/OUT getgamobjects")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Return the available objects in interface
@application.route("/getinterfaceobjects", methods=["POST", "GET"])
def getinterfaceobjects():
    log.debug("/getinterfaceobjects")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getinterfacebjects")
        wstatistics.startUpdate("getinterfacebjects")
        ret = wserver.getInterfaceObjects(request) 
        wstatistics.endUpdate("getinterfacebjects")
        log.debug("/OUT getinterfaceobjects {0}".format(ret))
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Add a data source
@application.route("/adddatasource", methods=["POST", "GET"])
def adddatasource():
    log.debug("/adddatasource")
    if (wserver.isTokenValid(request)):
        log.debug("/IN adddatasource")
        wstatistics.startUpdate("adddatasource")
        ret = wserver.addDatasource(request) 
        wstatistics.endUpdate("adddatasource")
        log.debug("/OUT adddatasource")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Add a gam
@application.route("/addgam", methods=["POST", "GET"])
def addgam():
    log.debug("/addgam")
    if (wserver.isTokenValid(request)):
        log.debug("/IN addgam")
        wstatistics.startUpdate("addgam")
        ret = wserver.addGam(request) 
        wstatistics.endUpdate("addgam")
        log.debug("/OUT addgam")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Add a interface
@application.route("/addinterface", methods=["POST", "GET"])
def addinterface():
    log.debug("/addinterface")
    if (wserver.isTokenValid(request)):
        log.debug("/IN addinterface")
        wstatistics.startUpdate("addinterface")
        ret = wserver.addInterface(request) 
        wstatistics.endUpdate("addinterface")
        log.debug("/OUT addinterface")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN
        
        
#Returns the class name
@application.route("/getclassname", methods=["POST", "GET"])
def getclassname():
    log.debug("/getclassname")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getclassname")
        wstatistics.startUpdate("getclassname")
        ret = wserver.getClassName(request) 
        wstatistics.endUpdate("getclassname")
        log.debug("/OUT getclassname")
        log.debug("return {0}".format(ret))
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Returns the class name
@application.route("/getcomponentpath", methods=["POST", "GET"])
def getcomponentpath():
    log.debug("/getcomponentpath")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getcomponentpath")
        wstatistics.startUpdate("getcomponentpath")
        ret = wserver.getComponentPath(request) 
        wstatistics.endUpdate("getcomponentpath")
        log.debug("/OUT getcomponentpath")
        log.debug("return {0}".format(ret))
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN
        
#Returns the class name
@application.route("/setcomponentspath", methods=["POST", "GET"])
def setcomponentspath():
    log.debug("/setcomponentspath")
    if (wserver.isTokenValid(request)):
        log.debug("/IN setcomponentspath")
        wstatistics.startUpdate("setcomponentspath")
        ret = wserver.setComponentsPath(request) 
        wstatistics.endUpdate("setcomponentspath")
        log.debug("/OUT setcomponentspath")
        log.debug("return {0}".format(ret))
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN
        
#Returns the description
@application.route("/getdescription", methods=["POST", "GET"])
def getdescription():
    log.debug("/getdescription")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getdescription")
        wstatistics.startUpdate("getdescription")
        ret = wserver.getDescription(request) 
        wstatistics.endUpdate("getdescription")
        log.debug("/OUT getdescription")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Removes a component
@application.route("/removecomponent", methods=["POST", "GET"])
def removecomponent():
    log.debug("/removecomponent")
    if (wserver.isTokenValid(request)):
        log.debug("/IN removecomponent")
        wstatistics.startUpdate("removecomponent")
        ret = wserver.removeComponent(request) 
        wstatistics.endUpdate("removecomponent")
        log.debug("/OUT removecomponent")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN        

        
#Returns the components of a project
@application.route("/getprojectcomponentlist", methods=["POST", "GET"])
def getprojectcomponentlist():
    log.debug("/getpage")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getprojectcomponentlist")
        wstatistics.startUpdate("getprojectcomponentlist")
        ret = wserver.getProjectComponentList(request) 
        wstatistics.endUpdate("getprojectcomponentlist")
        log.debug("/OUT getprojectcomponentlist")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


#Returns the properties of a given page 
@application.route("/getpage", methods=["POST", "GET"])
def getpage():
    log.debug("/getpage")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getpage")
        wstatistics.startUpdate("getpage")
        ret = wserver.getPage(request) 
        wstatistics.endUpdate("getpage")
        log.debug("/OUT getpage")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Returns the properties of a given schedule
@application.route("/getschedule", methods=["POST", "GET"])
def getschedule():
    log.debug("/getschedule")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getschedule")
        wstatistics.startUpdate("getschedule")
        ret = wserver.getSchedule(request)    
        wstatistics.endUpdate("getschedule")
        log.debug("/OUT getschedule")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Returns the variables associated to a given schedule
@application.route("/getschedulevariablesvalues", methods=["POST", "GET"])
def getschedulevariablesValues():
    log.debug("/getschedulevariablesvalues")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getschedulevariablesvalues")
        wstatistics.startUpdate("getschedulevariablesvalues")
        ret = wserver.getScheduleVariablesValues(request)
        wstatistics.endUpdate("getschedulevariablesvalues")
        log.debug("/OUT getschedulevariablesvalues")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Returns the variables associated to a given library (identified by its uid)
@application.route("/getlibraryvariablesvalues", methods=["POST", "GET"])
def getlibraryvariablesvalues():
    log.debug("/getlibraryvariablesvalues")
    if (wserver.isTokenValid(request)):
        log.debug("/IN getlibraryvariablesvalues")
        wstatistics.startUpdate("getlibraryvariablesvalues")
        ret = wserver.getLibraryVariablesValues(request)
        wstatistics.endUpdate("getlibraryvariablesvalues")
        log.debug("/OUT getlibraryvariablesvalues")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Tries to login a user
@application.route("/login", methods=["POST", "GET"])
def login():
    log.debug("/IN login")
    wstatistics.startUpdate("login")
    ret = wserver.login(request) 
    wstatistics.endUpdate("login")
    log.debug("/OUT login")
    return ret

#Logout a user
@application.route("/logout", methods=["POST", "GET"])
def logout():
    log.debug("/IN logout")
    if (wserver.isTokenValid(request)):
        wstatistics.startUpdate("logout")
        wserver.logout(request) 
        wstatistics.endUpdate("logout")
        log.debug("/OUT logout")
        return ""
    else:
        return HieratikaConstants.INVALID_TOKEN

#Updates a group of schedule variables
@application.route("/updateschedule", methods=["POST", "GET"])
def updateschedule():
    log.debug("/updateschedule")
    if (wserver.isTokenValid(request)):
        log.debug("/IN updateschedule")
        wstatistics.startUpdate("updateschedule")
        ret = wserver.updateSchedule(request)    
        wstatistics.endUpdate("updateschedule")
        log.debug("/OUT updateschedule")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Commits a group of schedule variables
@application.route("/commitschedule", methods=["POST", "GET"])
def commitschedule():
    log.debug("/commitschedule")
    if (wserver.isTokenValid(request)):
        log.debug("/IN commitschedule")
        wstatistics.startUpdate("commitschedule")
        ret = wserver.commitSchedule(request)    
        wstatistics.endUpdate("commitschedule")
        log.debug("/OUT commitschedule")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Creates a new schedule
@application.route("/createschedule", methods=["POST", "GET"])
def createschedule():
    log.debug("/createschedule")
    if (wserver.isTokenValid(request)):
        log.debug("/IN createschedule")
        wstatistics.startUpdate("createschedule")
        ret = wserver.createSchedule(request)
        wstatistics.endUpdate("createschedule")
        log.debug("/OUT createschedule")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Deletes an existent schedule
@application.route("/deleteschedule", methods=["POST", "GET"])
def deleteschedule():
    log.debug("/deleteschedule")
    if (wserver.isTokenValid(request)):
        log.debug("/IN deleteschedule")
        wstatistics.startUpdate("deleteschedule")
        ret = wserver.deleteSchedule(request)
        wstatistics.endUpdate("deleteschedule")
        log.debug("/OUT deleteschedule")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Obsoletes an existent schedule
@application.route("/obsoleteschedule", methods=["POST", "GET"])
def obsoleteschedule():
    log.debug("/obsoleteschedule")
    if (wserver.isTokenValid(request)):
        log.debug("/IN obsoleteschedule")
        wstatistics.startUpdate("obsoleteschedule")
        ret = wserver.obsoleteSchedule(request)
        wstatistics.endUpdate("obsoleteschedule")
        log.debug("/OUT obsoleteschedule")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Creates a new schedule folder
@application.route("/createschedulefolder", methods=["POST", "GET"])
def createschedulefolder():
    log.debug("/createschedulefolder")
    if (wserver.isTokenValid(request)):
        log.debug("/IN createschedulefolder")
        wstatistics.startUpdate("createschedulefolder")
        ret = wserver.createScheduleFolder(request)
        wstatistics.endUpdate("createschedulefolder")
        log.debug("/OUT createschedulefolder")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Deletes an existent schedule folder
@application.route("/deleteschedulefolder", methods=["POST", "GET"])
def deleteschedulefolder():
    log.debug("/deleteschedulefolder")
    if (wserver.isTokenValid(request)):
        log.debug("/IN deleteschedulefolder")
        wstatistics.startUpdate("deleteschedulefolder")
        ret = wserver.deleteScheduleFolder(request)
        wstatistics.endUpdate("deleteschedulefolder")
        log.debug("/OUT deleteschedulefolder")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

#Obsoletes an existent schedule folder
@application.route("/obsoleteschedulefolder", methods=["POST", "GET"])
def obsoleteschedulefolder():
    log.debug("/obsoleteschedulefolder")
    if (wserver.isTokenValid(request)):
        log.debug("/IN obsoleteschedulefolder")
        wstatistics.startUpdate("obsoleteschedulefolder")
        ret = wserver.obsoleteScheduleFolder(request)
        wstatistics.endUpdate("obsoleteschedulefolder")
        log.debug("/OUT obsoleteschedulefolder")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN


    
@application.route("/stream", methods=["POST", "GET"])
def stream():
    log.debug("/stream")
    if (wserver.isTokenValid(request)):
        if (request.method == "POST"):
            tokenId = request.form["token"]
        else:
            tokenId = request.args["token"]

        username = wserver.getAuth().getUsernameFromToken(tokenId)
        if (username is not None): 
            #Note that this cannot be interfaced through the wserver (otherwise the yield reply will not work properly)
            return Response(wserver.getServer().streamData(username, tokenId), mimetype="text/event-stream")
    else:
        return HieratikaConstants.INVALID_TOKEN

@application.route('/downloadCfg', methods=['GET', 'POST'])
def downloadCfg():
    log.debug("/downloadCfg")
    if (wserver.isTokenValid(request)):
        log.debug("/IN downloadCfg")
        wstatistics.startUpdate("downloadCfg")
        ret = wserver.downloadCfg(request)
        wstatistics.endUpdate("downloadCfg")
        log.debug("/OUT downloadCfg")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN
        
        

@application.route('/uploadCfg', methods=['GET', 'POST'])
def uploadCfg():
    log.debug("/uploadCfg")
    log.debug("/IN uploadCfg")
    wstatistics.startUpdate("uploadCfg")
    ret = wserver.uploadCfg(request)
    wstatistics.endUpdate("uploadCfg")
    log.debug("/OUT uploadCfg")
    return ret

@application.route("/statistics", methods=["POST", "GET"])
def statistics():
    log.debug("/statistics")
    if (wserver.isTokenValid(request)):
        log.debug("/IN statistics")
        ret = json.dumps(wstatistics.getStatistics()) 
        log.debug("/OUT statistics")
        return ret
    else:
        return HieratikaConstants.INVALID_TOKEN

@application.route("/")
def index():
    log.debug("/")
    if (wserver.getServer().isStandalone()):
        return application.send_static_file("index-standalone.html")
    else:
        return application.send_static_file("index.html")

@application.route("/pages/<filename>")
def pages(filename):
    return send_from_directory(wserver.getPagesFolder(), filename)

@application.route("/tmp/<filename>")
def tmp(filename):
    return send_from_directory('../../tmp', filename)

if __name__ == "__main__":
   
    #wserver.start()
    parser = argparse.ArgumentParser(description = "Flask http wserver for hieratika")
    parser.add_argument("-H", "--host", type=str, default="127.0.0.1", help="Server port")
    parser.add_argument("-p", "--port", type=int, default=5000, help="Server IP")
    parser.add_argument("-i", "--ini", type=str, help="The location of the ini file", required=True)
    args = parser.parse_args()

    print "\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
    print "==============================================================================================================================="
    print "Flash HTTP server for Hieratika"
    print "==============================================================================================================================="
    print "The preferred way to start this service is with gunicorn:"
    print "gunicorn --preload --log-file=- -k gevent -w 16 -b 0.0.0.0:80 'wservermain:start(config=\"PATH_TO_CONFIG.ini\")'"
    print "==============================================================================================================================="
   
    try:
        with open(args.ini, "r") as configFile:
            config = ConfigParser.ConfigParser()
            config.readfp(configFile)
            application = load(config) 
            if (application is not None):
                application.run(threaded=True, use_reloader = False, host=args.host, port=args.port)
    except (IOError, ConfigParser.Error) as e:
        #Trap both IOError 
        log.critical("Failed to load configuration file {0} : {1}".format(configFile, e))
        exit()

