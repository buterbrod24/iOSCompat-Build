# Local system export inventory (schema 1)

Analyzer accepts an optional local JSON file through --inventory. It must identify the target OS, exact build and arm64 architecture. Symbols are normalized without the Mach-O leading underscore. Only explicit observations are classified; unlisted symbols remain unknown. A present symbol does not prove ABI compatibility. An absent observation is scoped to the named provider and measurement method, not the whole system or dyld reexport graph.

Example (illustrative schema, not a collected inventory):

```json
{"schema":1,"target":"16.2","build":"20C65","architecture":"arm64","providers":{}}
```

Usage: python3 scripts/analyze_ipa.py app.ipa --inventory local-inventory.json --output report.json

Keep actual system inventories and IPA reports local. No firmware, extracted libraries, or third-party binaries are needed in this repository. A device collector and full export-trie reader are future work.
