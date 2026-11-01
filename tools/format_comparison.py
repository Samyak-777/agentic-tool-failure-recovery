import json

with open("compare_runs.json", "r", encoding="utf-8") as f:
    text = f.read()

idx_without = text.index("WITHOUT:")
idx_with = text.index("WITH:")

without_json = text[idx_without+8:idx_with].strip()
with_json = text[idx_with+5:].strip()

d_without = json.loads(without_json)
d_with = json.loads(with_json)

print("| Task ID | Mode | Without Reeti (`task_json` In-Memory) | With Reeti (`data/templates/` on Disk) |")
print("|---|---|---|---|")
for k in sorted(d_without.keys()):
    base_name = k.replace(".json", "")
    mode = base_name.split("_")[-1]
    
    pw = d_without[k]["passed"]
    rw = d_without[k]["reason"] or "Passed (0 missing tools)"
    tools_w = d_without[k]["tools"]
    
    pr = d_with[k]["passed"]
    rr = d_with[k]["reason"] or "Passed (0 missing tools)"
    tools_r = d_with[k]["tools"]
    
    status_w = "**PASS**" if pw else "FAIL"
    status_r = "**PASS**" if pr else "FAIL"
    
    print(f"| `{base_name}` | {mode} | {status_w} <br> _{rw}_ | {status_r} <br> _{rr}_ |")

