#!/bin/bash

# Stop and remove existing containers if they exist
echo "Cleaning up existing containers and volumes..."
docker stop rdflib_ocdm_dataset_db rdflib_ocdm_provenance_db 2>/dev/null || true
docker rm rdflib_ocdm_dataset_db rdflib_ocdm_provenance_db 2>/dev/null || true

# Create network if it doesn't exist
docker network create virtuoso-net 2>/dev/null || true

# Create test database directories if they don't exist
mkdir -p test/dataset_db
mkdir -p test/prov_db

# Start dataset database
echo "Starting dataset database..."
docker run -d \
  --name rdflib_ocdm_dataset_db \
  --network virtuoso-net \
  -p 8890:8890 \
  -p 1111:1111 \
  -e DBA_PASSWORD=dba \
  -e SPARQL_UPDATE=true \
  -v "$(pwd)/test/dataset_db:/database" \
  openlink/virtuoso-opensource-7@sha256:c08d54120b8085234f8244951232553428e235543412e41d75705736a3026f1b

# Start provenance database
echo "Starting provenance database..."
docker run -d \
  --name rdflib_ocdm_provenance_db \
  --network virtuoso-net \
  -p 8891:8890 \
  -p 1112:1111 \
  -e DBA_PASSWORD=dba \
  -e SPARQL_UPDATE=true \
  -v "$(pwd)/test/prov_db:/database" \
  openlink/virtuoso-opensource-7@sha256:c08d54120b8085234f8244951232553428e235543412e41d75705736a3026f1b

echo "Waiting for databases to initialize..."
sleep 15

# Set permissions for the 'nobody' user in both databases
echo "Setting permissions for the 'nobody' user in the dataset database..."
docker exec rdflib_ocdm_dataset_db /opt/virtuoso-opensource/bin/isql -U dba -P dba exec="DB.DBA.RDF_DEFAULT_USER_PERMS_SET ('nobody', 7);"

echo "Setting permissions for the 'nobody' user in the provenance database..."
docker exec rdflib_ocdm_provenance_db /opt/virtuoso-opensource/bin/isql -U dba -P dba exec="DB.DBA.RDF_DEFAULT_USER_PERMS_SET ('nobody', 7);"

# Assign SPARQL_UPDATE role to the SPARQL account
echo "Assigning SPARQL_UPDATE role to the SPARQL account in the dataset database..."
docker exec rdflib_ocdm_dataset_db /opt/virtuoso-opensource/bin/isql -U dba -P dba exec="DB.DBA.USER_GRANT_ROLE ('SPARQL', 'SPARQL_UPDATE');"

echo "Assigning SPARQL_UPDATE role to the SPARQL account in the provenance database..."
docker exec rdflib_ocdm_provenance_db /opt/virtuoso-opensource/bin/isql -U dba -P dba exec="DB.DBA.USER_GRANT_ROLE ('SPARQL', 'SPARQL_UPDATE');"

echo "Permissions set successfully."
echo "Databases started. You can check their status with:"
echo "docker ps | grep virtuoso"
echo "Dataset DB: http://localhost:8890/sparql"
echo "Provenance DB: http://localhost:8891/sparql"
