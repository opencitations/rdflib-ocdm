#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2016, Silvio Peroni <essepuntato@gmail.com>
# Copyright (c) 2023, Arcangelo Massari <arcangelo.massari@unibo.it>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.


from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from rdflib import RDF, RDFS, Graph, Literal, URIRef

from rdflib_ocdm.support import create_literal, create_type

if TYPE_CHECKING:
    from typing import ClassVar, Dict, Iterable, List, Optional

class AbstractEntity(ABC): # pragma: no cover
    """
    Abstract class which represents a generic entity. 
    It sits at the top of the entity class hierarchy.
    """

    short_name_to_type_iri: ClassVar[Dict[str, URIRef]] = {}

    def __init__(self) -> None:
        """
        Constructor of the ``AbstractEntity`` class.
        """
        self.g: Graph = Graph()
        self.res: URIRef = URIRef("")

    def remove_every_triple(self) -> None:
        """
        Remover method that removes every triple from the current entity.

        :return: None
        """
        self.g.remove((None, None, None))

    # LABEL
    def get_label(self) -> Optional[str]:
        """
        Getter method corresponding to the ``rdfs:label`` RDF predicate.

        :return: The requested value if found, None otherwise
        """
        return self._get_literal(RDFS.label)

    def create_label(self, string: str) -> None:
        """
        Setter method corresponding to the ``rdfs:label`` RDF predicate.

        **WARNING: this is a functional property, hence any existing value will be overwritten!**

        :param string: The value that will be set as the object of the property related to this method
        :type string: str
        :return: None
        """
        self.remove_label()
        self._create_literal(RDFS.label, string)

    def remove_label(self) -> None:
        """
        Remover method corresponding to the ``rdfs:label`` RDF predicate.

        :return: None
        """
        self.g.remove((self.res, RDFS.label, None))

    def _create_literal(self, p: URIRef, s: str, dt: URIRef = None, nor: bool = True) -> None:
        """
        Adds an RDF triple with a literal object inside the graph of the entity

        :param p: The predicate
        :type p: URIRef
        :param s: The string to add as a literal value
        :type s: str
        :param dt: The object's datatype, if present
        :type dt: URIRef, optional
        :param nor: Whether to normalize the graph or not
        :type nor: bool, optional
        :return: None
        """
        create_literal(self.g, self.res, p, s, dt, nor)

    # TYPE
    def get_types(self) -> List[URIRef]:
        """
        Getter method corresponding to the ``rdf:type`` RDF predicate.

        :return: A list containing the requested values if found, None otherwise
        """
        uri_list: List[URIRef] = self._get_multiple_uri_references(RDF.type)
        return uri_list

    def _create_type(self, res_type: URIRef, identifier: str = None) -> None:
        """
        Setter method corresponding to the ``rdf:type`` RDF predicate.

        :param res_type: The value that will be set as the object of the property related to this method
        :type res_type: URIRef
        :return: None
        """
        create_type(self.g, self.res, res_type, identifier)

    def remove_type(self) -> None:
        """
        Remover method corresponding to the ``rdf:type`` RDF predicate.

        :return: None
        """
        self.g.remove((self.res, RDF.type, None))

    # Overrides __str__ method
    def __str__(self) -> str:
        return str(self.res)

    def add_triples(self, iterable_of_triples: Iterable) -> None:
        """
        A utility method that allows to add a batch of triples into the graph of the entity.

        **WARNING: Only triples that have this entity as their subject will be imported!**

        :param iterable_of_triples: A collection of triples to be added to the entity
        :type iterable_of_triples: Iterable
        :return: None
        """
        for s, p, o in iterable_of_triples:
            if s == self.res:  # This guarantees that only triples belonging to the resource will be added
                self.g.add((s, p, o))

    def _get_literal(self, predicate: URIRef) -> Optional[str]:
        result: Optional[str] = None
        for o in self.g.objects(self.res, predicate):
            if type(o) == Literal:
                result = str(o)
                break
        return result

    def _get_multiple_literals(self, predicate: URIRef) -> List[str]:
        result: List[str] = []
        for o in self.g.objects(self.res, predicate):
            if type(o) == Literal:
                result.append(str(o))
        return result

    def _get_uri_reference(self, predicate: URIRef) -> Optional[URIRef]:
        result: Optional[URIRef] = None
        for o in self.g.objects(self.res, predicate):
            if type(o) == URIRef:
                result = o
                break
        return result

    def _get_multiple_uri_references(self, predicate: URIRef) -> List[URIRef]:
        result: List[URIRef] = []
        for o in self.g.objects(self.res, predicate):
            if type(o) == URIRef:
                result.append(o)
        return result