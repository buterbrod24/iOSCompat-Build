#!/usr/bin/env python3
"""Require real call to the original SDK default getter in independent client."""
import pathlib,re,sys
ir=pathlib.Path(sys.argv[1]).read_text()
target="$s10AppIntents0A6IntentPAAE14isDiscoverableSbvgZ"
defs=re.findall(r'^define [^\n]*? @"?([^"(\s]+)"?\([^\n]*\n(.*?)^\}',ir,re.M|re.S)
for name,body in defs:
    if 'stockDefaultTest' in name and re.search(r'\bcall\b[^\n]*@"'+re.escape(target)+r'"\(',body):
        print('Concrete SDK default test directly calls exact original getter:',name)
        break
else:
    raise SystemExit('Default test does not directly call expected SDK getter; no runtime claim allowed')
