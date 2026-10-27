# How a tokenizer splits a Python function
# From Volume 1, Section 3.3. Illustrative; test before use.
# SPDX-License-Identifier: MIT
# The sample function that Section 3.3 tokenizes; run any tokenizer on this file to see the split.
def signal_power(dbm):
    return 10 ** (dbm / 10)
