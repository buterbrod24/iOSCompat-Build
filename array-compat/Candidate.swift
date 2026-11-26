// Typed adapter for the concrete reference-element specialization.
// Uses the native public API compiled for the old deployment target.
public extension ContiguousArray where Element == AnyObject {
    @inline(never)
    mutating func ioscompatReserveCapacity(_ minimumCapacity: Int) {
        reserveCapacity(minimumCapacity)
    }
}
