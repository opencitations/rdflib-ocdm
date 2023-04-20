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

from oc_ocdm.support.reporter import Reporter
from rdflib import ConjunctiveGraph, URIRef
from SPARQLWrapper import JSON, SPARQLWrapper

from rdflib_ocdm.ocdm_graph import OCDMGraph


class Reader(object):
    def __init__(self, repok: Reporter = None, reperr: Reporter = None):
        if repok is None:
            self.repok: Reporter = Reporter(prefix="[Reader: INFO] ")
        else:
            self.repok: Reporter = repok

        if reperr is None:
            self.reperr: Reporter = Reporter(prefix="[Reader: ERROR] ")
        else:
            self.reperr: Reporter = reperr

    @staticmethod
    def import_entity_from_triplestore(ocdm_graph: OCDMGraph, ts_url: str, res: URIRef) -> URIRef:
        sparql: SPARQLWrapper = SPARQLWrapper(ts_url)
        query: str = f"CONSTRUCT {{<{res}> ?p ?o}} WHERE {{<{res}> ?p ?o}}"
        sparql.setQuery(query)
        sparql.setMethod('GET')
        result: ConjunctiveGraph = sparql.query().convert()
        if result is not None:
            for triple in result.triples((None, None, None)):
                ocdm_graph.add(triple)
        else:
            raise ValueError(f"The entity {res} was not found.")