#!/usr/bin/python

# SPDX-FileCopyrightText: 2023-2025 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

from __future__ import annotations

import re
from typing import Match

from rdflib import RDF, XSD, Dataset, Graph, Literal, URIRef

prov_regex: str = r"^(.+)/prov/([a-z][a-z])/([1-9][0-9]*)$"

def _get_match(regex: str, group: int, string: str) -> str:
    match: Match = re.match(regex, string)
    if match is not None:
        return match.group(group)
    else:
        return ""

def is_string_empty(string: str) -> bool:
    return string is None or string.strip() == ""

def get_prov_count(res: URIRef) -> str:
    string_iri: str = str(res)
    if "/prov/" in string_iri:
        return _get_match(prov_regex, 3, string_iri)

def get_entity_subgraph(graph: Graph, entity: URIRef) -> Graph:
    subj_graph: Dataset|Graph = Dataset() if isinstance(graph, Dataset) else Graph()
    if isinstance(graph, Dataset):
        for quad in graph.quads((entity, None, None, None)):
            subj_graph.add(quad)
    elif isinstance(graph, Graph):
        for triple in graph.triples((entity, None, None)):
            subj_graph.add(triple)
    return subj_graph

def create_literal(g: Graph, res: URIRef, p: URIRef, s: str, dt: URIRef = None, nor: bool = True) -> None:
    if not is_string_empty(s):
        datatype = dt if dt is not None else XSD.string
        g.add((res, p, Literal(s, datatype=datatype, normalize=nor)))

def create_type(g: Dataset|Graph, res: URIRef, res_type: URIRef, identifier: str = None) -> None:
    if isinstance(g, Dataset):
        g.add((res, RDF.type, res_type, identifier))
    elif isinstance(g, Graph):
        g.add((res, RDF.type, res_type))