import UIKit
import SwiftUI
import Foundation
import Darwin

// Each test returns a result, not a claim that a newer framework was ported.
struct ProbeCase {
    let name: String
    let run: () async throws -> String
}
enum ProbeFailure: Error, CustomStringConvertible {
    case failed(String)
    var description: String { switch self { case .failed(let reason): return reason } }
}
func require(_ ok: Bool, _ why: String) throws {
    if !ok { throw ProbeFailure.failed(why) }
}
@MainActor final class Suites {
    private var compat: UnsafeMutableRawPointer?
    private var stock: UnsafeMutableRawPointer?
    private let frameworks = Bundle.main.privateFrameworksPath ?? ""
    private func open(_ name: String) throws -> UnsafeMutableRawPointer {
        guard let h = dlopen(frameworks + "/" + name, RTLD_NOW | RTLD_LOCAL) else {
            throw ProbeFailure.failed(dlerror().map { String(cString: $0) } ?? "dlopen failed")
        }
        return h
    }
    private func compatibility() throws -> UnsafeMutableRawPointer {
        if let h = compat { return h }
        let h = try open("libAppIntentsCompat.dylib"); compat = h; return h
    }
    private func client() throws -> UnsafeMutableRawPointer {
        if let h = stock { return h }
        _ = try compatibility()
        let h = try open("libAppIntentsStockClient.dylib"); stock = h; return h
    }
    private func call(_ name: String, expected: Int32) throws -> String {
        guard let ptr = dlsym(try client(), name) else { throw ProbeFailure.failed("No entry: " + name) }
        typealias Test = @convention(c) () -> Int32
        let actual = unsafeBitCast(ptr, to: Test.self)()
        try require(actual == expected, "returned \(actual), expected \(expected)")
        return "returned \(actual)"
    }
    func cases() -> [ProbeCase] {
        let shortcut = "$s10AppIntents0A8ShortcutV6intent7phrases10shortTitle15systemImageNameACx_SayAA0aC6PhraseVyxGG10Foundation23LocalizedStringResourceVSSYttcAA0A6IntentRzlufC"
        let getter = "$s10AppIntents0A6IntentPAAE14isDiscoverableSbvgZ"
        return [
            .init(name:"AppIntents / load compatibility library") { _ = try self.compatibility(); return "loaded" },
            .init(name:"AppIntents / initializer export") { let h = try self.compatibility(); try require(dlsym(h,shortcut) != nil,"missing"); return "resolved" },
            .init(name:"AppIntents / default export") { let h = try self.compatibility(); try require(dlsym(h,getter) != nil,"missing"); return "resolved" },
            .init(name:"AppIntents / load independent SDK client") { _ = try self.client(); return "loaded" },
            .init(name:"AppIntents / stock shortcut construction") { try self.call("ioscompat_stock_shortcut_test",expected:1) },
            .init(name:"AppIntents / actual default getter") { try self.call("ioscompat_stock_default_test",expected:1) },
            .init(name:"AppIntents / explicit false") { try self.call("ioscompat_stock_explicit_test",expected:0) },
            .init(name:"AppIntents / native descriptor evidence") { measureAppIntents() },
            .init(name:"Swift Core / reference array copy-on-write") {
                let object = NSObject()
                let source = [object]
                var copy = source
                copy.reserveCapacity(64)
                copy.append(NSObject())
                try require(source.count == 1 && copy.count == 2 && copy[0] === object,"copy or identity mismatch")
                return "native Array baseline only"
            },
            .init(name:"Swift Core / contiguous reference buffer") {
                let item = NSObject()
                var a: ContiguousArray<NSObject> = [item]
                let before = a
                a.reserveCapacity(32)
                a.append(NSObject())
                try require(before.count == 1 && a.count == 2 && a[0] === item,"buffer or identity mismatch")
                return "native ContiguousArray baseline only"
            },
            .init(name:"Swift Core / runtime export evidence") {
                try self.exports("/usr/lib/swift/libswiftCore.dylib",[
                    "swift_conformsToProtocol","swift_conformsToProtocol2",
                    "swift_getOpaqueTypeMetadata","swift_getOpaqueTypeMetadata2",
                    "swift_getOpaqueTypeConformance","swift_getOpaqueTypeConformance2",
                    "swift_getTypeByMangledNameInContext","swift_getTypeByMangledNameInContext2",
                    "swift_getTypeByMangledNameInContextInMetadataState","swift_getTypeByMangledNameInContextInMetadataState2"])
            },
            .init(name:"Concurrency / AsyncStream legacy continuation") {
                let stream = AsyncStream<Int>(bufferingPolicy:.bufferingNewest(2)) { c in
                    c.yield(1); c.yield(2); c.yield(3); c.finish()
                }
                var values:[Int] = []
                for await x in stream { values.append(x) }
                try require(values == [2,3],"unexpected stream values \(values)")
                return "legacy bufferingNewest and finish"
            },
            .init(name:"Concurrency / AsyncThrowingStream legacy continuation") {
                let stream = AsyncThrowingStream<Int,Error> { c in c.yield(7); c.finish(throwing:ProbeFailure.failed("sentinel")) }
                var values:[Int] = []; var caught = false
                do { for try await x in stream { values.append(x) } }
                catch let e as ProbeFailure { caught = e.description == "sentinel" }
                catch { throw error }
                try require(values == [7] && caught,"value or error not delivered")
                return "legacy value and error delivery"
            },
            .init(name:"Concurrency / executor and stream exports") {
                try self.exports("/usr/lib/swift/libswift_Concurrency.dylib",[
                    "$sScF7enqueueyys11ExecutorJobVnFTq","$sScF7enqueueyys3JobVnFTq",
                    "$sScf7enqueueyys11ExecutorJobVnFTq","$sScf7enqueueyys3JobVnFTq",
                    "$sScS10makeStream2of15bufferingPolicyScSyxG6stream_ScS12ContinuationVyx_G12continuationtxm_AG09BufferingE0Oyx__GtFZ"])
            },
            .init(name:"SwiftUI / native hosting and layout") {
                let view = VStack { Text("Compatibility").font(.body); Color.blue.frame(width:24,height:24) }.padding()
                let host = UIHostingController(rootView:view)
                host.loadViewIfNeeded()
                host.view.frame = CGRect(x:0,y:0,width:240,height:160)
                host.view.setNeedsLayout(); host.view.layoutIfNeeded()
                let size = host.sizeThatFits(in:CGSize(width:240,height:160))
                try require(size.width.isFinite && size.height.isFinite && size.width > 0 && size.height > 0,"invalid size")
                return "native hosting size \(size.width) x \(size.height)"
            },
            .init(name:"SwiftUI / old transitions, scrolling and text") {
                let view = ScrollView { VStack { Text("Baseline").monospaced(); Text("Transition").transition(.opacity.combined(with:.move(edge:.top))) } }
                let host = UIHostingController(rootView:view)
                host.loadViewIfNeeded()
                host.view.frame = CGRect(x:0,y:0,width:240,height:160)
                host.view.layoutIfNeeded()
                try require(host.view.bounds.size.width == 240,"hosting bounds mismatch")
                return "native old API baseline only; no new animation behavior claim"
            },
            .init(name:"SwiftUI / protocol export evidence") {
                try self.exports("/System/Library/Frameworks/SwiftUI.framework/SwiftUI",[
                    "$s7SwiftUI4ViewMp","$s7SwiftUI10ShapeStyleMp","$s7SwiftUI6LayoutMp",
                    "$s7SwiftUI10ShapeStyleP7resolve2in8ResolvedQzAA17EnvironmentValuesV_tFTq",
                    "$s7SwiftUI19UIViewRepresentableP14_layoutOptionsyAA013_PlatformViewd6LayoutF0V0C4TypeQzFZTq",
                    "$s7SwiftUI29UIViewControllerRepresentableP14_layoutOptionsyAA013_PlatformViewe6LayoutG0V0cD4TypeQzFZTq"])
            }
        ]
    }
    private func exports(_ path:String, _ names:[String]) throws -> String {
        guard let h = dlopen(path,RTLD_LAZY|RTLD_LOCAL) else { throw ProbeFailure.failed("native provider unavailable") }
        defer { dlclose(h) }
        return "READ-ONLY evidence (absence is not a test failure):\n" + names.map { name in
            "\(dlsym(h,name) == nil ? "ABSENT" : "PRESENT") \(name)"
        }.joined(separator:"\n")
    }
}
