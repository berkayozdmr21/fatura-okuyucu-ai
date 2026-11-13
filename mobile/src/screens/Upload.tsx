import * as DocumentPicker from "expo-document-picker";
import * as ImagePicker from "expo-image-picker";
import { useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, Text, View } from "react-native";

import { api, ApiError } from "../api";
import { formatAmount, guessMime, safeFileName, STATUS_LABELS } from "../logic";
import { makeStyles, useColors } from "../theme";
import type { Doc, UploadFile } from "../types";

const MAX_BYTES = 15 * 1024 * 1024;

export function UploadScreen({ navigation }: { navigation: { navigate: (name: "DocumentDetail", params: { id: number }) => void } }) {
  const c = useColors();
  const s = makeStyles(c);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [last, setLast] = useState<Doc | null>(null);

  async function send(file: UploadFile, size?: number | null) {
    if (size && size > MAX_BYTES) {
      setError("Dosya 15 MB sınırını aşıyor.");
      return;
    }
    setBusy(true);
    setError(null);
    setLast(null);
    try {
      setLast(await api.upload(file));
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        const id = (e.payload as { document_id?: number } | undefined)?.document_id;
        setError("Bu dosya zaten yüklenmiş.");
        if (id) navigation.navigate("DocumentDetail", { id });
      } else {
        setError(e instanceof Error ? e.message : "Yüklenemedi.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function takePhoto() {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) {
      Alert.alert("Kamera izni gerekli", "Fiş fotoğrafı çekmek için ayarlardan kamera iznini ver.");
      return;
    }
    const res = await ImagePicker.launchCameraAsync({ mediaTypes: ["images"], quality: 0.8 });
    const a = res.canceled ? null : res.assets[0];
    if (a) {
      const mime = a.mimeType ?? "image/jpeg";
      await send({ uri: a.uri, name: safeFileName(a.fileName, mime), mimeType: mime }, a.fileSize);
    }
  }

  async function pickImage() {
    const res = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images"], quality: 0.8 });
    const a = res.canceled ? null : res.assets[0];
    if (a) {
      const mime = a.mimeType ?? guessMime(a.fileName ?? "", "image/jpeg");
      await send({ uri: a.uri, name: safeFileName(a.fileName, mime), mimeType: mime }, a.fileSize);
    }
  }

  async function pickFile() {
    const res = await DocumentPicker.getDocumentAsync({
      type: ["application/pdf", "application/xml", "text/xml"],
      copyToCacheDirectory: true,
    });
    const a = res.canceled ? null : res.assets[0];
    if (a) {
      const mime = a.mimeType ?? guessMime(a.name);
      await send({ uri: a.uri, name: safeFileName(a.name, mime), mimeType: mime }, a.size);
    }
  }

  return (
    <ScrollView style={s.screen} contentContainerStyle={s.pad}>
      <Text style={s.title}>Belge yükle</Text>
      <Pressable style={s.button} onPress={takePhoto} disabled={busy} accessibilityRole="button" accessibilityLabel="Fiş veya fatura fotoğrafı çek">
        <Text style={s.buttonText}>Fotoğraf çek</Text>
      </Pressable>
      <Pressable style={[s.button, s.buttonAlt]} onPress={pickImage} disabled={busy} accessibilityRole="button">
        <Text style={[s.buttonText, s.buttonAltText]}>Galeriden seç</Text>
      </Pressable>
      <Pressable style={[s.button, s.buttonAlt]} onPress={pickFile} disabled={busy} accessibilityRole="button">
        <Text style={[s.buttonText, s.buttonAltText]}>PDF veya XML seç</Text>
      </Pressable>
      <Text style={s.muted}>
        İpucu: Fişi düz bir zemine koy, iyi ışıkta, tamamı görünecek şekilde çek. E-fatura PDF’i veya XML’i fotoğraftan daha doğru okunur.
      </Text>

      {busy && <ActivityIndicator style={{ marginTop: 16 }} color={c.brand} />}
      {error && <Text style={s.error} accessibilityRole="alert">{error}</Text>}
      {last && (
        <Pressable style={[s.card, { marginTop: 16 }]} onPress={() => navigation.navigate("DocumentDetail", { id: last.id })} accessibilityRole="button">
          <Text style={[s.text, { fontWeight: "700" }]}>Yüklendi ve okundu</Text>
          <View style={s.row}>
            <Text style={s.text}>{formatAmount(last.data.total as number | null, last.data.currency as string | null)}</Text>
            <Text style={s.muted}>{STATUS_LABELS[last.status]}</Text>
          </View>
          <Text style={{ color: c.brand }}>Ayrıntıları aç</Text>
        </Pressable>
      )}
    </ScrollView>
  );
}
