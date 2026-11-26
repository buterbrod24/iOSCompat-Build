// Independent platform support for an isolated upstream Observation build.
// No changes to the system runtime.
import Foundation
import Darwin

internal struct _ManagedCriticalState<State> {
    private final class Storage {
        var state: State
        let lock = NSLock()
        init(_ value: State) { state = value }
    }
    private let storage: Storage
    internal init(_ initial: State) { storage = Storage(initial) }
    internal var id: ObjectIdentifier { ObjectIdentifier(storage) }
    internal func withCriticalRegion<R>(_ body: (inout State) throws -> R) rethrows -> R {
        storage.lock.lock()
        defer { storage.lock.unlock() }
        return try body(&storage.state)
    }
}
extension _ManagedCriticalState: @unchecked Sendable where State: Sendable {}

internal enum _ThreadLocal {
    private static let key: pthread_key_t = {
        var key = pthread_key_t()
        precondition(pthread_key_create(&key, nil) == 0)
        return key
    }()
    static var value: UnsafeMutableRawPointer? {
        get { pthread_getspecific(key) }
        set { precondition(pthread_setspecific(key, newValue) == 0) }
    }
}
