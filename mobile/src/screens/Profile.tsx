import { Pressable, ScrollView, Text, View } from "react-native";

import { useAuth } from "../auth";
import { makeStyles, useColors } from "../theme";

export function ProfileScreen() {
  const c = useColors();
  const s = makeStyles(c);
  const { user, logout } = useAuth();
  if (!user) return null;

  const row = (label: string, value: string) => (
    <View style={{ marginBottom: 10 }} key={label}>
      <Text style={s.label}>{label}</Text>
      <Text style={s.text}>{value}</Text>
    </View>
  );

  return (
    <ScrollView style={s.screen} contentContainerStyle={s.pad}>
      <Text style={s.title}>Hesabım</Text>
      <View style={s.card}>
        {row("Ad soyad", user.full_name)}
        {row("E-posta", user.email)}
        {row("Hesap türü", user.role === "accountant" ? "Muhasebeci" : "Müşteri")}
        {row("Büro", user.org_name)}
      </View>
      <Text style={s.muted}>
        Yüklediğin dosyalar varsayılan olarak 30 gün sonra otomatik silinir; okunan fatura verileri kayıtlı kalır.
        İnceleme, onay ve dışa aktarma işlemleri web ve masaüstü uygulamasındadır. Şifre değiştirme özelliği henüz yok.
      </Text>
      <Pressable style={[s.button, s.buttonAlt, { marginTop: 16 }]} onPress={logout} accessibilityRole="button">
        <Text style={[s.buttonText, s.buttonAltText]}>Çıkış yap</Text>
      </Pressable>
    </ScrollView>
  );
}
