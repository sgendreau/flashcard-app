import { Stack } from 'expo-router';
import { AuthProvider, useAuth } from '../src/context/AuthContext';
import { ThemeProvider } from '../src/context/ThemeContext';
import { StatusBar } from 'expo-status-bar';

function InnerLayout() {
  const { user } = useAuth();
  const themePref = (user as any)?.theme || 'light';

  return (
    <ThemeProvider initialTheme={themePref as any}>
      <StatusBar style={themePref === 'dark' ? 'light' : 'dark'} />
      <Stack screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="study" />
        <Stack.Screen name="class" />
        <Stack.Screen name="create-card" options={{ presentation: 'modal', animation: 'slide_from_bottom' }} />
        <Stack.Screen name="ai-generate" options={{ presentation: 'modal', animation: 'slide_from_bottom' }} />
      </Stack>
    </ThemeProvider>
  );
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <InnerLayout />
    </AuthProvider>
  );
}
