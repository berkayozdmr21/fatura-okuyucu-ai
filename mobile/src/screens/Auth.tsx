import { useState } from "react";
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, Text, TextInput, View } from "react-native";

import { ApiError } from "../api";
import { useAuth } from "../auth";
import { makeStyles, useColors } from "../theme";

export function LoginScreen({ navigation }: { navigation: { navigate: (name: "Register") => void } }) {
  const c = useColors();
  const s = makeStyles(c);
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await login(email.trim(), password);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Giriş yapılamadı.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <KeyboardAvoidingView style={s.screen} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <ScrollView contentContainerStyle={[s.pad, { justifyContent: "center", flexGrow: 1 }]} keyboardShouldPersistTaps="handled">
        <Text style={s.title}>Giriş yap</Text>
        <Text style={s.label}>E-posta</Text>
        <TextInput
          style={s.input}
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
          autoComplete="email"
          textContentType="username"
          accessibilityLabel="E-posta"
        />
        <Text style={s.label}>Şifre</Text>
        <TextInput
          style={s.input}
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          autoComplete="password"
          textContentType="password"
          accessibilityLabel="Şifre"
        />
        {error && <Text style={s.error} accessibilityRole="alert">{error}</Text>}
        <Pressable style={s.button} onPress={submit} disabled={busy || !email || !password} accessibilityRole="button">
          {busy ? <ActivityIndicator color={c.onBrand} /> : <Text style={s.buttonText}>Giriş yap</Text>}
        </Pressable>
        <Pressable onPress={() => navigation.navigate("Register")} accessibilityRole="link">
          <Text style={[s.text, { textAlign: "center", color: c.brand }]}>Hesabın yok mu? Kayıt ol</Text>
        </Pressable>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

export function RegisterScreen() {
  const c = useColors();
  const s = makeStyles(c);
  const { register } = useAuth();
  const [role, setRole] = useState<"client" | "accountant">("client");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [orgName, setOrgName] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await register({
        email: email.trim(),
        password,
        full_name: fullName.trim(),
        role,
        ...(role === "accountant" ? { org_name: orgName.trim() } : { invite_code: inviteCode.trim() }),
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Kayıt yapılamadı.");
    } finally {
      setBusy(false);
    }
  }

  const roleButton = (value: "client" | "accountant", label: string) => (
    <Pressable
      key={value}
      onPress={() => setRole(value)}
      accessibilityRole="radio"
      accessibilityState={{ selected: role === value }}
      style={[s.button, role !== value && s.buttonAlt, { flex: 1 }]}
    >
      <Text style={[s.buttonText, role !== value && s.buttonAltText]}>{label}</Text>
    </Pressable>
  );

  return (
    <KeyboardAvoidingView style={s.screen} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <ScrollView contentContainerStyle={s.pad} keyboardShouldPersistTaps="handled">
        <Text style={s.title}>Kayıt ol</Text>
        <View style={[s.row, { marginBottom: 6 }]}>{[roleButton("client", "Müşteri"), roleButton("accountant", "Muhasebeci")]}</View>
        <Text style={s.label}>Ad soyad</Text>
        <TextInput style={s.input} value={fullName} onChangeText={setFullName} autoComplete="name" />
        <Text style={s.label}>E-posta</Text>
        <TextInput style={s.input} value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" />
        <Text style={s.label}>Şifre (en az 8 karakter)</Text>
        <TextInput style={s.input} value={password} onChangeText={setPassword} secureTextEntry />
        {role === "accountant" ? (
          <>
            <Text style={s.label}>Büro adı</Text>
            <TextInput style={s.input} value={orgName} onChangeText={setOrgName} />
          </>
        ) : (
          <>
            <Text style={s.label}>Davet kodu (muhasebecinden al)</Text>
            <TextInput style={s.input} value={inviteCode} onChangeText={setInviteCode} autoCapitalize="characters" />
          </>
        )}
        {error && <Text style={s.error} accessibilityRole="alert">{error}</Text>}
        <Pressable style={s.button} onPress={submit} disabled={busy} accessibilityRole="button">
          {busy ? <ActivityIndicator color={c.onBrand} /> : <Text style={s.buttonText}>Kayıt ol</Text>}
        </Pressable>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
