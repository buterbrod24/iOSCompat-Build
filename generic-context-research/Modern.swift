public struct PackHolder<each T> {
    public var values:(repeat each T)
    public init(_ values:repeat each T) { self.values=(repeat each values) }
}

public struct ConstrainedPack<each T: Equatable> {
    public var values:(repeat each T)
    public init(_ values:repeat each T) { self.values=(repeat each values) }
}
