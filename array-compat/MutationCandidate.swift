// Source-level adapters only. No private buffer or specialized ABI aliases.
public extension ContiguousArray where Element == AnyObject {
    @inline(never)
    mutating func ioscompatAppendReference(_ value: AnyObject) {
        append(value)
    }

    @inline(never)
    mutating func ioscompatPrepareAndAppend(_ value: AnyObject, minimumCapacity: Int) {
        precondition(minimumCapacity >= 0)
        reserveCapacity(minimumCapacity)
        append(value)
    }
}
