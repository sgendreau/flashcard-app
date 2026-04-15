import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView,
  Platform, ActivityIndicator, ScrollView, Keyboard,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/context/AuthContext';

export default function RegisterScreen() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [referralCode, setReferralCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPass, setShowPass] = useState(false);
  const { register } = useAuth();
  const router = useRouter();

  const handleRegister = async () => {
    Keyboard.dismiss();
    if (!name.trim() || !email.trim() || !password.trim()) {
      setError('Veuillez remplir tous les champs');
      return;
    }
    if (password.length < 6) {
      setError('Le mot de passe doit contenir au moins 6 caractères');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await register(name.trim(), email.trim(), password, referralCode.trim() || undefined);
      router.replace('/(tabs)/home');
    } catch (e: any) {
      setError(e.message || "Erreur d'inscription");
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.flex}
      >
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <View style={styles.header}>
            <View style={styles.iconCircle}>
              <Ionicons name="school" size={40} color="#FF6B35" />
            </View>
            <Text style={styles.title}>FlashCards</Text>
            <Text style={styles.subtitle}>Crée ton compte</Text>
          </View>

          <View style={styles.form}>
            <Text style={styles.formTitle}>Inscription</Text>

            {error ? (
              <View style={styles.errorBox} testID="register-error">
                <Ionicons name="alert-circle" size={18} color="#EF4444" />
                <Text style={styles.errorText}>{error}</Text>
              </View>
            ) : null}

            <View style={styles.inputWrap}>
              <Ionicons name="person-outline" size={20} color="#6B7280" style={styles.inputIcon} />
              <TextInput
                testID="register-name-input"
                style={styles.input}
                placeholder="Prénom"
                placeholderTextColor="#9CA3AF"
                value={name}
                onChangeText={setName}
                autoCapitalize="words"
              />
            </View>

            <View style={styles.inputWrap}>
              <Ionicons name="mail-outline" size={20} color="#6B7280" style={styles.inputIcon} />
              <TextInput
                testID="register-email-input"
                style={styles.input}
                placeholder="Email"
                placeholderTextColor="#9CA3AF"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            <View style={styles.inputWrap}>
              <Ionicons name="lock-closed-outline" size={20} color="#6B7280" style={styles.inputIcon} />
              <TextInput
                testID="register-password-input"
                style={styles.input}
                placeholder="Mot de passe (min. 6 caractères)"
                placeholderTextColor="#9CA3AF"
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPass}
              />
              <TouchableOpacity testID="register-toggle-pass" onPress={() => setShowPass(!showPass)}>
                <Ionicons name={showPass ? 'eye-off-outline' : 'eye-outline'} size={20} color="#6B7280" />
              </TouchableOpacity>
            </View>

            <View style={styles.inputWrap}>
              <Ionicons name="gift-outline" size={20} color="#6B7280" style={styles.inputIcon} />
              <TextInput
                testID="register-referral-input"
                style={styles.input}
                placeholder="Code parrainage (optionnel)"
                placeholderTextColor="#9CA3AF"
                value={referralCode}
                onChangeText={setReferralCode}
                autoCapitalize="characters"
              />
            </View>

            <TouchableOpacity
              testID="register-submit-btn"
              style={[styles.btn, loading && styles.btnDisabled]}
              onPress={handleRegister}
              disabled={loading}
              activeOpacity={0.8}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.btnText}>S'inscrire</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              testID="register-go-login"
              style={styles.linkWrap}
              onPress={() => router.back()}
            >
              <Text style={styles.linkText}>
                Déjà un compte ? <Text style={styles.linkBold}>Se connecter</Text>
              </Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F4F6F8' },
  flex: { flex: 1 },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  header: { alignItems: 'center', marginBottom: 40 },
  iconCircle: {
    width: 80, height: 80, borderRadius: 40, backgroundColor: '#FFF3ED',
    alignItems: 'center', justifyContent: 'center', marginBottom: 16,
  },
  title: { fontSize: 32, fontWeight: '900', color: '#1F2937', letterSpacing: 0.5 },
  subtitle: { fontSize: 16, color: '#6B7280', marginTop: 4 },
  form: {
    backgroundColor: '#FFFFFF', borderRadius: 24, padding: 24,
    shadowColor: '#000', shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05, shadowRadius: 12, elevation: 3,
  },
  formTitle: { fontSize: 24, fontWeight: '800', color: '#1F2937', marginBottom: 20 },
  errorBox: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#FEF2F2',
    padding: 12, borderRadius: 12, marginBottom: 16, gap: 8,
  },
  errorText: { color: '#EF4444', fontSize: 14, fontWeight: '500', flex: 1 },
  inputWrap: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#F9FAFB',
    borderRadius: 16, borderWidth: 2, borderColor: '#E5E7EB',
    paddingHorizontal: 16, marginBottom: 16, height: 56,
  },
  inputIcon: { marginRight: 12 },
  input: { flex: 1, fontSize: 16, color: '#1F2937' },
  btn: {
    backgroundColor: '#FF6B35', borderRadius: 16, height: 56,
    alignItems: 'center', justifyContent: 'center', marginTop: 8,
  },
  btnDisabled: { opacity: 0.7 },
  btnText: { color: '#fff', fontSize: 18, fontWeight: '700' },
  linkWrap: { alignItems: 'center', marginTop: 20 },
  linkText: { fontSize: 15, color: '#6B7280' },
  linkBold: { color: '#FF6B35', fontWeight: '700' },
});
