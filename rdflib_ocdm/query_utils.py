#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2016, Silvio Peroni <essepuntato@gmail.com>
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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Tuple
    from rdflib.compare import IsomorphicGraph
    from rdflib_ocdm.ocdm_graph import OCDMGraphCommons

from rdflib import Dataset, Graph, URIRef
from rdflib.compare import graph_diff, to_isomorphic

from rdflib_ocdm.graph_utils import _extract_graph_iri
from rdflib_ocdm.support import get_entity_subgraph


def get_delete_query(data: Dataset|Graph, graph_iri: URIRef = None) -> Tuple[str, int]:
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

def get_insert_query(data: Dataset|Graph, graph_iri: URIRef = None) -> Tuple[str, int]:
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

def get_update_query(a_set: OCDMGraphCommons|Dataset|Graph, entity: URIRef, entity_type = 'graph') -> Tuple[str, int, int]:
    if entity_type == 'graph':
        to_be_deleted: bool = a_set.entity_index[entity]['to_be_deleted'] if entity in a_set.entity_index else False
        preexisting_graph = get_entity_subgraph(a_set.preexisting_graph, entity)
        graph_iri = None
    elif entity_type == 'prov':
        to_be_deleted = False
        preexisting_graph = Dataset()

    # Extract graph_iri: prefer entity_index (OCDMDataset), fallback to helper function (regular Dataset)
    if isinstance(a_set, Dataset):
        if hasattr(a_set, 'entity_index') and entity in a_set.entity_index:
            # Clean architectural solution: use stored graph_iri from entity_index
            graph_iri = a_set.entity_index[entity].get('graph_iri')
        else:
            # Fallback for regular Dataset (e.g., provenance graphs): use DRY helper function
            graph_iri = _extract_graph_iri(a_set, entity)
    elif isinstance(a_set, Graph):
        graph_iri = None
    if to_be_deleted:
        delete_string, removed_triples = get_delete_query(preexisting_graph, graph_iri)
        if delete_string != "":
            return delete_string, 0, removed_triples
        else:
            return "", 0, 0
    else:
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