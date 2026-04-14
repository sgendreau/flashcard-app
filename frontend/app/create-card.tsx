import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView,
  KeyboardAvoidingView, Platform, ActivityIndicator, Keyboard, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/utils/api';

interface Subject {
  id: string;
  name: string;
  color: string;
}

export default function CreateCardScreen() {
  const router = useRouter();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<string>('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingSubjects, setLoadingSubjects] = useState(true);

  useEffect(() => {
    api.get('/subjects').then((data) => {
      setSubjects(data.subjects || []);
      if (data.subjects?.length > 0) setSelectedSubject(data.subjects[0].id);
    }).catch(console.log).finally(() => setLoadingSubjects(false));
  }, []);

  const handleSave = async () => {
    Keyboard.dismiss();
    if (!selectedSubject || !question.trim() || !answer.trim()) {
      Alert.alert('Erreur', 'Veuillez remplir tous les champs');
      return;
    }
    setLoading(true);
    try {
      await api.post('/flashcards', {
        subject_id: selectedSubject,
        question: question.trim(),
        answer: answer.trim(),
      });
      Alert.alert('Succès', 'Flashcard créée !', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    } catch (e: any) {
      Alert.alert('Erreur', e.message || 'Erreur lors de la création');
    } finally {
      setLoading(false);
    }
  };

  if (loadingSubjects) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.center}><ActivityIndicator size="large" color="#FF6B35" /></View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity testID="create-card-close" onPress={() => router.back()} style={styles.closeBtn}>
              <Ionicons name="close" size={24} color="#1F2937" />
            </TouchableOpacity>
            <Text style={styles.title}>Nouvelle Flashcard</Text>
            <View style={{ width: 40 }} />
          </View>

          {/* Subject Selector */}
          <Text style={styles.label}>Matière</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.subjectScroll}>
            {subjects.map((s) => (
              <TouchableOpacity
                key={s.id}
                testID={`create-subject-${s.id}`}
                style={[
                  styles.subjectChip,
                  selectedSubject === s.id && { backgroundColor: s.color, borderColor: s.color },
                ]}
                onPress={() => setSelectedSubject(s.id)}
              >
                <Text style={[styles.chipText, selectedSubject === s.id && { color: '#fff' }]}>
                  {s.name}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          {/* Question */}
          <Text style={styles.label}>Question / Terme</Text>
          <TextInput
            testID="create-card-question"
            style={styles.textArea}
            placeholder="Ex: Théorème de Pythagore"
            placeholderTextColor="#9CA3AF"
            value={question}
            onChangeText={setQuestion}
            multiline
            numberOfLines={3}
            textAlignVertical="top"
          />

          {/* Answer */}
          <Text style={styles.label}>Réponse / Définition</Text>
          <TextInput
            testID="create-card-answer"
            style={styles.textArea}
            placeholder="Ex: a² + b² = c² dans un triangle rectangle"
            placeholderTextColor="#9CA3AF"
            value={answer}
            onChangeText={setAnswer}
            multiline
            numberOfLines={4}
            textAlignVertical="top"
          />

          {/* Save Button */}
          <TouchableOpacity
            testID="create-card-save-btn"
            style={[styles.saveBtn, loading && styles.saveBtnDisabled]}
            onPress={handleSave}
            disabled={loading}
            activeOpacity={0.8}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Ionicons name="checkmark-circle" size={22} color="#fff" />
                <Text style={styles.saveBtnText}>Créer la flashcard</Text>
              </>
            )}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F4F6F8' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { padding: 24, paddingBottom: 40 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 },
  closeBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 20, fontWeight: '800', color: '#1F2937' },
  label: { fontSize: 14, fontWeight: '700', color: '#1F2937', marginBottom: 8, marginTop: 16 },
  subjectScroll: { marginBottom: 8 },
  subjectChip: {
    paddingHorizontal: 18, paddingVertical: 10, borderRadius: 20,
    borderWidth: 2, borderColor: '#E5E7EB', backgroundColor: '#fff', marginRight: 8,
  },
  chipText: { fontSize: 14, fontWeight: '600', color: '#1F2937' },
  textArea: {
    backgroundColor: '#fff', borderRadius: 16, borderWidth: 2, borderColor: '#E5E7EB',
    padding: 16, fontSize: 16, color: '#1F2937', minHeight: 100,
  },
  saveBtn: {
    flexDirection: 'row', backgroundColor: '#FF6B35', borderRadius: 16, paddingVertical: 18,
    alignItems: 'center', justifyContent: 'center', gap: 10, marginTop: 28,
  },
  saveBtnDisabled: { opacity: 0.7 },
  saveBtnText: { color: '#fff', fontSize: 17, fontWeight: '700' },
});
