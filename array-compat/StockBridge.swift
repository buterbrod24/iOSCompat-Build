// An independent C-callable bridge. The caller owns an initialized
// ContiguousArray<AnyObject> and holds exclusive access for the entire call.
@_cdecl("ioscompat_stock_reserve")
public func stockReserve(_ raw: UnsafeMutableRawPointer, _ minimumCapacity:Int) {
    raw.assumingMemoryBound(to:ContiguousArray<AnyObject>.self).pointee.reserveCapacity(minimumCapacity)
}
