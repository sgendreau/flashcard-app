import React, { useState, useCallback } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView, RefreshControl,
  ActivityIndicator, TextInput, Alert, KeyboardAvoidingView, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/utils/api';

export default function ClassesScreen() {
  const router = useRouter();
  const [classes, setClasses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [showJoin, setShowJoin] = useState(false);
  const [className, setClassName] = useState('');
  const [joinCode, setJoinCode] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const fetchClasses = async () => {
    try {
      const data = await api.get('/classes');
      setClasses(data.classes || []);
    } catch (e) { console.log('Error:', e); }
    finally { setLoading(false); setRefreshing(false); }
  };

  useFocusEffect(useCallback(() => { fetchClasses(); }, []));
  const onRefresh = () => { setRefreshing(true); fetchClasses(); };

  const handleCreate = async () => {
    if (!className.trim()) return;
    setActionLoading(true);
    try {
      await api.post('/classes', { name: className.trim() });
      setClassName('');
      setShowCreate(false);
      fetchClasses();
      Alert.alert('Classe créée !', 'Partage le code avec tes camarades.');
    } catch (e: any) { Alert.alert('Erreur', e.message); }
    finally { setActionLoading(false); }
  };

  const handleJoin = async () => {
    if (!joinCode.trim()) return;
    setActionLoading(true);
    try {
      await api.post('/classes/join', { code: joinCode.trim().toUpperCase() });
      setJoinCode('');
      setShowJoin(false);
      fetchClasses();
      Alert.alert('Rejoint !', 'Tu fais maintenant partie de la classe.');
    } catch (e: any) { Alert.alert('Erreur', e.message); }
    finally { setActionLoading(false); }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.center}><ActivityIndicator size="large" color="#FF6B35" /></View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#FF6B35" />}
        >
          <Text style={styles.title}>Mes classes</Text>
          <Text style={styles.subtitle}>Partage et étudie des decks avec ta classe</Text>

          {/* Action buttons */}
          <View style={styles.actionsRow}>
            <TouchableOpacity
              testID="create-class-btn"
              style={styles.actionBtn}
              onPress={() => { setShowCreate(!showCreate); setShowJoin(false); }}
            >
              <Ionicons name="add-circle-outline" size={22} color="#FF6B35" />
              <Text style={styles.actionText}>Créer une classe</Text>
            </TouchableOpacity>
            <TouchableOpacity
              testID="join-class-btn"
              style={[styles.actionBtn, { backgroundColor: '#EEF2FF' }]}
              onPress={() => { setShowJoin(!showJoin); setShowCreate(false); }}
            >
              <Ionicons name="enter-outline" size={22} color="#3B82F6" />
              <Text style={[styles.actionText, { color: '#3B82F6' }]}>Rejoindre</Text>
            </TouchableOpacity>
          </View>

          {/* Create Form */}
          {showCreate && (
            <View style={styles.formCard}>
              <Text style={styles.formTitle}>Nouvelle classe</Text>
              <TextInput
                testID="create-class-name-input"
                style={styles.input}
                placeholder="Nom de la classe"
                placeholderTextColor="#9CA3AF"
                value={className}
                onChangeText={setClassName}
              />
              <TouchableOpacity
                testID="create-class-submit"
                style={[styles.submitBtn, actionLoading && { opacity: 0.7 }]}
                onPress={handleCreate}
                disabled={actionLoading}
              >
                {actionLoading ? <ActivityIndicator color="#fff" /> : (
                  <Text style={styles.submitText}>Créer</Text>
                )}
              </TouchableOpacity>
            </View>
          )}

          {/* Join Form */}
          {showJoin && (
            <View style={styles.formCard}>
              <Text style={styles.formTitle}>Rejoindre une classe</Text>
              <TextInput
                testID="join-class-code-input"
                style={styles.input}
                placeholder="Code de la classe (6 caractères)"
                placeholderTextColor="#9CA3AF"
                value={joinCode}
                onChangeText={setJoinCode}
                autoCapitalize="characters"
                maxLength={6}
              />
              <TouchableOpacity
                testID="join-class-submit"
                style={[styles.submitBtn, { backgroundColor: '#3B82F6' }, actionLoading && { opacity: 0.7 }]}
                onPress={handleJoin}
                disabled={actionLoading}
              >
                {actionLoading ? <ActivityIndicator color="#fff" /> : (
                  <Text style={styles.submitText}>Rejoindre</Text>
                )}
              </TouchableOpacity>
            </View>
          )}

          {/* Classes List */}
          {classes.length === 0 ? (
            <View style={styles.emptyWrap}>
              <Ionicons name="people-outline" size={64} color="#D1D5DB" />
              <Text style={styles.emptyTitle}>Aucune classe</Text>
              <Text style={styles.emptyDesc}>Crée ou rejoins une classe pour commencer</Text>
            </View>
          ) : (
            <View style={styles.classList}>
              {classes.map((cls) => (
                <TouchableOpacity
                  key={cls.id}
                  testID={`class-card-${cls.id}`}
                  style={styles.classCard}
                  onPress={() => router.push(`/class/${cls.id}`)}
                  activeOpacity={0.7}
                >
                  <View style={styles.classIconWrap}>
                    <Ionicons name="school-outline" size={28} color="#FF6B35" />
                  </View>
                  <View style={styles.classInfo}>
                    <Text style={styles.classCardName}>{cls.name}</Text>
                    <View style={styles.classMetaRow}>
                      <View style={styles.classMeta}>
                        <Ionicons name="people-outline" size={14} color="#6B7280" />
                        <Text style={styles.classMetaText}>{cls.member_count} membres</Text>
                      </View>
                      <View style={styles.classMeta}>
                        <Ionicons name="layers-outline" size={14} color="#6B7280" />
                        <Text style={styles.classMetaText}>{cls.deck_count} decks</Text>
                      </View>
                    </View>
                  </View>
                  <View style={styles.codeBadge}>
                    <Text style={styles.codeText}>{cls.code}</Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F4F6F8' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { padding: 20, paddingBottom: 40 },
  title: { fontSize: 28, fontWeight: '900', color: '#1F2937' },
  subtitle: { fontSize: 15, color: '#6B7280', marginTop: 4, marginBottom: 20 },
  actionsRow: { flexDirection: 'row', gap: 12, marginBottom: 16 },
  actionBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    paddingVertical: 14, borderRadius: 16, backgroundColor: '#FFF3ED',
  },
  actionText: { fontSize: 14, fontWeight: '700', color: '#FF6B35' },
  formCard: {
    backgroundColor: '#fff', borderRadius: 20, padding: 20, marginBottom: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.04, shadowRadius: 8, elevation: 2,
  },
  formTitle: { fontSize: 18, fontWeight: '700', color: '#1F2937', marginBottom: 12 },
  input: {
    backgroundColor: '#F9FAFB', borderRadius: 14, borderWidth: 2, borderColor: '#E5E7EB',
    paddingHorizontal: 16, paddingVertical: 14, fontSize: 16, color: '#1F2937', marginBottom: 12,
  },
  submitBtn: {
    backgroundColor: '#FF6B35', borderRadius: 14, paddingVertical: 14, alignItems: 'center',
  },
  submitText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  emptyWrap: { alignItems: 'center', paddingTop: 60, gap: 12 },
  emptyTitle: { fontSize: 20, fontWeight: '700', color: '#6B7280' },
  emptyDesc: { fontSize: 14, color: '#9CA3AF', textAlign: 'center' },
  classList: { gap: 12 },
  classCard: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff', borderRadius: 16,
    padding: 16, gap: 14,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.04, shadowRadius: 8, elevation: 2,
  },
  classIconWrap: {
    width: 52, height: 52, borderRadius: 14, backgroundColor: '#FFF3ED',
    alignItems: 'center', justifyContent: 'center',
  },
  classInfo: { flex: 1 },
  classCardName: { fontSize: 17, fontWeight: '700', color: '#1F2937' },
  classMetaRow: { flexDirection: 'row', gap: 16, marginTop: 4 },
  classMeta: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  classMetaText: { fontSize: 12, color: '#6B7280' },
  codeBadge: { backgroundColor: '#F3F4F6', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8 },
  codeText: { fontSize: 12, fontWeight: '800', color: '#6B7280', letterSpacing: 1 },
});
