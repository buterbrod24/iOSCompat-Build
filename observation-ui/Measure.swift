import Foundation
import Combine

@MainActor
private final class Model: Observable {
    let registrar = ObservationRegistrar()
    private var a = 0
    private var b = 0
    private var select = false
    var first: Int {
        get { registrar.access(self, keyPath: \.first); return a }
        set { registrar.withMutation(of: self, keyPath: \.first) { a = newValue } }
    }
    var second: Int {
        get { registrar.access(self, keyPath: \.second); return b }
        set { registrar.withMutation(of: self, keyPath: \.second) { b = newValue } }
    }
    var chooseSecond: Bool {
        get { registrar.access(self, keyPath: \.chooseSecond); return select }
        set { registrar.withMutation(of: self, keyPath: \.chooseSecond) { select = newValue } }
    }
}

@main struct Measure {
    @MainActor static func waitFor(_ predicate: () -> Bool) async -> Bool {
        for _ in 0..<100 {
            if predicate() { return true }
            try? await Task.sleep(nanoseconds: 5_000_000)
        }
        return predicate()
    }

    @MainActor static func main() async {
        var rows: [(String, Bool)] = []
        let model = Model()
        let bridge = CompatTrackedValue { model.first }
        var values: [Int] = []
        let subscription = bridge.$value.sink { values.append($0) }
        rows.append(("initial snapshot", bridge.value == 0 && values == [0]))
        model.second = 9
        try? await Task.sleep(nanoseconds: 20_000_000)
        rows.append(("unrelated property ignored", bridge.value == 0 && values == [0]))
        model.first = 1
        let first = await waitFor { bridge.value == 1 }
        rows.append(("post-mutation value", first && values == [0,1]))
        model.first = 2
        model.first = 3
        let coalesced = await waitFor { bridge.value == 3 }
        rows.append(("synchronous mutations coalesced", coalesced && values == [0,1,3]))
        model.first = 4
        let rearmed = await waitFor { bridge.value == 4 }
        rows.append(("tracking rearmed", rearmed && values == [0,1,3,4]))
        model.first = 5
        bridge.stop()
        try? await Task.sleep(nanoseconds: 20_000_000)
        rows.append(("queued callback invalidated by stop", bridge.value == 4))
        bridge.start()
        rows.append(("restart refreshes current value", bridge.value == 5 && values.last == 5))
        let conditional = Model()
        let selection = CompatTrackedValue { conditional.chooseSecond ? conditional.second : conditional.first }
        conditional.chooseSecond = true
        // The selection changes dependencies while leaving the value equal.
        // Wait for that asynchronous rearm before mutating the new dependency.
        try? await Task.sleep(nanoseconds: 30_000_000)
        conditional.second = 7
        let changed = await waitFor { selection.value == 7 }
        rows.append(("equal snapshot rearms changed dependencies", changed))
        weak var weakBridge: CompatTrackedValue<Int>?
        do {
            let transient = CompatTrackedValue { model.second }
            weakBridge = transient
            withExtendedLifetime(transient) {}
        }
        rows.append(("registration does not retain bridge", weakBridge == nil))
        withExtendedLifetime(subscription) {}
        for (name,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(name)") }
        print("TOTAL \(rows.filter { $0.1 }.count)/\(rows.count)")
        if rows.count != 9 || rows.contains(where: { !$0.1 }) { exit(1) }
    }
}
