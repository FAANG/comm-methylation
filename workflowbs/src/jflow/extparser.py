#
# Copyright (C) 2015 INRA
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import os

from jflow.component import Component

class ExternalParser(object):
    
    def parse_directory(self, component_directory):
        components = []
        for component_file in os.listdir(component_directory):
            try:
                components.append(self.parse(os.path.join(component_directory, component_file)))
            except: pass
        return components
    
    def parse(self, component_file):
        raise NotImplementedError("The ExternalParser.parser() function has to be implemented!")

    def build_component(self, component_name, fn_define_parameters, **kwargs):
        """
            Build and return an external component. The 3 methods get_abstraction, get_command and define_parameters must
            be defined. Any other attribut can be added to the class definition using **kwargs
            @param component_name: new component type name
            @param fn_define_parameters: callable which overload the  define_parameters function of component
            @param kwargs: any other method or attribut that must be added or overloaded in this new class definition
        """
        assert hasattr(fn_define_parameters, '__call__'), "The fn_define_parameters attribut must be callable"
        
        options = {'define_parameters'  : fn_define_parameters }
        
        if kwargs :
            for key, val in list(kwargs.items()) :
                options[key] = val
        
        ComponentType = type(component_name, (_SerializableNestedComponent,),options)
        
        setattr(_ExternalComponentFactory, component_name, ComponentType)

        return ComponentType


class _NestedClassGetter(object):
    """
        Altered version of what stands here : 
        http://stackoverflow.com/questions/1947904/how-can-i-pickle-a-nested-class-in-python
        
        _NestedClassGetter is a callable that will be called by __reduce__ for serialization 
        and that will provide us with an instance of our nested class
        
        used for nested object serialization.
        When called with the containing class as the first argument,
        and the name of the nested class as the second argument,
        returns an instance of the nested class.
    """
    def __call__(self, containing_class, class_name):
        nested_class = getattr(containing_class, class_name)

        # make an instance of a simple object, for which we can change the __class__ later on.
        nested_instance = _NestedClassGetter()

        # set the class of the instance, the __init__ will never be called on the class
        # but the original state will be set later on by pickle.
        nested_instance.__class__ = nested_class
        return nested_instance

class _SerializableNestedComponent(Component):
    """
        the component class used to create our serializable components
    """
    def __init__(self):
        Component.__init__(self)

    def __set_state__(self, state):
        self.__dict__ = state.copy()

    def __reduce__(self):
        state = self.__dict__.copy()
        return (_NestedClassGetter(), (_ExternalComponentFactory, self.__class__.__name__, ),  state, ) 

class _ExternalComponentFactory(object): 
    """
        _ExternalComponentFactory will contain all created external component types
    """
    pass


class _serializable_nested_function(object):
    """
        callable object used for the serialization of custom types
    """
    
    def __init__(self):
        self._container = object.__class__

    def __set_state__(self, state):
        self.__dict__ = state.copy()

    def __reduce__(self):
        state = self.__dict__.copy()
        return (_NestedClassGetter(), (self._container, self.__class__.__name__, ),  state, ) 
