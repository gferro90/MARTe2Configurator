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
class Page(object):
    """ Describes a hieratika page.

        A page is a container for a list of Variables.
       
        Typically a page is also an html user-interface which contains widgets that are identified by a unique key (which in turn corresponds to a given variable).
    """

    def __init__(self, name, url, description):
        """ Constructs a Page object against a given name, url and description.
        
        Args:
            name (str): the page name.
            url (str): the page url. It shall not contain the .html suffix.
            description (str): the page description.
        """
        self.name = name
        self.url = url
        self.description = description

    def getName(self):
        """ Returns the page name. This must be unique in whole psps environment.
       
        Returns: 
            The page name.
        """
        return self.name

    def getUrl(self):
        """ Returns the page url.
       
        Returns: 
            The page url.
        """
        return self.url

    def getDescription(self):
        """ Returns the page description.
       
        Returns: 
            The page description.
        """
        return self.description


    def __eq__(self, another):
        """ Two pages are equal if they have the same name
            
        Returns:
            True if self and another page names are equal.
        """
        if isinstance(self, another.__class__):
            areEqual = (self.getName() == another.getName())
        else:
            areEqual = (self.getName() == str(another))
        return areEqual

    def __hash__(self):
        """ The class is univocally identified by the page name.

        Returns:
            The page name.
        """
        return getName()

    def __str__(self):
        """ Gets the page name.
        
        Returns:
            The page name.
        """
        return self.getName()

