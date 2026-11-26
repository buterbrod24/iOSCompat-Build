import Darwin
import Dispatch

// Independent native Darwin stress controls. Each worker owns its observed model.
private final class WorkerModel: Observable {
    let registrar = ObservationRegistrar()
    private var storage = 0
    var value: Int {
        get { registrar.access(self, keyPath: \.value); return storage }
        set { registrar.withMutation(of: self, keyPath: \.value) { storage = newValue } }
    }
}
private final class Count: @unchecked Sendable {
    let state = _ManagedCriticalState(0)
    func increment() { state.withCriticalRegion { $0 += 1 } }
    var value: Int { state.withCriticalRegion { $0 } }
}

@main struct HostControls {
    static func main() {
        var rows = ObservationChecks.run()
        let count = Count()
        DispatchQueue.concurrentPerform(iterations: 1000) { _ in count.increment() }
        rows.append(("mutex serializes 1000 increments", count.value == 1000))
        let passed = Count()
        DispatchQueue.concurrentPerform(iterations: 128) { _ in
            let model = WorkerModel()
            let hits = Count()
            let read = withObservationTracking({ model.value }) { hits.increment() }
            model.value = 1
            model.value = 2
            if read == 0 && hits.value == 1 && model.value == 2 && _ThreadLocal.value == nil {
                passed.increment()
            }
        }
        rows.append(("128 isolated concurrent trackers and TLS cleanup", passed.value == 128))
        let model = WorkerModel()
        let outer = Count()
        let inner = Count()
        _ = withObservationTracking({
            withObservationTracking({ model.value }) { inner.increment() }
        }) { outer.increment() }
        model.value = 3
        model.value = 4
        rows.append(("nested tracking merges and cancels", outer.value == 1 && inner.value == 1))
        rows.append(("TLS restored after nested tracking", _ThreadLocal.value == nil))
        for (name, ok) in rows { print("\(ok ? "PASS" : "FAIL") \(name)") }
        print("TOTAL \(rows.filter { $0.1 }.count)/\(rows.count)")
        if rows.count != 12 || rows.contains(where: { !$0.1 }) { exit(1) }
    }
}
