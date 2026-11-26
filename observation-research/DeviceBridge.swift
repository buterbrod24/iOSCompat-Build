// C entry point for the original research app; does not expose object layouts.
@_cdecl("ioscompat_observation_controls")
public func observationControls() -> Int32 {
    let rows = ObservationChecks.run()
    guard rows.count == 8 else { return -1 }
    var mask: Int32 = 0
    for (i, row) in rows.enumerated() where row.1 { mask |= Int32(1) << i }
    return mask
}
