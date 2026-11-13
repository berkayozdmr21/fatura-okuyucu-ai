import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import { ActivityIndicator, View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { AuthProvider, useAuth } from "./src/auth";
import { AssistantScreen } from "./src/screens/Assistant";
import { LoginScreen, RegisterScreen } from "./src/screens/Auth";
import { DocumentDetailScreen } from "./src/screens/DocumentDetail";
import { DocumentsScreen } from "./src/screens/Documents";
import { ProfileScreen } from "./src/screens/Profile";
import { UploadScreen } from "./src/screens/Upload";
import { useColors } from "./src/theme";

const Tabs = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function MainTabs() {
  const c = useColors();
  return (
    <Tabs.Navigator
      initialRouteName="Documents"
      screenOptions={{
        tabBarActiveTintColor: c.brand,
        tabBarStyle: { backgroundColor: c.surface, borderTopColor: c.border },
        headerStyle: { backgroundColor: c.surface },
        headerTintColor: c.text,
      }}
    >
      <Tabs.Screen name="Documents" component={DocumentsScreen as never} options={{ title: "Belgeler", tabBarLabel: "Belgeler" }} />
      <Tabs.Screen name="Upload" component={UploadScreen as never} options={{ title: "Belge Yükle", tabBarLabel: "Yükle" }} />
      <Tabs.Screen name="Assistant" component={AssistantScreen as never} options={{ title: "Yardım", tabBarLabel: "Yardım" }} />
      <Tabs.Screen name="Profile" component={ProfileScreen} options={{ title: "Hesabım", tabBarLabel: "Hesabım" }} />
    </Tabs.Navigator>
  );
}

function Root() {
  const { user, loading } = useAuth();
  const c = useColors();

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", backgroundColor: c.bg }}>
        <ActivityIndicator color={c.brand} />
      </View>
    );
  }

  return (
    <Stack.Navigator screenOptions={{ headerStyle: { backgroundColor: c.surface }, headerTintColor: c.text }}>
      {user ? (
        <>
          <Stack.Screen name="Main" component={MainTabs} options={{ headerShown: false }} />
          <Stack.Screen name="DocumentDetail" component={DocumentDetailScreen as never} options={{ title: "Belge" }} />
        </>
      ) : (
        <>
          <Stack.Screen name="Login" component={LoginScreen as never} options={{ headerShown: false }} />
          <Stack.Screen name="Register" component={RegisterScreen} options={{ title: "Kayıt ol" }} />
        </>
      )}
    </Stack.Navigator>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <NavigationContainer>
          <Root />
        </NavigationContainer>
        <StatusBar style="auto" />
      </AuthProvider>
    </SafeAreaProvider>
  );
}
