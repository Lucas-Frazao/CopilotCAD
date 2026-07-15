/**
 * InterfacesPanel.tsx — Assembly interface connection list
 *
 * Each row is a mechanical/electrical interface on a part (mount face, bolt
 * pattern, etc.) with link status: open, linked, or verified.
 * Clicking a row notifies the parent to select that part in Explorer/Viewport.
 *
 * Feature: F-016
 */

/** Shape of one interface row — mirrors backend interfaces_list payload. */
export interface InterfaceListEntry {
  part_id: string;
  interface_id: string;
  name: string;
  type: string;
  status: "open" | "linked" | "verified";
  connected_part_id: string | null;
}

export interface InterfacesPanelProps {
  interfaces: InterfaceListEntry[];
  onSelectPart?: (partId: string) => void;
  /** Set when Problems panel reports an interface_conflict — row gets highlight. */
  highlightedInterfaceId?: string | null;
}

export default function InterfacesPanel({
  interfaces,
  onSelectPart,
  highlightedInterfaceId = null,
}: InterfacesPanelProps) {
  return (
    <div className="interfaces-panel">
      <div className="panel-placeholder">Interfaces</div>
      <div className="interfaces-body">
        {interfaces.length === 0 ? (
          <div className="interfaces-empty">No interfaces defined yet.</div>
        ) : (
          <ul className="interfaces-list" role="list">
            {interfaces.map((iface, index) => {
              const isHighlighted = iface.interface_id === highlightedInterfaceId;
              // Show type label only on the first row of each type group (visual grouping).
              const showTypeLabel = index === interfaces.findIndex((i) => i.type === iface.type);
              return (
                <li key={`${iface.part_id}-${iface.interface_id}`}>
                  <button
                    type="button"
                    className={`interfaces-row ${isHighlighted ? "highlighted" : ""}`}
                    data-testid={`interface-row-${iface.interface_id}`}
                    onClick={() => onSelectPart?.(iface.part_id)}
                  >
                    <span className="interfaces-id">{iface.interface_id}</span>
                    <span className="interfaces-name">{iface.name}</span>
                    {showTypeLabel ? (
                      <span className="interfaces-type">{iface.type}</span>
                    ) : (
                      // Screen-reader-only duplicate so type is still announced per row.
                      <span className="interfaces-type interfaces-type-sr" aria-label={iface.type} />
                    )}
                    <span className={`interfaces-status interfaces-status-${iface.status}`}>
                      {iface.status}
                    </span>
                    {iface.connected_part_id && (
                      <span className="interfaces-connected">{iface.connected_part_id}</span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
