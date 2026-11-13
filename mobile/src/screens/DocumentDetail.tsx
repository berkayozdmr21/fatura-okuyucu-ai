import { useEffect, useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, Text, View } from "react-native";

import { api, ApiError } from "../api";
import { useAuth } from "../auth";
import { confidenceLevel, FIELD_LABELS, STATUS_LABELS } from "../logic";
import { makeStyles, useColors } from "../theme";
import type { Doc } from "../types";

const FIELD_ORDER = Object.keys(FIELD_LABELS);

export function DocumentDetailScreen({
  route,
  navigation,
}: {
  route: { params: { id: number } };
  navigation: { goBack: () => void };
}) {
  const c = useColors();
  const s = makeStyles(c);
  const { user } = useAuth();
  const [doc, setDoc] = useState<Doc | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.getDoc(route.params.id).then(setDoc).catch((e: Error) => setError(e.message));
  }, [route.params.id]);

  function confirmDelete() {
    if (!doc) return;
    Alert.alert("Belgeyi sil", "Belge ve dosyası kalıcı olarak silinecek. Emin misin?", [
      { text: "Vazgeç", style: "cancel" },
      {
        text: "Sil",
        style: "destructive",
        onPress: async () => {
          setBusy(true);
          try {
            await api.deleteDoc(doc.id);
            navigation.goBack();
          } catch (e) {
            setError(e instanceof ApiError ? e.message : "Silinemedi.");
            setBusy(false);
          }
        },
      },
    ]);
  }

  if (error && !doc) return <Text style={[s.error, s.pad]}>{error}</Text>;
  if (!doc) return <ActivityIndicator style={{ marginTop: 40 }} color={c.brand} />;

  const levelColor = (level: string) => (level === "high" ? c.ok : level === "mid" ? c.warn : level === "low" ? c.danger : c.muted);
  const canDelete = user?.role === "accountant" || doc.status !== "approved";

  return (
    <ScrollView style={s.screen} contentContainerStyle={s.pad}>
      <Text style={s.title}>{String(doc.data.seller_name ?? doc.original_filename)}</Text>
      <Text style={s.muted}>{STATUS_LABELS[doc.status]} · {doc.original_filename}</Text>

      {doc.issues.length > 0 && (
        <View style={[s.card, { marginTop: 12 }]}>
          <Text style={s.h2}>Uyarılar</Text>
          {doc.issues.map((i, k) => (
            <Text key={k} style={{ color: i.severity === "error" ? c.danger : c.warn, marginBottom: 4 }}>
              {i.severity === "error" ? "Hata: " : "Uyarı: "}
              {i.message}
            </Text>
          ))}
          <Text style={s.muted}>Düzeltme ve onay web veya masaüstü uygulamasında muhasebeci tarafından yapılır.</Text>
        </View>
      )}

      <View style={[s.card, { marginTop: 12 }]}>
        <Text style={s.h2}>Okunan bilgiler</Text>
        {FIELD_ORDER.map((f) => {
          const level = confidenceLevel(doc.field_confidence[f]);
          return (
            <View key={f} style={{ marginBottom: 8 }}>
              <Text style={s.label}>
                {FIELD_LABELS[f]}
                {doc.field_confidence[f] !== undefined && (
                  <Text style={{ color: levelColor(level) }}>  %{Math.round(doc.field_confidence[f] * 100)}</Text>
                )}
              </Text>
              <Text style={s.text}>{doc.data[f] === null || doc.data[f] === undefined ? "-" : String(doc.data[f])}</Text>
            </View>
          );
        })}
      </View>

      {error && <Text style={s.error}>{error}</Text>}
      {canDelete && (
        <Pressable style={[s.button, s.buttonDanger]} onPress={confirmDelete} disabled={busy} accessibilityRole="button">
          <Text style={[s.buttonText, { color: c.danger }]}>Belgeyi sil</Text>
        </Pressable>
      )}
    </ScrollView>
  );
}
