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

##
# Project imports
##

##
# Logger configuration
##

##
# Class definition
##
class Schedule(object):
    """ Describes a hieratika parameter schedule.
    """

    def __init__(self, uid, name, pageName, owner, description = "", obsolete = False, inheritsFromUID = ""):
        """ Constructs a Schedule object against a uid, name and description.
        
        Args:
            uid (str): a unique system identifier for the schedule.
            name (str): the name of the schedule.
            pageName (str): the name of the Page associated to this schedule.
            description (str): a description of the schedule.
            owner (str): the username of the User which owns the schedule.
            obsolete (bool): True if the schedule has been marked as obsolete.
            inheritsFromUID (str): The UID of the schedule from which this schedule has inherited from (if None inheritsFromUID = "").
        """
        self.uid = uid
        self.name = name
        self.pageName = pageName 
        self.description = description
        self.owner = owner 
        self.obsolete = obsolete
        self.inheritsFromUID = inheritsFromUID

    @staticmethod
    def fromSerializableDict(dictionary):
        """
        Args:
            dictionary(dict): dictionary representation of a Schedule.
        Returns:
            A new Schedule instance with the properties defined in dictionary.
        """
        schedule = None
        try:
            schedule = Schedule(dictionary["uid"], dictionary["name"], dictionary["pageName"], dictionary["description"], dictionary["owner"], dictionary["obsolete"], dictionary["inheritsFromUID"])
        except Exception as e:
            log.critical("Could not create the Schedule {0}".format(e))
        return schedule

    def getUID(self):
        """ 
        Returns: 
            A unique system identifier for the schedule.
        """
        return self.uid

    def getName(self):
        """ 
        Returns:
            The schedule name (may not be unique).
        """
        return self.name

    def getDescription(self):
        """ 
        Returns:
            The schedule description.
        """
        return self.description

    def getOwner(self):
        """ 
        Returns:
            The username of the User which owns the schedule.
        """
        return self.owner

    def getPage(self):
        """ 
        Returns:
            The name of the page to which this schedule belongs to.
        """
        return self.page

    def isObsolete(self):
        """ 
        Returns:
            Returns true if the schedule has been marked as obsolete.
        """
        return self.obsolete

    def getInheritsFromUID(self):
        """ 
        Returns:
            Returns the unique identifier of the schedule from which this schedule has inherited from.
        """
        return self.inheritsFromUID

    def __eq__(self, another):
        """ Two schedules are equal if they have the same uid.
           
        Args:
            self (Schedule): this Schedule instance.
            another (Schedule or str): another Schedule or a string. 
        Returns:
            True if self and another uid are equal or if another is a string whose value is the self.getUID().
        """
        if isinstance(self, another.__class__):
            areEqual = (self.getUID() == another.getUID())
        else:
            areEqual = (self.getUID() == str(another))
        return areEqual

    def __cmp__(self, another):
        """ See __eq__
        """
        return (self == another) 

    def __hash__(self):
        """ The class is univocally identified by the uid.

        Returns:
            The uid.
        """
        return getUID()

    def __str__(self):
        """ Returns a string representation of a schedule.
            
        Returns:
            A string representation of a schedule which consists of the uid followed by the name,
        description and owner username.
        """
        return "{0} {1} {2} (owner:{3})".format(self.uid, self.name, self.description, self.owner) 

