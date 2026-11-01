with open("ToolMaze/evaluation/scripts/run_eval_care.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add argument
arg_target = '    parser.add_argument("--max-workers", type=int, default=2)'
arg_replacement = '    parser.add_argument("--max-workers", type=int, default=2)\n    parser.add_argument("--delay-seconds", type=float, default=None, help="Delay pacing in seconds between requests")'

pool_target = '    shared_pool = SharedKeyPool(keys, config["agent"]["base_url"], delay_seconds=1.0)'
pool_replacement = '    delay = args.delay_seconds if args.delay_seconds is not None else (1.5 if args.backend == "gemini" else 0.5)\n    shared_pool = SharedKeyPool(keys, config["agent"]["base_url"], delay_seconds=delay)'

if arg_target in content and pool_target in content:
    content = content.replace(arg_target, arg_replacement)
    content = content.replace(pool_target, pool_replacement)
    with open("ToolMaze/evaluation/scripts/run_eval_care.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully updated run_eval_care.py with --delay-seconds pacing!")
else:
    print("Could not find exact targets in run_eval_care.py")

