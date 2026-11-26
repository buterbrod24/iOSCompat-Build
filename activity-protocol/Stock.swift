import AppIntents
import Foundation

@available(iOS 17.0, *)
public struct StockActivityIntent: LiveActivityIntent {
    public static var title: LocalizedStringResource { "Stock activity reference" }
    public static var openAppWhenRun: Bool { true }
    public init() {}
    public func perform() async throws -> some IntentResult { .result() }
}
@available(iOS 17.0, *)
@inline(never)
public func stockThroughSystem<T:SystemIntent>(_ type:T.Type)->Bool {
    T.openAppWhenRun
}
@available(iOS 17.0, *)
@inline(never)
public func stockThroughActivity<T:LiveActivityIntent>(_ type:T.Type)->Bool {
    stockThroughSystem(type)
}
@available(iOS 17.0, *)
@inline(never)
public func stockDynamic(_ value:Any)->Bool {
    value is any LiveActivityIntent
}
