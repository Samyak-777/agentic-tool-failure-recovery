with open("ToolMaze/evaluation/scripts/run_eval_care.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines[410:435]):
    print(f"Line {411+i}: {line}", end="")
