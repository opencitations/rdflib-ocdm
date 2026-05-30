# SPDX-FileCopyrightText: 2025 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

from rdflib import BNode, Dataset, Graph, Literal, URIRef

from rdflib_ocdm.ocdm_graph import OCDMDataset, OCDMGraph
from rdflib_ocdm.query_utils import (get_delete_query, get_insert_query,
                                     get_update_query)


class TestQueryUtils:
    def test_get_delete_query_empty_graph(self):
        empty_graph = Graph()
        query, count = get_delete_query(empty_graph)
        assert query == ""
        assert count == 0

    def test_get_delete_query_empty_dataset(self):
        empty_dataset = Dataset()
        query, count = get_delete_query(empty_dataset)
        assert query == ""
        assert count == 0

    def test_get_insert_query_empty_graph(self):
        empty_graph = Graph()
        query, count = get_insert_query(empty_graph)
        assert query == ""
        assert count == 0

    def test_get_insert_query_empty_dataset(self):
        empty_dataset = Dataset()
        query, count = get_insert_query(empty_dataset)
        assert query == ""
        assert count == 0

    def test_get_delete_query_with_data(self):
        graph = Graph()
        graph.add((URIRef('http://example.org/s'), URIRef('http://example.org/p'), Literal('test')))
        query, count = get_delete_query(graph)
        assert "DELETE DATA" in query
        assert count == 1

    def test_get_insert_query_with_data(self):
        graph = Graph()
        graph.add((URIRef('http://example.org/s'), URIRef('http://example.org/p'), Literal('test')))
        query, count = get_insert_query(graph)
        assert "INSERT DATA" in query
        assert count == 1

    def test_get_delete_query_with_graph_iri(self):
        graph = Graph()
        graph.add((URIRef('http://example.org/s'), URIRef('http://example.org/p'), Literal('test')))
        graph_iri = URIRef('http://example.org/graph/')
        query, count = get_delete_query(graph, graph_iri)
        assert "DELETE DATA" in query
        assert f"GRAPH <{graph_iri}>" in query
        assert count == 1

    def test_get_insert_query_with_graph_iri(self):
        graph = Graph()
        graph.add((URIRef('http://example.org/s'), URIRef('http://example.org/p'), Literal('test')))
        graph_iri = URIRef('http://example.org/graph/')
        query, count = get_insert_query(graph, graph_iri)
        assert "INSERT DATA" in query
        assert f"GRAPH <{graph_iri}>" in query
        assert count == 1

    def test_get_update_query_with_graph_type(self):
        ocdm_graph = OCDMDataset()
        ocdm_graph.preexisting_finished()
        entity = URIRef('http://example.org/entity')
        ocdm_graph.add((entity, URIRef('http://example.org/p'), Literal('test'), Graph(identifier=URIRef('http://example.org/graph/'))))

        query, added, removed = get_update_query(ocdm_graph, entity, entity_type='graph')
        assert "INSERT DATA" in query
        assert added == 1
        assert removed == 0

    def test_get_update_query_with_prov_type(self):
        dataset = Dataset()
        entity = URIRef('http://example.org/prov/se/1')
        dataset.add((entity, URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), URIRef('http://www.w3.org/ns/prov#Entity'), Graph(identifier=URIRef('http://example.org/prov/'))))

        query, added, removed = get_update_query(dataset, entity, entity_type='prov')
        assert "INSERT DATA" in query
        assert added == 1
        assert removed == 0

    def test_get_update_query_with_graph_instance(self):
        ocdm_graph = OCDMGraph()
        ocdm_graph.preexisting_finished()
        entity = URIRef('http://example.org/entity')
        ocdm_graph.add((entity, URIRef('http://example.org/p'), Literal('test')))

        query, added, removed = get_update_query(ocdm_graph, entity, entity_type='graph')
        assert "INSERT DATA" in query
        assert added == 1
        assert removed == 0

    def test_get_update_query_with_blank_node_context(self):
        dataset = Dataset()
        entity = URIRef('http://example.org/entity')
        blank_context = BNode()
        dataset.add((entity, URIRef('http://example.org/p'), Literal('test'), Graph(identifier=blank_context)))

        query, added, removed = get_update_query(dataset, entity, entity_type='prov')
        assert query != "" or (added == 0 and removed == 0)

    def test_get_update_query_deleted_entity(self):
        ocdm_graph = OCDMDataset()
        entity = URIRef('http://example.org/entity')
        ocdm_graph.add((entity, URIRef('http://example.org/p'), Literal('test'), Graph(identifier=URIRef('http://example.org/graph/'))))
        ocdm_graph.preexisting_finished()

        ocdm_graph.mark_as_deleted(entity)

        query, added, removed = get_update_query(ocdm_graph, entity, entity_type='graph')
        assert "DELETE DATA" in query
        assert added == 0
        assert removed == 1

    def test_get_update_query_no_changes(self):
        ocdm_graph = OCDMDataset()
        entity = URIRef('http://example.org/entity')
        ocdm_graph.add((entity, URIRef('http://example.org/p'), Literal('test'), Graph(identifier=URIRef('http://example.org/graph/'))))
        ocdm_graph.preexisting_finished()

        query, added, removed = get_update_query(ocdm_graph, entity, entity_type='graph')
        assert query == ""
        assert added == 0
        assert removed == 0

    def test_get_update_query_with_modifications(self):
        ocdm_graph = OCDMDataset()
        entity = URIRef('http://example.org/entity')
        graph_id = URIRef('http://example.org/graph/')

        ocdm_graph.add((entity, URIRef('http://example.org/p1'), Literal('old'), Graph(identifier=graph_id)))
        ocdm_graph.preexisting_finished()

        ocdm_graph.remove((entity, URIRef('http://example.org/p1'), Literal('old'), Graph(identifier=graph_id)))
        ocdm_graph.add((entity, URIRef('http://example.org/p2'), Literal('new'), Graph(identifier=graph_id)))

        query, added, removed = get_update_query(ocdm_graph, entity, entity_type='graph')
        assert "DELETE DATA" in query
        assert "INSERT DATA" in query
        assert added == 1
        assert removed == 1
