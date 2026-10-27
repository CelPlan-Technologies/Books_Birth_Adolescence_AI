# Listing 28.1 — Collect license and size metadata
# From "The Birth and Adolescence of Artificial Intelligence", Volume 2, Section 28.8. Illustrative: checked against the documentation of the versions in Appendix B (Volume 2), not run end to end as one system. Test in staging before use.
# SPDX-License-Identifier: MIT
from huggingface_hub import model_info

repos = ["openai/gpt-oss-120b",
         "Qwen/Qwen3.8-2.4T-A95B",
         "google/gemma-4-31B-it",
         "Qwen/Qwen3-Embedding-8B"]
for rid in repos:
    m = model_info(rid)
    lic = (m.card_data or {}).get("license")
    st = m.safetensors
    n = st.total if st else None
    print(rid, lic, n, st.parameters if st else None)
# 4-bit checkpoints pack two weights per U8 element:
# cross-check the parameter count on the model card
# license 'other' means: read the LICENSE file
