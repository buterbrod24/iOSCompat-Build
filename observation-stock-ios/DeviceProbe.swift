import SwiftUI
import Foundation
import Darwin

@main struct ObservationStockProbe: App {
    var body: some Scene { WindowGroup { ProbeView() } }
}

private struct ProbeView: View {
    @State private var report = "Ready — independent SDK client"
    @State private var ran = false
    @State private var url: URL?
    private let names = ["stock tracking read", "stock unrelated property",
                         "stock mutation notification", "stock one-shot",
                         "stock explicit willSet/didSet", "stock identity isolation",
                         "stock throwing mutation", "stock protocol conformance",
                         "stock registrar copy identity", "stock registrar metadata identity"]
    private let symbols = [
        "$s11Observation04withA8Tracking_8onChangexxyXE_yyYbcyXKtlF",
        "$s11Observation0A9RegistrarV12withMutation2of7keyPath_q0_x_s03KeyG0Cyxq_Gq0_yKXEtKAA10ObservableRzr1_lF",
        "$s11Observation0A9RegistrarV6access_7keyPathyx_s03KeyE0Cyxq_GtAA10ObservableRzr0_lF",
        "$s11Observation0A9RegistrarV6didSet_7keyPathyx_s03KeyF0Cyxq_GtAA10ObservableRzr0_lF",
        "$s11Observation0A9RegistrarV7willSet_7keyPathyx_s03KeyF0Cyxq_GtAA10ObservableRzr0_lF",
        "$s11Observation0A9RegistrarVACycfC",
        "$s11Observation0A9RegistrarVMa",
        "$s11Observation0A9RegistrarVMn",
        "$s11Observation10ObservableMp"
    ]
    private var reportPath: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("iOSCompat-ObservationReport-0.2.0.txt")
    }
    var body: some View {
        VStack(spacing: 16) {
            Text("Observation Probe 0.2.0").font(.title2.bold())
            Button("Run independent checks") { ran = true; run() }.disabled(ran)
            if let url { ShareLink(item: url) { Text("Share TXT report") } }
            ScrollView {
                Text(report).font(.system(.body, design: .monospaced))
                    .textSelection(.enabled).frame(maxWidth: .infinity, alignment: .leading)
            }
        }.padding().onAppear {
            if let old = try? String(contentsOf: reportPath, encoding: .utf8) {
                report = old
                url = reportPath
                ran = true
            }
        }
    }
    private func persist(_ rows: [String]) -> Bool {
        report = rows.joined(separator: "\n")
        do {
            try report.write(to: reportPath, atomically: true, encoding: .utf8)
            url = reportPath
            return true
        } catch {
            report += "\nFAIL journal save: " + error.localizedDescription
            return false
        }
    }
    private func loadError() -> String { dlerror().map { String(cString: $0) } ?? "unknown loader error" }
    private func run() {
        let version = ProcessInfo.processInfo.operatingSystemVersion
        var rows = ["iOSCompat Observation Probe 0.2.0", "OS: " + ProcessInfo.processInfo.operatingSystemVersionString]
        guard version.majorVersion == 16 && version.minorVersion == 2 else {
            rows.append("STOP: this probe is restricted to iOS 16.2")
            _ = persist(rows)
            return
        }
        guard let frameworks = Bundle.main.privateFrameworksPath else {
            rows.append("FAIL missing Frameworks directory"); _ = persist(rows); return
        }
        rows.append("START candidate load")
        guard persist(rows) else { return }
        guard let candidate = dlopen(frameworks + "/libObservationResearch.dylib", RTLD_NOW | RTLD_LOCAL | RTLD_FIRST) else {
            rows.append("FAIL candidate load: " + loadError()); _ = persist(rows); return
        }
        rows.append("PASS candidate load")
        for name in symbols {
            guard dlsym(candidate, name) != nil else {
                rows.append("FAIL candidate export " + name); _ = persist(rows); return
            }
        }
        rows.append("PASS candidate exports 9/9")
        rows.append("START independent SDK client load")
        guard persist(rows) else { return }
        guard let stock = dlopen(frameworks + "/libStockObservationIOS.dylib", RTLD_NOW | RTLD_LOCAL | RTLD_FIRST) else {
            rows.append("FAIL client load: " + loadError()); _ = persist(rows); return
        }
        rows.append("PASS independent SDK client load")
        guard let entry = dlsym(stock, "ioscompat_stock_observation_checks") else {
            rows.append("FAIL missing stock entry"); _ = persist(rows); return
        }
        rows.append("START independent SDK batch (if interrupted, report this line)")
        guard persist(rows) else { return }
        typealias Check = @convention(c) () -> Int32
        let mask = unsafeBitCast(entry, to: Check.self)()
        guard mask >= 0 && mask <= 1023 else {
            rows.append("FAIL invalid batch result"); _ = persist(rows); return
        }
        for (i, name) in names.enumerated() {
            rows.append("\((mask & (Int32(1) << i)) != 0 ? "PASS" : "FAIL") \(name)")
        }
        rows.append("TOTAL \(mask.nonzeroBitCount)/10")
        _ = persist(rows)
        // Keep both handles alive: Swift metadata and conformances may outlive this call.
    }
}
