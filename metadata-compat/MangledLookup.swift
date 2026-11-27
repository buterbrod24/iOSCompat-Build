// Experimental source-level lookup of compiler-produced textual mangled names.
// No symbolic references, context pointers, generic argument vectors or ABI aliases.
public enum MangledLookup {
    public static func resolve(_ name: String) -> Any.Type? {
        guard !name.isEmpty, name.utf8.count <= 4096,
              name.utf8.allSatisfy({ (65...90).contains($0) || (97...122).contains($0) || (48...57).contains($0) || $0 == 95 }) else { return nil }
        return _typeByName(name)
    }

    public static func roundTrip(_ type: Any.Type) -> Bool {
        guard let name = _mangledTypeName(type), let resolved = resolve(name) else { return false }
        return ObjectIdentifier(type) == ObjectIdentifier(resolved)
    }
}
