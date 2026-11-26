// Independent platform support for an isolated upstream Observation build.
// Avoid Foundation, whose modern overlay imports Observation.
import Darwin

internal struct _ManagedCriticalState<State> {
    private final class Storage {
        var state: State
        let mutex: UnsafeMutablePointer<pthread_mutex_t>
        init(_ value: State) {
            state = value
            mutex = .allocate(capacity: 1)
            mutex.initialize(to: pthread_mutex_t())
            precondition(pthread_mutex_init(mutex, nil) == 0)
        }
        deinit {
            precondition(pthread_mutex_destroy(mutex) == 0)
            mutex.deinitialize(count: 1)
            mutex.deallocate()
        }
    }
    private let storage: Storage
    internal init(_ initial: State) { storage = Storage(initial) }
    internal var id: ObjectIdentifier { ObjectIdentifier(storage) }
    internal func withCriticalRegion<R>(_ body: (inout State) throws -> R) rethrows -> R {
        let owner = storage
        precondition(pthread_mutex_lock(owner.mutex) == 0)
        defer { precondition(pthread_mutex_unlock(owner.mutex) == 0) }
        return try body(&owner.state)
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
