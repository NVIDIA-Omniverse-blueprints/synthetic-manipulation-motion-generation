#!/bin/bash
set -e

# Default namespace to nvidia-omniverse-blueprint if not set
NAMESPACE=${NAMESPACE:-nvidia-omniverse-blueprint}

echo "=== Isaac Lab RHOAI Deployment ==="
echo "Using namespace: $NAMESPACE"

# Create BuildConfig
echo "Creating BuildConfig..."
oc new-build --binary --strategy=docker --name isaac-lab -n "$NAMESPACE"

# Build image
echo "Building image..."
oc start-build isaac-lab --from-dir=. --follow -n "$NAMESPACE"

# Create RHOAI ImageStream
echo "Creating RHOAI ImageStream..."
envsubst < deploy/imagestream.yaml | oc apply -f -

# Tag :latest as :1.0
echo "Tagging image as 1.0..."
oc tag "$NAMESPACE/isaac-lab:latest" "$NAMESPACE/isaac-lab:1.0"

echo ""
echo "✓ Deployment complete!"
echo "✓ Image ready in RHOAI"
echo ""
echo "Next: Create workbench in RHOAI UI and select 'Isaac Lab' image"
