#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2025 Arcangelo Massari <arcangelo.massari@unibo.it>
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

import unittest
from unittest.mock import MagicMock, patch

from rdflib import XSD, Graph, Literal, URIRef
from rdflib_ocdm.ocdm_graph import OCDMConjunctiveGraph, OCDMGraph
from rdflib_ocdm.reader import Reader


class TestReader(unittest.TestCase):    
    def setUp(self):
        """Set up test fixtures."""
        self.reader = Reader()
        self.ts_url = "http://example.org/sparql"
        self.res_list = ["http://example.org/res1", "http://example.org/res2"]
    
    def test_init_with_reporters(self):
        """Test initialization with custom reporters."""
        mock_repok = MagicMock()
        mock_reperr = MagicMock()
        
        reader = Reader(repok=mock_repok, reperr=mock_reperr)
        
        self.assertIs(reader.repok, mock_repok)
        self.assertIs(reader.reperr, mock_reperr)
    
    @patch('rdflib_ocdm.reader.SPARQLWrapper')
    def test_import_entities_ocdm_graph_success(self, mock_sparql):
        """Test successful import of entities into OCDMGraph."""
        mock_response = """<?xml version="1.0"?>
        <rdf:RDF
            xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
            xmlns:ex="http://example.org/">
            <rdf:Description rdf:about="http://example.org/res1">
                <ex:name>Test Resource</ex:name>
                <ex:count rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">42</ex:count>
            </rdf:Description>
        </rdf:RDF>"""
        
        mock_sparql.return_value.queryAndConvert.return_value = Graph().parse(data=mock_response, format='xml')
        
        ocdm_graph = OCDMGraph()
        self.reader.import_entities_from_triplestore(ocdm_graph, self.ts_url, self.res_list)
        
        self.assertEqual(len(ocdm_graph), 2)
        self.assertTrue((URIRef("http://example.org/res1"), 
                        URIRef("http://example.org/name"), 
                        Literal("Test Resource")) in ocdm_graph)
        self.assertTrue((URIRef("http://example.org/res1"), 
                        URIRef("http://example.org/count"), 
                        Literal(42, datatype=XSD.integer)) in ocdm_graph)
    
    @patch('rdflib_ocdm.reader.SPARQLWrapper')
    def test_import_entities_conjunctive_graph_success(self, mock_sparql):
        """Test successful import of entities into OCDMConjunctiveGraph."""
        mock_response = {
            "results": {
                "bindings": [
                    {
                        "g": {"value": "http://example.org/graph1"},
                        "s": {"value": "http://example.org/res1"},
                        "p": {"value": "http://example.org/name"},
                        "o": {"value": "Test Resource", "type": "literal"}
                    },
                    {
                        "g": {"value": "http://example.org/graph2"},
                        "s": {"value": "http://example.org/res1"},
                        "p": {"value": "http://example.org/count"},
                        "o": {"value": "42", "type": "literal", "datatype": str(XSD.integer)}
                    },
                    {
                        "g": {"value": "http://example.org/graph3"},
                        "s": {"value": "http://example.org/res1"},
                        "p": {"value": "http://example.org/description"},
                        "o": {"value": "A description with language", "type": "literal"},
                        "lang": {"value": "en"}
                    },
                    {
                        "g": {"value": "http://example.org/graph4"},
                        "s": {"value": "http://example.org/res1"},
                        "p": {"value": "http://example.org/date"},
                        "o": {"value": "2023-01-01", "type": "literal", "datatype": str(XSD.date)}
                    }
                ]
            }
        }
        
        mock_sparql.return_value.queryAndConvert.return_value = mock_response
        
        ocdm_graph = OCDMConjunctiveGraph()
        self.reader.import_entities_from_triplestore(ocdm_graph, self.ts_url, self.res_list)
        
        quads = list(ocdm_graph.quads())
        self.assertEqual(len(quads), 4)
        
        graph_uris = {str(quad[3]) for quad in quads}
        self.assertEqual(len(graph_uris), 4)
        
        expected_data = [
            {
                's': URIRef("http://example.org/res1"),
                'p': URIRef("http://example.org/name"),
                'o': Literal("Test Resource"),
                'graph': "http://example.org/graph1"
            },
            {
                's': URIRef("http://example.org/res1"),
                'p': URIRef("http://example.org/count"),
                'o': Literal("42", datatype=XSD.integer),
                'graph': "http://example.org/graph2"
            },
            {
                's': URIRef("http://example.org/res1"),
                'p': URIRef("http://example.org/description"),
                'o': Literal("A description with language", lang="en"),
                'graph': "http://example.org/graph3"
            },
            {
                's': URIRef("http://example.org/res1"),
                'p': URIRef("http://example.org/date"),
                'o': Literal("2023-01-01", datatype=XSD.date),
                'graph': "http://example.org/graph4"
            }
        ]
        
        found_quads = list(quads)
        self.assertEqual(len(found_quads), 4)
        
        for expected in expected_data:
            matching_quads = [
                q for q in found_quads
                if (str(q[0]) == str(expected['s']) and 
                    str(q[1]) == str(expected['p']) and
                    str(q[2]) == str(expected['o']))
            ]
            self.assertEqual(len(matching_quads), 1, 
                           f"Expected quad not found: {expected}")
            
            graph_uri = str(matching_quads[0][3])
            self.assertIn(expected['graph'], graph_uri)
    
    @patch('rdflib_ocdm.reader.SPARQLWrapper')
    def test_import_entities_no_results(self, mock_sparql):
        """Test behavior when no results are returned from the triplestore."""
        mock_sparql.return_value.queryAndConvert.return_value = Graph()
        
        ocdm_graph = OCDMGraph()
        
        with self.assertRaises(ValueError) as context:
            self.reader.import_entities_from_triplestore(ocdm_graph, self.ts_url, self.res_list)
        self.assertEqual(str(context.exception), "No entities were found.")
    
    @patch('rdflib_ocdm.reader.SPARQLWrapper')
    def test_import_entities_conjunctive_graph_no_results(self, mock_sparql):
        """Test behavior when no results are returned from the triplestore for OCDMConjunctiveGraph."""
        mock_sparql.return_value.queryAndConvert.return_value = {"results": {"bindings": []}}
        
        ocdm_graph = OCDMConjunctiveGraph()
        
        self.reader.import_entities_from_triplestore(ocdm_graph, self.ts_url, self.res_list)
        self.assertEqual(len(list(ocdm_graph.quads())), 0)
    
    @patch('rdflib_ocdm.reader.SPARQLWrapper')
    def test_import_entities_conjunctive_graph_invalid_response(self, mock_sparql):
        """Test behavior when an invalid response is returned from the triplestore."""
        mock_sparql.return_value.queryAndConvert.return_value = {}
        
        ocdm_graph = OCDMConjunctiveGraph()
        
        with self.assertRaises(ValueError) as context:
            self.reader.import_entities_from_triplestore(ocdm_graph, self.ts_url, self.res_list)
        self.assertEqual(str(context.exception), "No entities were found.")
    
    def test_import_entities_invalid_graph_type(self):
        """Test behavior when an invalid graph type is provided."""
        with self.assertRaises(TypeError) as context:
            self.reader.import_entities_from_triplestore("not_a_graph", self.ts_url, self.res_list)
        self.assertIn("must be either OCDMGraph or OCDMConjunctiveGraph", str(context.exception))
    
    @patch('rdflib_ocdm.reader.SPARQLWrapper')
    def test_import_entities_with_uri_object(self, mock_sparql):
        """Test importing entities with URI objects in the response."""
        mock_response = {
            "results": {
                "bindings": [
                    {
                        "g": {"value": "http://example.org/graph1"},
                        "s": {"value": "http://example.org/res1"},
                        "p": {"value": "http://example.org/seeAlso"},
                        "o": {"value": "http://example.org/other-resource", "type": "uri"}
                    }
                ]
            }
        }
        
        mock_sparql.return_value.queryAndConvert.return_value = mock_response
        
        ocdm_graph = OCDMConjunctiveGraph()
        self.reader.import_entities_from_triplestore(ocdm_graph, self.ts_url, self.res_list)
        
        quads = list(ocdm_graph.quads())
        self.assertEqual(len(quads), 1)
        
        s, p, o, g = quads[0]
        self.assertEqual(str(s), "http://example.org/res1")
        self.assertEqual(str(p), "http://example.org/seeAlso")
        self.assertEqual(str(o), "http://example.org/other-resource")
        self.assertIsInstance(o, URIRef)
    
    @patch('rdflib_ocdm.reader.SPARQLWrapper')
    def test_import_entities_retry_mechanism(self, mock_sparql):
        """Test that the retry mechanism works as expected."""
        from rdflib_ocdm.retry_utils import execute_with_retry

        mock_sparql.return_value.queryAndConvert.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            Graph().parse(data="""<?xml version="1.0"?>
                <rdf:RDF
                    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                    xmlns:ex="http://example.org/">
                    <rdf:Description rdf:about="http://example.org/res1">
                        <ex:name>Test Resource</ex:name>
                    </rdf:Description>
                </rdf:RDF>""", format='xml')
        ]
        
        ocdm_graph = OCDMGraph()
        self.reader.import_entities_from_triplestore(ocdm_graph, self.ts_url, self.res_list, max_retries=2)
        
        self.assertEqual(len(ocdm_graph), 1)
        self.assertEqual(mock_sparql.return_value.queryAndConvert.call_count, 3)

if __name__ == '__main__':
    unittest.main()
