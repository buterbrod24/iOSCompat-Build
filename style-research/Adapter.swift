import SwiftUI

// Explicit resolver; never claims to implement the modern native ShapeStyle ABI.
public struct CompatStyleResolver {
    private let resolveValue:(EnvironmentValues)->AnyShapeStyle
    public init<S:ShapeStyle>(_ resolve:@escaping(EnvironmentValues)->S) {
        resolveValue={ AnyShapeStyle(resolve($0)) }
    }
    public func resolve(in environment:EnvironmentValues)->AnyShapeStyle {
        resolveValue(environment)
    }
}
@MainActor
private struct CompatForeground:ViewModifier {
    @Environment(\.self) private var environment
    let resolver:CompatStyleResolver
    func body(content:Content)->some View {
        content.foregroundStyle(resolver.resolve(in:environment))
    }
}
public extension View {
    @MainActor
    func compatForegroundStyle(_ resolver:CompatStyleResolver)->some View {
        modifier(CompatForeground(resolver:resolver))
    }
}
@MainActor
public struct CompatFilledShape<S:Shape>:View {
    @Environment(\.self) private var environment
    let shape:S
    let resolver:CompatStyleResolver
    public init(_ shape:S,style:CompatStyleResolver) {
        self.shape=shape;self.resolver=style
    }
    public var body:some View {
        shape.fill(resolver.resolve(in:environment))
    }
}
