#!/usr/bin/python

# SPDX-FileCopyrightText: 2025 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from rdflib import Dataset

from rdflib import URIRef


def _extract_graph_iri_from_context(context) -> Optional[URIRef]:
    """
    Extract a valid graph IRI from a context object.

    Returns the context identifier if it's a non-default named graph.
    Default graphs (starting with 'urn:x-rdflib:') are ignored.

    :param context: The context object (usually from quad or _spoc)
    :return: The graph IRI as URIRef, or None if not valid
    """
    if context is None:
        return None
    context_identifier = (
        context.identifier if hasattr(context, "identifier") else context
    )
    if isinstance(context_identifier, URIRef):
        if not str(context_identifier).startswith("urn:x-rdflib:"):
            return context_identifier
    return None


def _extract_graph_iri(dataset: Dataset, subject: URIRef) -> Optional[URIRef]:
    """
    Extract the graph IRI for a given subject from a Dataset.

    Returns the first non-default named graph IRI found for the subject.
    Default graphs (starting with 'urn:x-rdflib:') are ignored.

    :param dataset: The Dataset to search in
    :param subject: The subject URIRef to find the graph IRI for
    :return: The graph IRI as URIRef, or None if not found
    """
    for _, _, _, c in dataset.quads((subject, None, None, None)):
        graph_iri = _extract_graph_iri_from_context(c)
        if graph_iri is not None:
            return graph_iri
    return None
