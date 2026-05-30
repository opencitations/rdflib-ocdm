#!/usr/bin/python

# SPDX-FileCopyrightText: 2016 Silvio Peroni <essepuntato@gmail.com>
# SPDX-FileCopyrightText: 2023-2025 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Tuple
    from rdflib.compare import IsomorphicGraph
    from rdflib_ocdm.ocdm_graph import OCDMGraphCommons

from rdflib import Dataset, Graph, URIRef
from rdflib.compare import graph_diff, to_isomorphic

from rdflib_ocdm.graph_utils import _extract_graph_iri
from rdflib_ocdm.support import get_entity_subgraph


def get_delete_query(data: Dataset | Graph, graph_iri: URIRef | None = None) -> Tuple[str, int]:
    num_of_statements: int = len(data)
    if num_of_statements <= 0:
        return "", 0
    else:
        statements: str = data.serialize(format="nt11").replace('\n', '')
        if graph_iri:
            delete_string: str = f"DELETE DATA {{ GRAPH <{graph_iri}> {{ {statements} }} }}"
        else:
            delete_string: str = f"DELETE DATA {{ {statements} }}"
        return delete_string, num_of_statements

def get_insert_query(data: Dataset | Graph, graph_iri: URIRef | None = None) -> Tuple[str, int]:
    num_of_statements: int = len(data)
    if num_of_statements <= 0:
        return "", 0
    else:
        statements: str = data.serialize(format="nt11").replace('\n', '')
        if graph_iri:
            insert_string: str = f"INSERT DATA {{ GRAPH <{graph_iri}> {{ {statements} }} }}"
        else:
            insert_string: str = f"INSERT DATA {{ {statements} }}"
        return insert_string, num_of_statements

def get_update_query(a_set: OCDMGraphCommons | Dataset | Graph, entity: URIRef, entity_type: str = 'graph') -> Tuple[str, int, int]:
    to_be_deleted: bool = False
    preexisting_graph: Dataset | Graph = Dataset()
    graph_iri: URIRef | None = None

    if entity_type == 'graph':
        assert hasattr(a_set, 'entity_index') and hasattr(a_set, 'preexisting_graph')
        to_be_deleted = a_set.entity_index[entity]['to_be_deleted'] if entity in a_set.entity_index else False  # type: ignore[union-attr]
        preexisting_graph = get_entity_subgraph(a_set.preexisting_graph, entity)  # type: ignore[union-attr]

    if isinstance(a_set, Dataset):
        if hasattr(a_set, 'entity_index') and entity in a_set.entity_index:  # type: ignore[operator]
            graph_iri = a_set.entity_index[entity].get('graph_iri')  # type: ignore[union-attr]
        else:
            graph_iri = _extract_graph_iri(a_set, entity)

    if to_be_deleted:
        delete_string, removed_triples = get_delete_query(preexisting_graph, graph_iri)
        if delete_string != "":
            return delete_string, 0, removed_triples
        else:
            return "", 0, 0
    else:
        assert isinstance(a_set, (Graph, Dataset))
        current_graph = get_entity_subgraph(a_set, entity)

        # Convert Dataset to Graph for isomorphic comparison if needed
        if isinstance(preexisting_graph, Dataset):
            preexisting_for_comparison = Graph()
            for s, p, o, _ in preexisting_graph.quads((None, None, None, None)):
                preexisting_for_comparison.add((s, p, o))
        else:
            preexisting_for_comparison = preexisting_graph

        if isinstance(current_graph, Dataset):
            current_for_comparison = Graph()
            for s, p, o, _ in current_graph.quads((None, None, None, None)):
                current_for_comparison.add((s, p, o))
        else:
            current_for_comparison = current_graph

        preexisting_iso: IsomorphicGraph = to_isomorphic(preexisting_for_comparison)
        current_iso: IsomorphicGraph = to_isomorphic(current_for_comparison)
        if preexisting_iso == current_iso:
            # Both graphs have exactly the same content!
            return "", 0, 0
        _, in_first, in_second = graph_diff(preexisting_iso, current_iso)
        delete_string, removed_triples = get_delete_query(in_first, graph_iri)
        insert_string, added_triples = get_insert_query(in_second, graph_iri)
        if delete_string != "" and insert_string != "":
            return delete_string + '; ' + insert_string, added_triples, removed_triples
        elif delete_string != "":
            return delete_string, 0, removed_triples
        elif insert_string != "":
            return insert_string, added_triples, 0
        else:
            return "", 0, 0