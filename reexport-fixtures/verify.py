import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from reexport_graph import load_images,trace
from export_trie import inspect_exports
root=pathlib.Path(sys.argv[1])
images=load_images([root/"libLeaf.dylib",root/"libFacade.dylib"])
leaf="@rpath/libLeaf.dylib"
facade="@rpath/libFacade.dylib"
assert "_ioscompat_leaf_value" in images[leaf]["symbols"],images
assert leaf in images[facade]["reexport_libraries"],images
result=trace(images,facade,"_ioscompat_leaf_value")
assert result["status"]=="candidate_path_found",result
assert result["paths"][0]["chain"][-1]["provider"]==leaf,result
assert trace(images,facade,"_ioscompat_not_present")["status"]=="not_observed"
assert trace({facade:images[facade]},facade,"_ioscompat_leaf_value")["blockers"]
print("PASS leaf direct export")
print("PASS facade declared reexport")
print("PASS static provider chain")
print("PASS unknown name stays not observed")
print("PASS missing provider stays unresolved")
print("TOTAL 5/5")
