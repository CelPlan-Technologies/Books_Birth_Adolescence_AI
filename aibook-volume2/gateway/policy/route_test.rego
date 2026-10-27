# Tests of route.rego (Listing 35.2) against matrix.yaml (Listing 30.1) and Table 30.5, Volume 2.
# SPDX-License-Identifier: MIT
# Run from the repository root (list the files; loading the whole folder would also load audit-record.json as data):
#   opa test -v gateway/policy/route.rego gateway/policy/route_test.rego gateway/policy/matrix.yaml
# Named-user data are a fixture here; in service they come from each Restricted document's access list.
package gateway.route_test

import rego.v1

import data.gateway.route

named := {"hr-17": ["alice"]}

# every condition false: bob is not a named user, may not read, has released nothing, and is not drafting
none := {"user": "bob", "doc": "hr-17", "user_may_read": false, "user_released": false, "task": "qa"}

# every condition true
all := {"user": "alice", "doc": "hr-17", "user_may_read": true, "user_released": true, "task": "drafting"}

dec(dest, classes, ctx) := d if {
	d := route.decision with input as object.union(ctx, {"dest": dest, "classes": classes})
		with data.named as named
}

# one cell of Table 30.5: its decision with every condition false, then with every condition true
cell(dest, c, want_none, want_all) if {
	dec(dest, [c], none) == want_none
	dec(dest, [c], all) == want_all
}

# ---- every cell of Table 30.5
test_box_r1 if cell("box", "R1", "allow", "allow")
test_box_r2 if cell("box", "R2", "allow", "allow")
test_box_r3_own_or_readable if cell("box", "R3", "deny", "allow")
test_box_r4 if cell("box", "R4", "deny", "deny")
test_box_r5 if cell("box", "R5", "allow", "allow")

test_rack_r1 if cell("rack", "R1", "allow", "allow")
test_rack_r2 if cell("rack", "R2", "allow", "allow")
test_rack_r3 if cell("rack", "R3", "allow", "allow")
test_rack_r4_named_users if cell("rack", "R4", "deny", "allow")
test_rack_r5_unless_shared if cell("rack", "R5", "deny", "allow")

test_cloud_r1 if cell("cloud", "R1", "allow", "allow")
test_cloud_r2 if cell("cloud", "R2", "allow", "allow")
test_cloud_r3_drafting if cell("cloud", "R3", "deny", "transform")
test_cloud_r4 if cell("cloud", "R4", "deny", "deny")
test_cloud_r5_unless_sent if cell("cloud", "R5", "deny", "allow")

test_web_r1 if cell("web", "R1", "allow", "allow")
test_web_r2 if cell("web", "R2", "transform", "transform")
test_web_r3 if cell("web", "R3", "transform", "transform")
test_web_r4 if cell("web", "R4", "deny", "deny")
test_web_r5 if cell("web", "R5", "transform_on_box", "transform_on_box")

# a condition opens only its own cell: named users are per user and per document,
# and drafting does not release Personal content
test_named_user_must_be_listed_for_that_document if {
	dec("rack", ["R4"], object.union(all, {"user": "bob"})) == "deny"
	dec("rack", ["R4"], object.union(all, {"doc": "hr-99"})) == "deny"
}

test_drafting_alone_does_not_release_personal if {
	dec("cloud", ["R5"], object.union(none, {"task": "drafting"})) == "deny"
}

# ---- mixed classes: the most restrictive outcome wins
test_worked_example_30_2 if {
	# Public, Internal and Confidential passages (Worked Example 30.2)
	dec("rack", ["R1", "R2", "R3"], none) == "allow"
	dec("cloud", ["R1", "R2", "R3"], none) == "deny"
	dec("cloud", ["R1", "R2", "R3"], all) == "transform"
	dec("web", ["R1", "R2", "R3"], none) == "transform"
	dec("box", ["R1", "R2", "R3"], none) == "deny"
}

test_restricted_blocks_cloud_and_web if {
	dec("cloud", ["R1", "R4"], all) == "deny"
	dec("web", ["R1", "R4"], all) == "deny"
	dec("rack", ["R1", "R4"], all) == "allow"
	dec("rack", ["R1", "R4"], none) == "deny"
}

test_personal_query_rewritten_on_box if {
	dec("web", ["R1", "R5"], none) == "transform_on_box"
	dec("web", ["R2", "R3", "R5"], none) == "transform_on_box"
}

rank_of(x) := i if route.order[i] == x

# every pair of classes, at every destination, under both condition settings:
# the decision is the more restrictive of the two single-class decisions
test_every_pair_is_most_restrictive if {
	every dest in ["box", "rack", "cloud", "web"] {
		every ctx in [none, all] {
			every a in ["R1", "R2", "R3", "R4", "R5"] {
				every b in ["R1", "R2", "R3", "R4", "R5"] {
					dec(dest, [a, b], ctx) == route.order[min({rank_of(dec(dest, [a], ctx)), rank_of(dec(dest, [b], ctx))})]
				}
			}
		}
	}
}

# ---- empty, unknown or missing input, and missing data: deny
test_empty_classes_deny if {
	every dest in ["box", "rack", "cloud", "web"] {
		dec(dest, [], all) == "deny"
	}
}

test_unknown_label_denies if {
	dec("rack", ["R9"], all) == "deny"
	dec("rack", ["R1", "R9"], all) == "deny"
	dec("rack", ["r1"], all) == "deny"
	dec("rack", [""], all) == "deny"
}

test_unknown_destination_denies if {
	dec("mars", ["R1"], all) == "deny"
	dec("", ["R1"], all) == "deny"
}

test_missing_fields_deny if {
	route.decision with input as {"dest": "rack"}
		with data.named as named == "deny"
	route.decision with input as {"classes": ["R1"]}
		with data.named as named == "deny"
	route.decision with input as {} == "deny"
}

# the defect of the first release: the matrix not loaded at the path the policy reads
test_matrix_not_loaded_denies if {
	route.decision with input as object.union(all, {"dest": "rack", "classes": ["R1"]})
		with data.destinations as {} == "deny"
}
