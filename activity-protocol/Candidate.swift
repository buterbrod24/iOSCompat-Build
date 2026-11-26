import AppIntents
import Foundation

// Independent protocol for structural research. This does NOT claim native
// LiveActivityIntent identity and is not registered with any system service.
@available(iOS 16.0, *)
public protocol CompatLiveActivityIntent: SystemIntent {}

@available(iOS 16.0, *)
public struct LocalActivityIntent: CompatLiveActivityIntent {
    public static var title: LocalizedStringResource { "Local activity reference" }
    public static var openAppWhenRun: Bool { true }
    public init() {}
    public func perform() async throws -> some IntentResult { .result() }
}
@available(iOS 16.0, *)
@inline(never)
public func localThroughSystem<T:SystemIntent>(_ type:T.Type)->Bool {
    T.openAppWhenRun
}
@available(iOS 16.0, *)
@inline(never)
public func localThroughActivity<T:CompatLiveActivityIntent>(_ type:T.Type)->Bool {
    localThroughSystem(type)
}
@available(iOS 16.0, *)
@inline(never)
public func localDynamic(_ value:Any)->Bool {
    value is any CompatLiveActivityIntent
}
