# SPDX-FileCopyrightText: 2025 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

from unittest.mock import MagicMock, patch

import pytest
from rdflib import XSD, Graph, Literal, URIRef

from rdflib_ocdm.ocdm_graph import OCDMDataset, OCDMGraph
from rdflib_ocdm.reader import Reader


class TestReader:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.reader = Reader()
        self.ts_url = "http://example.org/sparql"
        self.res_list = [URIRef("http://example.org/res1"), URIRef("http://example.org/res2")]

    def test_init_with_reporters(self):
        mock_repok = MagicMock()
        mock_reperr = MagicMock()

        reader = Reader(repok=mock_repok, reperr=mock_reperr)

        assert reader.repok is mock_repok
        assert reader.reperr is mock_reperr

    @patch('rdflib_ocdm.reader.SPARQLWrapper')
    def test_import_entities_ocdm_graph_success(self, mock_sparql):
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

        assert len(ocdm_graph) == 2
        assert (URIRef("http://example.org/res1"),
                URIRef("http://example.org/name"),
                Literal("Test Resource")) in ocdm_graph
        assert (URIRef("http://example.org/res1"),
                URIRef("http://example.org/count"),
                Literal(42, datatype=XSD.integer)) in ocdm_graph

    @patch('rdflib_ocdm.reader.SPARQLWrapper')
    def test_import_entities_conjunctive_graph_success(self, mock_sparql):
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

        ocdm_graph = OCDMDataset()
        self.reader.import_entities_from_triplestore(ocdm_graph, self.ts_url, self.res_list)

        quads = list(ocdm_graph.quads())
        assert len(quads) == 4

        graph_uris = {str(quad[3]) for quad in quads}
        assert len(graph_uris) == 4

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
        assert len(found_quads) == 4

        for expected in expected_data:
            matching_quads = [
                q for q in found_quads
                if (str(q[0]) == str(expected['s']) and
                    str(q[1]) == str(expected['p']) and
                    str(q[2]) == str(expected['o']))
            ]
            assert len(matching_quads) == 1, f"Expected quad not found: {expected}"

            graph_uri = str(matching_quads[0][3])
            assert expected['graph'] in graph_uri

    @patch('rdflib_ocdm.reader.SPARQLWrapper')
    def test_import_entities_no_results(self, mock_sparql):
        mock_sparql.return_value.queryAndConvert.return_value = Graph()

        ocdm_graph = OCDMGraph()

        with pytest.raises(ValueError) as exc_info:
            self.reader.import_entities_from_triplestore(ocdm_graph, self.ts_url, self.res_list)
        assert str(exc_info.value) == "No entities were found."

    @patch('rdflib_ocdm.reader.SPARQLWrapper')
    def test_import_entities_conjunctive_graph_no_results(self, mock_sparql):
        mock_sparql.return_value.queryAndConvert.return_value = {"results": {"bindings": []}}

        ocdm_graph = OCDMDataset()

        self.reader.import_entities_from_triplestore(ocdm_graph, self.ts_url, self.res_list)
        assert len(list(ocdm_graph.quads())) == 0

    @patch('rdflib_ocdm.reader.SPARQLWrapper')
    def test_import_entities_conjunctive_graph_invalid_response(self, mock_sparql):
        mock_sparql.return_value.queryAndConvert.return_value = {}

        ocdm_graph = OCDMDataset()

        with pytest.raises(ValueError) as exc_info:
            self.reader.import_entities_from_triplestore(ocdm_graph, self.ts_url, self.res_list)
        assert str(exc_info.value) == "No entities were found."

    def test_import_entities_invalid_graph_type(self):
        with pytest.raises(TypeError) as exc_info:
            self.reader.import_entities_from_triplestore("not_a_graph", self.ts_url, self.res_list)  # type: ignore[arg-type]
        assert "must be either OCDMGraph or OCDMDataset" in str(exc_info.value)

    @patch('rdflib_ocdm.reader.SPARQLWrapper')
    def test_import_entities_with_uri_object(self, mock_sparql):
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

        ocdm_graph = OCDMDataset()
        self.reader.import_entities_from_triplestore(ocdm_graph, self.ts_url, self.res_list)

        quads = list(ocdm_graph.quads())
        assert len(quads) == 1

        s, p, o, g = quads[0]
        assert str(s) == "http://example.org/res1"
        assert str(p) == "http://example.org/seeAlso"
        assert str(o) == "http://example.org/other-resource"
        assert isinstance(o, URIRef)

    @patch('rdflib_ocdm.reader.SPARQLWrapper')
    def test_import_entities_retry_mechanism(self, mock_sparql):
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

        assert len(ocdm_graph) == 1
        assert mock_sparql.return_value.queryAndConvert.call_count == 3
