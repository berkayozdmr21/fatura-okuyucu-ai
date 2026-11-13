import { StyleSheet, useColorScheme } from "react-native";

const light = {
  bg: "#f6f7f9", surface: "#ffffff", text: "#17202a", muted: "#5b6772", border: "#dde2e8",
  brand: "#0f766e", onBrand: "#ffffff", danger: "#b42318", warn: "#b54708", ok: "#067647", soft: "#ccfbf1",
};
const dark: typeof light = {
  bg: "#0e1418", surface: "#161e24", text: "#e8edf1", muted: "#9aa7b2", border: "#2a353e",
  brand: "#2dd4bf", onBrand: "#06201c", danger: "#fda29b", warn: "#fec84b", ok: "#75e0a7", soft: "#0f3a36",
};

export type Colors = typeof light;

export function useColors(): Colors {
  return useColorScheme() === "dark" ? dark : light;
}

/** Ortak stiller; renkler temaya göre üretilir. Dokunma hedefleri en az 44 dp. */
export function makeStyles(c: Colors) {
  return StyleSheet.create({
    screen: { flex: 1, backgroundColor: c.bg },
    pad: { padding: 16 },
    title: { fontSize: 22, fontWeight: "700", color: c.text, marginBottom: 12 },
    h2: { fontSize: 16, fontWeight: "700", color: c.text, marginTop: 12, marginBottom: 6 },
    text: { color: c.text, fontSize: 15 },
    muted: { color: c.muted, fontSize: 13 },
    error: { color: c.danger, marginVertical: 6 },
    card: { backgroundColor: c.surface, borderRadius: 12, borderWidth: 1, borderColor: c.border, padding: 14, marginBottom: 10 },
    input: {
      backgroundColor: c.surface, borderWidth: 1, borderColor: c.border, borderRadius: 8, paddingHorizontal: 12,
      minHeight: 48, color: c.text, marginBottom: 10, fontSize: 16,
    },
    label: { color: c.muted, fontSize: 13, marginBottom: 4 },
    button: { backgroundColor: c.brand, borderRadius: 8, minHeight: 48, alignItems: "center", justifyContent: "center", paddingHorizontal: 16, marginBottom: 10 },
    buttonText: { color: c.onBrand, fontWeight: "700", fontSize: 16 },
    buttonAlt: { backgroundColor: "transparent", borderWidth: 1, borderColor: c.brand },
    buttonAltText: { color: c.brand },
    buttonDanger: { backgroundColor: "transparent", borderWidth: 1, borderColor: c.danger },
    row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: 8 },
  });
}
