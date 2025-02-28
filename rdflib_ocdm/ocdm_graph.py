#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2023 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.

from __future__ import annotations

from typing import TYPE_CHECKING

import rdflib
import rdflib.plugin as plugin
from rdflib.exceptions import ParserError
from rdflib.parser import InputSource, Parser, create_input_source

if TYPE_CHECKING:
    _SubjectType = Node
    _PredicateType = Node
    _ObjectType = Node
    _TripleType = Tuple["_SubjectType", "_PredicateType", "_ObjectType"]
    from typing import (IO, TYPE_CHECKING, Any, BinaryIO, List, Optional, TextIO,
                        Union, List, Tuple)

import pathlib
from copy import deepcopy
from datetime import datetime, timedelta, timezone

from rdflib import ConjunctiveGraph, Graph, URIRef
from rdflib.term import Node
from rdflib_ocdm.counter_handler.counter_handler import CounterHandler
from rdflib_ocdm.prov.prov_entity import ProvEntity
from rdflib_ocdm.prov.provenance import OCDMProvenance
from rdflib_ocdm.prov.snapshot_entity import SnapshotEntity


class OCDMGraphCommons():
    def __init__(self, counter_handler: CounterHandler):
        self.__merge_index = dict()
        self.__entity_index = dict()
        self.all_entities = set()
        self.provenance = OCDMProvenance(self, counter_handler)

    def preexisting_finished(self: Graph|ConjunctiveGraph|OCDMGraphCommons, resp_agent: str = None, primary_source: str = None, c_time: str = None):
        self.preexisting_graph = deepcopy(self)
        for subject in self.subjects(unique=True):
            self.entity_index[subject] = {'to_be_deleted': False, 'is_restored': False, 'resp_agent': resp_agent, 'source': primary_source}
            self.all_entities.add(subject)
            count = self.provenance.counter_handler.read_counter(subject)
            if count == 0:
                if c_time is None:
                    cur_time: str = (datetime.now(tz=timezone.utc).replace(microsecond=0) - timedelta(seconds=5)).isoformat(sep="T")
                else:
                    cur_time: str = (datetime.fromtimestamp(c_time, tz=timezone.utc).replace(microsecond=0) - timedelta(seconds=5)).isoformat(sep="T")
                new_snapshot: SnapshotEntity = self.provenance._create_snapshot(subject, cur_time)
                new_snapshot.has_description(f"The entity '{str(subject)}' has been created.")

    def merge(self: Graph|ConjunctiveGraph|OCDMGraphCommons, res: URIRef, other: URIRef):
        triples_list: List[Tuple] = list(self.triples((None, None, other)))
        for triple in triples_list:
            self.remove(triple)
            new_triple = (triple[0], triple[1], res)
            self.add(new_triple)
        triples_list: List[Tuple] = list(self.triples((other, None, None)))
        for triple in triples_list:
            self.remove(triple)
        self.__merge_index.setdefault(res, set()).add(other)
        self.entity_index[other]['to_be_deleted'] = True
    
    def mark_as_deleted(self, res: URIRef) -> None:
        self.entity_index[res]['to_be_deleted'] = True

    def mark_as_restored(self, res: URIRef) -> None:
        """
        Marks an entity as being restored after deletion.
        This will:
        1. Set is_restored flag to True in the entity_index
        2. Set to_be_deleted flag to False
        
        :param res: The URI reference of the entity to restore
        :type res: URIRef
        :return: None
        """
        if res in self.entity_index:
            self.entity_index[res]['is_restored'] = True
            self.entity_index[res]['to_be_deleted'] = False

    @property
    def merge_index(self) -> dict:
        return self.__merge_index

    @property
    def entity_index(self) -> dict:
        return self.__entity_index
    
    def generate_provenance(self, c_time: float = None) -> None:
        return self.provenance.generate_provenance(c_time)
    
    def get_entity(self, res: str) -> Optional[SnapshotEntity]:
        return self.provenance.get_entity(res)
    
    def commit_changes(self):
        self.__merge_index = dict()
        self.__entity_index = dict()
        self.preexisting_graph = deepcopy(self)
    
    def get_provenance_graphs(self) -> ConjunctiveGraph:
        prov_g = ConjunctiveGraph()
        for _, prov_entity in self.provenance.res_to_entity.items():
            for triple in prov_entity.g.triples((None, None, None)):
                prov_g.add((triple[0], triple[1], triple[2], URIRef(prov_entity.prov_subject + '/prov/')))
        return prov_g

class OCDMGraph(OCDMGraphCommons, Graph):
    def __init__(self, counter_handler: CounterHandler = None):
        Graph.__init__(self)
        self.preexisting_graph = Graph()
        OCDMGraphCommons.__init__(self, counter_handler)

    def add(self, triple: "_TripleType", resp_agent = None, primary_source = None):
        """Add a triple with self as context"""
        s, p, o = triple
        assert isinstance(s, Node), "Subject %s must be an rdflib term" % (s,)
        assert isinstance(p, Node), "Predicate %s must be an rdflib term" % (p,)
        assert isinstance(o, Node), "Object %s must be an rdflib term" % (o,)
        self._Graph__store.add((s, p, o), self, quoted=False)
        
        # Add the subject to all_entities if it's not already present
        if s not in self.all_entities:
            self.all_entities.add(s)
        
        if s not in self.entity_index:
            self.entity_index[s] = {'to_be_deleted': False, 'is_restored': False, 'resp_agent': resp_agent, 'source': primary_source}
        
        return self

    def parse(
        self,
        source: Optional[
            Union[IO[bytes], TextIO, InputSource, str, bytes, pathlib.PurePath]
        ] = None,
        publicID: Optional[str] = None,  # noqa: N803
        format: Optional[str] = None,
        location: Optional[str] = None,
        file: Optional[Union[BinaryIO, TextIO]] = None,
        data: Optional[Union[str, bytes]] = None,
        resp_agent: URIRef = None,
        primary_source: URIRef = None,
        **args: Any,
    ) -> "Graph":
        """
        Parse an RDF source adding the resulting triples to the Graph.

        The source is specified using one of source, location, file or data.

        .. caution::

           This method can access directly or indirectly requested network or
           file resources, for example, when parsing JSON-LD documents with
           ``@context`` directives that point to a network location.

           When processing untrusted or potentially malicious documents,
           measures should be taken to restrict network and file access.

           For information on available security measures, see the RDFLib
           :doc:`Security Considerations </security_considerations>`
           documentation.

        :Parameters:

          - ``source``: An InputSource, file-like object, or string. In the case
            of a string the string is the location of the source.
          - ``location``: A string indicating the relative or absolute URL of
            the source. Graph's absolutize method is used if a relative location
            is specified.
          - ``file``: A file-like object.
          - ``data``: A string containing the data to be parsed.
          - ``format``: Used if format can not be determined from source, e.g.
            file extension or Media Type. Defaults to text/turtle. Format
            support can be extended with plugins, but "xml", "n3" (use for
            turtle), "nt" & "trix" are built in.
          - ``publicID``: the logical URI to use as the document base. If None
            specified the document location is used (at least in the case where
            there is a document location).

        :Returns:

          - self, the graph instance.

        Examples:

        >>> my_data = '''
        ... <rdf:RDF
        ...   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        ...   xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
        ... >
        ...   <rdf:Description>
        ...     <rdfs:label>Example</rdfs:label>
        ...     <rdfs:comment>This is really just an example.</rdfs:comment>
        ...   </rdf:Description>
        ... </rdf:RDF>
        ... '''
        >>> import os, tempfile
        >>> fd, file_name = tempfile.mkstemp()
        >>> f = os.fdopen(fd, "w")
        >>> dummy = f.write(my_data)  # Returns num bytes written
        >>> f.close()

        >>> g = Graph()
        >>> result = g.parse(data=my_data, format="application/rdf+xml")
        >>> len(g)
        2

        >>> g = Graph()
        >>> result = g.parse(location=file_name, format="application/rdf+xml")
        >>> len(g)
        2

        >>> g = Graph()
        >>> with open(file_name, "r") as f:
        ...     result = g.parse(f, format="application/rdf+xml")
        >>> len(g)
        2

        >>> os.remove(file_name)

        >>> # default turtle parsing
        >>> result = g.parse(data="<http://example.com/a> <http://example.com/a> <http://example.com/a> .")
        >>> len(g)
        3

        """

        source = create_input_source(
            source=source,
            publicID=publicID,
            location=location,
            file=file,
            data=data,
            format=format,
        )
        if format is None:
            format = source.content_type
        could_not_guess_format = False
        if format is None:
            if (
                hasattr(source, "file")
                and getattr(source.file, "name", None)
                and isinstance(source.file.name, str)
            ):
                format = rdflib.util.guess_format(source.file.name)
            if format is None:
                format = "turtle"
                could_not_guess_format = True
        parser = plugin.get(format, Parser)()
        try:
            # TODO FIXME: Parser.parse should have **kwargs argument.
            parser.parse(source, self, **args)
        except SyntaxError as se:
            if could_not_guess_format:
                raise ParserError(
                    "Could not guess RDF format for %r from file extension so tried Turtle but failed."
                    "You can explicitly specify format using the format argument."
                    % source
                )
            else:
                raise se
        finally:
            if source.auto_close:
                source.close()

        for subject in self.subjects(unique=True):
            if subject not in self.all_entities:
                self.all_entities.add(subject)

            if subject not in self.entity_index:
                self.entity_index[subject] = {'to_be_deleted': False, 'is_restored': False, 'resp_agent': resp_agent, 'source': primary_source}

        return self

class OCDMConjunctiveGraph(OCDMGraphCommons, ConjunctiveGraph):
    def __init__(self, counter_handler: CounterHandler = None):
        ConjunctiveGraph.__init__(self)
        self.preexisting_graph = ConjunctiveGraph()
        OCDMGraphCommons.__init__(self, counter_handler)

    def add(
        self,
        triple_or_quad: Union[
            Tuple["_SubjectType", "_PredicateType", "_ObjectType", Optional[Any]],
            "_TripleType",
        ],
        resp_agent = None, 
        primary_source = None
    ) -> "ConjunctiveGraph":
        """
        Add a triple or quad to the store.

        if a triple is given it is added to the default context
        """

        s, p, o, c = self._spoc(triple_or_quad, default=True)

        _assertnode(s, p, o)

        # type error: Argument "context" to "add" of "Store" has incompatible type "Optional[Graph]"; expected "Graph"
        self.store.add((s, p, o), context=c, quoted=False)  # type: ignore[arg-type]

        # Add the subject to all_entities if it's not already present
        if s not in self.all_entities:
            self.all_entities.add(s)

        if s not in self.entity_index:
            self.entity_index[s] = {'to_be_deleted': False, 'is_restored': False, 'resp_agent': resp_agent, 'source': primary_source}

        return self

    def parse(
        self,
        source: Optional[
            Union[IO[bytes], TextIO, InputSource, str, bytes, pathlib.PurePath]
        ] = None,
        publicID: Optional[str] = None,  # noqa: N803
        format: Optional[str] = None,
        location: Optional[str] = None,
        file: Optional[Union[BinaryIO, TextIO]] = None,
        data: Optional[Union[str, bytes]] = None,
        resp_agent: URIRef = None,
        primary_source: URIRef = None,
        **args: Any,
    ) -> "Graph":
        """
        Parse source adding the resulting triples to its own context
        (sub graph of this graph).

        See :meth:`rdflib.graph.Graph.parse` for documentation on arguments.

        :Returns:

        The graph into which the source was parsed. In the case of n3
        it returns the root context.

        .. caution::

           This method can access directly or indirectly requested network or
           file resources, for example, when parsing JSON-LD documents with
           ``@context`` directives that point to a network location.

           When processing untrusted or potentially malicious documents,
           measures should be taken to restrict network and file access.

           For information on available security measures, see the RDFLib
           :doc:`Security Considerations </security_considerations>`
           documentation.
        """

        source = create_input_source(
            source=source,
            publicID=publicID,
            location=location,
            file=file,
            data=data,
            format=format,
        )

        # NOTE on type hint: `xml.sax.xmlreader.InputSource.getPublicId` has no
        # type annotations but given that systemId should be a string, and
        # given that there is no specific mention of type for publicId, it
        # seems reasonable to assume it should also be a string. Furthermore,
        # create_input_source will ensure that publicId is not None, though it
        # would be good if this guarantee was made more explicit i.e. by type
        # hint on InputSource (TODO/FIXME).
        g_id: str = publicID and publicID or source.getPublicId()
        if not isinstance(g_id, Node):
            g_id = URIRef(g_id)

        context = Graph(store=self.store, identifier=g_id)
        context.remove((None, None, None))  # hmm ?
        context.parse(source, publicID=publicID, format=format, **args)
        # TODO: FIXME: This should not return context, but self.

        for subject in self.subjects(unique=True):
            if subject not in self.all_entities:
                self.all_entities.add(subject)

            if subject not in self.entity_index:
                self.entity_index[subject] = {'to_be_deleted': False, 'is_restored': False, 'resp_agent': resp_agent, 'source': primary_source}

        return context

def _assertnode(*terms):
    for t in terms:
        assert isinstance(t, Node), "Term %s must be an rdflib term" % (t,)
    return True