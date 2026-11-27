import SwiftUI
import Foundation
import Darwin
import WitnessFixture

@main struct LegacyWitnessApp: App {
    var body: some Scene { WindowGroup { ProbeView() } }
}

private struct ProbeView: View {
    @State private var report = "Ready"
    @State private var ran = false
    @State private var reportURL: URL?
    private var path: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("iOSCompat-LegacyWitnessReport-0.1.0.txt")
    }
    var body: some View {
        VStack(spacing: 16) {
            Text("Legacy Witness Probe 0.1.0").font(.title2.bold())
            Button("Run checks") { ran = true; run() }.disabled(ran)
            if let reportURL { ShareLink(item: reportURL) { Text("Share TXT report") } }
            ScrollView {
                Text(report).font(.system(.body, design: .monospaced))
                    .textSelection(.enabled).frame(maxWidth: .infinity, alignment: .leading)
            }
        }.padding().onAppear {
            if let saved = try? String(contentsOf: path, encoding: .utf8) {
                report = saved; reportURL = path; ran = true
            }
        }
    }
    private func persist(_ lines: [String]) -> Bool {
        report = lines.joined(separator: "\n")
        do {
            try report.write(to: path, atomically: true, encoding: .utf8)
            reportURL = path
            return true
        } catch { report += "\nFAIL journal save"; return false }
    }
    private func run() {
        var lines = ["iOSCompat Legacy Witness Probe 0.1.0",
                     "OS: " + ProcessInfo.processInfo.operatingSystemVersionString]
        func log(_ line: String) -> Bool {
            lines.append(line); return persist(lines)
        }
        let v = ProcessInfo.processInfo.operatingSystemVersion
        guard v.majorVersion == 16 && v.minorVersion == 2 else {
            _ = log("STOP requires iOS 16.2"); return
        }
        guard log("START") else { return }
        guard let root = Bundle.main.privateFrameworksURL else {
            _ = log("STOP no frameworks directory"); return
        }
        guard log("BEGIN open fixture") else { return }
        guard let fixture = dlopen(root.appendingPathComponent("libWitnessFixture.dylib").path, RTLD_LAZY | RTLD_LOCAL) else {
            _ = log("STOP fixture unavailable"); return
        }
        defer { dlclose(fixture) }
        guard log("BEGIN open runtime") else { return }
        guard let runtime = dlopen("/usr/lib/swift/libswiftCore.dylib", RTLD_LAZY | RTLD_LOCAL) else {
            _ = log("STOP runtime unavailable"); return
        }
        defer { dlclose(runtime) }
        guard log("BEGIN resolve symbols") else { return }
        guard let descriptor = dlsym(fixture, "$s14WitnessFixture14CompatReadableMp"),
              let address = dlsym(runtime, "swift_conformsToProtocol") else {
            _ = log("STOP expected symbol unavailable"); return
        }
        typealias Lookup = @convention(c) (UnsafeRawPointer, UnsafeRawPointer) -> UnsafeRawPointer?
        let lookup = unsafeBitCast(address, to: Lookup.self)
        func query(_ type: Any.Type) -> UnsafeRawPointer? {
            lookup(unsafeBitCast(type, to: UnsafeRawPointer.self), UnsafeRawPointer(descriptor))
        }
        var passed = 0
        func result(_ name: String, _ ok: Bool) -> Bool {
            if ok { passed += 1 }
            return log("\(ok ? "PASS" : "FAIL") \(name)")
        }
        guard log("BEGIN positive array") else { return }
        let a = query(WitnessBox<[Int]>.self)
        guard result("positive array", a != nil), log("BEGIN positive string") else { return }
        let b = query(WitnessBox<String>.self)
        guard result("positive string", b != nil), log("BEGIN negative integer") else { return }
        let c = query(WitnessBox<Int>.self)
        guard result("negative integer", c == nil), log("BEGIN stable array witness") else { return }
        guard result("stable array witness", a != nil && query(WitnessBox<[Int]>.self) == a),
              log("BEGIN public dispatch") else { return }
        guard result("public dispatch", witnessCast(WitnessBox([1, 2])) == 2),
              log("BEGIN public rejection") else { return }
        guard result("public rejection", witnessCast(WitnessBox(42)) == nil) else { return }
        guard log("TOTAL \(passed)/6") else { return }
        _ = log("COMPLETE")
    }
}
