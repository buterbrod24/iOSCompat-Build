"""Conservative callable IR shape check, not a proof of Swift ABI compatibility."""
import pathlib
import re
import sys

ATTRS = re.compile(r"\b(?:swiftself|swifterror|swiftasync|sret|byval|byref|inreg|inalloca|nest|preallocated|zeroext|signext)\b")
TYPE = re.compile(r"(?:\b(?:void|ptr|i[0-9]+|half|float|double|fp128)\b|%[-a-zA-Z0-9_.$]+|\{[^{}]*\}|\[[^\[\]]*\])")

def split_params(s):
    if not s.strip():
        return []
    parts, start, stack = [], 0, []
    pairs = {"(":")","[":"]","{":"}","<":">"}
    for i, c in enumerate(s):
        if c in pairs:
            stack.append(pairs[c])
        elif c in pairs.values():
            if not stack or stack.pop() != c:
                raise ValueError("unbalanced parameter")
        elif c == "," and not stack:
            parts.append(s[start:i].strip())
            start = i+1
    if stack:
        raise ValueError("unbalanced parameter")
    return parts+[s[start:].strip()]

def shape(fragment):
    match = TYPE.search(fragment)
    if not match:
        raise ValueError("unsupported IR type: "+fragment)
    return (re.sub(r"\s+", "", match.group()), tuple(sorted(ATTRS.findall(fragment))))

def signature(ir, symbol, kind):
    needle = '@"'+symbol+'"('
    rows = [line for line in ir.splitlines() if line.startswith(kind+" ") and needle in line]
    if len(rows) != 1:
        raise ValueError(f"{kind}: {symbol}: expected one signature, got {len(rows)}")
    head, tail = rows[0].split(needle, 1)
    convention = re.search(r"\b(swiftcc|swiftasynccc|ccc|fastcc)\b", head)
    if not convention:
        raise ValueError("unknown calling convention")
    depth = 1
    for i, c in enumerate(tail):
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return (convention.group(), shape(head[convention.end():]), tuple(shape(p) for p in split_params(tail[:i])))
    raise ValueError("unterminated function signature")

def main():
    stock,candidate = (pathlib.Path(p).read_text() for p in sys.argv[1:3])
    required=pathlib.Path("observation-research/required-exports.txt").read_text().splitlines()[:5]
    passed = 0
    for symbol in required:
        try:
            a = signature(stock,symbol[1:],"declare")
            b = signature(candidate,symbol[1:],"define")
            ok = a == b
            print("MATCH" if ok else "DIFFERENT",symbol)
            print("  stock:",a)
            print("  candidate:",b)
            passed += int(ok)
        except ValueError as exc:
            print("UNVERIFIED",symbol,str(exc))
    print("CALLABLE IR SHAPES",passed,"/",len(required))
    print("LIMIT: no validation of pointee layouts, metadata, ownership semantics or runtime behavior")
    if passed != len(required):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
