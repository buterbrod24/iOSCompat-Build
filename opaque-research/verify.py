"""Verify exact compiler-generated opaque descriptor owner pairs, no pointer access."""
import argparse,json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from swift_symbol_roles import demangle,opaque_pairs

def main():
    p=argparse.ArgumentParser()
    p.add_argument("names",type=Path)
    p.add_argument("--demangler",required=True)
    a=p.parse_args()
    rows=demangle(a.names.read_text().splitlines(),a.demangler)
    pairs=opaque_pairs(rows)
    print(json.dumps(pairs,indent=2))
    names=("first","second","integer","text","nested")
    index={r["symbol"]:r for r in rows}
    matched={name for name in names for pair in pairs["pairs"]
             if index[pair["callable"]]["label"].startswith("OpaqueFixture."+name+"(")
             or index[pair["callable"]]["label"].startswith("OpaqueFixture."+name+"<")}
    if matched!=set(names):
        raise SystemExit("missing fixture owner pairs: "+str(set(names)-matched))
if __name__=="__main__":main()
