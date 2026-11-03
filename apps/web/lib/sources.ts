import type { Citation } from "./types";

export interface SourceGroup {
  key: string;
  title: string;
  publisher?: string;
  url?: string;
  sourceType: string;
  /** How many retrieved passages of this source supported the answer. */
  passages: number;
  /** In-text `[n]` markers that point into this source. */
  markers: number[];
  warnings: string[];
}

interface UnderlyingSource {
  source_id?: string;
  title?: string;
  publisher?: string;
  url?: string | null;
}

function underlyingOf(citation: Citation): UnderlyingSource | undefined {
  const list = citation.sources;
  if (!Array.isArray(list) || list.length === 0) return undefined;
  const first = list[0];
  return first && typeof first === "object" ? (first as UnderlyingSource) : undefined;
}

/**
 * Collapse per-passage citations into the documents a reader would recognise.
 * Retrieval returns many passages of the same reviewed document; listing each
 * internal passage label ("Knowledge claim", …) reads as noise, while
 * "RAISE Agrifood Knowledge v0.3 · 24 reviewed passages" is the real attribution.
 */
export function groupSources(citations: Citation[]): SourceGroup[] {
  const groups = new Map<string, SourceGroup>();
  for (const citation of citations) {
    const underlying = underlyingOf(citation);
    const url = underlying?.url || citation.url || undefined;
    const key =
      underlying?.source_id || url || citation.document_id || citation.title || citation.item_id || "unknown";
    const existing = groups.get(key);
    const group: SourceGroup = existing ?? {
      key,
      title: underlying?.title || citation.title || citation.item_id || url || "—",
      publisher: underlying?.publisher || undefined,
      url,
      sourceType: citation.source_type,
      passages: 0,
      markers: [],
      warnings: []
    };
    group.passages += 1;
    if (typeof citation.marker === "number" && !group.markers.includes(citation.marker)) {
      group.markers.push(citation.marker);
    }
    if (citation.warning && !group.warnings.includes(citation.warning)) {
      group.warnings.push(citation.warning);
    }
    groups.set(key, group);
  }
  return [...groups.values()]
    .map((group) => ({ ...group, markers: group.markers.sort((a, b) => a - b) }))
    .sort((left, right) => {
      const leftFirst = left.markers[0] ?? Number.MAX_SAFE_INTEGER;
      const rightFirst = right.markers[0] ?? Number.MAX_SAFE_INTEGER;
      return leftFirst - rightFirst || right.passages - left.passages;
    });
}
