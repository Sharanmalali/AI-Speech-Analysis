import { describe, expect, it } from "vitest";

import { cn, formatBytes, formatPct, formatTimestamp, titleCase } from "@/lib/utils";

describe("utils", () => {
  it("cn merges and dedupes tailwind classes", () => {
    expect(cn("p-2", "p-4")).toBe("p-4");
    expect(cn("text-sm", false && "hidden", "font-bold")).toBe("text-sm font-bold");
  });

  it("formatTimestamp formats mm:ss and hh:mm:ss", () => {
    expect(formatTimestamp(0)).toBe("00:00");
    expect(formatTimestamp(65)).toBe("01:05");
    expect(formatTimestamp(3661)).toBe("01:01:01");
  });

  it("formatBytes is human readable", () => {
    expect(formatBytes(0)).toBe("0 B");
    expect(formatBytes(1024)).toBe("1.0 KB");
    expect(formatBytes(1048576)).toBe("1.0 MB");
  });

  it("formatPct handles null", () => {
    expect(formatPct(null)).toBe("n/a");
    expect(formatPct(0.6699)).toBe("67.0%");
  });

  it("titleCase capitalises", () => {
    expect(titleCase("typical")).toBe("Typical");
  });
});
