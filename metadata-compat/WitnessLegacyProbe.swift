import Foundation
import Darwin
import WitnessFixture

// Only compiler-owned fixture types and the fixture's own protocol descriptor.
// No pointer stripping, witness dereference, or replacement of a system symbol.
@main struct WitnessLegacyProbe {
    typealias Lookup = @convention(c) (UnsafeRawPointer, UnsafeRawPointer) -> UnsafeRawPointer?
    static func main() {
        #if arch(arm64)
        guard let fixture = dlopen("@rpath/libWitnessFixture.dylib", RTLD_LAZY | RTLD_LOCAL) else {
            print("STOP fixture handle unavailable"); exit(2)
        }
        defer { dlclose(fixture) }
        guard let runtime = dlopen("/usr/lib/swift/libswiftCore.dylib", RTLD_LAZY | RTLD_LOCAL) else {
            print("STOP runtime handle unavailable"); exit(2)
        }
        defer { dlclose(runtime) }
        guard let descriptor = dlsym(fixture, "$s14WitnessFixture14CompatReadableMp"),
              let address = dlsym(runtime, "swift_conformsToProtocol") else {
            print("STOP expected fixture descriptor or legacy symbol unavailable"); exit(2)
        }
        let lookup = unsafeBitCast(address, to: Lookup.self)
        func query(_ type: Any.Type) -> UnsafeRawPointer? {
            lookup(unsafeBitCast(type, to: UnsafeRawPointer.self), UnsafeRawPointer(descriptor))
        }
        let a = query(WitnessBox<[Int]>.self)
        let b = query(WitnessBox<String>.self)
        let c = query(WitnessBox<Int>.self)
        let rows = [
            ("positive array", a != nil),
            ("positive string", b != nil),
            ("negative integer", c == nil),
            ("stable array witness", a != nil && query(WitnessBox<[Int]>.self) == a),
            ("public dispatch agrees", witnessCast(WitnessBox([1, 2])) == 2),
            ("public rejection agrees", witnessCast(WitnessBox(42)) == nil)
        ]
        for (name, ok) in rows { print("\(ok ? "PASS" : "FAIL") \(name)") }
        print("TOTAL \(rows.filter { $0.1 }.count)/\(rows.count)")
        if rows.contains(where: { !$0.1 }) { exit(1) }
        #else
        print("STOP requires arm64"); exit(2)
        #endif
    }
}
