#!/bin/bash

echo "Stopping databases..."
docker stop rdflib_ocdm_dataset_db rdflib_ocdm_provenance_db

echo "Removing containers..."
docker rm rdflib_ocdm_dataset_db rdflib_ocdm_provenance_db

echo "Cleaning up network..."
docker network rm virtuoso-net

echo "Cleanup complete."
