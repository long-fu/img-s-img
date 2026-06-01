#!/bin/bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -e QDRANT__SERVICE__API_KEY=my_secret_key \
  -v "$(pwd)"/qdrant_storage:/qdrant/storage \
  qdrant/qdrant