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
__date__ = "22/11/2017"

##
# Standard imports
##
import logging

##
# Project imports
##
from variable import Variable

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class VariableEnum(Variable):
    """ Describes a hieratika variable enum Variable.
        A VariableEnum is a Variable which accepts as value only a predefinied list of choices (see getChoices).
    """

    def __init__(self, name, alias, description = "", vtype = "", permissions = [], numberOfElements = [], value = [], validations = [], lockVariable = "", choices = []):
        """ Constructs a new VariableEnum object.
        
        Args:
            name (str): see Variable.__init__
            alias (str): see Variable.__init__
            description (str): see Variable.__init__
            vtype (str): see Variable.__init__
            numberOfElements ([int]): see Variable.__init__
            permissions (str): see Variable.__init__
            value (str): see Variable.__init__
            validations ([str]): see Variable.__init__
            lockVariable ([str]): see Variable.__init__
            choices ([str]): list of possible values that can be assigned to this variable.
        """
        super(VariableEnum, self).__init__(name, alias, description, vtype, permissions, numberOfElements, value, validations)
        self.validations = validations
        self.choices = choices

    def getChoices(self):
        """ Only meaningful for enum types.
        
        Returns:
            The list of possible enum choices.
        """
        return self.choices      

    def setChoices(self, choices):
        """ Set the available choices (only meaningful for enum types)
        
        Args:
            choices ([str]): the list of available choices for the enum.
        """
        self.choices = choices

    def asSerializableDict(self):
        """ 
        Returns:
            A json serializable representation of the VariableEnum which serialises all of its properties and Variable members (see Variable.asSerializableDict) together with the available choices (see getChoices).
        """
        variable = super(VariableEnum, self).asSerializableDict()
        variable["choices"] = map(str, self.getChoices())
        return variable

