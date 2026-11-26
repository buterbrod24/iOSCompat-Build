// Independent SDK test; no donated intents, registration, or application data.
import AppIntents
import Foundation

@available(iOS 16.0, *)
public struct ProbeIntent: AppIntent {
    public static var title: LocalizedStringResource { "Compatibility test" }
    public init() {}
    public func perform() async throws -> some IntentResult { .result() }
}

// Availability is compile-time only for this isolated, explicitly rebound test.
// Do not use this entry in an application with unmodified imports.
@available(iOS 17.0, *)
@_cdecl("ioscompat_stock_shortcut_test")
public func stockShortcutTest() -> Int32 {
    let value = AppShortcut(intent: ProbeIntent(), phrases: [],
                            shortTitle: "Compatibility test", systemImageName: "star")
    // Force the value to escape without registering or executing it.
    return withExtendedLifetime(value) { 1 }
}

// Concrete static access must compile to the default extension getter,
// not the newer generic protocol witness dispatch. CI checks the IR.
@available(iOS 17.0, *)
@_cdecl("ioscompat_stock_default_test")
public func stockDefaultTest() -> Int32 {
    ProbeIntent.isDiscoverable ? 1 : 0
}

@available(iOS 16.0, *)
public struct ExplicitHiddenIntent: AppIntent {
    public static var title: LocalizedStringResource { "Hidden compatibility test" }
    public static var isDiscoverable: Bool { false }
    public init() {}
    public func perform() async throws -> some IntentResult { .result() }
}

@available(iOS 17.0, *)
@_cdecl("ioscompat_stock_explicit_test")
public func stockExplicitTest() -> Int32 {
    ExplicitHiddenIntent.isDiscoverable ? 1 : 0
}
