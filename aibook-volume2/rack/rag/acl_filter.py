# Listing 33.3 — The permission filter in every search
# From "The Birth and Adolescence of Artificial Intelligence", Volume 2, Section 33.4. Illustrative: checked against the documentation of the versions in Appendix B (Volume 2), not run end to end as one system. Test in staging before use.
# SPDX-License-Identifier: MIT
import os
from qdrant_client import QdrantClient
from qdrant_client import models as m
qdrant = QdrantClient(url="https://qdrant:6333",
    api_key=os.environ["QDRANT_API_KEY"])
# payload indexes: acl, deny (keyword),
# class_rank (integer)
# user.clearance (from the token): the most
# sensitive class the user may read, 1-4

def search(qvec, user):   # from the token
    who = [f"g:{g}" for g in user.groups]
    who.append(f"u:{user.id}")
    f = m.Filter(must=[
        m.FieldCondition(key="acl",
            match=m.MatchAny(any=who)),
        m.FieldCondition(key="class_rank",
            range=m.Range(lte=user.clearance))],
        must_not=[m.FieldCondition(key="deny",
            match=m.MatchAny(any=who))])
    return qdrant.query_points(
        collection_name="corporate",
        query=qvec, limit=30,
        query_filter=f).points
