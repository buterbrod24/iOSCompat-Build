// Independent compiler evidence only, no system registration or app modification.
import AppIntents
import Foundation

@available(iOS 16.0, *)
public struct ReferenceIntent: AppIntent {
    public static var title: LocalizedStringResource { "Compatibility reference" }
    public init() {}
    public func perform() async throws -> some IntentResult { .result() }
}

@available(iOS 17.0, *)
public struct ReferenceLiveIntent: LiveActivityIntent {
    public static var title: LocalizedStringResource { "Compatibility reference" }
    public init() {}
    public func perform() async throws -> some IntentResult { .result() }
}

@available(iOS 17.0, *)
@inline(never)
public func discoverability<T: AppIntent>(_ type: T.Type) -> Bool {
    T.isDiscoverable
}

@available(iOS 17.0, *)
@inline(never)
public func shortcut<T: AppIntent>(_ intent: T, _ phrases: [AppShortcutPhrase<T>], _ title: LocalizedStringResource) -> AppShortcut {
    AppShortcut(intent: intent, phrases: phrases, shortTitle: title, systemImageName: "star")
}

 // Old public overload: use an optional title to select the iOS 16 signature.
@available(iOS 16.0, *)
@inline(never)
public func legacyShortcut<T: AppIntent>(_ intent: T, _ phrases: [AppShortcutPhrase<T>], _ title: LocalizedStringResource) -> AppShortcut {
    AppShortcut(intent: intent, phrases: phrases, shortTitle: Optional(title), systemImageName: "star")
}

@available(iOS 16.1, *)
public struct ReferenceStartingIntent: LiveActivityStartingIntent {
    public static var title: LocalizedStringResource { "Legacy activity reference" }
    public init() {}
    public func perform() async throws -> some IntentResult { .result() }
}

@available(iOS 16.0, *)
public struct ReferenceSystemIntent: SystemIntent {
    public static var title: LocalizedStringResource { "System intent reference" }
    public init() {}
    public func perform() async throws -> some IntentResult { .result() }
}
