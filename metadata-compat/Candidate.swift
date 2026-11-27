// Source-level metadata lookup for explicitly registered application types.
// Does not parse Swift mangled names or manufacture runtime metadata.
import Foundation

public final class MetadataRegistry {
    private let lock = NSLock()
    private var types: [String: Any.Type] = [:]
    public init() {}
    @discardableResult public func register(_ name: String, type: Any.Type) -> Bool {
        guard !name.isEmpty else { return false }
        lock.lock(); defer { lock.unlock() }
        if let existing = types[name] {
            return ObjectIdentifier(existing) == ObjectIdentifier(type)
        }
        types[name] = type
        return true
    }
    public func resolve(_ name: String) -> Any.Type? {
        lock.lock(); defer { lock.unlock() }
        return types[name]
    }
    public func resolve<T>(_ name: String, as type: T.Type) -> T.Type? {
        guard let found = resolve(name), ObjectIdentifier(found) == ObjectIdentifier(type) else { return nil }
        return type
    }
}
