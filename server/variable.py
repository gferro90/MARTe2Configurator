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

##
# Logger configuration
##
log = logging.getLogger("{0}".format(__name__))

##
# Class definition
##
class Variable(object):
    """ Describes a hieratika variable.
        Variables may contain other variables (i.e. they can represent a member of a structure), where their name is the key of a __dict__ representation of the Variable object.
    """

    def __init__(self, name, alias, description = "", vtype = "", permissions = [], numberOfElements = [], value = [], validations = [], lockVariable = ""):
        """ Constructs a new Variable object.
        
        Args:
            name (str): the variable name. This name can either encode a @ separated path of a name which univocally identifies the variable in the system; or it can be the relative name of the variable when it represents a member of another variable.
            alias (str): free format text which provides a meaningful name to the variable.
            description (str): one-line description of the variable.
            vtype (str): the variable type as one of: uint8, int8, uint16, int16, uint32, int32, uint64, int64, string, enum, lock, schedule, library.
            numberOfElements ([int]): as an array where each entry contains the number of elements on any given direction. 
            permissions (str): user groups that are allowed to change this variable.
            value (str): string encoded variable value.
            validations ([str]): list of validation expresssions that are associated to this variable. The format is to be interpreted and parsed by the client applications (the current format is any equation in the form EXPR OP EXPR. The EXPRs are either a mathematical expression containing at least the name of this variable inside single quotes. It may also contain the name of other variables and constant values. The OP is one of the following operators: <, <=, ==, >, >=. ). An example is 'VAR1' <= (2 * 'VAR2'), where VAR1 = self.getName().
            lockVariable (str): name of another variable (with type lock) which sets if this variable value can be changed.
        """
        self.name = name
        self.alias = alias 
        self.description = description
        self.vtype = vtype 
        self.permissions = permissions
        self.numberOfElements = numberOfElements
        self.value = value
        self.parent = None
        self.isStruct = False
        self.members = {}
        self.validations = validations
        self.lockVariable = lockVariable

    def getName(self):
        """ 
        Returns: 
            The variable name (see __init__).
        """
        return self.name

    def setName(self, name):
        """ Sets the variable name.
        
        Args:
            name(str): the new variable name.
        """
        self.name = name

    def getAlias(self):
        """ 
        Returns: 
            The variable alias (see __init__).
        """
        return self.alias

    def getType(self):
        """
        Returns:
            The variable type (see __init__)
        """
        return self.vtype 

    def getNumberOfElements(self):
        """
        Returns:
            The variable numberOfElements(see __init__)
        """
        return self.numberOfElements

    def getDescription(self):
        """
        Returns:
            The variable description(see __init__)
        """
        return self.description

    def getParent(self):
        """
        Returns:
            The variable parent (i.e. in the case of structure, the variable which is owner of this member variable"
        """
        return self.parent

    def getPermissions(self):
        """
        Returns:
            The variable permissions(see __init__)
        """
        return self.permissions

    def getValidations(self):
        """
        Returns:
            The variable validations(see __init__)
        """
        return self.validations

    def setValidations(self, validations):
        """ Sets the validations functions for the variable (see __init__)
        
        Args:
            validations ([str]): array of validation functions that are associated to this variable.
        """
        self.validations = validations

    def getLockVariable(self):
        """
        Returns:
            The variable lock variable(see __init__)
        """
        return self.lockVariable

    def setLockVariable(self, lockVariable):
        """ Sets this variable lock variable (see __init__)
        
        Args:
            lockVariable (str): the name of the variable which will set the locking state of this variable.
        """
        self.lockVariable = lockVariable


    def setValue(self, value):
        """ Sets the variables value.
        
        Args:
            value (str): value to be updated.
        """
        self.value = value

    def getValue(self):
        """
        Returns:
            The variable value(see __init__)
        """
        return self.value

    def getAbsoluteName(self):
        """
        Returns:
            The a @ separated name which univocally identifies the variable in the system. Each @ separates a substructure variable.
        """
        varName = self.name
        p = self.parent
        while (p is not None):
            varName = p.getName() + "@" + varName
            p = p.getParent()
        return varName

    def setParent(self, parent):
        """ Sets the parent variable of this variable, i.e. the structured variable only this member variable.
        
        Args:
        	parent (Variable): the parent variable.
        """
        self.parent = parent

    def addMember(self, variable):
        """ Adds a variable a member of this variable. IsStruct() will return True
        
        Args:
        	variable (Variable): the member variable.
        """
        variable.setParent(self)
        self.members[variable.getName()] = variable
        self.isStruct = True

    def IsStruct(self):
        """ 
        Returns:
            True if this variable is a struct (or a substruct).
        """
        return self.isStruct

    def getMember(self, memberName):
        """ Gets a member variable of this variable.
        
        Args:
        	memberName (str): the name of the member variable to be retrieved.
		Returns:
        	The member variable or None if it does not exist.
        """
        try:
            member = self.members[memberName]
        except KeyError as e:
            log.critical("Could not retrieve member {0}".format(e))
            member = None
        return member

    def getMembers(self):
        """
        Returns:
            All the member variables from this variable (in the format of a dictionary [memberName][Variable]
        """
        return self.members

    def __eq__(self, another):
        """ Two Variables are equal if they have the same absolute name.
           
        Args:
            self (Variable): this variable instance.
            another (Variable or str): another Variable or a string. 
        Returns:
            True if self and another Variable are equal or if another is a string whose value is the self.getAbsoluteName().
        """
        if isinstance(self, another.__class__):
            areEqual = (self.getAbsoluteName() == another.getAbsoluteName())
        else:
            areEqual = (self.getAbsoluteName() == str(another))
        return areEqual

    def __cmp__(self, another):
        """ See __eq__
        """
        return (self == another) 

    def __hash__(self):
        """ The class is univocally identified by the absolute name.

        Returns:
            The absolute name of the variable.
        """
        return self.getAbsoluteName()

    def __str__(self):
        """ Returns a string representation of a Variable.
            
		Returns:
        	A string representation of a Variable which consists of the absolute name followed by the value.
        """
        return "{0} [{1}] : {2}".format(self.getAbsoluteName(), self.getNumberOfElements(), self.getValue()) 

    def asSerializableDict(self):
        """ 
        Returns:
            A recursive json serializable representation of the Variable which serialises all of its properties and Variable members.
            Note that if a Variable contains members, then it is considered to a structure holder and thus it will not contain a value nor a numberOfElements.
        """
        variable = {
            "name": self.getName(),
            "alias": self.getAlias(),
            "type": self.getType(),
            "description": self.getDescription(),
            "permissions": map(str, self.getPermissions()),
            "validations": map(str, self.getValidations()),
            "isStruct": self.isStruct,
            "lockVariable": self.lockVariable
        }
        if (len(self.members) == 0):
            variable["numberOfElements"] = self.getNumberOfElements()
            variable["value"] = self.getValue()

        for memberName in self.members:
            variable[memberName] = self.members[memberName].asSerializableDict()
        return variable

