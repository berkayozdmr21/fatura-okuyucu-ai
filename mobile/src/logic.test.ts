import { describe, expect, it } from "vitest";

import { confidenceLevel, errorMessage, formatAmount, formatDate, guessMime, safeFileName, tabForScreen } from "./logic";

describe("biçimlendirme", () => {
  it("tutarı Türkçe biçimde yazar", () => {
    expect(formatAmount(1234.5)).toBe("₺1.234,50");
    expect(formatAmount(1234567.891)).toBe("₺1.234.567,89");
    expect(formatAmount(0.9, "USD")).toBe("$0,90");
    expect(formatAmount(null)).toBe("-");
  });

  it("tarihi gün.ay.yıl yapar", () => {
    expect(formatDate("2025-03-12")).toBe("12.03.2025");
    expect(formatDate(undefined)).toBe("-");
  });

  it("güven seviyeleri", () => {
    expect(confidenceLevel(0.9)).toBe("high");
    expect(confidenceLevel(0.7)).toBe("mid");
    expect(confidenceLevel(0.69)).toBe("low");
  });
});

describe("hata mesajı", () => {
  it("API hata biçimlerini okur", () => {
    expect(errorMessage({ detail: "Davet kodu geçersiz" }, "x")).toBe("Davet kodu geçersiz");
    expect(errorMessage({ detail: [{ msg: "kısa", loc: ["body", "password"] }] }, "x")).toBe("password: kısa");
    expect(errorMessage(undefined, "yedek")).toBe("yedek");
  });
});

describe("chatbot ekran eşlemesi", () => {
  it("mobilde olan ekranları sekmeye çevirir", () => {
    expect(tabForScreen("upload")).toBe("Upload");
    expect(tabForScreen("documents")).toBe("Documents");
    expect(tabForScreen("home")).toBe("Documents");
  });

  it("mobilde olmayan ekranlar null döner", () => {
    expect(tabForScreen("review")).toBeNull();
    expect(tabForScreen("export")).toBeNull();
    expect(tabForScreen("team")).toBeNull();
    expect(tabForScreen("bilinmeyen")).toBeNull();
  });
});

describe("dosya yardımcıları", () => {
  it("MIME türünü tahmin eder", () => {
    expect(guessMime("fatura.PDF")).toBe("application/pdf");
    expect(guessMime("foto.jpeg")).toBe("image/jpeg");
    expect(guessMime("bilinmeyen.bin")).toBe("application/octet-stream");
  });

  it("güvenli dosya adı üretir", () => {
    expect(safeFileName("fatura 1.pdf", "application/pdf")).toBe("fatura_1.pdf");
    expect(safeFileName(null, "image/jpeg")).toBe("belge.jpg");
    expect(safeFileName("IMG_0001", "image/png")).toBe("IMG_0001.png");
    expect(safeFileName("../../etc/passwd", "application/pdf")).toBe("etc_passwd.pdf");
    expect(safeFileName("...", "image/png")).toBe("belge.png");
  });
});
