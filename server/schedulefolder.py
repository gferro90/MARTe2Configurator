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
__date__ = "18/01/2018"

##
# Standard imports
##

##
# Project imports
##

##
# Logger configuration
##

##
# Class definition
##
class ScheduleFolder(object):
    """ Describes a hieratika parameter schedule folder.
    """

    def __init__(self, name, obsolete = False):
        """ Constructs a Schedule folder object against a name.
        
        Args:
            name (str): the name of the folder.
            obsolete (bool): True if the folder has been marked as obsolete.
        """
        self.name = name
        self.obsolete = obsolete

    @staticmethod
    def fromSerializableDict(dictionary):
        """
        Args:
            dictionary(dict): dictionary representation of a ScheduleFolder.
        Returns:
            A new ScheduleFolder instance with the properties defined in dictionary.
        """
        schedule = None
        try:
            schedule = ScheduleFolder(dictionary["name"], dictionary["obsolete"])
        except Exception as e:
            log.critical("Could not create the ScheduleFolder {0}".format(e))
        return schedule


    def getName(self):
        """ 
        Returns:
            The folder name (may not be unique).
        """
        return self.name

    def isObsolete(self):
        """ 
        Returns:
            Returns true if the folder has been marked as obsolete.
        """
        return self.obsolete
       

    def __str__(self):
        """ Returns a string representation of the folder.
            
        Returns:
            The folder name.
        """
        return "{0}".format(self.name) 

