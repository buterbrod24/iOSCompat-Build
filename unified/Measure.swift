// Read-only inspection of native Swift protocol descriptors.
// Layout: Swift ABI ProtocolDescriptor header (24 bytes), then
// GenericRequirementDescriptor (12 bytes), then ProtocolRequirement (8 bytes).
// Only known native exported descriptor addresses are read; no memory writes.
import Foundation
import Darwin
import AppIntents

public func measureAppIntents() -> String {
    var lines = ["iOSCompat AppIntents ABI 0.1.0", "OS: \(ProcessInfo.processInfo.operatingSystemVersionString)"]
    guard let h = dlopen("/System/Library/Frameworks/AppIntents.framework/AppIntents", RTLD_NOW | RTLD_LOCAL) else {
        return lines.joined(separator: "\n") + "\nFAIL native AppIntents load"
    }
    defer { dlclose(h) }
    let protocols = [
        ("AppIntent", "$s10AppIntents0A6IntentMp"),
        ("SystemIntent", "$s10AppIntents12SystemIntentMp"),
        ("LiveActivityStartingIntent", "$s10AppIntents26LiveActivityStartingIntentMp"),
        ("LiveActivityIntent", "$s10AppIntents18LiveActivityIntentMp")
    ]
    let requirements = [
        ("openAppWhenRun", "$s10AppIntents0A6IntentP04openA7WhenRunSbvgZTq"),
        ("title", "$s10AppIntents0A6IntentP5title10Foundation23LocalizedStringResourceVvgZTq"),
        ("isDiscoverable", "$s10AppIntents0A6IntentP14isDiscoverableSbvgZTq"),
        ("authenticationPolicy", "$s10AppIntents0A6IntentP20authenticationPolicyAA0c14AuthenticationE0OvgZTq"),
        ("description", "$s10AppIntents0A6IntentP11descriptionAA0C11DescriptionVSgvgZTq"),
        ("perform", "$s10AppIntents0A6IntentP7perform13PerformResultQzyYaKFTq"),
        ("SystemIntent.base", "$s10AppIntents12SystemIntentPAA0aD0Tb"),
        ("LiveActivityStartingIntent.base", "$s10AppIntents26LiveActivityStartingIntentPAA06SystemF0Tb"),
        ("LiveActivityIntent.base", "$s10AppIntents18LiveActivityIntentPAA06SystemE0Tb")
    ]
    for (name, symbol) in protocols {
        guard let ptr = dlsym(h, symbol) else {
            lines.append("\n\(name): ABSENT"); continue
        }
        let flags = ptr.load(as: UInt32.self)
        let generic = Int(ptr.load(fromByteOffset: 12, as: UInt32.self))
        let count = Int(ptr.load(fromByteOffset: 16, as: UInt32.self))
        // Fail closed on a non-protocol context kind or unreasonable counts.
        guard flags & 0x1f == 3, generic <= 64, count <= 128 else {
            lines.append("\n\(name): UNSUPPORTED flags=\(flags) signature=\(generic) requirements=\(count)")
            continue
        }
        let start = ptr.advanced(by: 24 + generic * 12)
        lines.append("\n\(name): flags=0x\(String(flags,radix:16)) signature=\(generic) requirements=\(count)")
        for i in 0..<count {
            let item = start.advanced(by: i*8)
            let f = item.load(as: UInt32.self)
            let relative = item.load(fromByteOffset: 4, as: Int32.self)
            let address = UInt(bitPattern: item)
            let matching = requirements.compactMap { pair -> String? in
                guard let sym = dlsym(h, pair.1), UInt(bitPattern: sym) == address else { return nil }
                return pair.0
            }.joined(separator: ",")
            // No dereference of relative implementation or invocation through it.
            lines.append("  slot \(i): flags=0x\(String(f,radix:16)) default=\(relative != 0) \(matching)")
        }
    }
    for (name, symbol) in requirements {
        lines.append("export \(name): \(dlsym(h, symbol) != nil)")
    }
    let old = "$s10AppIntents0A8ShortcutV6intent7phrases10shortTitle15systemImageNameACx_SayAA0aC6PhraseVyxGG10Foundation23LocalizedStringResourceVSgSSSgYttcAA0A6IntentRzlufC"
    let modern = "$s10AppIntents0A8ShortcutV6intent7phrases10shortTitle15systemImageNameACx_SayAA0aC6PhraseVyxGG10Foundation23LocalizedStringResourceVSSYttcAA0A6IntentRzlufC"
    lines.append("export old shortcut initializer: \(dlsym(h, old) != nil)")
    lines.append("export new shortcut initializer: \(dlsym(h, modern) != nil)")
    lines.append("export discoverability default: \(dlsym(h, "$s10AppIntents0A6IntentPAAE14isDiscoverableSbvgZ") != nil)")
    return lines.joined(separator: "\n")
}
