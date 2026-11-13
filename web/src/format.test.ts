import { describe, expect, it } from "vitest";

import { errorMessage } from "./api";
import { confidenceLevel, formatDate, formatSize, parseFieldInput } from "./format";
import { navFor, routeForScreen } from "./screens";

describe("format", () => {
  it("tarihi gün.ay.yıl yapar", () => {
    expect(formatDate("2025-03-12")).toBe("12.03.2025");
    expect(formatDate(null)).toBe("-");
  });

  it("boyutu okunur yazar", () => {
    expect(formatSize(500)).toBe("500 B");
    expect(formatSize(2048)).toBe("2 KB");
    expect(formatSize(5 * 1024 * 1024)).toBe("5.0 MB");
  });

  it("güven seviyeleri", () => {
    expect(confidenceLevel(0.99)).toBe("high");
    expect(confidenceLevel(0.75)).toBe("mid");
    expect(confidenceLevel(0.3)).toBe("low");
    expect(confidenceLevel(undefined)).toBe("none");
  });

  it("form girdisini API türüne çevirir", () => {
    expect(parseFieldInput("total", "1.234,56")).toBe(1234.56);
    expect(parseFieldInput("total", "1234.56")).toBe(1234.56);
    expect(parseFieldInput("total", "abc")).toBeNull();
    expect(parseFieldInput("invoice_no", "  ABC123 ")).toBe("ABC123");
    expect(parseFieldInput("invoice_no", "   ")).toBeNull();
  });
});

describe("errorMessage", () => {
  it("düz mesaj ve doğrulama hatası", () => {
    expect(errorMessage({ detail: "Davet kodu geçersiz" }, "x")).toBe("Davet kodu geçersiz");
    expect(errorMessage({ detail: [{ msg: "kısa", loc: ["body", "password"] }] }, "x")).toBe("password: kısa");
    expect(errorMessage(null, "yedek")).toBe("yedek");
  });
});

describe("yönlendirme", () => {
  it("chatbot ekran kodlarını rotaya çevirir", () => {
    expect(routeForScreen("upload")).toBe("/upload");
    expect(routeForScreen("review")).toBe("/documents?status=needs_review");
    expect(routeForScreen("yok")).toBeNull();
  });

  it("müşteri menüsünde muhasebeci ekranları yok", () => {
    const client = navFor("client").map((i) => i.to);
    expect(client).not.toContain("/export");
    expect(client).not.toContain("/team");
    expect(navFor("accountant").map((i) => i.to)).toContain("/export");
  });
});
