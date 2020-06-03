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
from abc import ABCMeta, abstractmethod
import ConfigParser
import datetime
import json
import logging
import multiprocessing
import multiprocessing.managers
import os
import time
import threading

##
# Project imports
##
from hieratika.util.broadcastqueue import BroadcastQueue
from hieratika.util.shareddict import SharedDictionary

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class HieratikaServer(object):
    """ Abstract class for any server implementation.
        It implements the inter-client SSE streaming mechanism which allows to notify all the registered clients
        about changes in the schedule or in the plant.
    """
    
    __metaclass__ = ABCMeta

    def __init__(self):
        super(HieratikaServer, self).__init__()
        
    def loadCommon(self, config):
        """ Loads parameters that are common to all server implementations.
        
        Args:
            config (ConfigParser): parameters that are common to all server implementations:
            - udpBroadcastPort (int): the port that is used by the broadcastqueue.
        Returns:
            True if all the parameters are successfully loaded.
        """
        self.streamUsers = SharedDictionary() 
        try:
            #IPC using UDP sockets
            udpPort = config.getint("hieratika", "udpBroadcastQueuePort")
            self.standalone = config.getboolean("hieratika", "standalone")
            self.udpQueue = BroadcastQueue(udpPort)
        except (KeyError, ValueError, ConfigParser.Error) as e:
            log.critical("Failed to load configuration parameters {0}".format(e))
            return False
        return True

    def getTid(self):
        """
        Returns:
            A keyword which univocally identifies both the process and the thread.
        """
        tid = str(os.getpid())
        tid += "_"
        tid += str(threading.current_thread().ident) 
        return tid
 
    def streamData(self, username, token):
        """ Streams data back to the client using SSE.
            The inferface is provided by a broadcastqueue.
         
        Args:
            username (str): user requesting for data to be streamed.
            token (str): login token of the user requesting for data to be streamed.
        """
        #TODO This implementation has a design choice that has to be discussed in the future: all the variables are always streamed, even if the client might 
        #have no interest on them (because e.g. the page he is browsing has none the variables that have been updated). This design choice makes the server
        #processing lighter at the expense of increased bandwidth and more processing on the client (which has to decide if the updated variables are relevant to him or not).
        #An alternative would be to use a registrar at the server side and to filter before sending to the client. Given that the current architecture is multi process and multi threading
        #this might also have a performance impact which is not negligible, as the registrar would have to be implemented using multi process safe components (e.g. multiprocessing.Manager()) or 
        #to use a local mechanism which allows to register variables using the UDP queue. This strategy would allow to have the registrar structures local to the streamData thread and would potentially
        #increase performance.
        tid = None
        try:
            log.info("Streaming data for user {0} ({1})".format(username, token))
            while True:
                if (tid == None):
                    # The first time just register the Queue and send back the TID so that updates from this client are not sent back to itself (see updateschedule)
                    tid = self.getTid()
                    encodedPy = {"reset": True, "tid": tid}
                    encodedJson = json.dumps(encodedPy)
                else:
                    # Monitor on change
                    encodedJson = self.udpQueue.get()
                    if (encodedJson == None):
                        encodedJson = ""
                        time.sleep(0.01)
                    else:
                        log.debug("Streaming {0}".format(encodedJson))
                        encodedPy = json.loads(encodedJson)
                        if ("logout" in encodedPy):
                            if (encodedPy["logout"] == token):
                                log.info("Stopping streamData as user {0} in instance ({1}) logged out".format(username, token))
                                break
                            else:
                                encodedJson = ""
                                time.sleep(0.01)
                yield "data: {0}\n\n".format(encodedJson)
        except Exception as e:
            log.critical("streamData failed for user {0} in instance ({1}) {2}".format(username, token, e))
            self.streamData(username, token)
        log.info("Stopped streamData for user {0} in instance ({1})".format(username, token))

    def queueStreamData(self, jSonData):
        """ Streams the input jSonData to all the SSE registered clients. This data contains the id of the client thread (received the first time the client registered in streamData), the scheduleUID related to the update and a dictionary with the list of variables that were update. If the update is from the plant the tid and scheduleUID parameters are ignored.
        
        Args 
            jSonData (json): the data to be streamed in the format {tid: threadIdWhichTriggeredTheUpdate, scheduleUID:idOfScheduleWhichTriggeredTheUpdate, variables:{varibleName1:variableValue1, ...}}
        """
        self.udpQueue.put(jSonData)

    def userLoggedIn(self, username, token):
        """ Called everytime a user is logged in into the system.
        
        Args:
            username (str): the username of the user.
        """
        pass

    def userLoggedOut(self, username, token):
        """ Called everytime a user is logged in into the system.
        
        Args:
            username (str): the username of the user.
        """
        self.udpQueue.put(json.dumps({"logout": token}))

    def isStandalone(self):
        """
        Returns:
            True if the server is configured to run standalone (i.e. not distributed and not multi-user).
        """
        return self.standalone

    @abstractmethod
    def load(self, config):
        """ Configures the server against a set of parameters. This set of parameters is specific for each server implementation.
        
        Args:
            config(ConfigParser): the server specific implementation parameters are in the section "server-impl".
        Returns:
            True if the server is successfully configured.
        """
        pass

    @abstractmethod
    def getVariablesInfo(self, pageName, requestedVariables):
        """ Returns all the available information (and meta-information) for all of the requestedVariables which belong to a given
        configuration. In hieratika a configuration is identified by a unique name (pageName).

        Args:
           pageName (str): name of the page (which also corresponds to the name of the configuration entity).
           requestedVariables ([str]): identifiers of the variables to be queried.
        Returns:
            A list of Variables ([Variable]) with all the information available for each of the request variables 
        """
        pass

    @abstractmethod
    def getLibraryVariablesInfo(self, libraryType, requestedVariables):
        """ Returns all the available information (and meta-information) for all of the requestedVariables which belong to a given library type.

        Args:
           libraryType (str): the library type (see hlibrary).
           requestedVariables ([str]): identifiers of the variables to be queried.
        Returns:
            A list of Variables ([Variable]) with all the information available for each of the request variables 
        """
        pass

    @abstractmethod
    def getTransformationsInfo(self, pageName):
        """ Returns all the available information (and meta-information) for all of the TransformationFunction(s) that belong to a given
        configuration. In hieratika a configuration is identified by a unique name (pageName).

        Args:
           pageName (str): name of the page (which also corresponds to the name of the configuration entity).
        Returns:
            A list of TransformationFunction ([TransformationFunction]) for the requested page. 
        """
        pass

    @abstractmethod
    def getScheduleFolders(self, username, pageName, parentFolders):
        """ Gets all the schedule folders that are avaiable for a given user in a given page.

        Args:
           username (str): the username to which the returned schedules belong to. 
           pageName (str): the name of the page associated to the schedule.
           parentFolders ([str]): list of the parent folders of the folders to be retrieved.
        Returns:
            An array with all the ScheduleFolders that are available for the requested user in the 
            specified page.
        """
        pass


    @abstractmethod
    def getSchedules(self, username, pageName, parentFolders):
        """ Gets all the schedules that are avaiable for a given user in a given page.

        Args:
           username (str): the username to which the returned schedules belong to. 
           pageName (str): the name of the page associated to the schedule.
           parentFolders ([str]): list of the parent folders of the folders to be retrieved.
        Returns:
            An array with all the schedules that are available for the requested user in the 
            specified page.
        """
        pass

    @abstractmethod
    def getLibraries(self, username, htype):
        """ Gets all the libraries (for a given type) that are avaiable for a given user.

        Args:
           username (str): the username to which the returned libraries belong to. 
           htype (str): the library type.
        Returns:
            An array with all the libraries (of the requested type) that are available for the requested user.
        """
        pass


    @abstractmethod
    def getPages(self):
        """
        Returns:
            All the pages that are available.
        """
        pass

    @abstractmethod
    def getPage(self, pageName):
        """Gets the page associated to a given name

       Args:
           pageName (str): the page name to query.

       Returns:
           The Page or None if the name is not found.
        """
        pass

    @abstractmethod
    def getSchedule(self, scheduleUID):
        """ Gets the schedule associated to a given unique identifier.

        Args:
            scheduleUID (str): unique schedule identifier.
        Returns:
           The Schedule or None if the scheduleUID is not found.
        """
        pass

    @abstractmethod
    def getScheduleVariablesValues(self, scheduleUID):
        """ Gets all the variables values associated to a given schedule.
        
        Args:
            scheduleUID(str): unique schedule identifier.
        Returns:
            A dictionary of variableId:variableValue pairs          
        """
        pass

    @abstractmethod
    def getLibraryVariablesValues(self, libraryUID):
        """ Gets all the variables values associated to a given library.
        
        Args:
            libraryUID(str): unique library identifier.
        Returns:
            A dictionary of variableId:variableValue pairs          
        """
        pass

    @abstractmethod
    def commitSchedule(self, tid, scheduleUID, variables):
        """ Permanently updates the requested variable values for a given schedule. 
    
        Args:
            tid (str): unique identifier of the calling thread/process
            scheduleUID (str): unique schedule identifier
            variables ({variableName1:value1, variableName2:value2, ...}):  dictionary with variables to be updated.

        Returns:
            A tupple where the first element is one of HieratikaConstants.OK, HieratikaConstants.IN_USE and the second element the list of variables that were updated in the form of a dictionary {variableName1:value1, variableName2:value2, ...}
        """
        pass

    @abstractmethod
    def updatePlant(self, pageName, variables):
        """ Updates the variable values of the plant (associated to a given page).
    
        Args:
            pageName (str): name of the page holding these variables.
            variables ({variableName1:value1, variableName2:value2, ...}):  dictionary with variables to be updated.

        Returns:
            The list of variables that were updated in the form of a dictionary {variableName1:value1, variableName2:value2, ...}
        """
        pass

    @abstractmethod
    def updatePlantFromSchedule(self, pageName, scheduleUID):
        """ Updates the variable values of the plant (associated to a given page) against the variables that are set in a given schedule.
    
        Args:
            pageName (str): name of the page holding these variables.
            scheduleUID (str): unique schedule identifier

        Returns:
            The list of variables that were updated in the form of a dictionary {variableName1:value1, variableName2:value2, ...}
        """
        pass


    @abstractmethod
    def createSchedule(self, name, description, username, pageName, parentFolders, sourceScheduleUID = None, inheritFromSchedule = False):
        """ Creates a new schedule either based on a existing schedule (if sourceSchedule is not None) or from the plant. 

        Args:
            name (str): the name of the schedule to create.
            description (str): the description of the schedule to create.
            username (str): the owner of the schedule.
            pageName (str): name of the page to which the schedule belongs to.
            parentFolders ([str]): list of the parent folders of the new schedule to be created.
            sourceScheduleUID (str): create the schedule by copying from the schedule with this unique identifier. If sourceScheduleUID is None, copy from the plant.
            inheritFromSchedule (bool): if True the created schedule will be marked as being inherited from the sourceScheduleUID and an hardlink between the two will be created. This mean that that the sourceScheduleUID will
            not be modifiable nor deletable while this link exists (i.e. while the created schedule exists).

        Returns:
            The unique identifier of the created schedule or None if the schedule could not be created.
        """
        pass

    @abstractmethod
    def deleteSchedule(self, scheduleUID):
        """ Deletes an existent schedule. 

        Args:
            scheduleUID (str): unique schedule identifier
        Returns:
            HieratikaConstants.OK if the schedule was successfully delete, HieratikaConstants.NOT_FOUND if the schedule was not found or HieratikaConstants.IN_USE if the schedule is being (or was already used) and thus cannot be deleted.
        """
        pass

    @abstractmethod
    def obsoleteSchedule(self, scheduleUID):
        """ Obsoletes an existent schedule. 

        Args:
            scheduleUID (str): unique schedule identifier
        Returns:
            HieratikaConstants.OK if the schedule was successfully delete, HieratikaConstants.NOT_FOUND if the schedule was not found or HieratikaConstants.IN_USE if the schedule is being (or was already used) and thus cannot be deleted.
        """
        pass

    @abstractmethod
    def createScheduleFolder(self, name, username, parentFolders, pageName):
        """ Creates a new schedule folder. 

        Args:
            name (str): the name of the folder to create.
            username (str): the owner of the schedule folder.
            parentFolders ([str]): list of the parent folders of the new folder to be created.
            pageName (str): name of the page to which the schedule folder belongs to.
        Returns:
            HieratikaConstants.OK if the schedule was successfully created, HieratikaConstants.NOT_FOUND if the parent folders do not exist or HieratikaConstants.UNKNOWN_ERROR if case of any other error.
        """
        pass

    @abstractmethod
    def deleteScheduleFolder(self, name, username, parentFolders, pageName):
        """ Delete a schedule folder. 

        Args:
            name (str): the name of the folder to delete.
            username (str): the owner of the schedule folder.
            parentFolders ([str]): list of the parent folders of the folder to be deleted.
            pageName (str): name of the page to which the schedule folder belongs to.
        Returns:
            HieratikaConstants.OK if the schedule was successfully deleted or HieratikaConstants.UNKNOWN_ERROR if case of any other error.
        """
        pass

    @abstractmethod
    def obsoleteScheduleFolder(self, name, username, parentFolders, pageName):
        """ Obsoletes a schedule folder. 

        Args:
            name (str): the name of the folder to obsolete.
            username (str): the owner of the schedule folder.
            parentFolders ([str]): list of the parent folders of the new folder to be obsolete.
            pageName (str): name of the page to which the schedule folder belongs to.
        Returns:
            HieratikaConstants.OK if the schedule was successfully obsolete or HieratikaConstants.UNKNOWN_ERROR if case of any other error.
        """
        pass

    @abstractmethod
    def deleteLibrary(self, libraryUID):
        """ Deletes an existent library. 

        Args:
            libraryUID (str): unique library identifier
        Returns:
            HieratikaConstants.OK if the library was successfully delete, HieratikaConstants.NOT_FOUND if the library was not found or HieratikaConstants.IN_USE if the library is being (or was already used) and thus cannot be deleted.
        """
        pass

    @abstractmethod
    def obsoleteLibrary(self, libraryUID):
        """ Obsoletes an existent library. 

        Args:
            libraryUID (str): unique library identifier
        Returns:
            HieratikaConstants.OK if the library was successfully delete, HieratikaConstants.NOT_FOUND if the library was not found or HieratikaConstants.IN_USE if the library is being (or was already used) and thus cannot be deleted.
        """
        pass

    @abstractmethod
    def saveLibrary(self, htype, name, description, username, variables):
        """ Saves (and creates if needed) a library of the given type, with the given name, for the provided user. 
    
        Args:
            htype (str): the library type.
            name (str): the library name.
            description (str): the library description.
            username (str): the library owner.
            variables ({variableName1:value1, variableName2:value2, ...}):  dictionary with the library variables to be stored.

        Returns:
            A tupple where the first element is one of HieratikaConstants.OK, HieratikaConstants.IN_USE or HieratikaConstants, and the second element is the new library if successfully saved/created, None otherwise.
        """
        pass
