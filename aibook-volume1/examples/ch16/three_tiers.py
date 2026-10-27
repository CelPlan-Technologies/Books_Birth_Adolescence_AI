# One client library, three tiers (Python)
# From Volume 1, Section 16.4. Illustrative; test before use.
# SPDX-License-Identifier: MIT
# Python: one client library, three tiers
import os
from openai import OpenAI
box = OpenAI(base_url="http://localhost:11434/v1",
             api_key="unused")          # Ollama
rack = OpenAI(base_url="http://rack:8000/v1",
              api_key=os.environ["LLM_KEY"]) # vLLM
cloud = OpenAI()   # OpenAI; key from OPENAI_API_KEY
reply = rack.chat.completions.create(
    model="Qwen/Qwen3-32B-FP8",
    messages=[{"role": "user", "content": "Hello"}],
    extra_body={"chat_template_kwargs":
                {"enable_thinking": False}})
