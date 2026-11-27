import Observation
import Darwin

// This file is compiled with the unmodified Apple SDK before the candidate exists.
@available(iOS 17.0, *)
private final class Model: Observable, @unchecked Sendable {
    let registrar = ObservationRegistrar()
    private var stored = 0
    private var other = 0
    var value: Int {
        get { registrar.access(self, keyPath: \.value); return stored }
        set { registrar.withMutation(of: self, keyPath: \.value) { stored = newValue } }
    }
    var unrelated: Int {
        get { registrar.access(self, keyPath: \.unrelated); return other }
        set { registrar.withMutation(of: self, keyPath: \.unrelated) { other = newValue } }
    }
    func explicitMutation(_ value: Int) {
        registrar.willSet(self, keyPath: \.value)
        stored = value
        registrar.didSet(self, keyPath: \.value)
    }
}
private final class Count: @unchecked Sendable { var value = 0 }
private enum Expected: Error { case failure }

@available(iOS 17.0, *)
@_cdecl("ioscompat_stock_observation_checks")
public func stockObservationChecks() -> Int32 {
        var rows: [(String, Bool)] = []
        let model = Model()
        let hits = Count()
        let read = withObservationTracking({ model.value }) { hits.value += 1 }
        rows.append(("stock tracking read", read == 0))
        model.unrelated = 1
        rows.append(("stock unrelated property", hits.value == 0))
        model.value = 2
        rows.append(("stock mutation notification", hits.value == 1 && model.value == 2))
        model.value = 3
        rows.append(("stock one-shot", hits.value == 1))
        _ = withObservationTracking({ model.value }) { hits.value += 1 }
        model.explicitMutation(4)
        rows.append(("stock explicit willSet/didSet", hits.value == 2 && model.value == 4))
        let other = Model()
        let second = Count()
        _ = withObservationTracking({ model.value }) { second.value += 1 }
        other.value = 9
        rows.append(("stock identity isolation", second.value == 0))
        var caught = false
        do {
            try model.registrar.withMutation(of: model, keyPath: \.value) { throw Expected.failure }
        } catch Expected.failure { caught = true } catch {}
        rows.append(("stock throwing mutation", caught && second.value == 1 && model.value == 4))
        let erased: Any = model
        rows.append(("stock protocol conformance", erased is any Observable && !((42 as Any) is any Observable)))
        let copy = model.registrar
        let copiedHits = Count()
        _ = withObservationTracking({ model.value }) { copiedHits.value += 1 }
        copy.willSet(model, keyPath: \.value)
        copy.didSet(model, keyPath: \.value)
        rows.append(("stock registrar copy identity", copiedHits.value == 1))
        let meta: Any.Type = ObservationRegistrar.self
        rows.append(("stock registrar metadata identity", ObjectIdentifier(meta) == ObjectIdentifier(ObservationRegistrar.self)))
        guard rows.count == 10 else { return -1 }
        var mask: Int32 = 0
        for (i, row) in rows.enumerated() where row.1 { mask |= Int32(1) << i }
        return mask
}
