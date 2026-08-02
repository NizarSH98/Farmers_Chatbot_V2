import { describe, expect, it } from "vitest";

import { t } from "./i18n";

describe("Arabic-first copy", () => {
  it("uses plain Arabic without mojibake", () => {
    expect(t("ar", "welcome")).toContain("كيف");
    expect(t("ar", "composer")).toContain("سؤالك");
    expect(t("ar", "welcome")).not.toContain("Ø");
  });

  it("keeps the languages mutually exclusive", () => {
    expect(t("ar", "settings")).not.toBe(t("en", "settings"));
    expect(t("en", "settings")).toBe("Settings");
  });
});
