# Listing 35.2 — Routing policy in Rego (excerpt)
# SPDX-License-Identifier: MIT
# From "The Birth and Adolescence of Artificial Intelligence", Volume 2, Section 35.1. Illustrative, abridged: checked against the documentation of the versions in Appendix B (Volume 2), not run end to end as one system. Test in staging before use.
# The routing matrix is matrix.yaml (Listing 30.1), loaded unchanged as data: its destinations table is
# data.destinations. data.named maps each Restricted document to its named users (from the document's access list).
# The gateway builds the whole input on the server from the verified token, the labels of the passages kept
# (gateway/retrieval/rrf.py) and its own classifier; no field of the input is taken from the client.
# Tests: opa test -v gateway/policy/route.rego gateway/policy/route_test.rego gateway/policy/matrix.yaml
package gateway.route
import rego.v1

cell(c) := data.destinations[input.dest][c]

# the outcome of one class c at input.dest
out(c) := "allow" if cell(c) == "allow"
out(c) := "allow" if {
    cell(c) == "named_users"
    input.user in data.named[input.doc]
}
out(c) := "allow" if {
    cell(c) == "own_or_readable"
    input.user_may_read
}
out(c) := "allow" if {
    cell(c) in {"deny_unless_shared", "deny_unless_sent"}
    input.user_released
}
out(c) := "transform" if {
    cell(c) == "transform_drafting"
    input.task == "drafting"
}
out(c) := "transform" if cell(c) == "generic_query"
out(c) := "transform_on_box" if cell(c) == "generic_query_on_box"

# every class present is evaluated and the most restrictive
# outcome wins; no outcome, or no class at all, means deny
order := ["deny", "transform_on_box", "transform", "allow"]
rank(c) := i if order[i] == out(c)
rank(c) := 0 if not out(c)
ranks := {rank(c) | some c in input.classes}
default decision := "deny"
decision := order[min(ranks)] if count(ranks) > 0
