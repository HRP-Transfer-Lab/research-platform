#!/usr/bin/env python3
import argparse, json, pathlib

def records(path):
    path=pathlib.Path(path)
    if path.is_dir():
        for f in sorted(path.glob("*.json")):
            yield json.loads(f.read_text(encoding="utf-8"))
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip(): yield json.loads(line)

def contains_ci(value, needle):
    return needle.lower() in json.dumps(value, ensure_ascii=False).lower()

def main():
    p=argparse.ArgumentParser(description="Query a versioned HRP Transfer Evidence Registry release.")
    p.add_argument("records")
    p.add_argument("--route"); p.add_argument("--bucket"); p.add_argument("--product")
    p.add_argument("--tag"); p.add_argument("--population"); p.add_argument("--text")
    p.add_argument("--compact", action="store_true")
    a=p.parse_args(); out=[]
    for r in records(a.records):
        if a.route and r["review"]["primary_classification"] != a.route: continue
        if a.bucket and r["review_bucket"] != a.bucket: continue
        if a.product and not any(x.get("product")==a.product for x in r["product_relevance"]): continue
        if a.tag and a.tag not in r["tags"]: continue
        if a.population and not contains_ci(r["study"].get("population"), a.population): continue
        if a.text and not contains_ci(r, a.text): continue
        out.append(r)
    if a.compact:
        print(json.dumps([{"record_id":r["record_id"],"title":r["bibliography"]["title"],"route":r["review"]["primary_classification"],"bucket":r["review_bucket"],"products":[p["product"] for p in r["product_relevance"]]} for r in out],indent=2,ensure_ascii=False))
    else:
        print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__ == "__main__": main()
