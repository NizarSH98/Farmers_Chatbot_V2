import { describe, expect, it } from "vitest";

import { groupSources } from "./sources";
import type { Citation } from "./types";

const corpus = {
  source_id: "RAISE-AGRIFOOD-APPROVED-V0.3",
  title: "RAISE Agrifood Knowledge v0.3",
  publisher: "RAISE project",
  url: null
};

describe("groupSources", () => {
  it("collapses passages of one reviewed document into a single source", () => {
    const citations: Citation[] = [
      { source_type: "raise_knowledge", title: "Knowledge claim", item_id: "a", sources: [corpus] },
      { source_type: "raise_knowledge", title: "Arabic guidance — machine draft", item_id: "b", sources: [corpus] },
      { source_type: "raise_knowledge", title: "Knowledge claim", item_id: "c", sources: [corpus], marker: 2 }
    ];
    const groups = groupSources(citations);
    expect(groups).toHaveLength(1);
    expect(groups[0]).toMatchObject({
      title: "RAISE Agrifood Knowledge v0.3",
      publisher: "RAISE project",
      passages: 3,
      markers: [2]
    });
  });

  it("keeps distinct documents apart and orders cited ones first", () => {
    const groups = groupSources([
      { source_type: "web", title: "FAO olive note", url: "https://fao.example/olive" },
      { source_type: "raise_knowledge", item_id: "a", sources: [corpus], marker: 1 }
    ]);
    expect(groups.map((group) => group.title)).toEqual([
      "RAISE Agrifood Knowledge v0.3",
      "FAO olive note"
    ]);
    expect(groups[1].url).toBe("https://fao.example/olive");
  });
});
