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
from flask import request
import json
import logging

##
# Project imports
##
from hconstants import HieratikaConstants
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
class WServer(object):
    """ Provides an interface point between the specific server implementation (see HieratikaServer)
        and the webserver. In particular this class parses and transforms the web form parameters into 
        the list of the parameters that are expected by the HieratikaServer implementation.
    """

    def __init__(self):
        """ NOOP
        """
        self.pagesFolder = ""
        #Maximum number of variables that can be streamed for each queue stream. TODO read from configuration
        self.streamDataMaxVariables = 100

    def isTokenValid(self, request):
        """ Verifies if a given token is valid.
            A token is valid iff a user has been properly validated.
            
        Args:
            request.form["token"]: a token generated after a successful user login.
        Returns:
            True if the token is valid.
        """
        if (request.method == "POST"):
            ok = ("token" in request.form)
            if (ok):
                tokenId = request.form["token"]
        else:
            ok = ("token" in request.args)
            if (ok):
                tokenId = request.args["token"]
        if (ok): 
            log.debug("self.authImpl.isTokenValid({0})".format(tokenId))
            ok = self.authImpl.isTokenValid(tokenId)
            log.debug("Token: {0} is valid? {1}".format(tokenId, str(ok)))
        return ok
   
    def setServer(self, serverImpl):
        """ Sets the HieratikaServer implementation to be used.
        
        Args:
            serverImpl (HieratikaServer): the HieratikaServer final implementation to be used.
        """
        self.serverImpl = serverImpl

    def getServer(self):
        """ 
        Returns:
            The HieratikaServer final implementation being used.
        """
        return self.serverImpl 

    def setAuth(self, authImpl):
        """ Sets the HieratikaAuth implementation to be used.
        
        Args:
            authImpl (HieratikaAuth): the HieratikaAuth final implementation to be used.
        """
        self.authImpl = authImpl

    def getAuth(self):
        """ 
        Returns:
            The HieratikaAuth final implementation being used.
        """
        return self.authImpl 

    def getVariablesInfo(self, request):
        """ Returns the all the available information (and meta-information) for all of the requestedVariables in a given configuration set (identified by the pageName).

        Args:
           request.form["pageName"]: name of the page (which corresponds to the name of the configuration).
           request.form["variables"]: identifiers of the variables to be queried.
        Returns:
            A json encoded list of variables or HieratikaConstants.INVALID_TOKEN if the token is not valid.
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
            projectName = request.form["projectName"]
            pageName = request.form["pageName"]
            userName = request.form["userName"]
            requestedVariables = json.loads(request.form["variables"])
            variables = self.serverImpl.getVariablesInfo(userName, projectName, pageName, requestedVariables)
            variablesStr = [v.asSerializableDict() for v in variables]
            toReturn = json.dumps(variablesStr)
        except KeyError as e:
            log.critical(str(e))
            toReturn = HieratikaConstants.INVALID_PARAMETERS

        return toReturn 


    def updatePlant(self, request):
        """ Updates the values of the requested variables in the plant.
            All the variables that are successfully updated will be streamed to all the clients.

        Args:
            request.form["pageName"]: name of the page (which corresponds to the name of the configuration).
            request.form["tid"]: the unique thread (and process) identifier which was returned to the client when registered to the data stream (see streamData).
            request.form["variables"]: a dictionary with the list of variables to be updated in the form {variableName1:variableValue1, ...}
        Returns:
            The string ok if the values are successfully updated.
        """
        toReturn = HieratikaConstants.OK
        try:
            projectName = request.form["projectName"]
            userName = request.form["userName"]
            variables = request.form["variables"]
            variablesToUpdate = json.loads(variables)
            toStream = {
                "tid": request.form["tid"],
                "variables": {}
            }
            variablesToStream = self.serverImpl.updatePlant(projectName, userName, variablesToUpdate)
            #Send n variables at the time in order not to overflow the queue size..
            keys = variablesToStream.keys()
            n = self.streamDataMaxVariables
            for i in xrange(0, len(keys), n):
                toStream["variables"] = {}
                for k in keys[i: i + n]:
                    toStream["variables"][k] = variablesToStream[k]
                self.serverImpl.queueStreamData(json.dumps(toStream))
        except KeyError as e:
            log.critical(str(e))
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn

    def updatePlantFromSchedule(self, request):
        """ Updates the values of the plant from a given schedule.
            All the variables that are successfully updated will be streamed to all the clients.

        Args:
            request.form["pageName"]: name of the page (which corresponds to the name of the configuration).
            request.form["tid"]: the unique thread (and process) identifier which was returned to the client when registered to the data stream (see streamData).
            request.form["scheduleUID"]: the unique identifier of the schedule to be set against the plant.
        Returns:
            The string ok if the values are successfully updated.
        """
        toReturn = HieratikaConstants.OK
        try:
            projectName = request.form["projectName"]
            userName = request.form["userName"]
            scheduleUID = request.form["scheduleUID"]
            toStream = {
                "tid": request.form["tid"],
                "variables": {}
            }
            variablesToStream = self.serverImpl.updatePlantFromSchedule(pageName, userName, scheduleUID)
            #Send n variables at the time in order not to overflow the queue size..
            keys = variablesToStream.keys()
            n = self.streamDataMaxVariables
            for i in xrange(0, len(keys), n):
                toStream["variables"] = {}
                for k in keys[i: i + n]:
                    toStream["variables"][k] = variablesToStream[k]
                self.serverImpl.queueStreamData(json.dumps(toStream))
        except KeyError as e:
            log.critical(str(e))
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn


    def getScheduleFolders(self, request):
        """ Gets all the folders that are avaiable for a given user in a given page and in a given folder.

        Args:
           request.form["username"]: the username to which the returned schedules belong to. 
           request.form["pageName"]: the name of the page associated to the schedule.
           request.form["parentFolders"]: the list of the parent folders of the schedules to be retrieved.
        Returns:
            A list with all the folders found.
        """
        toReturn = ""
        try:
            pageName = request.form["pageName"]
            username = request.form["username"]
            parentFolders = json.loads(request.form["parentFolders"])
            
            folders = self.serverImpl.getScheduleFolders(username, pageName, parentFolders)
            foldersStr = [f.__dict__ for f in folders]
            toReturn = json.dumps(foldersStr)
            log.debug("For {0} in {1} returning: {2}".format(username, pageName, toReturn))
        except Exception as e:
            log.critical(str(e))
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn

    def getSchedules(self, request):
        """ Gets all the schedules that are avaiable for a given user in a given page and in a given folder.

        Args:
           request.form["username"]: the username to which the returned schedules belong to. 
           request.form["pageName"]: the name of the page associated to the schedule.
           request.form["parentFolders"]: the list of the parent folders of the schedules to be retrieved.
        Returns:
            A json representation of all the schedules that are available for the requested user in the 
            specified page.
        """
        toReturn = ""
        try:
            pageName = request.form["pageName"]
            username = request.form["username"]
            parentFolders = json.loads(request.form["parentFolders"])
            
            schedules = self.serverImpl.getSchedules(username, pageName, parentFolders)
            schedulesStr = [s.__dict__ for s in schedules]
            toReturn = json.dumps(schedulesStr)
            log.debug("For {0} in {1} returning: {2}".format(username, pageName, toReturn))
        except Exception as e:
            log.critical(str(e))
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn

    def getSchedule(self, request):
        """
        Args:
            request.form["scheduleUID"]: the unique identifier of the schedule to get.

        Returns:
            A json representation of the Schedule or an empty string if the schedule is not found.
        """
        toReturn = ""
        try: 
            scheduleUID = request.form["scheduleUID"]
            schedule = self.serverImpl.getSchedule(scheduleUID)
            if (schedule is not None):
                toReturn = json.dumps(schedule.__dict__)
                log.debug("Returning schedule: {0}".format(toReturn))
        except KeyError as e:
            log.critical(str(e))
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn

    def getScheduleVariablesValues(self, request):
        """ Gets all the variables values for a given schedule (identified by its uid).
        
        Args:
            request.form["scheduleUID"]: the schedule identifier.
    
        Returns:
            A json dictionary in the form  {variableName1:variableValue1, ...} with each schedule variable.
        """
        try: 
            variables = []
            scheduleUID = request.form["scheduleUID"]
            variables = self.serverImpl.getScheduleVariablesValues(scheduleUID)
            toReturn = json.dumps(variables)
        except KeyError as e:
            log.critical(str(e))
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn


    def updateSchedule(self, request):
        """ Updates other users of the same schedule that the variable values have changed. Note that these changes are not permanently stored.
   
        Args:
            request.form["scheduleUID"]: unique schedule identifier.
            request.form["tid"]: the unique thread (and process) identifier which was returned to the client when registered to the data stream (see streamData).
            request.form["variables"]: a dictionary with the list of variables to be updated in the form {variableName1:variableValue1, ...}

        Returns:
            ok if the schedule is successfully updated or an empty string otherwise.
        """
        toReturn = HieratikaConstants.OK
        try: 
            tid = request.form["tid"]
            username = request.form["username"]
            projectName = request.form["projectName"]
            xmlFile = request.form["page"]
            variablesToStream = json.loads(request.form["variables"])

            toStream = {
                "tid": tid,
                "variables": {}
            }
            #Send 100 variables at the time in order not to overflow the queue size..
            keys = variablesToStream.keys()
            n = self.streamDataMaxVariables 
            for i in xrange(0, len(keys), n):
                toStream["variables"] = {}
                for k in keys[i: i + n]:
                    toStream["variables"][k] = variablesToStream[k]
                self.serverImpl.queueStreamData(json.dumps(toStream))

        except KeyError as e:
            log.critical(str(e))
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn

    def createSchedule(self, request):
        """ Creates a new schedule either based on a existing schedule (if sourceSchedule is available on the request.form) or from the plant. 

        Args:
            request.form["name"]: the name of the schedule to create.
            request.form["description"]: the description of the schedule to create.
            request.form["username"]: the owner of the schedule.
            request.form["pageName"]: name of the page to which the schedule belongs to.
            request.form["parentFolders"]: a list of the parent folders of the folder to be created.
            request.form["sourceScheduleUID"]: create the schedule by copying from the schedule with the unique identifier given by sourceScheduleUID. If sourceSchedule is not set, copy from the plant.
            request.from["inheritFromSchedule"]: if True the created schedule will be marked as being inherited from the sourceScheduleUID and an hardlink between the two will be created. This mean that that the sourceScheduleUID will not be modifiable nor deletable while this link exists (i.e. while the created schedule exists).
        Returns:
            The unique identifier of the created schedule or HieratikaConstants.INVALID_PARAMETERS if the schedule could not be created.
        """
        try:
            name = request.form["name"]
            description = request.form["description"]
            username = request.form["username"]
            pageName = request.form["pageName"]
            parentFolders = json.loads(request.form["parentFolders"])
            sourceScheduleUID = None
            inheritFromSchedule = False
            if "sourceScheduleUID" in request.form:
                sourceScheduleUID = request.form["sourceScheduleUID"]
            if "inheritFromSchedule" in request.form:
                inheritFromSchedule = request.form["inheritFromSchedule"]
                inheritFromSchedule = (inheritFromSchedule == "true")
            toReturn = self.serverImpl.createSchedule(name, description, username, pageName, parentFolders, sourceScheduleUID, inheritFromSchedule) 
            if (toReturn == None):
                toReturn = HieratikaConstants.INVALID_PARAMETERS
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn

    def deleteSchedule(self, request):
        """ Deletes an existent schedule. 

        Args:
            request.form["scheduleUID"]: the schedule identifier.
        Returns:
            HieratikaConstants.OK if the schedule was successfully delete, HieratikaConstants.NOT_FOUND if the schedule was not found or HieratikaConstants.IN_USE if the schedule is being (or was already) used and thus cannot be deleted.
        """
        try:
            scheduleUID = request.form["scheduleUID"]
            toReturn = self.serverImpl.deleteSchedule(scheduleUID) 
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn

    def obsoleteSchedule(self, request):
        """ Obsoletes an existent schedule. 

        Args:
            request.form["scheduleUID"]: the schedule identifier.
        Returns:
            HieratikaConstants.OK if the schedule was successfully obsoleted, HieratikaConstants.NOT_FOUND if the schedule was not found or HieratikaConstants.IN_USE if the schedule is being (or was already) used and thus cannot be deleted.
        """
        try:
            scheduleUID = request.form["scheduleUID"]
            toReturn = self.serverImpl.obsoleteSchedule(scheduleUID) 
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn

    def createScheduleFolder(self, request):
        """ Creates a new schedule folder. 

        Args:
            request.form["name"]: the name of the schedule folder to create.
            request.form["username"]: the owner of the folder.
            request.form["parentFolders"]: a list of the parent folders of the folder to be created.
            request.form["pageName"]: name of the page to which the schedule folder belongs to.
        Returns:
            HieratikaConstants.OK if the schedule was successfully created, HieratikaConstants.NOT_FOUND if the parent folders do not exist or HieratikaConstants.UNKNOWN_ERROR if case of any other error.
        """
        try:
            name = request.form["name"]
            username = request.form["username"]
            parentFolders = json.loads(request.form["parentFolders"])
            pageName = request.form["pageName"]
            toReturn = self.serverImpl.createScheduleFolder(name, username, parentFolders, pageName) 
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn

    def deleteScheduleFolder(self, request):
        """ Deletes a schedule folder. 

        Args:
            request.form["name"]: the name of the schedule folder to delete.
            request.form["username"]: the owner of the folder.
            request.form["parentFolders"]: a list of the parent folders of the folder to be deleted.
            request.form["pageName"]: name of the page to which the schedule folder belongs to.
        Returns:
            HieratikaConstants.OK if the schedule was successfully deleted or HieratikaConstants.UNKNOWN_ERROR if case of any other error.
        """
        try:
            name = request.form["name"]
            username = request.form["username"]
            parentFolders = json.loads(request.form["parentFolders"])
            pageName = request.form["pageName"]
            toReturn = self.serverImpl.deleteScheduleFolder(name, username, parentFolders, pageName) 
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn

    def obsoleteScheduleFolder(self, request):
        """ Creates a new schedule folder. 

        Args:
            request.form["name"]: the name of the schedule folder to obsolete.
            request.form["username"]: the owner of the folder.
            request.form["parentFolders"]: a list of the parent folders of the folder to be obsoleted.
            request.form["pageName"]: name of the page to which the schedule folder belongs to.
        Returns:
            HieratikaConstants.OK if the schedule was successfully obsoleted or HieratikaConstants.UNKNOWN_ERROR if case of any other error.
        """
        try:
            name = request.form["name"]
            username = request.form["username"]
            parentFolders = json.loads(request.form["parentFolders"])
            pageName = request.form["pageName"]
            toReturn = self.serverImpl.obsoleteScheduleFolder(name, username, parentFolders, pageName) 
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn



    def getUsers(self, request):
        """
        Returns:
            All the system users.
        """
        users = self.authImpl.getUsers()
        usersStr = [u.asSerializableDict() for u in users]
        log.debug("Returning users: {0}".format(usersStr))
        toReturn = json.dumps(usersStr)
        return toReturn

    def getUser(self, request):
        """
        Args:
            request.form["username"]: the username of the user to get.

        Returns:
            A json representation of the User or an empty string if the user is not found.
        """
        toReturn = ""
        try: 
            username = request.form["username"]
            user = self.authImpl.getUser(username)
            if (user is not None):
                toReturn = json.dumps(user)
                log.debug("Returning user: {0}".format(toReturn))
        except KeyError as e:
            log.critical(str(e))
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn

    def getConfigurations(self, request):
        """
        Returns:
            All the pages that are available.
        """
        pages = self.serverImpl.getConfigurations()
        pagesStr = [p.__dict__ for p in pages]
        log.debug("Returning pages: {0}".format(pagesStr))
        toReturn = json.dumps(pagesStr)
        return toReturn

    def copyComponent(self, request):
        """
        Returns:
            All the pages that are available.
        """
        username = request.form["username"]
        projectName = request.form["projectName"]
        sourceCompName = request.form["sourceCompName"]
        destCompName = request.form["destCompName"]
        page = self.serverImpl.copyComponent(projectName, username, sourceCompName, destCompName)
        return HieratikaConstants.OK

    def getConfiguration(self, request):
        """
        Returns:
            All the pages that are available.
        """
        username = request.form["username"]
        projectName = request.form["projectName"]        
        page = self.serverImpl.getConfiguration(projectName, username)
        return HieratikaConstants.OK

        
    def createProject(self, request):
        """
        Creates:
            A new project.
        Args:
            request.form["username"]: the owner of the folder.
            request.form["projectName"]: the name of the project folder to create.
        Returns:
            HieratikaConstants.OK if the schedule was successfully created, HieratikaConstants.NOT_FOUND if the parent folders do not exist or HieratikaConstants.UNKNOWN_ERROR if case of any other error.
        """
        try:
            username = request.form["username"]
            projectName = request.form["projectName"]
            log.debug("Returning: {0} {1}".format(username, projectName))
            toReturn = self.serverImpl.createProject(username, projectName) 
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn


    def deleteProject(self, request):
        """
        Deletes:
            A project.
        Args:
            request.form["username"]: the owner of the folder.
            request.form["projectName"]: the name of the project folder to create.
        Returns:
            HieratikaConstants.OK if the schedule was successfully created, HieratikaConstants.NOT_FOUND if the parent folders do not exist or HieratikaConstants.UNKNOWN_ERROR if case of any other error.
        """
        try:
            username = request.form["username"]
            projectName = request.form["projectName"]
            log.debug("Returning: {0} {1}".format(username, projectName))
            toReturn = self.serverImpl.deleteProject(username, projectName) 
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn        
        
    def copyProject(self, request):
        """
        Deletes:
            A project.
        Args:
            request.form["username"]: the owner of the folder.
            request.form["projectName"]: the name of the project folder to create.
        Returns:
            HieratikaConstants.OK if the schedule was successfully created, HieratikaConstants.NOT_FOUND if the parent folders do not exist or HieratikaConstants.UNKNOWN_ERROR if case of any other error.
        """
        try:
            username = request.form["username"]
            projectName = request.form["projectName"]
            newProjectName = request.form["newProjectName"]
            log.debug("Copy {0} to {1} for {2}".format(projectName, newProjectName, username))
            toReturn = self.serverImpl.copyProject(username, projectName, newProjectName) 
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn        


    def getDatasources(self, request):
        """
        Returns:
            All the datasources that are available.
        """
        datasources = self.serverImpl.getDatasources()
        datasourcesStr = [p.__dict__ for p in datasources]
        log.debug("Returning pages: {0}".format(datasourcesStr))
        toReturn = json.dumps(datasourcesStr)
        return toReturn

    def getCfgFiles(self, request):
        """
        Returns:
            All the gams that are available.
        """
        gams = self.serverImpl.getCfgFiles()
        gamsStr = [p.__dict__ for p in gams]
        log.debug("Returning pages: {0}".format(gamsStr))
        toReturn = json.dumps(gamsStr)
        return toReturn        

    def getGams(self, request):
        """
        Returns:
            All the gams that are available.
        """
        gams = self.serverImpl.getGams()
        gamsStr = [p.__dict__ for p in gams]
        log.debug("Returning pages: {0}".format(gamsStr))
        toReturn = json.dumps(gamsStr)
        return toReturn        

    def getInterfaces(self, request):
        """
        Returns:
            All the interfaces that are available.
        """
        interfaces = self.serverImpl.getInterfaces()
        interfacesStr = [p.__dict__ for p in interfaces]
        log.debug("Returning pages: {0}".format(interfacesStr))
        toReturn = json.dumps(interfacesStr)
        return toReturn        

        
    def getDatasourceObjects(self, request):
        datasource = request.form["datasource"]
        objects = self.serverImpl.getDatasourceObjects(datasource)
        objectsStr = [p.__dict__ for p in objects]
        log.debug("Returning pages: {0}".format(objectsStr))
        toReturn = json.dumps(objectsStr)
        return toReturn

    def getGamObjects(self, request):
        gam = request.form["gam"]
        objects = self.serverImpl.getGamObjects(gam)
        objectsStr = [p.__dict__ for p in objects]
        log.debug("Returning pages: {0}".format(objectsStr))
        toReturn = json.dumps(objectsStr)
        return toReturn

    def getInterfaceObjects(self, request):
        interface = request.form["interface"]
        objects = self.serverImpl.getInterfaceObjects(interface)
        objectsStr = [p.__dict__ for p in objects]
        log.debug("Returning pages: {0}".format(objectsStr))
        toReturn = json.dumps(objectsStr)
        return toReturn
        
    def downloadCfg(self, request): 
        username = request.form["username"]
        projectName = request.form["projectName"]
        try:
            toReturn = self.serverImpl.downloadCfg(username, projectName) 
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn           
        
    def uploadCfg(self, request): 
        if 'file' not in request.files:
            log.debug("No file part")
            return HieratikaConstants.INVALID_PARAMETERS
        file = request.files['file']
        if file.filename == '':
            log.debug("No selected file")
            return HieratikaConstants.INVALID_PARAMETERS
        try:
            toReturn = self.serverImpl.uploadCfg(file) 
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn           
        
                

    def addDatasource(self, request):
        """
        Adds:
            The requested data source.
        Args:
            request.form["projectName"]: the name of the project folder to create.
            request.form["username"]: the owner of the folder.
            request.form["datasourceName"]: the name of the data source to be copied.
            request.form["objectName"]: name of the object to be created.
        Returns:
            HieratikaConstants.OK if the schedule was successfully created, HieratikaConstants.NOT_FOUND if the parent folders do not exist or HieratikaConstants.UNKNOWN_ERROR if case of any other error.
        """
        try:
            projectName = request.form["projectName"]
            username = request.form["username"]
            datasourceName = request.form["datasourceName"]
            objectName = request.form["objectName"]
            componentName = request.form["componentName"]
            log.debug("Returning: {0} {1} {2} {3}".format(projectName, username, datasourceName, objectName, componentName))
            toReturn = self.serverImpl.addDatasource(projectName, username, datasourceName, objectName, componentName) 
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn

    def addGam(self, request):
        """
        Adds:
            The requested GAM.
        Args:
            request.form["projectName"]: the name of the project folder to create.
            request.form["username"]: the owner of the folder.
            request.form["gamName"]: the name of the gam to be copied.
            request.form["objectName"]: name of the object to be created.
        Returns:
            HieratikaConstants.OK if the schedule was successfully created, HieratikaConstants.NOT_FOUND if the parent folders do not exist or HieratikaConstants.UNKNOWN_ERROR if case of any other error.
        """
        try:
            projectName = request.form["projectName"]
            username = request.form["username"]
            gamName = request.form["gamName"]
            objectName = request.form["objectName"]
            componentName = request.form["componentName"]
            log.debug("Returning: {0} {1} {2} {3}".format(projectName, username, gamName, objectName, componentName))
            toReturn = self.serverImpl.addGam(projectName, username, gamName, objectName, componentName) 
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn


    def addInterface(self, request):
        """
        Adds:
            The requested Interface.
        Args:
            request.form["projectName"]: the name of the project folder to create.
            request.form["username"]: the owner of the folder.
            request.form["interfaceName"]: the name of the interface to be copied.
            request.form["objectName"]: name of the object to be created.
        Returns:
            HieratikaConstants.OK if the schedule was successfully created, HieratikaConstants.NOT_FOUND if the parent folders do not exist or HieratikaConstants.UNKNOWN_ERROR if case of any other error.
        """
        try:
            projectName = request.form["projectName"]
            username = request.form["username"]
            interfaceName = request.form["interfaceName"]
            objectName = request.form["objectName"]
            componentName = request.form["componentName"]
            log.debug("Returning: {0} {1} {2} {3}".format(projectName, username, interfaceName, objectName, componentName))
            toReturn = self.serverImpl.addInterface(projectName, username, interfaceName, objectName, componentName) 
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn

    def getClassName(self, request):
        try:
            projectName = request.form["projectName"]
            username = request.form["username"]
            xmlFile = request.form["xmlFile"]
            className = self.serverImpl.getClassName(projectName, username, xmlFile)
            toReturn = json.dumps(className)
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn   

        
    def getComponentDescription(self, request):
        try:
            projectName = request.form["projectName"]
            username = request.form["username"]
            xmlFile = request.form["xmlFile"]
            description = self.serverImpl.getComponentDescription(projectName, username, xmlFile)
            toReturn = json.dumps(description)
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn            
        
    def removeComponent(self, request):
        try:
            projectName = request.form["projectName"]
            username = request.form["username"]
            componentName = request.form["componentName"]
            self.serverImpl.removeComponent(projectName, username, componentName)
            return HieratikaConstants.OK
        except KeyError as e:
            log.critical(e)
            return HieratikaConstants.INVALID_PARAMETERS

    def getProjectComponentList(self, request):
        """
        Adds:
            The requested Interface.
        Args:
            request.form["projectName"]: the name of the project folder to create.
            request.form["username"]: the owner of the folder.
        Returns:
            HieratikaConstants.OK if the schedule was successfully created, HieratikaConstants.NOT_FOUND if the parent folders do not exist or HieratikaConstants.UNKNOWN_ERROR if case of any other error.
        """
        try:
            projectName = request.form["projectName"]
            username = request.form["username"]
            log.debug("Returning: {0} {1}".format(projectName, username))
            components = self.serverImpl.getProjectComponentList(projectName, username)
            componentsStr = [p.__dict__ for p in components]
            log.debug("Returning components: {0}".format(componentsStr))
            toReturn = json.dumps(componentsStr)
            return toReturn
        except KeyError as e:
            log.critical(e)
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn


    def getPage(self, request):
        """
        Args:
           request.form["pageName"]: shall contain the page name.
        Returns:
            A page with a given name or HieratikaConstants.INVALID_TOKEN if the token is not valid.
        """

        try: 
            pageName = request.form["pageName"]
            log.debug("Looking for page: {0}".format(pageName))
            page = self.serverImpl.getPage(pageName)
            log.debug("Returning page: {0}".format(str(page)))
            toReturn = json.dumps(page.__dict__)
        except KeyError as e:
            log.critical(str(e))
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn

    def setPagesFolder(self, pagesFolder):
        """ Sets the pages folder.
        
        Args:
            pagesFolder (str): folder which holds the html pages with the user-interfaces.
        """
        self.pagesFolder = pagesFolder

    def getPagesFolder(self):
        """ Gets the pages folder.
        
        Returns:
            The folder which holds the html pages with the user-interfaces.
        """
        return self.pagesFolder

    def login(self, request):
        """Logs a user into the system.
           Note that the same user might be logged from different locations. One authentication token will 
           be generate for each login.
           
       Args:
           request.form["username"]: shall contain the username.
           request.form["password"]: shall contain the user password.

       Returns:
           A json representation of the User.
        """
        try: 
            username = request.form["username"]
            password = request.form["password"]
            log.debug("Logging in: {0}".format(username))
            self.serverImpl.setUser(username)
            user = self.authImpl.login(username, password)
            if (user is not None):
                user = user.asSerializableDict()
            else:
                user = {"username":""}
            toReturn = json.dumps(user)
            log.debug("{0}".format(str(user)))
        except KeyError as e:
            log.critical("Missing field ({0})".format(e))
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn

    def logout(self, request):
        """ Logs out a user from the system.
       
        Args:
           request.form["token"]: the token associated to the user being logged out.
        """
        try:
            token = request.form["token"]
            self.authImpl.logout(token)
        except KeyError as e:
            log.critical("Tried to logout without specifying a token")

    def commitSchedule(self, request):
        """ Updates the variable values for a given schedule. 
   
        Args:
            request.form["scheduleUID"]: unique schedule identifier.
            request.form["tid"]: the unique thread (and process) identifier which was returned to the client when registered to the data stream (see streamData).
            request.form["variables"]: a dictionary with the list of variables to be updated in the form {variableName1:variableValue1, ...}

        Returns:
            HieratikaConstants.OK if the schedule was successfully commited, or one of HieratikaConstants.IN_USE, HieratikaConstants.UNKNOWN_ERROR if the library could not be saved.
        """
        toReturn = ""
        try: 
            tid = request.form["tid"]
            projectName = request.form["projectName"]
            username = request.form["username"]
            xmlFile = request.form["page"]
            variables = json.loads(request.form["variables"])
            toStream = {
                "tid": tid,
                "variables": [] 
            }
            ret = self.serverImpl.commitSchedule(tid, projectName, username, variables, xmlFile)
            toReturn = ret[0]
            variablesToStream = ret[1]
            #Send 100 variables at the time in order not to overflow the queue size..
            keys = variablesToStream.keys()
            n = self.streamDataMaxVariables 
            for i in xrange(0, len(variablesToStream), n):
                toStream["variables"] = {}
                for k in keys[i: i + n]:
                    toStream["variables"][k] = variablesToStream[k]
                self.serverImpl.queueStreamData(json.dumps(toStream))
        except KeyError as e:
            log.critical(str(e))
            toReturn = HieratikaConstants.INVALID_PARAMETERS
        return toReturn


