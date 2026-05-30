#!/usr/bin/python

# SPDX-FileCopyrightText: 2023-2025 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

from __future__ import annotations

from typing import TYPE_CHECKING

import rdflib
import rdflib.plugin as plugin
from rdflib.exceptions import ParserError
from rdflib.parser import InputSource, Parser, create_input_source

if TYPE_CHECKING:
    from typing import IO, BinaryIO, Optional, TextIO, Tuple, Union

    from rdflib.term import Node as _Node

    _TripleType = Tuple[_Node, _Node, _Node]

import pathlib
import warnings
from copy import deepcopy
from datetime import datetime, timedelta, timezone

from rdflib import Dataset, Graph, URIRef
from rdflib.term import Node

from rdflib_ocdm.counter_handler.counter_handler import CounterHandler
from rdflib_ocdm.graph_utils import _extract_graph_iri, _extract_graph_iri_from_context
from rdflib_ocdm.prov.provenance import OCDMProvenance
from rdflib_ocdm.prov.snapshot_entity import SnapshotEntity


class OCDMGraphCommons:
    preexisting_graph: Graph | Dataset

    def __init__(self, counter_handler: CounterHandler):
        self.__merge_index: dict = dict()
        self.__entity_index: dict = dict()
        self.all_entities: set = set()
        self.provenance = OCDMProvenance(self, counter_handler)

    def preexisting_finished(self, resp_agent: str | None = None, primary_source: str | None = None, c_time: str | None = None) -> None:
        assert isinstance(self, (Graph, Dataset))
        self.preexisting_graph = deepcopy(self)

        unique_subjects: set = set()
        if isinstance(self, Dataset):
            for s, _, _, _ in self.quads((None, None, None, None)):
                unique_subjects.add(s)
        else:
            unique_subjects = set(self.subjects(unique=True))

        for subject in unique_subjects:
            existing_graph_iri = self.entity_index.get(subject, {}).get('graph_iri')
            self.entity_index[subject] = {'to_be_deleted': False, 'is_restored': False, 'resp_agent': resp_agent, 'source': primary_source, 'graph_iri': existing_graph_iri}

            if isinstance(self, Dataset) and existing_graph_iri is None:
                self.entity_index[subject]['graph_iri'] = _extract_graph_iri(self, subject)

            self.all_entities.add(subject)
            count = self.provenance.counter_handler.read_counter(str(subject))
            if count == 0:
                if c_time is None:
                    cur_time = (datetime.now(tz=timezone.utc).replace(microsecond=0) - timedelta(seconds=5)).isoformat(sep="T")
                else:
                    cur_time = (datetime.fromtimestamp(float(c_time), tz=timezone.utc).replace(microsecond=0) - timedelta(seconds=5)).isoformat(sep="T")
                new_snapshot: SnapshotEntity = self.provenance._create_snapshot(URIRef(str(subject)), cur_time)
                new_snapshot.has_description(f"The entity '{str(subject)}' has been created.")

    def merge(self, res: URIRef, other: URIRef) -> None:
        assert isinstance(self, (Graph, Dataset))
        other_graph_iri = None
        if isinstance(self, Dataset):
            other_graph_iri = _extract_graph_iri(self, other)

            quads_list = list(self.quads((None, None, other, None)))
            for s, p, o, c in quads_list:
                self.remove((s, p, o, c))  # type: ignore[arg-type]
                self.add((s, p, res, c))  # type: ignore[arg-type]
            quads_list_del = list(self.quads((other, None, None, None)))
            for s, p, o, c in quads_list_del:
                self.remove((s, p, o, c))  # type: ignore[arg-type]
        elif isinstance(self, Graph):
            triples_list = list(self.triples((None, None, other)))
            for triple in triples_list:
                self.remove(triple)
                new_triple = (triple[0], triple[1], res)
                self.add(new_triple)
            triples_list_del = list(self.triples((other, None, None)))
            for triple in triples_list_del:
                self.remove(triple)

        self._OCDMGraphCommons__merge_index.setdefault(res, set()).add(other)
        if other not in self.entity_index:
            self.entity_index[other] = {'to_be_deleted': False, 'is_restored': False, 'resp_agent': None, 'source': None, 'graph_iri': other_graph_iri}
        else:
            if other_graph_iri is not None and self.entity_index[other].get('graph_iri') is None:
                self.entity_index[other]['graph_iri'] = other_graph_iri
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
    
    def generate_provenance(self, c_time: float | None = None) -> None:
        return self.provenance.generate_provenance(c_time)

    def get_entity(self, res: str) -> SnapshotEntity | None:
        entity = self.provenance.get_entity(res)
        if isinstance(entity, SnapshotEntity):
            return entity
        return None
    
    def commit_changes(self) -> None:
        self._OCDMGraphCommons__merge_index = dict()
        self._OCDMGraphCommons__entity_index = dict()
        assert isinstance(self, (Graph, Dataset))
        self.preexisting_graph = deepcopy(self)

    def get_provenance_graphs(self) -> Dataset:
        prov_g = Dataset()
        for _, prov_entity in self.provenance.res_to_entity.items():
            for triple in prov_entity.g.triples((None, None, None)):
                prov_g.add((triple[0], triple[1], triple[2], URIRef(prov_entity.prov_subject + '/prov/')))  # type: ignore[arg-type]
        return prov_g

class OCDMGraph(OCDMGraphCommons, Graph):
    def __init__(self, counter_handler: CounterHandler | None = None):
        Graph.__init__(self)
        self.preexisting_graph: Graph | Dataset = Graph()
        OCDMGraphCommons.__init__(self, counter_handler)  # type: ignore[arg-type]

    def add(self, triple: _TripleType, resp_agent: object = None, primary_source: object = None):  # type: ignore[override]
        s, p, o = triple
        assert isinstance(s, Node), "Subject %s must be an rdflib term" % (s,)
        assert isinstance(p, Node), "Predicate %s must be an rdflib term" % (p,)
        assert isinstance(o, Node), "Object %s must be an rdflib term" % (o,)
        self.store.add((s, p, o), self, quoted=False)
        
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
        resp_agent: URIRef | None = None,
        primary_source: URIRef | None = None,
        **args: object,
    ) -> Graph:
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
            _file = getattr(source, "file", None)
            if _file is not None and getattr(_file, "name", None) and isinstance(_file.name, str):
                format = rdflib.util.guess_format(_file.name)
            if format is None:
                format = "turtle"
                could_not_guess_format = True
        parser = plugin.get(format, Parser)()
        try:
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

class OCDMDataset(OCDMGraphCommons, Dataset):
    def __init__(self, counter_handler: CounterHandler | None = None):
        Dataset.__init__(self)
        self.preexisting_graph: Graph | Dataset = Dataset()
        OCDMGraphCommons.__init__(self, counter_handler)  # type: ignore[arg-type]

    def __deepcopy__(self, memo):
        new_graph = OCDMDataset(counter_handler=self.provenance.counter_handler)

        # Copy graph data
        for quad in self.quads((None, None, None, None)):
            new_graph.add(quad)  # type: ignore[arg-type]

        # Copy entity index and metadata
        for key, value in self.entity_index.items():
            new_graph.entity_index[key] = value.copy()
        new_graph.all_entities = self.all_entities.copy()
        for key, value in self.merge_index.items():
            new_graph._OCDMGraphCommons__merge_index[key] = value.copy()  # type: ignore[attr-defined]

        return new_graph

    def add(  # type: ignore[override]
        self,
        triple_or_quad: tuple[Node, Node, Node] | tuple[Node, Node, Node, Graph | None],
        resp_agent: object = None,
        primary_source: object = None,
    ) -> Dataset:

        s, p, o, c = self._spoc(triple_or_quad, default=True)

        _assertnode(s, p, o)

        # type error: Argument "context" to "add" of "Store" has incompatible type "Optional[Graph]"; expected "Graph"
        self.store.add((s, p, o), context=c, quoted=False)  # type: ignore[arg-type]

        # Add the subject to all_entities if it's not already present
        if s not in self.all_entities:
            self.all_entities.add(s)

        if s not in self.entity_index:
            self.entity_index[s] = {'to_be_deleted': False, 'is_restored': False, 'resp_agent': resp_agent, 'source': primary_source, 'graph_iri': None}

        # Store graph_iri in entity_index for later retrieval
        # We already have the context from _spoc, use it directly for efficiency
        if self.entity_index[s]['graph_iri'] is None:
            self.entity_index[s]['graph_iri'] = _extract_graph_iri_from_context(c)

        return self

    def parse(  # type: ignore[override]
        self,
        source: IO[bytes] | TextIO | InputSource | str | bytes | pathlib.PurePath | None = None,
        publicID: str | None = None,  # noqa: N803
        format: str | None = None,
        location: str | None = None,
        file: BinaryIO | TextIO | None = None,
        data: str | bytes | None = None,
        resp_agent: URIRef | None = None,
        primary_source: URIRef | None = None,
        **args: object,
    ) -> Graph:
        source = create_input_source(
            source=source,
            publicID=publicID,
            location=location,
            file=file,
            data=data,
            format=format,
        )

        g_id = publicID or source.getPublicId() or ""
        if not isinstance(g_id, Node):
            g_id = URIRef(g_id)

        context = Graph(store=self.store, identifier=g_id)
        context.remove((None, None, None))  # type: ignore[arg-type]
        context.parse(source, publicID=publicID, format=format, **args)  # type: ignore[arg-type]
        # TODO: FIXME: This should not return context, but self.

        unique_subjects = set()
        for s, _, _, _ in self.quads((None, None, None, None)):
            unique_subjects.add(s)

        for subject in unique_subjects:
            if subject not in self.all_entities:
                self.all_entities.add(subject)

            if subject not in self.entity_index:
                self.entity_index[subject] = {'to_be_deleted': False, 'is_restored': False, 'resp_agent': resp_agent, 'source': primary_source, 'graph_iri': None}

            # Store graph_iri for this subject by finding its context
            if 'graph_iri' not in self.entity_index[subject] or self.entity_index[subject]['graph_iri'] is None:
                self.entity_index[subject]['graph_iri'] = _extract_graph_iri(self, subject)

        return context

def _assertnode(*terms):
    for t in terms:
        assert isinstance(t, Node), "Term %s must be an rdflib term" % (t,)
    return True


# Backward compatibility alias
class OCDMConjunctiveGraph(OCDMDataset):
    """
    Deprecated: Use OCDMDataset instead.

    This class is maintained for backward compatibility only.
    OCDMConjunctiveGraph has been renamed to OCDMDataset to reflect
    the migration from the deprecated ConjunctiveGraph to Dataset.
    """
    def __init__(self, counter_handler: CounterHandler | None = None):
        warnings.warn(
            "OCDMConjunctiveGraph is deprecated, use OCDMDataset instead",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(counter_handler)