#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2023-2025 Arcangelo Massari <arcangelo.massari@unibo.it>
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

from typing import List, Union

from oc_ocdm.support.reporter import Reporter
from rdflib import ConjunctiveGraph, Graph, Literal, URIRef
from rdflib_ocdm.ocdm_graph import OCDMConjunctiveGraph, OCDMGraph
from rdflib_ocdm.retry_utils import execute_with_retry
from SPARQLWrapper import JSON, POST, XML, SPARQLWrapper


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
    def import_entities_from_triplestore(ocdm_graph: Union[OCDMGraph, OCDMConjunctiveGraph], ts_url: str, res_list: List[URIRef], max_retries: int = 5) -> None:
        sparql: SPARQLWrapper = SPARQLWrapper(ts_url)
        
        if isinstance(ocdm_graph, OCDMConjunctiveGraph):
            query: str = f'''
                SELECT ?g ?s ?p ?o (LANG(?o) AS ?lang)
                WHERE {{
                    GRAPH ?g {{
                        ?s ?p ?o.
                        VALUES ?s {{<{'> <'.join(res_list)}>}}
                    }}
                }}
            '''
            sparql.setQuery(query)
            sparql.setMethod(POST)
            sparql.setReturnFormat(JSON)
            
            # Use the retry utility function instead of duplicating retry logic
            result = execute_with_retry(
                sparql.queryAndConvert,
                max_retries=max_retries
            )
            
            if result and 'results' in result and 'bindings' in result['results']:
                temp_graph = ConjunctiveGraph()
                for binding in result['results']['bindings']:
                    graph_uri = Graph(identifier=URIRef(binding['g']['value']))
                    subject = URIRef(binding['s']['value'])
                    predicate = URIRef(binding['p']['value'])
                    
                    obj_data = binding['o']
                    if obj_data['type'] == 'uri':
                        obj = URIRef(obj_data['value'])
                    else:
                        value = obj_data['value']
                        lang = binding.get('lang', {}).get('value')
                        datatype = obj_data.get('datatype')
                        
                        if lang:
                            obj = Literal(value, lang=lang)
                        elif datatype:
                            obj = Literal(value, datatype=URIRef(datatype))
                        else:
                            obj = Literal(value)

                    temp_graph.add((subject, predicate, obj, graph_uri))
                
                for quad in temp_graph.quads():
                    ocdm_graph.add(quad)
            else:
                raise ValueError("No entities were found.")
        
        elif isinstance(ocdm_graph, OCDMGraph):
            query: str = f'''
                CONSTRUCT {{
                    ?s ?p ?o
                }}
                WHERE {{
                    ?s ?p ?o. 
                    VALUES ?s {{<{'> <'.join(res_list)}>}}
                }}
            '''
            sparql.setQuery(query)
            sparql.setMethod(POST)
            sparql.setReturnFormat(XML)
            
            # Use the retry utility function instead of duplicating retry logic
            result: Graph = execute_with_retry(
                sparql.queryAndConvert,
                max_retries=max_retries
            )
            
            if result is not None and len(result) > 0:
                for triple in result:
                    ocdm_graph.add(triple)
            else:
                raise ValueError("No entities were found.")
        
        else:
            raise TypeError("ocdm_graph must be either OCDMGraph or OCDMConjunctiveGraph")