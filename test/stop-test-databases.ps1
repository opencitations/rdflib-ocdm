Write-Host "Stopping databases..."
docker stop rdflib_ocdm_dataset_db rdflib_ocdm_provenance_db

Write-Host "Removing containers..."
docker rm rdflib_ocdm_dataset_db rdflib_ocdm_provenance_db

Write-Host "Cleaning up network..."
docker network rm virtuoso-net

Write-Host "Cleanup complete."
