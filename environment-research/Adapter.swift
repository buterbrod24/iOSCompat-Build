import SwiftUI

private struct CompatScopeKey:EnvironmentKey {
    static var defaultValue:CompatObjectScope { CompatObjectScope() }
}
private extension EnvironmentValues {
    var compatObjectScope:CompatObjectScope {
        get { self[CompatScopeKey.self] }
        set { self[CompatScopeKey.self]=newValue }
    }
}
@propertyWrapper
struct CompatEnvironmentObject<T:AnyObject & Observable>:DynamicProperty {
    @Environment(\.compatObjectScope) private var scope
    init(_ type:T.Type) {}
    var wrappedValue:T? { scope.object(T.self) }
}
@MainActor
private struct CompatScopeModifier<T:AnyObject & Observable>:ViewModifier {
    @Environment(\.compatObjectScope) private var inherited
    let value:T?
    func body(content:Content)->some View {
        content.environment(\.compatObjectScope,inherited.setting(T.self,value))
    }
}
extension View {
    @MainActor
    func compatEnvironment<T:AnyObject & Observable>(_ type:T.Type,_ value:T?)->some View {
        modifier(CompatScopeModifier(value:value))
    }
}
@MainActor
private struct CompatProjection<Model:AnyObject & Observable,Value:Equatable,Content:View>:View {
    @StateObject private var tracked:CompatTrackedValue<Value>
    let content:(Value)->Content
    init(model:Model,path:KeyPath<Model,Value>,content:@escaping(Value)->Content) {
        _tracked=StateObject(wrappedValue:CompatTrackedValue { model[keyPath:path] })
        self.content=content
    }
    var body:some View {
        content(tracked.value).onAppear { tracked.start() }.onDisappear { tracked.stop() }
    }
}
private struct ProjectionIdentity:Hashable {
    let model:ObjectIdentifier
    let path:AnyKeyPath
}
@MainActor
struct CompatEnvironmentProjection<Model:AnyObject & Observable,Value:Equatable,Content:View,Missing:View>:View {
    @CompatEnvironmentObject private var model:Model?
    private let path:KeyPath<Model,Value>
    private let content:(Value)->Content
    private let missing:()->Missing
    init(_ type:Model.Type,path:KeyPath<Model,Value>,
         @ViewBuilder content:@escaping(Value)->Content,@ViewBuilder missing:@escaping()->Missing) {
        _model=CompatEnvironmentObject(type)
        self.path=path;self.content=content;self.missing=missing
    }
    var body:some View {
        if let model {
            CompatProjection(model:model,path:path,content:content)
                .id(ProjectionIdentity(model:ObjectIdentifier(model),path:path))
        } else { missing() }
    }
}
