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
