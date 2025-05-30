# Stop and remove existing containers if they exist
Write-Host "Cleaning up existing containers and volumes..."
docker stop rdflib_ocdm_dataset_db rdflib_ocdm_provenance_db 2>$null
docker rm rdflib_ocdm_dataset_db rdflib_ocdm_provenance_db 2>$null

# Create network if it doesn't exist
docker network create virtuoso-net 2>$null

# Create test database directories if they don't exist
New-Item -Path "test/dataset_db" -ItemType Directory -Force | Out-Null
New-Item -Path "test/prov_db" -ItemType Directory -Force | Out-Null

# Start dataset database
Write-Host "Starting dataset database..."
docker run -d `
  --name rdflib_ocdm_dataset_db `
  --network virtuoso-net `
  -p 8890:8890 `
  -p 1111:1111 `
  -e DBA_PASSWORD=dba `
  -e SPARQL_UPDATE=true `
  -v "${PWD}/test/dataset_db:/database" `
  openlink/virtuoso-opensource-7@sha256:c08d54120b8085234f8244951232553428e235543412e41d75705736a3026f1b

# Start provenance database
Write-Host "Starting provenance database..."
docker run -d `
  --name rdflib_ocdm_provenance_db `
  --network virtuoso-net `
  -p 8891:8890 `
  -p 1112:1111 `
  -e DBA_PASSWORD=dba `
  -e SPARQL_UPDATE=true `
  -v "${PWD}/test/prov_db:/database" `
  openlink/virtuoso-opensource-7@sha256:c08d54120b8085234f8244951232553428e235543412e41d75705736a3026f1b

Write-Host "Waiting for databases to initialize..."
Start-Sleep -Seconds 15

# Set permissions for the 'nobody' user in both databases
Write-Host "Setting permissions for the 'nobody' user in the dataset database..."
docker exec rdflib_ocdm_dataset_db /opt/virtuoso-opensource/bin/isql -U dba -P dba exec="DB.DBA.RDF_DEFAULT_USER_PERMS_SET ('nobody', 7);"

Write-Host "Setting permissions for the 'nobody' user in the provenance database..."
docker exec rdflib_ocdm_provenance_db /opt/virtuoso-opensource/bin/isql -U dba -P dba exec="DB.DBA.RDF_DEFAULT_USER_PERMS_SET ('nobody', 7);"

# Assign SPARQL_UPDATE role to the SPARQL account
Write-Host "Assigning SPARQL_UPDATE role to the SPARQL account in the dataset database..."
docker exec rdflib_ocdm_dataset_db /opt/virtuoso-opensource/bin/isql -U dba -P dba exec="DB.DBA.USER_GRANT_ROLE ('SPARQL', 'SPARQL_UPDATE');"

Write-Host "Assigning SPARQL_UPDATE role to the SPARQL account in the provenance database..."
docker exec rdflib_ocdm_provenance_db /opt/virtuoso-opensource/bin/isql -U dba -P dba exec="DB.DBA.USER_GRANT_ROLE ('SPARQL', 'SPARQL_UPDATE');"

Write-Host "Permissions set successfully."
Write-Host "Databases started. You can check their status with:"
Write-Host "docker ps | findstr virtuoso"
Write-Host "Dataset DB: http://localhost:8890/sparql"
Write-Host "Provenance DB: http://localhost:8891/sparql"
