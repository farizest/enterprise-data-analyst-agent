#!/bin/bash

echo "🚀 Step 1: Enterprise Data Ingestion (AdventureWorks -> Postgres)"
set -e
export MSYS_NO_PATHCONV=1

echo "🔍 Finding your running PostgreSQL container..."
CONTAINER_ID=$(docker compose ps -q db || docker compose ps -q postgres)

if [ -z "$CONTAINER_ID" ]; then
    CONTAINER_ID=$(docker ps -q --filter "ancestor=postgres")
fi

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ Error: Could not find your Postgres container."
    exit 1
fi
echo "   [+] Found Postgres Container ID: $CONTAINER_ID"

WORKSPACE_DIR="./aw_temp"
rm -rf $WORKSPACE_DIR
mkdir -p $WORKSPACE_DIR
cd $WORKSPACE_DIR

echo "📥 1. Cloning lorint's AdventureWorks repository..."
git clone https://github.com/lorint/AdventureWorks-for-Postgres.git .

echo "📥 2. Downloading raw Microsoft CSVs..."
curl -L -o aw.zip "https://github.com/Microsoft/sql-server-samples/releases/download/adventureworks/AdventureWorks-oltp-install-script.zip"
unzip -q -o aw.zip

echo "🧹 3. Moving CSVs out of subfolders..."
find . -name "*.csv" -exec mv {} . \; 2>/dev/null || true

echo "🔄 4. Converting CSVs (Bypassing Windows Volume Mounts!)..."
# 🛡️ THE FIX: Create a container, copy files in, execute, copy out, and destroy!
docker create --name ruby_converter -w /workspace ruby:3.2 bash -c "ruby update_csvs.rb"
docker cp . ruby_converter:/workspace
docker start -a ruby_converter
docker cp ruby_converter:/workspace/. .
docker rm ruby_converter

echo "🗄️ 5. Copying formatted data into your Postgres container..."
docker cp . ${CONTAINER_ID}:/tmp/aw_data

echo "⚙️ 6. Preparing Database & Executing SQL..."
docker exec ${CONTAINER_ID} bash -c "psql -U admin -d postgres -c 'CREATE DATABASE adventureworks;' || true"
docker exec ${CONTAINER_ID} bash -c "cd /tmp/aw_data && psql -U admin -d adventureworks -v ON_ERROR_STOP=1 -f install.sql"

echo "🧹 7. Cleaning up temporary files..."
cd ..
rm -rf $WORKSPACE_DIR

echo "✅ AdventureWorks successfully loaded into PostgreSQL!"