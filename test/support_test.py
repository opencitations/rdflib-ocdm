#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

from rdflib import RDF, Dataset, Graph, Literal, URIRef

from rdflib_ocdm.support import (_get_match, create_literal, create_type,
                                 get_entity_subgraph, get_prov_count,
                                 is_string_empty)


class TestSupport(unittest.TestCase):
    """Test support.py edge cases"""

    def test_get_match_no_match(self):
        """Test _get_match when regex doesn't match"""
        result = _get_match(r"^test(\d+)$", 1, "no-match-here")
        self.assertEqual(result, "")

    def test_get_match_with_match(self):
        """Test _get_match when regex matches"""
        result = _get_match(r"^test(\d+)$", 1, "test123")
        self.assertEqual(result, "123")

    def test_is_string_empty_none(self):
        """Test is_string_empty with None"""
        self.assertTrue(is_string_empty(None))

    def test_is_string_empty_whitespace(self):
        """Test is_string_empty with whitespace"""
        self.assertTrue(is_string_empty("   "))
        self.assertTrue(is_string_empty("\t\n"))

    def test_is_string_empty_non_empty(self):
        """Test is_string_empty with non-empty string"""
        self.assertFalse(is_string_empty("test"))
        self.assertFalse(is_string_empty(" test "))

    def test_get_prov_count_valid(self):
        """Test get_prov_count with valid provenance URI"""
        uri = URIRef('http://example.org/entity/123/prov/se/5')
        result = get_prov_count(uri)
        self.assertEqual(result, "5")

    def test_get_prov_count_invalid(self):
        """Test get_prov_count with invalid URI (no match)"""
        uri = URIRef('http://example.org/entity/123')
        result = get_prov_count(uri)
        self.assertIsNone(result)

    def test_get_entity_subgraph_dataset(self):
        """Test get_entity_subgraph with Dataset"""
        dataset = Dataset()
        entity = URIRef('http://example.org/entity')
        graph_id = URIRef('http://example.org/graph/')

        dataset.add((entity, URIRef('http://example.org/p1'), Literal('value1'), Graph(identifier=graph_id)))
        dataset.add((entity, URIRef('http://example.org/p2'), Literal('value2'), Graph(identifier=graph_id)))
        dataset.add((URIRef('http://example.org/other'), URIRef('http://example.org/p3'), Literal('value3'), Graph(identifier=graph_id)))

        subgraph = get_entity_subgraph(dataset, entity)
        self.assertEqual(len(subgraph), 2)
        self.assertIsInstance(subgraph, Dataset)

    def test_get_entity_subgraph_graph(self):
        """Test get_entity_subgraph with Graph"""
        graph = Graph()
        entity = URIRef('http://example.org/entity')

        graph.add((entity, URIRef('http://example.org/p1'), Literal('value1')))
        graph.add((entity, URIRef('http://example.org/p2'), Literal('value2')))
        graph.add((URIRef('http://example.org/other'), URIRef('http://example.org/p3'), Literal('value3')))

        subgraph = get_entity_subgraph(graph, entity)
        self.assertEqual(len(subgraph), 2)
        self.assertIsInstance(subgraph, Graph)

    def test_create_literal_valid(self):
        """Test create_literal with valid string"""
        graph = Graph()
        res = URIRef('http://example.org/entity')
        p = URIRef('http://example.org/property')

        create_literal(graph, res, p, 'test value')
        values = list(graph.objects(res, p))
        self.assertEqual(len(values), 1)
        self.assertEqual(str(values[0]), 'test value')

    def test_create_literal_empty_string(self):
        """Test create_literal with empty string"""
        graph = Graph()
        res = URIRef('http://example.org/entity')
        p = URIRef('http://example.org/property')

        create_literal(graph, res, p, '')
        values = list(graph.objects(res, p))
        self.assertEqual(len(values), 0)

    def test_create_literal_none(self):
        """Test create_literal with None"""
        graph = Graph()
        res = URIRef('http://example.org/entity')
        p = URIRef('http://example.org/property')

        create_literal(graph, res, p, None)
        values = list(graph.objects(res, p))
        self.assertEqual(len(values), 0)

    def test_create_type_dataset(self):
        """Test create_type with Dataset"""
        dataset = Dataset()
        res = URIRef('http://example.org/entity')
        res_type = URIRef('http://example.org/Type')
        graph_id = 'http://example.org/graph/'

        # create_type expects a string identifier for Dataset
        create_type(dataset, res, res_type, graph_id)

        # Check that the type was added to the dataset using quads
        # (Dataset.objects() doesn't search named graphs by default)
        types = [o for s, p, o, g in dataset.quads((res, RDF.type, None, None))]
        self.assertEqual(len(types), 1)
        self.assertEqual(types[0], res_type)

    def test_create_type_graph(self):
        """Test create_type with Graph (not Dataset)"""
        graph = Graph()
        res = URIRef('http://example.org/entity')
        res_type = URIRef('http://example.org/Type')

        create_type(graph, res, res_type)

        # Check that the type was added to the graph
        types = list(graph.objects(res, RDF.type))
        self.assertEqual(len(types), 1)
        self.assertEqual(types[0], res_type)


if __name__ == '__main__':
    unittest.main()
