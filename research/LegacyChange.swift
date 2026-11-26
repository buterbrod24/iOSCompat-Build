import SwiftUI

// Source-level backport research, deliberately NOT exported under a native
// opaque-result symbol. Native SwiftUI modifier metadata is not interchangeable.
@available(iOS 16.0, *)
public struct LegacyChangeState<Value: Equatable> {
    private var previous: Value?
    private var started = false
    public init() {}
    public mutating func receive(_ value: Value, initial: Bool) -> (Value,Value)? {
        guard started else {
            started = true; previous = value
            return initial ? (value,value) : nil
        }
        // Outer optional indicates that a value was captured, even if Value is Optional.
        guard let old = previous else {
            preconditionFailure("Missing previous state")
        }
        previous = value
        return old == value ? nil : (old,value)
    }
}

@available(iOS 16.0, *)
private struct LegacyChangeModifier<Value:Equatable>:ViewModifier {
    let value:Value
    let initial:Bool
    let action:(Value,Value)->Void
    @State private var state = LegacyChangeState<Value>()
    private func receive(_ value:Value) {
        if let pair = state.receive(value,initial:initial) { action(pair.0,pair.1) }
    }
    func body(content:Content)->some View {
        content.onAppear { receive(value) }
               .onChange(of:value) { next in receive(next) }
    }
}

@available(iOS 16.0, *)
public extension View {
    func ioscompatOnChange<Value:Equatable>(of value:Value, initial:Bool = false,
                                             _ action:@escaping (Value,Value)->Void)->some View {
        modifier(LegacyChangeModifier(value:value,initial:initial,action:action))
    }
    func ioscompatOnChange<Value:Equatable>(of value:Value, initial:Bool = false,
                                             _ action:@escaping ()->Void)->some View {
        ioscompatOnChange(of:value,initial:initial) { _,_ in action() }
    }
}
