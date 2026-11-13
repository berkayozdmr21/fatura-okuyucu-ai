import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, FlatList, KeyboardAvoidingView, Platform, Pressable, Text, TextInput, View } from "react-native";

import { api, ApiError } from "../api";
import { tabForScreen, type TabName } from "../logic";
import { makeStyles, useColors } from "../theme";
import type { ChatReply } from "../types";

interface Message {
  id: number;
  from: "user" | "bot";
  text: string;
  reply?: ChatReply;
}

export function AssistantScreen({ navigation }: { navigation: { navigate: (name: TabName) => void } }) {
  const c = useColors();
  const s = makeStyles(c);
  const [messages, setMessages] = useState<Message[]>([
    { id: 0, from: "bot", text: "Merhaba! Bir şeyi bulamazsan veya nasıl yapacağını bilmiyorsan bana sor, seni doğrudan o ekrana götürürüm." },
  ]);
  const [topics, setTopics] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const nextId = useRef(1);
  const listRef = useRef<FlatList<Message>>(null);

  useEffect(() => {
    api.chatTopics().then(setTopics).catch(() => undefined);
  }, []);

  async function ask(text: string) {
    const message = text.trim();
    if (!message || busy) return;
    setInput("");
    setMessages((m) => [...m, { id: nextId.current++, from: "user", text: message }]);
    setBusy(true);
    try {
      const reply = await api.chat(message);
      setMessages((m) => [...m, { id: nextId.current++, from: "bot", text: reply.answer, reply }]);
    } catch (e) {
      setMessages((m) => [...m, { id: nextId.current++, from: "bot", text: e instanceof ApiError ? e.message : "Şu an cevap veremiyorum." }]);
    } finally {
      setBusy(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 50);
    }
  }

  const chip = (label: string) => (
    <Pressable key={label} onPress={() => ask(label)} style={{ borderWidth: 1, borderColor: c.border, borderRadius: 999, paddingHorizontal: 12, paddingVertical: 8, marginRight: 6, marginTop: 6 }} accessibilityRole="button">
      <Text style={{ color: c.text, fontSize: 13 }}>{label}</Text>
    </Pressable>
  );

  return (
    <KeyboardAvoidingView style={s.screen} behavior={Platform.OS === "ios" ? "padding" : undefined} keyboardVerticalOffset={90}>
      <FlatList
        ref={listRef}
        contentContainerStyle={s.pad}
        data={messages}
        keyExtractor={(m) => String(m.id)}
        ListFooterComponent={busy ? <ActivityIndicator color={c.brand} /> : null}
        renderItem={({ item: m }) => {
          const tab = m.reply?.action ? tabForScreen(m.reply.action.screen) : null;
          return (
            <View style={[s.card, { alignSelf: m.from === "user" ? "flex-end" : "flex-start", maxWidth: "90%", backgroundColor: m.from === "user" ? c.soft : c.surface }]}>
              <Text style={s.text}>{m.text}</Text>
              {m.reply?.steps.map((step, i) => (
                <Text key={i} style={[s.text, { marginTop: 4 }]}>{i + 1}. {step}</Text>
              ))}
              {m.reply?.action && tab && (
                <Pressable style={[s.button, { marginTop: 8, marginBottom: 0, minHeight: 40 }]} onPress={() => navigation.navigate(tab)} accessibilityRole="button">
                  <Text style={s.buttonText}>{m.reply.action.label}</Text>
                </Pressable>
              )}
              {m.reply && m.reply.suggestions.length > 0 && (
                <View style={{ flexDirection: "row", flexWrap: "wrap" }}>{m.reply.suggestions.map(chip)}</View>
              )}
            </View>
          );
        }}
        ListHeaderComponent={
          messages.length === 1 && topics.length > 0 ? <View style={{ flexDirection: "row", flexWrap: "wrap", marginBottom: 8 }}>{topics.slice(0, 5).map(chip)}</View> : null
        }
      />
      <View style={[s.row, { padding: 10, borderTopWidth: 1, borderTopColor: c.border }]}>
        <TextInput
          style={[s.input, { flex: 1, marginBottom: 0 }]}
          value={input}
          onChangeText={setInput}
          placeholder="Örn. yükleme nerede?"
          placeholderTextColor={c.muted}
          maxLength={1000}
          onSubmitEditing={() => ask(input)}
          returnKeyType="send"
          accessibilityLabel="Sorunu yaz"
        />
        <Pressable style={[s.button, { marginBottom: 0 }]} onPress={() => ask(input)} disabled={busy || !input.trim()} accessibilityRole="button">
          <Text style={s.buttonText}>Gönder</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}
