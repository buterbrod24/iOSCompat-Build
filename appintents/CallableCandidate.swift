// Isolated candidate: preserve every caller value through the old public initializer.
// No protocol descriptors, no system registration, no application patch.
import AppIntents
import Foundation

@available(iOS 16.0, *)
@inline(never)
public func ioscompatShortcut<T: AppIntent>(intent: T, phrases: [AppShortcutPhrase<T>], shortTitle: LocalizedStringResource, systemImageName: String) -> AppShortcut {
    // Capture the typed old initializer to avoid a call-site literal restriction
    // while preserving the original string and title. Compiler acceptance is a gate.
    let old: (T, [AppShortcutPhrase<T>], LocalizedStringResource?, String?) -> AppShortcut = AppShortcut.init(intent:phrases:shortTitle:systemImageName:)
    return old(intent, phrases, .some(shortTitle), .some(systemImageName))
}

@available(iOS 16.0, *)
public extension AppIntent {
    // Only the SDK's measured default implementation, not witness dispatch.
    @inline(never)
    static var ioscompatDefaultDiscoverable: Bool { true }
}
