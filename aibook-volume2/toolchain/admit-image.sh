#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Listing 31.3 — Admitting an image to the internal registry
# From "The Birth and Adolescence of Artificial Intelligence", Volume 2, Section 31.5. Illustrative: checked against the documentation of the versions in Appendix B (Volume 2), not run end to end as one system. Test in staging before use.
# This file is the complete version of the printed listing. It fails closed: a failed or missing step
# (variable, tool, digest, scan, inventory, copy, digest check, signature) stops it with a nonzero status
# before anything is signed, and only the digest that was scanned and found unchanged in the registry is signed.
# Requires: docker with buildx, jq, cosign. Inputs (environment):
#   KMS_KEY   cosign key reference, e.g. awskms:///alias/registry-signing (required)
#   TRIVY     admitted Trivy image, pinned by digest: registry.internal/sec/trivy@sha256:<64 hex> (required)
#   SYFT      admitted Syft image, pinned by digest:  registry.internal/sec/syft@sha256:<64 hex>  (required)
#   SRC       source image tag (default vllm/vllm-openai:v0.31.0)
#   R         destination repository (default registry.internal/llm/vllm-openai)
#   EXPECT    optional: the digest recorded when the release was reviewed; the run stops if the tag now differs
# Source format: SRC must be an index (manifest list), the form in which multi-platform images are published,
# with exactly one linux/amd64 child; check this when the release is reviewed. The script admits that one child,
# by its own digest, as a single-platform image. A source that is a single manifest (no index) is refused at
# step 1, not admitted; supporting one would need its platform read from the image configuration. To admit several platforms, extend it
# to check the index and every admitted child digest.
# Tested with command stubs (tests/test_admit_image.py), not against a registry, Trivy or a KMS key.
set -euo pipefail

die() { echo "admit-image: $*" >&2; exit 1; }
: "${KMS_KEY:?set KMS_KEY (cosign key reference)}"
: "${TRIVY:?set TRIVY (admitted Trivy image, @sha256)}"
: "${SYFT:?set SYFT (admitted Syft image, @sha256)}"
SRC=${SRC:-vllm/vllm-openai:v0.31.0}
R=${R:-registry.internal/llm/vllm-openai}
TAG=${SRC##*:}
for t in "$TRIVY" "$SYFT"; do
  [[ $t =~ @sha256:[0-9a-f]{64}$ ]] || die "tool image not pinned by digest: $t"
done
for c in docker jq cosign; do command -v "$c" >/dev/null || die "missing command: $c"; done
is_digest() { [[ $1 =~ ^sha256:[0-9a-f]{64}$ ]]; }
manifest() { docker buildx imagetools inspect "$1" --format '{{json .Manifest}}'; }

# 1. resolve the tag once to the digest of its linux/amd64 manifest (exactly one)
SRCMF=$(manifest "$SRC") || die "cannot inspect $SRC"
jq -e 'has("manifests")' <<<"$SRCMF" >/dev/null \
  || die "$SRC is a single manifest, not an index; this script admits one platform from an index"
DIG=$(jq -er '[.manifests[]
        | select(.platform.os == "linux" and .platform.architecture == "amd64")]
        | if length == 1 then .[0].digest else error("not exactly one linux/amd64 manifest") end' <<<"$SRCMF") \
  || die "cannot resolve one linux/amd64 digest for $SRC"
is_digest "$DIG" || die "bad digest: $DIG"
if [[ -n ${EXPECT:-} ]]; then
  [[ $DIG == "$EXPECT" ]] || die "$SRC now resolves to $DIG, not the reviewed $EXPECT"
fi
IMG=${SRC%:*}@$DIG
echo "admit-image: source $IMG"

# 2. scan and inventory that exact image; a HIGH or CRITICAL finding with a fix stops here
docker run --rm "$TRIVY" image --exit-code 1 \
  --severity HIGH,CRITICAL --ignore-unfixed "$IMG" \
  || die "vulnerability scan failed or found HIGH/CRITICAL issues in $IMG"
sbom=$(mktemp)
trap 'rm -f "$sbom"' EXIT
docker run --rm "$SYFT" "$IMG" -o spdx-json > "$sbom" \
  || die "SBOM generation failed for $IMG"
[[ -s $sbom ]] && jq -e . "$sbom" >/dev/null || die "SBOM is empty or not JSON"
mv "$sbom" "vllm-${DIG#sha256:}.spdx.json"

# 3. copy that image; verify that the registry holds the same digest; sign only that digest.
#    --prefer-index=false keeps the single-platform manifest as it is: by default imagetools create wraps a
#    non-index source in a new index, whose digest differs from DIG, and the check below would stop the run.
docker buildx imagetools create --prefer-index=false -t "$R:$TAG" "$IMG" \
  || die "copy to $R:$TAG failed"
GOT=$(manifest "$R:$TAG" | jq -er .digest) || die "cannot read the digest of $R:$TAG"
[[ $GOT == "$DIG" ]] || die "$R:$TAG has digest $GOT, not the scanned $DIG; not signing"
cosign sign --yes --key "$KMS_KEY" "$R@$DIG" || die "signing failed"
cosign verify --key "$KMS_KEY" "$R@$DIG" >/dev/null || die "signature does not verify"
echo "admit-image: admitted and signed $R@$DIG"
