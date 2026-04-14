import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView,
  KeyboardAvoidingView, Platform, ActivityIndicator, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../src/context/ThemeContext';
import { useResponsive } from '../src/utils/responsive';
import { api } from '../src/utils/api';

interface Subject { id: string; name: string; color: string; }

export default function AIGenerateScreen() {
  const { colors } = useTheme();
  const { isTablet } = useResponsive();
  const router = useRouter();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [inputText, setInputText] = useState('');
  const [count, setCount] = useState('5');
  const [loading, setLoading] = useState(false);
  const [loadingSubjects, setLoadingSubjects] = useState(true);
  const [generatedCards, setGeneratedCards] = useState<any[]>([]);

  useEffect(() => {
    api.get('/subjects').then((d) => {
      setSubjects(d.subjects || []);
      if (d.subjects?.length) setSelectedSubject(d.subjects[0].id);
    }).catch(console.log).finally(() => setLoadingSubjects(false));
  }, []);

  const handleGenerate = async () => {
    if (!inputText.trim()) { Alert.alert('Erreur', 'Colle du texte de cours pour générer des flashcards'); return; }
    setLoading(true);
    setGeneratedCards([]);
    try {
      const data = await api.post('/ai/generate', {
        subject_id: selectedSubject,
        text: inputText.trim(),
        count: parseInt(count) || 5,
      });
      setGeneratedCards(data.cards || []);
      Alert.alert('Généré !', `${data.generated} flashcards créées par l'IA`);
    } catch (e: any) {
      Alert.alert('Erreur', e.message || "Erreur de génération");
    } finally {
      setLoading(false);
    }
  };

  if (loadingSubjects) {
    return <SafeAreaView style={[s.safe, { backgroundColor: colors.bg }]}><View style={s.center}><ActivityIndicator size="large" color={colors.primary} /></View></SafeAreaView>;
  }

  return (
    <SafeAreaView style={[s.safe, { backgroundColor: colors.bg }]}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={[s.scroll, isTablet && { paddingHorizontal: 60 }]} keyboardShouldPersistTaps="handled">
          <View style={s.header}>
            <TouchableOpacity testID="ai-close-btn" onPress={() => router.back()} style={[s.closeBtn, { backgroundColor: colors.surface }]}>
              <Ionicons name="close" size={24} color={colors.text} />
            </TouchableOpacity>
            <Text style={[s.title, { color: colors.text }]}>Générer avec l'IA</Text>
            <Ionicons name="sparkles" size={24} color={colors.primary} />
          </View>

          <View style={[s.card, { backgroundColor: colors.surface }]}>
            <View style={s.aiHeaderRow}>
              <Ionicons name="sparkles" size={28} color={colors.primary} />
              <View style={{ flex: 1 }}>
                <Text style={[s.aiTitle, { color: colors.text }]}>Claude Sonnet</Text>
                <Text style={[s.aiDesc, { color: colors.textSecondary }]}>Colle un texte de cours et l'IA génère des flashcards automatiquement</Text>
              </View>
            </View>
          </View>

          {/* Subject */}
          <Text style={[s.label, { color: colors.text }]}>Matière</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.chipScroll}>
            {subjects.map((sub) => (
              <TouchableOpacity key={sub.id} testID={`ai-subject-${sub.id}`}
                style={[s.chip, { borderColor: colors.border, backgroundColor: colors.surface },
                  selectedSubject === sub.id && { backgroundColor: sub.color, borderColor: sub.color }]}
                onPress={() => setSelectedSubject(sub.id)}>
                <Text style={[s.chipText, { color: colors.text }, selectedSubject === sub.id && { color: '#fff' }]}>{sub.name}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          {/* Count */}
          <Text style={[s.label, { color: colors.text }]}>Nombre de cartes</Text>
          <View style={s.countRow}>
            {['3', '5', '8', '10'].map((n) => (
              <TouchableOpacity key={n} testID={`ai-count-${n}`}
                style={[s.countBtn, { borderColor: colors.border, backgroundColor: colors.surface },
                  count === n && { backgroundColor: colors.primary, borderColor: colors.primary }]}
                onPress={() => setCount(n)}>
                <Text style={[s.countText, { color: colors.text }, count === n && { color: '#fff' }]}>{n}</Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Text Input */}
          <Text style={[s.label, { color: colors.text }]}>Texte de cours</Text>
          <TextInput
            testID="ai-text-input"
            style={[s.textArea, { backgroundColor: colors.surfaceAlt, borderColor: colors.border, color: colors.text }]}
            placeholder="Colle ici un extrait de cours, une leçon, des notes..."
            placeholderTextColor={colors.textMuted}
            value={inputText}
            onChangeText={setInputText}
            multiline
            numberOfLines={8}
            textAlignVertical="top"
          />

          {/* Generate */}
          <TouchableOpacity testID="ai-generate-btn"
            style={[s.genBtn, { backgroundColor: colors.primary }, loading && { opacity: 0.7 }]}
            onPress={handleGenerate} disabled={loading}>
            {loading ? (
              <><ActivityIndicator color="#fff" /><Text style={s.genText}>Génération en cours...</Text></>
            ) : (
              <><Ionicons name="sparkles" size={20} color="#fff" /><Text style={s.genText}>Générer les flashcards</Text></>
            )}
          </TouchableOpacity>

          {/* Results */}
          {generatedCards.length > 0 && (
            <View style={{ marginTop: 24 }}>
              <Text style={[s.label, { color: colors.text }]}>Cartes générées ({generatedCards.length})</Text>
              {generatedCards.map((card, i) => (
                <View key={i} style={[s.genCard, { backgroundColor: colors.surface, borderColor: colors.border }]}>
                  <Text style={[s.genQ, { color: colors.text }]}>{card.question}</Text>
                  <Text style={[s.genA, { color: colors.textSecondary }]}>{card.answer}</Text>
                </View>
              ))}
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1 }, center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { padding: 24, paddingBottom: 40 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 },
  closeBtn: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 20, fontWeight: '800', flex: 1, textAlign: 'center' },
  card: { borderRadius: 20, padding: 20, marginBottom: 20 },
  aiHeaderRow: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  aiTitle: { fontSize: 18, fontWeight: '800' },
  aiDesc: { fontSize: 13, marginTop: 4 },
  label: { fontSize: 14, fontWeight: '700', marginBottom: 8, marginTop: 12 },
  chipScroll: { marginBottom: 8 },
  chip: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 16, borderWidth: 2, marginRight: 8 },
  chipText: { fontSize: 13, fontWeight: '600' },
  countRow: { flexDirection: 'row', gap: 10, marginBottom: 8 },
  countBtn: { width: 48, height: 48, borderRadius: 14, borderWidth: 2, alignItems: 'center', justifyContent: 'center' },
  countText: { fontSize: 16, fontWeight: '700' },
  textArea: { borderRadius: 16, borderWidth: 2, padding: 16, fontSize: 15, minHeight: 160 },
  genBtn: { flexDirection: 'row', borderRadius: 16, paddingVertical: 18, alignItems: 'center', justifyContent: 'center', gap: 10, marginTop: 20 },
  genText: { color: '#fff', fontSize: 17, fontWeight: '700' },
  genCard: { borderRadius: 14, padding: 16, marginBottom: 10, borderWidth: 1 },
  genQ: { fontSize: 15, fontWeight: '700' },
  genA: { fontSize: 13, marginTop: 6 },
});
