#!/bin/bash
set -e

echo "=== Isaac Lab RHOAI Deployment ==="

# Create BuildConfig
echo "Creating BuildConfig..."
oc new-build --binary --strategy=docker --name isaac-lab -n nvidia-omniverse-blueprint

# Build image
echo "Building image..."
oc start-build isaac-lab --from-dir=. --follow -n nvidia-omniverse-blueprint

# Create RHOAI ImageStream
echo "Creating RHOAI ImageStream..."
oc apply -f deploy/imagestream.yaml

# Tag :latest as :1.0
echo "Tagging image as 1.0..."
oc tag nvidia-omniverse-blueprint/isaac-lab:latest nvidia-omniverse-blueprint/isaac-lab:1.0

echo ""
echo "✓ Deployment complete!"
echo "✓ Image ready in RHOAI"
echo ""
echo "Next: Create workbench in RHOAI UI and select 'Isaac Lab' image"
