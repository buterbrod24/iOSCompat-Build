import SwiftUI
import Foundation
import Darwin

@main struct ExportProbe:App {
    var body:some Scene { WindowGroup { ProbeView() } }
}
private struct ProbeView:View {
    @State private var report="Ready — scoped native lookup"
    @State private var ran=false
    @State private var url:URL?
    private var path:URL {
        FileManager.default.urls(for:.documentDirectory,in:.userDomainMask)[0]
            .appendingPathComponent("iOSCompat-SystemExportReport-0.1.0.txt")
    }
    var body:some View {
        VStack(spacing:16) {
            Text("System Export Probe 0.1.0").font(.title2.bold())
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
    private func lookup(_ handle:UnsafeMutableRawPointer?,_ symbol:String)->String {
        guard let handle else { return "UNKNOWN" }
        _=dlerror()
        let ptr=dlsym(handle,symbol)
        let error=dlerror()
        if ptr != nil && error == nil { return "PRESENT" }
        if ptr == nil && error != nil { return "ABSENT" }
        return "UNKNOWN"
    }
    private func run() {
        let v=ProcessInfo.processInfo.operatingSystemVersion
        var rows=["iOSCompat System Export Probe 0.1.0","OS: "+ProcessInfo.processInfo.operatingSystemVersionString]
        guard v.majorVersion==16 && v.minorVersion==2 else {
            rows.append("STOP: restricted to iOS 16.2");_=persist(rows);return
        }
        guard let manifestURL=Bundle.main.url(forResource:"queries",withExtension:"json"),
              let data=try? Data(contentsOf:manifestURL),
              let queries=try? JSONDecoder().decode([String:[String]].self,from:data) else {
            rows.append("STOP: manifest unavailable");_=persist(rows);return
        }
        rows.append("START")
        guard persist(rows) else { return }
        var total=0
        for provider in queries.keys.sorted() {
            rows.append("PROVIDER\t"+provider)
            guard persist(rows) else { return }
            let first=dlopen(provider,RTLD_LAZY|RTLD_LOCAL|RTLD_FIRST)
            let tree=dlopen(provider,RTLD_LAZY|RTLD_LOCAL)
            defer { if let first { dlclose(first) }; if let tree { dlclose(tree) } }
            rows.append("HANDLES\t\(first == nil ? "UNAVAILABLE" : "OPEN")\t\(tree == nil ? "UNAVAILABLE" : "OPEN")")
            for symbol in queries[provider] ?? [] {
                rows.append("LOOKUP\t"+symbol+"\t"+lookup(first,symbol)+"\t"+lookup(tree,symbol))
                total+=1
                guard persist(rows) else { return }
            }
        }
        rows.append("TOTAL\t\(total)")
        rows.append("COMPLETE")
        _=persist(rows)
    }
}
