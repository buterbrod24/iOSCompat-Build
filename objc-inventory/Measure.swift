import Foundation

@main struct Measure {
    @MainActor static func main() {
        let rows=ObjCInventory.run()
        for row in rows { print(row) }
        let known=rows.contains { $0.hasPrefix("CLASS\tUIView\tPRESENT") }
            && rows.contains { $0.hasPrefix("METHOD\tUIView\t-\ttraitCollection\tPRESENT") }
            && rows.contains { $0.hasPrefix("PROTOCOL\tUITraitEnvironment\tPRESENT") }
        print("TOTAL OBSERVATIONS \(rows.count)")
        print(known && rows.count==36 ? "PASS baseline inventory" : "FAIL baseline inventory")
        if !known || rows.count != 36 { exit(1) }
    }
}
