import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView,
  Platform, ActivityIndicator, ScrollView, Keyboard, Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/context/AuthContext';
import { QUIKKO_LOGO } from '../../assets/logo-base64';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPass, setShowPass] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleLogin = async () => {
    Keyboard.dismiss();
    if (!email.trim() || !password.trim()) { setError('Veuillez remplir tous les champs'); return; }
    setError(''); setLoading(true);
    try { await login(email.trim(), password); router.replace('/(tabs)/home'); }
    catch (e: any) { setError(e.message || 'Erreur de connexion'); }
    finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={s.safe}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={s.flex}>
        <ScrollView contentContainerStyle={s.scroll} keyboardShouldPersistTaps="handled">
          <View style={s.header}>
            <Image source={{ uri: QUIKKO_LOGO }} style={s.logo} />
            <Text style={s.title}>quikko</Text>
            <Text style={s.subtitle}>Révise vite, retiens tout</Text>
          </View>

          <View style={s.form}>
            <Text style={s.formTitle}>Connexion</Text>
            {error ? (
              <View style={s.errorBox} testID="login-error">
                <Ionicons name="alert-circle" size={18} color="#E8594D" />
                <Text style={s.errorText}>{error}</Text>
              </View>
            ) : null}
            <View style={s.inputWrap}>
              <Ionicons name="mail-outline" size={20} color="#9696AD" style={s.inputIcon} />
              <TextInput testID="login-email-input" style={s.input} placeholder="Email" placeholderTextColor="#9696AD"
                value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} />
            </View>
            <View style={s.inputWrap}>
              <Ionicons name="lock-closed-outline" size={20} color="#9696AD" style={s.inputIcon} />
              <TextInput testID="login-password-input" style={s.input} placeholder="Mot de passe" placeholderTextColor="#9696AD"
                value={password} onChangeText={setPassword} secureTextEntry={!showPass} />
              <TouchableOpacity testID="login-toggle-pass" onPress={() => setShowPass(!showPass)}>
                <Ionicons name={showPass ? 'eye-off-outline' : 'eye-outline'} size={20} color="#9696AD" />
              </TouchableOpacity>
            </View>
            <TouchableOpacity testID="login-submit-btn" style={[s.btn, loading && s.btnDis]} onPress={handleLogin} disabled={loading} activeOpacity={0.8}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>Se connecter</Text>}
            </TouchableOpacity>
            <TouchableOpacity testID="login-go-register" style={s.linkWrap} onPress={() => router.push('/(auth)/register')}>
              <Text style={s.linkText}>Pas encore de compte ? <Text style={s.linkBold}>S{"'"}inscrire</Text></Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#1A1A2E' },
  flex: { flex: 1 },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  header: { alignItems: 'center', marginBottom: 36 },
  logo: { width: 180, height: 98, borderRadius: 18, marginBottom: 12 },
  title: { fontSize: 36, fontWeight: '900', color: '#E8594D', letterSpacing: 1 },
  subtitle: { fontSize: 15, color: '#A0A0C0', marginTop: 4 },
  form: { backgroundColor: '#1E2A45', borderRadius: 24, padding: 24 },
  formTitle: { fontSize: 24, fontWeight: '800', color: '#F0F0F8', marginBottom: 20 },
  errorBox: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#3A1F1D', padding: 12, borderRadius: 12, marginBottom: 16, gap: 8 },
  errorText: { color: '#E8594D', fontSize: 14, fontWeight: '500', flex: 1 },
  inputWrap: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#263352', borderRadius: 16, borderWidth: 2, borderColor: '#2A3555', paddingHorizontal: 16, marginBottom: 16, height: 56 },
  inputIcon: { marginRight: 12 },
  input: { flex: 1, fontSize: 16, color: '#F0F0F8' },
  btn: { backgroundColor: '#E8594D', borderRadius: 16, height: 56, alignItems: 'center', justifyContent: 'center', marginTop: 8 },
  btnDis: { opacity: 0.7 },
  btnText: { color: '#fff', fontSize: 18, fontWeight: '700' },
  linkWrap: { alignItems: 'center', marginTop: 20 },
  linkText: { fontSize: 15, color: '#A0A0C0' },
  linkBold: { color: '#E8594D', fontWeight: '700' },
});
