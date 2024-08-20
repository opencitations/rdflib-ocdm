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

if TYPE_CHECKING:
    _SubjectType = Node
    _PredicateType = Node
    _ObjectType = Node
    _TripleType = Tuple["_SubjectType", "_PredicateType", "_ObjectType"]
    from typing import List, Tuple, Optional, Union, Any

from copy import deepcopy
from datetime import datetime, timezone, timedelta

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

    def preexisting_finished(self: Graph|ConjunctiveGraph|OCDMGraphCommons, resp_agent: str = None, source: str = None, c_time: str = None):
        self.preexisting_graph = deepcopy(self)
        for subject in self.subjects(unique=True):
            self.__entity_index[subject] = {'to_be_deleted': False, 'resp_agent': resp_agent, 'source': source}
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
        self.__entity_index[other]['to_be_deleted'] = True
    
    def mark_as_deleted(self, res: URIRef) -> None:
        self.__entity_index[res]['to_be_deleted'] = True

    @property
    def merge_index(self) -> dict:
        return self.__merge_index

    @property
    def entity_index(self) -> dict:
        return self.__entity_index
    
    def generate_provenance(self, c_time: float = None) -> None:
        return self.provenance.generate_provenance(c_time)
    
    def get_entity(self, res: str) -> Optional[ProvEntity]:
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

    def add(self, triple: "_TripleType"):
        """Add a triple with self as context"""
        s, p, o = triple
        assert isinstance(s, Node), "Subject %s must be an rdflib term" % (s,)
        assert isinstance(p, Node), "Predicate %s must be an rdflib term" % (p,)
        assert isinstance(o, Node), "Object %s must be an rdflib term" % (o,)
        self._Graph__store.add((s, p, o), self, quoted=False)
        
        # Add the subject to all_entities if it's not already present
        if s not in self.all_entities:
            self.all_entities.add(s)
        
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

        return self

def _assertnode(*terms):
    for t in terms:
        assert isinstance(t, Node), "Term %s must be an rdflib term" % (t,)
    return True