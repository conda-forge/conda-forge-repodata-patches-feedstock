Checklist

* [ ] Used a static YAML file for the patch if possible ([instructions](https://github.com/conda-forge/conda-forge-repodata-patches-feedstock/blob/main/recipe/README.md)).
* [ ] Only wrote code directly into `recipe/generate_patch_json.py` if absolutely necessary.
* [ ] Ran `pre-commit run -a` (or `cd recipe && pixi run pre-commit`) and ensured all files pass the linting checks.
* [ ] Ran `python recipe/show_diff.py` (or `cd recipe && pixi run diff`) and posted the output as part of the PR.
* [ ] Modifications won't affect packages built in the future.
  <!-- Make sure to add a condition `timestamp_le: NOW` so your changes only affect packages built in the past. Replace NOW with the result of one of these:
  - cd recipe && pixi run timestamp
  - python -c "import time; print(f'{time.time():.0f}000')"
  - date +%s000
  - The number displayed on https://currentmillis.com
  -->

<!-- Put any other comments or information here -->
