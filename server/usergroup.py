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
class UserGroup(object):
    """ Describes a psps user group.
       
        Users that belong to the same group share the same access rights. 
    """

    def __init__(self, name):
        """ Constructs a UserGroup object against a given group name.
        
        Args:
            name(string): the group name.
        """
        self.name = name

    def getName(self):
        """ Returns the group name
       
        Returns: 
            The group name.
        """
        return self.name

    def __eq__(self, another):
        """ Two groups are equal if they have the same group name
            
        Returns:
            True if self and another group names are equal.
        """
        if isinstance(self, another.__class__):
            areEqual = (self.getName() == another.getName())
        else:
            areEqual = (self.getName() == str(another))
        return areEqual

    def __hash__(self):
        """ The class is univocally identified by the group name.

        Returns:
            The group name.
        """
        return getName()

    def __str__(self):
        """ Gets the group name.
        
        Returns:
            The group name.
        """
        return self.getName()

