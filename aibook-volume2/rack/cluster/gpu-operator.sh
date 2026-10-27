# Listing 33.1 — Installing the GPU Operator
# From "The Birth and Adolescence of Artificial Intelligence", Volume 2, Section 33.2. Illustrative: checked against the documentation of the versions in Appendix B (Volume 2), not run end to end as one system. Test in staging before use.
# SPDX-License-Identifier: MIT
helm repo add nvidia \
  https://helm.ngc.nvidia.com/nvidia
helm repo update
# MIG layout for node B: GPU 7 as four
# 24 GB slices, GPUs 0-6 whole
cat > config.yaml <<'EOF'
version: v1
mig-configs:
  rack-b:
    - devices: [7]
      mig-enabled: true
      mig-devices: {"1g.24gb": 4}
    - devices: [0, 1, 2, 3, 4, 5, 6]
      mig-enabled: false
EOF
kubectl create namespace gpu-operator
kubectl -n gpu-operator create configmap \
  custom-mig-config --from-file=config.yaml
helm install gpu-operator nvidia/gpu-operator \
  -n gpu-operator --version v26.7.2 --wait \
  --set mig.strategy=mixed \
  --set migManager.config.name=custom-mig-config
kubectl label node gpu-b --overwrite \
  nvidia.com/mig.config=rack-b
# verify, once nvidia.com/mig.config.state
# is success: node A 8 GPUs; node B 7 GPUs
# and 4 slices of 1g.24gb
C='NAME:.metadata.name'
C+=',GPU:.status.allocatable.nvidia\.com/gpu'
C+=',MIG:.status.allocatable.nvidia\.com/mig-1g\.24gb'
kubectl get nodes -o custom-columns="$C"
