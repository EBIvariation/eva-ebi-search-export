# EBI-search export
These are script used by the EVA to dump data to json so they are indexed by EBI search.


## Study export
Study export grabs the study from the public API endpoint to get all public studies available and dump it in EBI search 
json format.

```bash
study_export.py --output_file <path_to_output.json>
```
