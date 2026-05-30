#!/usr/bin/python

# SPDX-FileCopyrightText: 2023-2026 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

from __future__ import annotations

import re
from typing import Match, Optional

from rdflib import RDF, XSD, Dataset, Graph, Literal, URIRef

prov_regex: str = r"^(.+)/prov/([a-z][a-z])/([1-9][0-9]*)$"


def _get_match(regex: str, group: int, string: str) -> str:
    match: Match[str] | None = re.match(regex, string)
    if match is not None:
        return match.group(group)
    else:
        return ""


def is_string_empty(string: str | None) -> bool:
    return string is None or string.strip() == ""


def get_prov_count(res: URIRef) -> Optional[str]:
    string_iri: str = str(res)
    if "/prov/" in string_iri:
        return _get_match(prov_regex, 3, string_iri)
    return None


def get_entity_subgraph(graph: Dataset | Graph, entity: URIRef) -> Dataset | Graph:
    if isinstance(graph, Dataset):
        subj_graph: Dataset = Dataset()
        for quad in graph.quads((entity, None, None, None)):
            subj_graph.add(quad)  # type: ignore[arg-type]
        return subj_graph
    subj_graph_g: Graph = Graph()
    for triple in graph.triples((entity, None, None)):
        subj_graph_g.add(triple)
    return subj_graph_g


def create_literal(
    g: Graph,
    res: URIRef,
    p: URIRef,
    s: str | None,
    dt: URIRef | None = None,
    nor: bool = True,
) -> None:
    if not is_string_empty(s):
        datatype = dt if dt is not None else XSD.string
        g.add((res, p, Literal(s, datatype=datatype, normalize=nor)))


def create_type(
    g: Dataset | Graph, res: URIRef, res_type: URIRef, identifier: str | None = None
) -> None:
    if isinstance(g, Dataset):
        g.add((res, RDF.type, res_type, identifier))  # type: ignore[arg-type]
    elif isinstance(g, Graph):
        g.add((res, RDF.type, res_type))
