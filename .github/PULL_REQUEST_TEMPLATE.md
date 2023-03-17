Checklist
* [ ] Ran `python show_diff.py` and posted the output as part of the PR.
* [ ] Modifications won't affect packages built in the future. <!-- Make sure to add a condition `and record.get("timestamp", 0) < NOW` so your changes only affect packages built in the past. Replace NOW with `python -c "import time; print(f'{time.time():.0f}000')"` -->
