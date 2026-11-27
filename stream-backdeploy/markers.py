import json, pathlib, sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from backdeploy_markers import inspect_markers

for file in sorted(pathlib.Path(sys.argv[1]).glob("*.o")):
    result=inspect_markers(file.read_bytes())
    print(file.name, json.dumps(result,ensure_ascii=True))
print("Only defined nlist names; optimizer may inline or remove markers.")
