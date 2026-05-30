#!/usr/bin/python

# SPDX-FileCopyrightText: 2023-2026 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

from __future__ import annotations

from typing import List, Union

from oc_ocdm.support.reporter import Reporter
from rdflib import Dataset, Graph, Literal, URIRef
from SPARQLWrapper import JSON, POST, XML, SPARQLWrapper

from rdflib_ocdm.ocdm_graph import OCDMDataset, OCDMGraph
from rdflib_ocdm.retry_utils import execute_with_retry


class Reader:
    def __init__(self, repok: Reporter | None = None, reperr: Reporter | None = None):
        if repok is None:
            self.repok: Reporter = Reporter(prefix="[Reader: INFO] ")
        else:
            self.repok: Reporter = repok

        if reperr is None:
            self.reperr: Reporter = Reporter(prefix="[Reader: ERROR] ")
        else:
            self.reperr: Reporter = reperr

    @staticmethod
    def import_entities_from_triplestore(
        ocdm_graph: Union[OCDMGraph, OCDMDataset],
        ts_url: str,
        res_list: List[URIRef],
        max_retries: int = 5,
    ) -> None:
        sparql: SPARQLWrapper = SPARQLWrapper(ts_url)

        if isinstance(ocdm_graph, OCDMDataset):
            query: str = f"""
                SELECT ?g ?s ?p ?o (LANG(?o) AS ?lang)
                WHERE {{
                    GRAPH ?g {{
                        ?s ?p ?o.
                        VALUES ?s {{<{"> <".join(res_list)}>}}
                    }}
                }}
            """
            sparql.setQuery(query)
            sparql.setMethod(POST)
            sparql.setReturnFormat(JSON)

            result: dict = execute_with_retry(  # type: ignore[type-arg]
                sparql.queryAndConvert, max_retries=max_retries
            )

            if result and "results" in result and "bindings" in result["results"]:
                temp_graph = Dataset()
                for binding in result["results"]["bindings"]:
                    graph_uri = Graph(identifier=URIRef(binding["g"]["value"]))
                    subject = URIRef(binding["s"]["value"])
                    predicate = URIRef(binding["p"]["value"])

                    obj_data = binding["o"]
                    if obj_data["type"] == "uri":
                        obj = URIRef(obj_data["value"])
                    else:
                        value = obj_data["value"]
                        lang = binding.get("lang", {}).get("value")
                        datatype = obj_data.get("datatype")

                        if lang:
                            obj = Literal(value, lang=lang)
                        elif datatype:
                            obj = Literal(value, datatype=URIRef(datatype))
                        else:
                            obj = Literal(value)

                    temp_graph.add((subject, predicate, obj, graph_uri))

                for quad in temp_graph.quads():
                    ocdm_graph.add(quad)  # type: ignore[arg-type]
            else:
                raise ValueError("No entities were found.")

        elif isinstance(ocdm_graph, OCDMGraph):
            query: str = f"""
                CONSTRUCT {{
                    ?s ?p ?o
                }}
                WHERE {{
                    ?s ?p ?o. 
                    VALUES ?s {{<{"> <".join(res_list)}>}}
                }}
            """
            sparql.setQuery(query)
            sparql.setMethod(POST)
            sparql.setReturnFormat(XML)

            result_graph: Graph = execute_with_retry(  # type: ignore[type-arg]
                sparql.queryAndConvert, max_retries=max_retries
            )

            if result_graph is not None and len(result_graph) > 0:
                for triple in result_graph:
                    ocdm_graph.add(triple)
            else:
                raise ValueError("No entities were found.")

        else:
            raise TypeError("ocdm_graph must be either OCDMGraph or OCDMDataset")
