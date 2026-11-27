import Combine

// Original source-level bridge, not a SwiftUI ABI replacement.
// Reads and model writes must be confined to MainActor.
@MainActor
final class CompatTrackedValue<Value: Equatable>: ObservableObject {
    @Published private(set) var value: Value
    private let read: () -> Value
    private var active = false
    private var epoch: UInt64 = 0

    init(read: @escaping () -> Value) {
        self.read = read
        self.value = read()
        start()
    }

    func start() {
        guard !active else { return }
        active = true
        arm()
    }

    func stop() {
        active = false
        epoch &+= 1
        // The upstream one-shot registration may remain until mutation.
        // Its weak callback cannot retain this object or publish stale data.
    }

    private func arm() {
        epoch &+= 1
        let expected = epoch
        let snapshot = withObservationTracking({ read() }) { [weak self] in
            // Observation's callback occurs at willSet, so read after the
            // synchronous mutation finishes, not from inside the callback.
            Task { @MainActor [weak self] in
                guard let self, self.active, self.epoch == expected else { return }
                self.arm()
            }
        }
        // Always rearm, even when the new dependency set yields an equal value.
        if snapshot != value { value = snapshot }
    }
}
