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

import os
import unittest

from rdflib import Literal, URIRef
from SPARQLWrapper import JSON, POST, SPARQLWrapper

from rdflib_ocdm.ocdm_graph import OCDMGraph
from rdflib_ocdm.storer import Storer


class TestStorer(unittest.TestCase):
    def setUp(self):
        self.subject = 'https://w3id.org/oc/meta/br/0605'
        self.endpoint = 'http://localhost:9999/blazegraph/sparql'
        self.base_dir = 'test/'
        self.cur_time = 1607375859.846196
        self.ocdm_graph = OCDMGraph()
        self.ocdm_graph.parse(os.path.join('test', 'br.nt'))
        self.storer = Storer(self.ocdm_graph)
        self.ts = SPARQLWrapper(self.endpoint)
        self.ts.setQuery('DELETE {?x ?y ?z} WHERE {?x ?y ?z}')
        self.ts.setMethod(POST)
        self.ts.setReturnFormat(JSON)
        self.ts.query()

    def test_upload_all_graph(self):
        self.maxDiff = None
        self.storer.upload_all(self.endpoint, self.base_dir)
        query = '''
            SELECT ?s ?p ?o
            WHERE {
                VALUES (?s) {(<https://w3id.org/oc/meta/br/0605>) (<https://w3id.org/oc/meta/br/0636066666>)}
                ?s ?p ?o
            }
        '''
        self.ts.setQuery(query)
        results = self.ts.queryAndConvert()
        results = {(result['s']['value'], result['p']['value'], result['o']['value']) for result in results['results']['bindings']}
        expected_results = {
            ('https://w3id.org/oc/meta/br/0636066666', 'http://purl.org/dc/terms/title', "Ironing Out Tau'S Role In Parkinsonism"), 
            ('https://w3id.org/oc/meta/br/0605', 'http://purl.org/dc/terms/title', 'A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy')}
        self.assertEqual(results, expected_results)
        self.ocdm_graph.commit_changes()
        self.ocdm_graph.remove((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy')))
        self.ocdm_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
        self.ocdm_graph.generate_provenance(c_time=self.cur_time)
        self.storer.upload_all(self.endpoint, self.base_dir)
        query = '''
            SELECT ?s ?p ?o
            WHERE {
                VALUES (?s) {(<https://w3id.org/oc/meta/br/0605>) (<https://w3id.org/oc/meta/br/0636066666>)}
                ?s ?p ?o
            }
        '''
        self.ts.setQuery(query)
        results = self.ts.queryAndConvert()
        results = {(result['s']['value'], result['p']['value'], result['o']['value']) for result in results['results']['bindings']}
        expected_results = {
            ('https://w3id.org/oc/meta/br/0636066666', 'http://purl.org/dc/terms/title', "Ironing Out Tau'S Role In Parkinsonism"), 
            ('https://w3id.org/oc/meta/br/0605', 'http://purl.org/dc/terms/title', 'Bella zì')}
        self.assertEqual(results, expected_results)

    def test_upload_all_provenance(self):
        self.maxDiff = None
        self.ocdm_graph.preexisting_finished(resp_agent='https://orcid.org/0000-0002-8420-0696', source='https://api.crossref.org/', c_time=self.cur_time)
        self.ocdm_graph.remove((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy')))
        self.ocdm_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
        self.ocdm_graph.generate_provenance(c_time=self.cur_time)
        prov_storer = Storer(self.ocdm_graph.provenance)
        prov_storer.upload_all(self.endpoint)
        query = '''
            PREFIX prov: <http://www.w3.org/ns/prov#> 
            SELECT ?g ?s ?p ?o
            WHERE {
                GRAPH ?g {
                    ?s a prov:Entity;
                        ?p ?o.
                }
            }
        '''
        self.ts.setQuery(query)
        results = self.ts.queryAndConvert()
        results = {(result['g']['value'], result['s']['value'], result['p']['value'], result['o']['value']) for result in results['results']['bindings']}
        expected_result = {
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/2', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://www.w3.org/ns/prov#Entity'), 
            ('https://w3id.org/oc/meta/br/0636066666/prov/', 'https://w3id.org/oc/meta/br/0636066666/prov/se/1', 'http://www.w3.org/ns/prov#generatedAtTime', '2020-12-07T21:17:34.000Z'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/1', 'http://www.w3.org/ns/prov#generatedAtTime', '2020-12-07T21:17:34.000Z'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/1', 'http://www.w3.org/ns/prov#invalidatedAtTime', '2020-12-07T21:17:39.000Z'), 
            ('https://w3id.org/oc/meta/br/0636066666/prov/', 'https://w3id.org/oc/meta/br/0636066666/prov/se/1', 'http://www.w3.org/ns/prov#specializationOf', 'https://w3id.org/oc/meta/br/0636066666'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/2', 'https://w3id.org/oc/ontology/hasUpdateQuery', 'DELETE DATA { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy" . }; INSERT DATA { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "Bella zì" . }'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/2', 'http://www.w3.org/ns/prov#hadPrimarySource', 'https://api.crossref.org/'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/2', 'http://www.w3.org/ns/prov#generatedAtTime', '2020-12-07T21:17:39.000Z'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/2', 'http://www.w3.org/ns/prov#specializationOf', 'https://w3id.org/oc/meta/br/0605'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/2', 'http://purl.org/dc/terms/description', "The entity 'https://w3id.org/oc/meta/br/0605' was modified."), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/2', 'http://www.w3.org/ns/prov#wasAttributedTo', 'https://orcid.org/0000-0002-8420-0696'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/2', 'http://www.w3.org/ns/prov#wasDerivedFrom', 'https://w3id.org/oc/meta/br/0605/prov/se/1'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/1', 'http://purl.org/dc/terms/description', "The entity 'https://w3id.org/oc/meta/br/0605' has been created."), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/1', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://www.w3.org/ns/prov#Entity'), 
            ('https://w3id.org/oc/meta/br/0636066666/prov/', 'https://w3id.org/oc/meta/br/0636066666/prov/se/1', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://www.w3.org/ns/prov#Entity'), 
            ('https://w3id.org/oc/meta/br/0636066666/prov/', 'https://w3id.org/oc/meta/br/0636066666/prov/se/1', 'http://purl.org/dc/terms/description', "The entity 'https://w3id.org/oc/meta/br/0636066666' has been created."), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/1', 'http://www.w3.org/ns/prov#specializationOf', 'https://w3id.org/oc/meta/br/0605'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/1', 'http://www.w3.org/ns/prov#wasAttributedTo', 'https://orcid.org/0000-0002-8420-0696'), 
            ('https://w3id.org/oc/meta/br/0636066666/prov/', 'https://w3id.org/oc/meta/br/0636066666/prov/se/1', 'http://www.w3.org/ns/prov#hadPrimarySource', 'https://api.crossref.org/'), 
            ('https://w3id.org/oc/meta/br/0636066666/prov/', 'https://w3id.org/oc/meta/br/0636066666/prov/se/1', 'http://www.w3.org/ns/prov#wasAttributedTo', 'https://orcid.org/0000-0002-8420-0696'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/1', 'http://www.w3.org/ns/prov#hadPrimarySource', 'https://api.crossref.org/')}
        self.assertEqual(results, expected_result)