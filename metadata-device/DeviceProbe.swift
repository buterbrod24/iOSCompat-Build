import SwiftUI
import Foundation

@main struct MetadataDeviceProbe:App {
    var body:some Scene { WindowGroup { ProbeView() } }
}
private struct ProbeView:View {
    @State private var report="Ready — native metadata controls"
    @State private var ran=false
    @State private var url:URL?
    private var path:URL {
        FileManager.default.urls(for:.documentDirectory,in:.userDomainMask)[0]
            .appendingPathComponent("iOSCompat-MetadataReport-0.1.0.txt")
    }
    var body:some View {
        VStack(spacing:16) {
            Text("Metadata Probe 0.1.0").font(.title2.bold())
            Button("Run checks") { ran=true; run() }.disabled(ran)
            if let url { ShareLink(item:url) { Text("Share TXT report") } }
            ScrollView {
                Text(report).font(.system(.body,design:.monospaced))
                    .textSelection(.enabled).frame(maxWidth:.infinity,alignment:.leading)
            }
        }.padding().onAppear {
            if let saved=try? String(contentsOf:path,encoding:.utf8) {
                report=saved;url=path;ran=true
            }
        }
    }
    private func persist(_ rows:[String])->Bool {
        report=rows.joined(separator:"\n")
        do { try report.write(to:path,atomically:true,encoding:.utf8);url=path;return true }
        catch { report+="\nFAIL journal save: "+error.localizedDescription;return false }
    }
    private func run() {
        let v=ProcessInfo.processInfo.operatingSystemVersion
        var rows=["iOSCompat Metadata Probe 0.1.0","OS: "+ProcessInfo.processInfo.operatingSystemVersionString]
        guard v.majorVersion==16 && v.minorVersion==2 else {
            rows.append("STOP: restricted to iOS 16.2");_=persist(rows);return
        }
        rows.append("START native public metadata identity and conformance controls")
        guard persist(rows) else { return }
        let checks=MetadataChecks.run()
        for (n,ok) in checks { rows.append("\(ok ? "PASS" : "FAIL") \(n)") }
        rows.append("TOTAL \(checks.filter{$0.1}.count)/12")
        rows.append("NOTE: native public API behavior only; private entrypoints not invoked. No direct cache or completion-state inspection.")
        rows.append("COMPLETE")
        _=persist(rows)
    }
}
