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
import random
import shutil
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from oc_ocdm.support.reporter import Reporter
from rdflib import Graph, Literal, URIRef
from SPARQLWrapper import JSON, POST, SPARQLWrapper

from rdflib_ocdm.ocdm_graph import OCDMConjunctiveGraph, OCDMGraph
from rdflib_ocdm.storer import Storer


class TestStorer(unittest.TestCase):
    endpoint = 'http://localhost:8890/sparql'

    def reset_server(self):
        try:
            # Use Docker exec to run ISQL commands on the dataset container
            reset_command = [
                'docker', 'exec', 'rdflib_ocdm_dataset_db',
                '/opt/virtuoso-opensource/bin/isql',
                '-U', 'dba',
                '-P', 'dba',
                'exec=RDF_GLOBAL_RESET();'
            ]
            
            process = subprocess.run(
                reset_command,
                capture_output=True,
                text=True
            )
            
            if process.returncode != 0:
                print(f"Error executing RDF_GLOBAL_RESET: {process.stderr}")
            else:
                print("RDF_GLOBAL_RESET executed successfully")
        except Exception as e:
            print(f"Error resetting database: {e}")

    def setUp(self):
        self.subject = 'https://w3id.org/oc/meta/br/0605'
        self.base_dir = 'test/'
        self.cur_time = 1607375859.846196
        self.ocdm_graph = OCDMGraph()
        self.ocdm_graph.parse(os.path.join('test', 'br_small.nq'))
        self.storer = Storer(self.ocdm_graph)
        self.reset_server()
        self.ts = SPARQLWrapper(self.endpoint)
        self.ts.setMethod(POST)
        self.ts.setReturnFormat(JSON)

        # Add retry logic for the initial query
        max_retries = 5
        retry_count = 0
        base_wait_time = 1

        while retry_count <= max_retries:
            try:
                self.ts.query()
                break
            except Exception as e:
                retry_count += 1
                if retry_count <= max_retries:
                    wait_time = (base_wait_time * (2 ** (retry_count - 1))) + (random.random() * 0.5)
                    print(f"Query attempt {retry_count}/{max_retries} failed: {e}. Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Failed to connect to triplestore after {max_retries} attempts: {e}")

    def tearDown(self):
        """Clean up error files created during tests"""
        tp_err_dir = os.path.join(self.base_dir, 'tp_err')
        if os.path.exists(tp_err_dir):
            shutil.rmtree(tp_err_dir)

    def test_upload_all_graph(self):
        self.maxDiff = None
        ocdm_graph = OCDMConjunctiveGraph()
        ocdm_graph.preexisting_finished()
        ocdm_graph.parse(os.path.join('test', 'br_small.nq'))
        storer = Storer(ocdm_graph)
        storer.upload_all(self.endpoint, self.base_dir)
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
        ocdm_graph.commit_changes()
        ocdm_graph.remove((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy'), Graph(identifier=URIRef('https://w3id.org/oc/meta/br/'))))
        ocdm_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì'), Graph(identifier=URIRef('https://w3id.org/oc/meta/br/'))))
        ocdm_graph.generate_provenance(c_time=self.cur_time)
        storer.upload_all(self.endpoint, self.base_dir)
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
        ocdm_graph = OCDMConjunctiveGraph()
        ocdm_graph.parse(os.path.join('test', 'br_small.nq'), resp_agent='https://orcid.org/0000-0002-8420-0696', primary_source='https://api.crossref.org/')
        ocdm_graph.preexisting_finished(resp_agent='https://orcid.org/0000-0002-8420-0696', primary_source='https://api.crossref.org/', c_time=self.cur_time)
        ocdm_graph.remove((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy'), Graph(identifier=URIRef('https://w3id.org/oc/meta/br/'))))
        ocdm_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì'), Graph(identifier=URIRef('https://w3id.org/oc/meta/br/'))), resp_agent='https://orcid.org/0000-0002-8420-0696', primary_source='https://api.crossref.org/')
        ocdm_graph.generate_provenance(c_time=self.cur_time)
        prov_storer = Storer(ocdm_graph.provenance)
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
            ('https://w3id.org/oc/meta/br/0636066666/prov/', 'https://w3id.org/oc/meta/br/0636066666/prov/se/1', 'http://www.w3.org/ns/prov#generatedAtTime', '2020-12-07T21:17:34Z'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/1', 'http://www.w3.org/ns/prov#generatedAtTime', '2020-12-07T21:17:34Z'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/1', 'http://www.w3.org/ns/prov#invalidatedAtTime', '2020-12-07T21:17:39Z'), 
            ('https://w3id.org/oc/meta/br/0636066666/prov/', 'https://w3id.org/oc/meta/br/0636066666/prov/se/1', 'http://www.w3.org/ns/prov#specializationOf', 'https://w3id.org/oc/meta/br/0636066666'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/2', 'https://w3id.org/oc/ontology/hasUpdateQuery', 'DELETE DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy" . } }; INSERT DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "Bella zì" . } }'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/2', 'http://www.w3.org/ns/prov#hadPrimarySource', 'https://api.crossref.org/'), 
            ('https://w3id.org/oc/meta/br/0605/prov/', 'https://w3id.org/oc/meta/br/0605/prov/se/2', 'http://www.w3.org/ns/prov#generatedAtTime', '2020-12-07T21:17:39Z'), 
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

    def test_storer_error_handling_with_base_dir(self):
        """Test storer error handling when triplestore fails with base_dir"""
        with tempfile.TemporaryDirectory() as temp_dir:
            ocdm_graph = OCDMGraph()
            ocdm_graph.add((URIRef('http://example.org/s'), URIRef('http://example.org/p'), Literal('test')))
            storer = Storer(ocdm_graph)

            # Mock execute_with_retry to always raise ValueError
            with patch('rdflib_ocdm.storer.execute_with_retry', side_effect=ValueError("Connection failed")):
                result = storer.upload_all('http://invalid-endpoint:9999/sparql', base_dir=temp_dir)

                # Check that upload failed
                self.assertFalse(result)

                # Check that error file was created
                tp_err_dir = os.path.join(temp_dir, 'tp_err')
                self.assertTrue(os.path.exists(tp_err_dir))

                # Check that error file contains the query
                error_files = os.listdir(tp_err_dir)
                self.assertEqual(len(error_files), 1)
                self.assertTrue(error_files[0].endswith('_not_uploaded.txt'))

    def test_storer_error_handling_without_base_dir(self):
        """Test storer error handling when triplestore fails without base_dir"""
        ocdm_graph = OCDMGraph()
        ocdm_graph.add((URIRef('http://example.org/s'), URIRef('http://example.org/p'), Literal('test')))
        storer = Storer(ocdm_graph)

        # Mock execute_with_retry to always raise ValueError
        with patch('rdflib_ocdm.storer.execute_with_retry', side_effect=ValueError("Connection failed")):
            result = storer.upload_all('http://invalid-endpoint:9999/sparql', base_dir=None)

            # Check that upload failed but no exception is raised
            self.assertFalse(result)

    def test_storer_unsupported_output_format(self):
        """Test that storer raises ValueError for unsupported output format"""
        ocdm_graph = OCDMGraph()
        with self.assertRaises(ValueError) as context:
            Storer(ocdm_graph, output_format='unsupported-format')
        self.assertIn("not supported", str(context.exception))
        self.assertIn("unsupported-format", str(context.exception))

    def test_storer_custom_reporters(self):
        """Test storer with custom Reporter objects"""
        ocdm_graph = OCDMGraph()
        ocdm_graph.add((URIRef('http://example.org/s'), URIRef('http://example.org/p'), Literal('test')))

        custom_repok = Reporter(prefix="[CUSTOM OK] ")
        custom_reperr = Reporter(prefix="[CUSTOM ERROR] ")

        storer = Storer(ocdm_graph, repok=custom_repok, reperr=custom_reperr)

        # Verify custom reporters are used
        self.assertEqual(storer.repok, custom_repok)
        self.assertEqual(storer.reperr, custom_reperr)

    def test_storer_batch_upload_multiple_batches(self):
        """Test storer with batch_size that triggers multiple batches"""
        ocdm_graph = OCDMConjunctiveGraph()
        ocdm_graph.preexisting_finished()

        # Add multiple entities to trigger batch processing
        for i in range(5):
            ocdm_graph.add((
                URIRef(f'http://example.org/entity/{i}'),
                URIRef('http://purl.org/dc/terms/title'),
                Literal(f'Entity {i}'),
                Graph(identifier=URIRef('http://example.org/graph/'))
            ))

        storer = Storer(ocdm_graph)

        # Use batch_size=2 to ensure multiple batches are created
        result = storer.upload_all(self.endpoint, self.base_dir, batch_size=2)

        # Verify upload succeeded
        self.assertTrue(result)

        # Verify entities are in the triplestore
        query = '''
            SELECT (COUNT(?s) as ?count)
            WHERE {
                ?s <http://purl.org/dc/terms/title> ?o .
                FILTER(STRSTARTS(STR(?s), "http://example.org/entity/"))
            }
        '''
        self.ts.setQuery(query)
        results = self.ts.queryAndConvert()
        count = int(results['results']['bindings'][0]['count']['value'])
        self.assertEqual(count, 5)

    def test_storer_negative_batch_size(self):
        """Test storer with negative batch_size defaults to 10"""
        ocdm_graph = OCDMConjunctiveGraph()
        ocdm_graph.preexisting_finished()
        ocdm_graph.add((URIRef('http://example.org/s'), URIRef('http://example.org/p'), Literal('test'), Graph(identifier=URIRef('http://example.org/graph/'))))

        storer = Storer(ocdm_graph)

        # Use negative batch_size
        result = storer.upload_all(self.endpoint, self.base_dir, batch_size=-5)

        # Should succeed (defaults to 10)
        self.assertTrue(result)

    def test_storer_zero_batch_size(self):
        """Test storer with zero batch_size defaults to 10"""
        ocdm_graph = OCDMConjunctiveGraph()
        ocdm_graph.preexisting_finished()
        ocdm_graph.add((URIRef('http://example.org/s'), URIRef('http://example.org/p'), Literal('test'), Graph(identifier=URIRef('http://example.org/graph/'))))

        storer = Storer(ocdm_graph)

        # Use zero batch_size
        result = storer.upload_all(self.endpoint, self.base_dir, batch_size=0)

        # Should succeed (defaults to 10)
        self.assertTrue(result)