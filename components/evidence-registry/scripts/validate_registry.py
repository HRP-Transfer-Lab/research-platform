#!/usr/bin/env python3
import argparse, json, pathlib, sys

REQUIRED = {"record_id", "release_id", "review_bucket", "bibliography", "review", "study", "protocol", "outcomes", "product_relevance", "tags"}

def load_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("records")
    p.add_argument("--taxonomy", required=True)
    p.add_argument("--manifest", required=True)
    args=p.parse_args()
    tax=load_json(args.taxonomy)
    manifest=load_json(args.manifest)
    routes=set(tax["routes"]); buckets=set(tax["review_buckets"]); products=set(tax["products"])
    ids=set(); count=0; errors=[]
    for lineno,line in enumerate(pathlib.Path(args.records).read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        count += 1
        try: r=json.loads(line)
        except Exception as e:
            errors.append(f"line {lineno}: invalid JSON: {e}"); continue
        missing=REQUIRED-set(r)
        if missing: errors.append(f"line {lineno}: missing {sorted(missing)}")
        rid=r.get("record_id")
        if rid in ids: errors.append(f"line {lineno}: duplicate record_id {rid}")
        ids.add(rid)
        if r.get("release_id") != manifest["release_id"]: errors.append(f"line {lineno}: release mismatch")
        if r.get("review_bucket") not in buckets: errors.append(f"line {lineno}: unknown bucket {r.get('review_bucket')}")
        route=r.get("review",{}).get("primary_classification")
        if route not in routes: errors.append(f"line {lineno}: unknown route/classification {route}")
        if not r.get("bibliography",{}).get("url"): errors.append(f"line {lineno}: missing source URL")
        for pr in r.get("product_relevance",[]):
            if pr.get("product") not in products: errors.append(f"line {lineno}: unknown product {pr.get('product')}")
    if count != manifest["record_count"]: errors.append(f"manifest count {manifest['record_count']} != records {count}")
    if errors:
        print("REGISTRY INVALID")
        for e in errors: print("-",e)
        return 1
    print(f"REGISTRY VALID: {count} records; release={manifest['release_id']}; taxonomy={manifest['taxonomy_version']}")
    return 0
if __name__ == "__main__": raise SystemExit(main())
