import UIKit
import SwiftUI
import Foundation
import Darwin
import AppIntents

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
        var tests: [ProbeCase] = [
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
        tests.append(contentsOf: batchCases())
        tests.append(contentsOf: activityCases())
        tests.append(contentsOf: runtimeBaselineCases())
        tests.append(contentsOf: executorCases())
        return tests
    }

    private var batchHandles: [String: UnsafeMutableRawPointer] = [:]
    private var streamStarted = false
    func resetBatchAttempt() { streamStarted = false }
    private func batchHandle(_ name: String) throws -> UnsafeMutableRawPointer {
        if let h = batchHandles[name] { return h }
        let h = try open(name)
        batchHandles[name] = h
        return h
    }
    private func batchCases() -> [ProbeCase] {
        [
            .init(name:"Concurrency / new compatibility library loads") {
                _ = try self.batchHandle("libConcurrencyCompat.dylib")
                return "loaded"
            },
            .init(name:"Concurrency / independent stock client loads") {
                _ = try self.batchHandle("libConcurrencyCompat.dylib")
                let h = try self.batchHandle("libConcurrencyStockClient.dylib")
                try require(dlsym(h,"ioscompat_stock_stream_tests") != nil,"missing independent test entry")
                return "loaded and entry resolved"
            },
            .init(name:"Concurrency / stock makeStream functional batch") {
                try await self.runStreamBatch()
            },
            .init(name:"SwiftUI / new compatibility library loads") {
                _ = try self.batchHandle("libSwiftUICompat.dylib")
                return "loaded"
            },
            .init(name:"SwiftUI / independent stock client loads") {
                _ = try self.batchHandle("libSwiftUICompat.dylib")
                let h = try self.batchHandle("libSwiftUIStockClient.dylib")
                try require(dlsym(h,"ioscompat_stock_toolbar_test") != nil,"missing independent test entry")
                return "loaded and entry resolved"
            },
            .init(name:"SwiftUI / stock topBarLeading construction") {
                let h = try self.batchHandle("libSwiftUIStockClient.dylib")
                guard let entry = dlsym(h,"ioscompat_stock_toolbar_test") else {
                    throw ProbeFailure.failed("missing stock toolbar entry")
                }
                typealias Test = @convention(c) () -> Int32
                let result = unsafeBitCast(entry,to:Test.self)()
                try require(result == 1,"toolbar hosting returned \(result)")
                return "rebound SDK getter invoked; hosting layout completed (not visual equivalence)"
            },
            .init(name:"SwiftUI / source-level change state") {
                try Self.checkChangeState()
            },
            .init(name:"Swift Core / reserve adapter loads") {
                let h = try self.batchHandle("libSwiftCoreCompat.dylib")
                try require(dlsym(h,"$ss15ContiguousArrayV15reserveCapacityyySiFyXl_Ts5") != nil,"missing specialized export")
                return "adapter loaded and exact export resolved"
            },
            .init(name:"Swift Core / independent reserve SDK bridge loads") {
                _ = try self.batchHandle("libSwiftCoreCompat.dylib")
                let h = try self.batchHandle("libSwiftCoreStockClient.dylib")
                try require(dlsym(h,"ioscompat_stock_reserve") != nil,"missing stock bridge entry")
                return "independent SDK client loaded"
            },
            .init(name:"Swift Core / rebound reserve functional batch") {
                _ = try self.batchHandle("libSwiftCoreCompat.dylib")
                let h = try self.batchHandle("libSwiftCoreStockClient.dylib")
                guard let entry = dlsym(h,"ioscompat_stock_reserve") else {
                    throw ProbeFailure.failed("missing stock reserve entry")
                }
                let bridge = unsafeBitCast(entry,to:ReserveProbe.Bridge.self)
                let rows = ReserveProbe.run(bridge)
                let passed = rows.filter{$0.1}.count
                let detail = rows.map{"\($0.1 ? "PASS" : "FAIL") \($0.0)"}.joined(separator:"\n")
                try require(passed == 12 && rows.count == 12,"reserve checks \(passed)/\(rows.count)\n"+detail)
                return "12/12 independent SDK reserve subchecks\n"+detail
            },
            .init(name:"SwiftUI / paired toolbar SDK client loads") {
                let compat = try self.batchHandle("libSwiftUICompat.dylib")
                try require(dlsym(compat,"$s7SwiftUI20ToolbarItemPlacementV14topBarTrailingACvgZ") != nil,"missing trailing export")
                let h = try self.batchHandle("libSwiftUIToolbarPairStockClient.dylib")
                try require(dlsym(h,"ioscompat_stock_toolbar_pair_test") != nil,"missing pair entry")
                return "trailing getter resolved and paired client loaded"
            },
            .init(name:"SwiftUI / paired stock toolbar construction") {
                _ = try self.batchHandle("libSwiftUICompat.dylib")
                let h = try self.batchHandle("libSwiftUIToolbarPairStockClient.dylib")
                guard let entry = dlsym(h,"ioscompat_stock_toolbar_pair_test") else {
                    throw ProbeFailure.failed("missing paired toolbar entry")
                }
                typealias Test = @convention(c) () -> Int32
                let result = unsafeBitCast(entry,to:Test.self)()
                try require(result == 1,"paired toolbar returned \(result)")
                return "both rebound stock getters invoked; hosting layout completed, not visual equivalence"
            }
        ]
    }
    private func activityCases() -> [ProbeCase] {
        [
            .init(name:"Activity / inherited generic witness") {
                try require(localThroughActivity(LocalActivityIntent.self),"local witness returned false")
                return "independent nominal protocol"
            },
            .init(name:"Activity / native SystemIntent dispatch") {
                try require(localThroughSystem(LocalActivityIntent.self),"native witness returned false")
                return "native base dispatch"
            },
            .init(name:"Activity / positive dynamic cast") {
                try require(localDynamic(LocalActivityIntent()),"local cast failed")
                return "local type accepted"
            },
            .init(name:"Activity / negative dynamic cast") {
                try require(!localDynamic(42),"unrelated type accepted")
                return "unrelated type rejected"
            },
            .init(name:"Activity / native SystemIntent conformance") {
                try require((LocalActivityIntent() as Any) is any SystemIntent,"native base cast failed")
                return "native base conformance"
            },
            .init(name:"Activity / perform") {
                _ = try await LocalActivityIntent().perform()
                return "local perform completed; no system registration claim"
            }
        ]
    }
    private func executorCases() -> [ProbeCase] {
        [
            .init(name:"Executor / first job") {
                let actor = ExecutorControl()
                await actor.increment()
                let result = await actor.value()
                try require(result == 1,"first job failed")
                return "native serial executor control"
            },
            .init(name:"Executor / 100 concurrent submissions") {
                let actor = ExecutorControl()
                await withTaskGroup(of: Void.self) { group in
                    for _ in 0..<100 { group.addTask { await actor.increment() } }
                }
                let result = await actor.value()
                try require(result == 100,"lost increments")
                return "100/100 increments"
            },
            .init(name:"Executor / sequential order") {
                let actor = ExecutorControl()
                for i in 0..<32 { await actor.append(i) }
                let result = await actor.snapshot()
                try require(result == Array(0..<32),"order mismatch")
                return "32 ordered operations"
            },
            .init(name:"Executor / independent actors") {
                let a = ExecutorControl(), b = ExecutorControl()
                await a.increment()
                await a.increment()
                await b.increment()
                let av = await a.value(), bv = await b.value()
                try require(av == 2 && bv == 1,"actor state mismatch")
                return "independent native actor state; no new runtime ABI claim"
            }
        ]
    }
    private func runtimeBaselineCases() -> [ProbeCase] {
        [
            .init(name:"Runtime / generic metadata identity") {
                func identity<T>(_ value:T) -> ObjectIdentifier { ObjectIdentifier(T.self) }
                try require(identity(42) == ObjectIdentifier(Int.self),"Int metadata mismatch")
                try require(identity("test") == ObjectIdentifier(String.self),"String metadata mismatch")
                return "native generic metadata positive controls; no new entry point invoked"
            },
            .init(name:"Runtime / existential conformance controls") {
                let values:[Any] = [42, "test", NSObject()]
                try require(values[0] is any BinaryInteger,"integer conformance absent")
                try require(!(values[1] is any BinaryInteger),"unexpected integer conformance")
                try require(values[2] is NSObject,"object cast failed")
                return "native dynamic conformance controls"
            },
            .init(name:"Runtime / opaque result identity") {
                func opaque() -> some Equatable { 42 }
                let a = opaque(), b = opaque()
                try require(a == b,"opaque equality mismatch")
                try require((a as Any) is Int,"opaque concrete type mismatch")
                return "native opaque metadata baseline only"
            }
        ]
    }
    private func runStreamBatch() async throws -> String {
        guard !streamStarted else { throw ProbeFailure.failed("Stream batch already attempted in this process; reopen to retry") }
        let h = try batchHandle("libConcurrencyStockClient.dylib")
        guard let entry = dlsym(h,"ioscompat_stock_stream_tests") else {
            throw ProbeFailure.failed("missing independent stream entry")
        }
        streamStarted = true
        let box = StreamResult()
        // The asynchronous callback owns one retained reference until delivery.
        // On timeout it remains valid for late delivery; no dangling callback pointer.
        let context = Unmanaged.passRetained(box).toOpaque()
        typealias Callback = @convention(c) (UnsafeMutableRawPointer?,Int32) -> Void
        typealias Test = @convention(c) (UnsafeMutableRawPointer?,Callback) -> Void
        let callback: Callback = { raw, mask in
            guard let raw = raw else { return }
            Unmanaged<StreamResult>.fromOpaque(raw).takeRetainedValue().set(mask)
        }
        unsafeBitCast(entry,to:Test.self)(context,callback)
        for _ in 0..<200 {
            if let mask = box.get() {
                let names = ["newest buffering","yield after finish","throwing error propagation","oldest buffering","reference identity","reference stream ends"]
                let lines = names.enumerated().map { i,name in
                    "\(mask & (Int32(1) << i) != 0 ? "PASS" : "FAIL") \(name)"
                }
                let detail = lines.joined(separator:"\n")
                try require(mask == 63,"stock mask \(mask)/63\n"+detail)
                return "6/6 independent SDK subchecks\n"+detail
            }
            try await Task.sleep(nanoseconds:50_000_000)
        }
        throw ProbeFailure.failed("Stock async completion timed out; reopen before retrying")
    }
    private static func checkChangeState() throws -> String {
        var a = LegacyChangeState<Int>()
        try require(a.receive(1,initial:false)==nil,"unexpected initial callback")
        let a2 = a.receive(2,initial:false)
        try require(a2?.0==1 && a2?.1==2,"old/new mismatch")
        try require(a.receive(2,initial:false)==nil,"equal values callback")
        let a3 = a.receive(1,initial:false)
        try require(a3?.0==2 && a3?.1==1,"change back mismatch")
        var b = LegacyChangeState<Int>()
        let b1 = b.receive(7,initial:true)
        try require(b1?.0==7 && b1?.1==7,"initial pair mismatch")
        try require(b.receive(7,initial:true)==nil,"repeat initial callback")
        var c = LegacyChangeState<Int?>()
        let c1 = c.receive(nil,initial:true)
        try require(c1 != nil && c1!.0==nil && c1!.1==nil,"initial nil mismatch")
        let c2 = c.receive(4,initial:false)
        try require(c2 != nil && c2!.0==nil && c2!.1==4,"nil to value mismatch")
        let c3 = c.receive(nil,initial:false)
        try require(c3 != nil && c3!.0==4 && c3!.1==nil,"value to nil mismatch")
        try require(c.receive(nil,initial:false)==nil,"equal nil callback")
        return "10/10 source-level state subchecks; no opaque SwiftUI ABI claim"
    }
    private func exports(_ path:String, _ names:[String]) throws -> String {
        guard let h = dlopen(path,RTLD_LAZY|RTLD_LOCAL) else { throw ProbeFailure.failed("native provider unavailable") }
        defer { dlclose(h) }
        return "READ-ONLY evidence (absence is not a test failure):\n" + names.map { name in
            "\(dlsym(h,name) == nil ? "ABSENT" : "PRESENT") \(name)"
        }.joined(separator:"\n")
    }
}


private final class StreamResult: @unchecked Sendable {
    private let lock = NSLock()
    private var mask: Int32?
    func set(_ value:Int32) { lock.lock(); defer { lock.unlock() }; mask = value }
    func get() -> Int32? { lock.lock(); defer { lock.unlock() }; return mask }
}
