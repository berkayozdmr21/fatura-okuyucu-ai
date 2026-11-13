import { useFocusEffect } from "@react-navigation/native";
import { useCallback, useState } from "react";
import { FlatList, Pressable, RefreshControl, Text, View } from "react-native";

import { api } from "../api";
import { formatAmount, formatDate, STATUS_LABELS } from "../logic";
import { makeStyles, useColors } from "../theme";
import type { Doc } from "../types";

export function DocumentsScreen({ navigation }: { navigation: { navigate: (name: "DocumentDetail", params: { id: number }) => void } }) {
  const c = useColors();
  const s = makeStyles(c);
  const [docs, setDocs] = useState<Doc[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      setDocs(await api.listDocs());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Yüklenemedi.");
    }
  }, []);

  // Sekmeye her dönüşte yenile (yükleme sonrası liste güncel olsun)
  useFocusEffect(useCallback(() => { void load(); }, [load]));

  async function onRefresh() {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }

  const statusColor = (status: string) =>
    status === "approved" ? c.ok : status === "needs_review" ? c.warn : status === "rejected" || status === "failed" ? c.danger : c.muted;

  return (
    <View style={s.screen}>
      <FlatList
        contentContainerStyle={s.pad}
        data={docs ?? []}
        keyExtractor={(d) => String(d.id)}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListHeaderComponent={<Text style={s.title}>Belgelerim</Text>}
        ListEmptyComponent={
          error ? <Text style={s.error}>{error}</Text> : <Text style={s.muted}>{docs === null ? "Yükleniyor…" : "Henüz belge yok. “Yükle” sekmesinden fiş fotoğrafı çek."}</Text>
        }
        renderItem={({ item: d }) => (
          <Pressable
            style={s.card}
            onPress={() => navigation.navigate("DocumentDetail", { id: d.id })}
            accessibilityRole="button"
            accessibilityLabel={`${d.data.seller_name ?? d.original_filename}, ${STATUS_LABELS[d.status]}`}
          >
            <View style={s.row}>
              <Text style={[s.text, { fontWeight: "700", flex: 1 }]} numberOfLines={1}>
                {String(d.data.seller_name ?? d.original_filename)}
              </Text>
              <Text style={s.text}>{formatAmount(d.data.total as number | null, d.data.currency as string | null)}</Text>
            </View>
            <View style={s.row}>
              <Text style={s.muted}>{formatDate(d.data.invoice_date as string | null)} · {String(d.data.invoice_no ?? "no yok")}</Text>
              <Text style={{ color: statusColor(d.status), fontWeight: "700", fontSize: 13 }}>{STATUS_LABELS[d.status]}</Text>
            </View>
            {d.issues.length > 0 && <Text style={{ color: c.warn, fontSize: 13, marginTop: 4 }}>⚠ {d.issues[0].message}</Text>}
          </Pressable>
        )}
      />
    </View>
  );
}
