import Darwin

// Manual Observable conformance avoids macro/toolchain dependence.
// The test executable uses an isolated module name, never the simulator's Observation.
private final class Model: Observable, @unchecked Sendable {
    let registrar = ObservationRegistrar()
    private var a = 0
    private var b = 0
    var first: Int {
        get { registrar.access(self, keyPath: \.first); return a }
        set { registrar.withMutation(of: self, keyPath: \.first) { a = newValue } }
    }
    var second: Int {
        get { registrar.access(self, keyPath: \.second); return b }
        set { registrar.withMutation(of: self, keyPath: \.second) { b = newValue } }
    }
}
private final class Counter: @unchecked Sendable {
    // All reads and writes in these controls are synchronous on one thread.
    var value = 0
}
private enum Sentinel: Error { case expected }

enum ObservationChecks {
    static func run() -> [(String, Bool)] {
        var rows: [(String, Bool)] = []
        let model = Model()
        let hits = Counter()
        let before = Counter()
        let result = withObservationTracking({ model.first }) {
            hits.value += 1
            before.value = model.first
        }
        rows.append(("tracking returns value", result == 0))
        model.second = 1
        rows.append(("unrelated property ignored", hits.value == 0))
        model.first = 7
        rows.append(("tracked mutation notifies", hits.value == 1 && model.first == 7))
        rows.append(("willSet observes old value", before.value == 0))
        model.first = 8
        rows.append(("one-shot notification", hits.value == 1))
        _ = withObservationTracking({ model.first }) { hits.value += 1 }
        let other = Model()
        other.first = 9
        rows.append(("independent registrar identity", hits.value == 1))
        model.first = 10
        rows.append(("tracking can be installed again", hits.value == 2))
        let failure = Counter()
        _ = withObservationTracking({ model.first }) { failure.value += 1 }
        var caught = false
        do {
            try model.registrar.withMutation(of: model, keyPath: \.first) {
                throw Sentinel.expected
            }
        } catch Sentinel.expected { caught = true } catch {}
        rows.append(("throwing mutation propagates error", caught && failure.value == 1 && model.first == 10))
        return rows
    }
}
