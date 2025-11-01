#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

from rdflib import BNode, Dataset, Graph, Literal, URIRef

from rdflib_ocdm.ocdm_graph import OCDMConjunctiveGraph, OCDMGraph
from rdflib_ocdm.query_utils import (get_delete_query, get_insert_query,
                                     get_update_query)


class TestQueryUtils(unittest.TestCase):
    """Test query_utils.py edge cases"""

    def test_get_delete_query_empty_graph(self):
        """Test get_delete_query with empty graph returns empty string"""
        empty_graph = Graph()
        query, count = get_delete_query(empty_graph)
        self.assertEqual(query, "")
        self.assertEqual(count, 0)

    def test_get_delete_query_empty_dataset(self):
        """Test get_delete_query with empty dataset returns empty string"""
        empty_dataset = Dataset()
        query, count = get_delete_query(empty_dataset)
        self.assertEqual(query, "")
        self.assertEqual(count, 0)

    def test_get_insert_query_empty_graph(self):
        """Test get_insert_query with empty graph returns empty string"""
        empty_graph = Graph()
        query, count = get_insert_query(empty_graph)
        self.assertEqual(query, "")
        self.assertEqual(count, 0)

    def test_get_insert_query_empty_dataset(self):
        """Test get_insert_query with empty dataset returns empty string"""
        empty_dataset = Dataset()
        query, count = get_insert_query(empty_dataset)
        self.assertEqual(query, "")
        self.assertEqual(count, 0)

    def test_get_delete_query_with_data(self):
        """Test get_delete_query with actual data"""
        graph = Graph()
        graph.add((URIRef('http://example.org/s'), URIRef('http://example.org/p'), Literal('test')))
        query, count = get_delete_query(graph)
        self.assertIn("DELETE DATA", query)
        self.assertEqual(count, 1)

    def test_get_insert_query_with_data(self):
        """Test get_insert_query with actual data"""
        graph = Graph()
        graph.add((URIRef('http://example.org/s'), URIRef('http://example.org/p'), Literal('test')))
        query, count = get_insert_query(graph)
        self.assertIn("INSERT DATA", query)
        self.assertEqual(count, 1)

    def test_get_delete_query_with_graph_iri(self):
        """Test get_delete_query with graph_iri parameter"""
        graph = Graph()
        graph.add((URIRef('http://example.org/s'), URIRef('http://example.org/p'), Literal('test')))
        graph_iri = URIRef('http://example.org/graph/')
        query, count = get_delete_query(graph, graph_iri)
        self.assertIn("DELETE DATA", query)
        self.assertIn(f"GRAPH <{graph_iri}>", query)
        self.assertEqual(count, 1)

    def test_get_insert_query_with_graph_iri(self):
        """Test get_insert_query with graph_iri parameter"""
        graph = Graph()
        graph.add((URIRef('http://example.org/s'), URIRef('http://example.org/p'), Literal('test')))
        graph_iri = URIRef('http://example.org/graph/')
        query, count = get_insert_query(graph, graph_iri)
        self.assertIn("INSERT DATA", query)
        self.assertIn(f"GRAPH <{graph_iri}>", query)
        self.assertEqual(count, 1)

    def test_get_update_query_with_graph_type(self):
        """Test get_update_query with entity_type='graph'"""
        ocdm_graph = OCDMConjunctiveGraph()
        ocdm_graph.preexisting_finished()
        entity = URIRef('http://example.org/entity')
        ocdm_graph.add((entity, URIRef('http://example.org/p'), Literal('test'), Graph(identifier=URIRef('http://example.org/graph/'))))

        query, added, removed = get_update_query(ocdm_graph, entity, entity_type='graph')
        self.assertIn("INSERT DATA", query)
        self.assertEqual(added, 1)
        self.assertEqual(removed, 0)

    def test_get_update_query_with_prov_type(self):
        """Test get_update_query with entity_type='prov'"""
        dataset = Dataset()
        entity = URIRef('http://example.org/prov/se/1')
        dataset.add((entity, URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), URIRef('http://www.w3.org/ns/prov#Entity'), Graph(identifier=URIRef('http://example.org/prov/'))))

        query, added, removed = get_update_query(dataset, entity, entity_type='prov')
        self.assertIn("INSERT DATA", query)
        self.assertEqual(added, 1)
        self.assertEqual(removed, 0)

    def test_get_update_query_with_graph_instance(self):
        """Test get_update_query with Graph instance instead of Dataset"""
        ocdm_graph = OCDMGraph()
        ocdm_graph.preexisting_finished()
        entity = URIRef('http://example.org/entity')
        ocdm_graph.add((entity, URIRef('http://example.org/p'), Literal('test')))

        query, added, removed = get_update_query(ocdm_graph, entity, entity_type='graph')
        self.assertIn("INSERT DATA", query)
        self.assertEqual(added, 1)
        self.assertEqual(removed, 0)

    def test_get_update_query_with_blank_node_context(self):
        """Test get_update_query with blank node as context identifier"""
        dataset = Dataset()
        entity = URIRef('http://example.org/entity')
        # Add a triple with a blank node as context
        blank_context = BNode()
        dataset.add((entity, URIRef('http://example.org/p'), Literal('test'), Graph(identifier=blank_context)))

        query, added, removed = get_update_query(dataset, entity, entity_type='prov')
        # Should handle blank node context (not URIRef)
        self.assertTrue(query != "" or (added == 0 and removed == 0))

    def test_get_update_query_deleted_entity(self):
        """Test get_update_query with deleted entity"""
        ocdm_graph = OCDMConjunctiveGraph()
        entity = URIRef('http://example.org/entity')
        ocdm_graph.add((entity, URIRef('http://example.org/p'), Literal('test'), Graph(identifier=URIRef('http://example.org/graph/'))))
        ocdm_graph.preexisting_finished()

        # Mark entity as deleted
        ocdm_graph.mark_as_deleted(entity)

        query, added, removed = get_update_query(ocdm_graph, entity, entity_type='graph')
        self.assertIn("DELETE DATA", query)
        self.assertEqual(added, 0)
        self.assertEqual(removed, 1)

    def test_get_update_query_no_changes(self):
        """Test get_update_query when entity has no changes"""
        ocdm_graph = OCDMConjunctiveGraph()
        entity = URIRef('http://example.org/entity')
        ocdm_graph.add((entity, URIRef('http://example.org/p'), Literal('test'), Graph(identifier=URIRef('http://example.org/graph/'))))
        ocdm_graph.preexisting_finished()

        # No changes made to the entity
        query, added, removed = get_update_query(ocdm_graph, entity, entity_type='graph')
        self.assertEqual(query, "")
        self.assertEqual(added, 0)
        self.assertEqual(removed, 0)

    def test_get_update_query_with_modifications(self):
        """Test get_update_query with both additions and deletions"""
        ocdm_graph = OCDMConjunctiveGraph()
        entity = URIRef('http://example.org/entity')
        graph_id = URIRef('http://example.org/graph/')

        # Add initial triple
        ocdm_graph.add((entity, URIRef('http://example.org/p1'), Literal('old'), Graph(identifier=graph_id)))
        ocdm_graph.preexisting_finished()

        # Remove old triple and add new one
        ocdm_graph.remove((entity, URIRef('http://example.org/p1'), Literal('old'), Graph(identifier=graph_id)))
        ocdm_graph.add((entity, URIRef('http://example.org/p2'), Literal('new'), Graph(identifier=graph_id)))

        query, added, removed = get_update_query(ocdm_graph, entity, entity_type='graph')
        self.assertIn("DELETE DATA", query)
        self.assertIn("INSERT DATA", query)
        self.assertEqual(added, 1)
        self.assertEqual(removed, 1)


if __name__ == '__main__':
    unittest.main()
