import Observation

// Compiled against Apple's unmodified SDK, never the candidate module.
public final class StockModel: Observable {
    public init() {}
    public var value: Int = 0
}

public func stockExercise(_ model: StockModel) -> Int {
    let registrar = ObservationRegistrar()
    registrar.access(model, keyPath: \.value)
    registrar.willSet(model, keyPath: \.value)
    model.value += 1
    registrar.didSet(model, keyPath: \.value)
    return registrar.withMutation(of: model, keyPath: \.value) {
        model.value += 1
        return model.value
    }
}

public func stockRegistrarType() -> Any.Type { ObservationRegistrar.self }
