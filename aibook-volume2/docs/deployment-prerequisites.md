<!-- SPDX-License-Identifier: MIT -->
# Deployment prerequisites

What `toolchain/compose.yaml` (Listing 31.1) and `toolchain/embed.yaml` (Listing 31.2) assume, and how to check it before starting anything. Both files are listings: they show the shape of a deployment, with placeholder image digests that deliberately point nowhere.

## Box services: `toolchain/compose.yaml`

Runs in WSL2 on the Box, with Docker Engine and the Compose plugin (v2).

1. **Image digests.** `cp toolchain/.env.example toolchain/.env` and replace both placeholders with the digests of images admitted to the internal registry (Listing 31.3, `toolchain/admit-image.sh`). Use digests (`@sha256:...`), not tags.
2. **Database password.** Create `toolchain/secrets/pg_pw.txt` as described in `toolchain/secrets/pg_pw.txt.example` (mode 600; ignored by Git).
3. **Check, then start.**

   ```bash
   cd toolchain
   docker compose config --quiet     # syntax, variables and secret paths
   docker compose pull               # fails until the digests are real
   docker compose up -d && docker compose ps
   ```

Both services publish their ports on 127.0.0.1 only.

## Rack embedding service: `toolchain/embed.yaml`

Requires a Kubernetes cluster with the NVIDIA GPU Operator and MIG configured (Listing 33.1, `rack/cluster/gpu-operator.sh`), so that nodes advertise `nvidia.com/mig-1g.24gb`.

1. **Namespace and model store.** Adapt `toolchain/k8s-prereqs.example.yaml`: the `retrieval` namespace and the `model-store` PersistentVolumeClaim (ReadOnlyMany, typically NFS). The volume must already hold the model folder named in the Deployment (`/Qwen3-Embedding-4B`), acquired and hashed with `toolchain/acquire-models.sh rack`.
2. **Image.** Replace `registry.local/tei@sha256:...` with the digest of the admitted Text Embeddings Inference image. If the registry needs credentials, create the pull Secret as shown in the template.
3. **Probes.** The startup probe allows up to 10 minutes for the model to load; the readiness probe then keeps the pod out of the Service whenever `/health` fails.
4. **Check, then apply.**

   ```bash
   kubectl apply --dry-run=server -f toolchain/k8s-prereqs.yaml
   kubectl apply --dry-run=server -f toolchain/embed.yaml
   kubectl apply -f toolchain/k8s-prereqs.yaml -f toolchain/embed.yaml
   kubectl -n retrieval rollout status deploy/embed
   ```

   A server-side dry run checks the manifests against the cluster's API, quotas and admission policies; it does not pull the image or load the model.

## Not supplied in this release

- The CPU replica of the embedding service mentioned in Section 33.6 (a second Deployment with the CPU image of Text Embeddings Inference and no MIG limit).
- Kubernetes manifests for the vLLM replicas of Chapter 33 (`rack/serving/gpt-oss-120b.sh` is the container command; Section 33.3 describes the Deployment, Service, probes and placement around it).
- NetworkPolicies limiting who may reach the model servers (only the gateway, Chapter 35).

## What was checked for the release

See `.github/workflows/check.yml` and `EVIDENCE.md`: YAML parsing of both files, `docker compose config` with the example `.env` and a dummy password file, and offline schema validation of the Kubernetes manifests (kubeconform). No image was pulled and no cluster was contacted: a server-side dry run must be done in the target cluster.
