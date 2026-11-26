#!/usr/bin/env python3
"""Compare exact public callable signatures; never alias protocol data."""
import pathlib
import re
import sys

TARGETS = {
    "$s16AppIntentsCompat17ioscompatShortcut6intent7phrases10shortTitle15systemImageName0aB00aE0Vx_SayAG0aE6PhraseVyxGG10Foundation23LocalizedStringResourceVSStAG0A6IntentRzlF": "$s10AppIntents0A8ShortcutV6intent7phrases10shortTitle15systemImageNameACx_SayAA0aC6PhraseVyxGG10Foundation23LocalizedStringResourceVSSYttcAA0A6IntentRzlufC",
    "$s10AppIntents0A6IntentP0aB6CompatE28ioscompatDefaultDiscoverableSbvgZ": "$s10AppIntents0A6IntentPAAE14isDiscoverableSbvgZ",
}
OLD = "$s10AppIntents0A8ShortcutV6intent7phrases10shortTitle15systemImageNameACx_SayAA0aC6PhraseVyxGG10Foundation23LocalizedStringResourceVSgSSSgYttcAA0A6IntentRzlufC"


def signatures(ir, kind):
    return re.findall(r'^' + kind + r' ([^\n]*?) @"([^"]+)"\((.*)\) #\d+', ir, re.M)


def signature(ir, kind, name):
    hits = [(ret, args) for ret, sym, args in signatures(ir, kind) if sym == name]
    if len(hits) != 1:
        raise ValueError(f"Expected one {kind} for {name}: {hits}")
    ret, args = hits[0]
    if not ret.startswith("swiftcc "):
        raise ValueError(f"Unexpected calling convention or linkage: {ret}")
    normalized = [re.sub(r' %[A-Za-z0-9_.$-]+$', '', arg.strip()) for arg in args.split(',') if arg.strip()]
    return ret, normalized


def check(stock, candidate):
    aliases = []
    for name, target in TARGETS.items():
        a = signature(candidate, 'define', name)
        b = signature(stock, 'declare', target)
        if a != b:
            raise ValueError(f"ABI mismatch: {target}: {a!r} != {b!r}")
        print(f"Matched {target}: {a!r}")
        aliases.append(('_' + name, '_' + target))
    imported = {n for _, n, _ in signatures(candidate, 'declare')}
    if OLD not in imported or not re.search(r'\bcall\b[^\n]*@"' + re.escape(OLD) + r'"\(', candidate):
        raise ValueError('Old native initializer must be called')
    if imported.intersection(TARGETS.values()):
        raise ValueError('Candidate imports its future alias')
    return aliases


if __name__ == '__main__':
    stock, candidate = [pathlib.Path(p).read_text() for p in sys.argv[1:3]]
    aliases = check(stock, candidate)
    pathlib.Path(sys.argv[3]).write_text(''.join(a + '\t' + b + '\n' for a, b in aliases))
    print('Two callable ABI candidates; no protocol descriptor compatibility claim.')
