#!/bin/bash

echo "Stopping databases..."
docker stop rdflib_ocdm_dataset_db rdflib_ocdm_provenance_db 2>/dev/null || true

echo "Removing containers..."
docker rm rdflib_ocdm_dataset_db rdflib_ocdm_provenance_db 2>/dev/null || true

echo "Cleaning up network..."
docker network rm virtuoso-net 2>/dev/null || true

echo "Cleanup complete."
