import SwiftUI

@available(iOS 17.0, *)
public struct StockAdaptiveStyle:ShapeStyle {
    public init() {}
    public func resolve(in environment:EnvironmentValues)->some ShapeStyle {
        environment.colorScheme == .dark ? Color.white : Color.black
    }
}
@available(iOS 17.0, *)
public func stockResolve<S:ShapeStyle>(_ style:S,_ environment:EnvironmentValues)->S.Resolved {
    style.resolve(in:environment)
}
@available(iOS 17.0, *)
public func stockColor(_ color:Color,_ environment:EnvironmentValues)->Color.Resolved {
    color.resolve(in:environment)
}
@available(iOS 17.0, *)
public func stockText<S:ShapeStyle>(_ text:Text,_ style:S)->Text {
    text.foregroundStyle(style)
}
