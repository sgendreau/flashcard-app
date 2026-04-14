import React, { useState, useEffect } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/utils/api';
import * as Clipboard from 'expo-clipboard';

export default function ClassDetailScreen() {
  const { classId } = useLocalSearchParams<{ classId: string }>();
  const router = useRouter();
  const [classData, setClassData] = useState<any>(null);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [sharing, setSharing] = useState(false);

  const fetchClass = async () => {
    try {
      const [clsRes, subjRes] = await Promise.all([
        api.get(`/classes/${classId}`),
        api.get('/subjects'),
      ]);
      setClassData(clsRes.class);
      setSubjects(subjRes.subjects || []);
    } catch (e: any) { Alert.alert('Erreur', e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchClass(); }, [classId]);

  const copyCode = async () => {
    if (classData?.code) {
      await Clipboard.setStringAsync(classData.code);
      Alert.alert('Copié !', `Code: ${classData.code}`);
    }
  };

  const shareDeck = async (subjectId: string, subjectName: string) => {
    setSharing(true);
    try {
      await api.post(`/classes/${classId}/share`, {
        subject_id: subjectId,
        name: `${subjectName} — Deck partagé`,
      });
      Alert.alert('Partagé !', `Le deck "${subjectName}" a été partagé avec la classe.`);
      fetchClass();
    } catch (e: any) { Alert.alert('Erreur', e.message); }
    finally { setSharing(false); }
  };

  const studySharedDeck = (deckId: string) => {
    router.push(`/class/study-deck?classId=${classId}&deckId=${deckId}`);
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.center}><ActivityIndicator size="large" color="#FF6B35" /></View>
      </SafeAreaView>
    );
  }

  if (!classData) return null;

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Header */}
        <View style={styles.headerRow}>
          <TouchableOpacity testID="class-back-btn" onPress={() => router.back()} style={styles.backBtn}>
            <Ionicons name="arrow-back" size={24} color="#1F2937" />
          </TouchableOpacity>
          <Text style={styles.title} numberOfLines={1}>{classData.name}</Text>
          <View style={{ width: 40 }} />
        </View>

        {/* Code */}
        <TouchableOpacity testID="copy-code-btn" style={styles.codeCard} onPress={copyCode}>
          <View>
            <Text style={styles.codeLabel}>Code de la classe</Text>
            <Text style={styles.codeValue}>{classData.code}</Text>
          </View>
          <Ionicons name="copy-outline" size={22} color="#FF6B35" />
        </TouchableOpacity>

        {/* Members */}
        <Text style={styles.sectionTitle}>Membres ({classData.members?.length || 0})</Text>
        <View style={styles.membersRow}>
          {(classData.members || []).map((m: any, i: number) => (
            <View key={i} style={styles.memberChip}>
              <View style={styles.memberAvatar}>
                <Text style={styles.memberAvatarText}>{m.name?.charAt(0)?.toUpperCase()}</Text>
              </View>
              <Text style={styles.memberName}>{m.name}</Text>
              {m.role === 'admin' && (
                <Ionicons name="shield-checkmark" size={14} color="#FF6B35" />
              )}
            </View>
          ))}
        </View>

        {/* Shared Decks */}
        <Text style={styles.sectionTitle}>Decks partagés ({classData.shared_decks?.length || 0})</Text>
        {(classData.shared_decks || []).length === 0 ? (
          <Text style={styles.emptyText}>Aucun deck partagé. Partage le premier !</Text>
        ) : (
          (classData.shared_decks || []).map((deck: any) => (
            <TouchableOpacity
              key={deck.id}
              testID={`shared-deck-${deck.id}`}
              style={styles.deckCard}
              onPress={() => studySharedDeck(deck.id)}
            >
              <View style={styles.deckInfo}>
                <Text style={styles.deckName}>{deck.name}</Text>
                <Text style={styles.deckMeta}>Par {deck.shared_by_name} • {deck.card_count} cartes</Text>
              </View>
              <Ionicons name="play-circle" size={28} color="#FF6B35" />
            </TouchableOpacity>
          ))
        )}

        {/* Share a deck */}
        <Text style={[styles.sectionTitle, { marginTop: 24 }]}>Partager un deck</Text>
        <View style={styles.shareGrid}>
          {subjects.map((s: any) => (
            <TouchableOpacity
              key={s.id}
              testID={`share-subject-${s.id}`}
              style={styles.shareCard}
              onPress={() => shareDeck(s.id, s.name)}
              disabled={sharing}
            >
              <Text style={[styles.shareName, { color: s.color }]}>{s.name}</Text>
              <Ionicons name="share-outline" size={18} color={s.color} />
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F4F6F8' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { padding: 20, paddingBottom: 40 },
  headerRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 },
  backBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 22, fontWeight: '900', color: '#1F2937', flex: 1, textAlign: 'center' },
  codeCard: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: '#FFF3ED', borderRadius: 16, padding: 16, marginBottom: 24,
    borderWidth: 2, borderColor: '#FF6B35', borderStyle: 'dashed',
  },
  codeLabel: { fontSize: 12, color: '#6B7280', fontWeight: '600' },
  codeValue: { fontSize: 28, fontWeight: '900', color: '#FF6B35', letterSpacing: 4 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: '#1F2937', marginBottom: 12 },
  membersRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 24 },
  memberChip: {
    flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: '#fff',
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20,
  },
  memberAvatar: {
    width: 28, height: 28, borderRadius: 14, backgroundColor: '#3B82F6',
    alignItems: 'center', justifyContent: 'center',
  },
  memberAvatarText: { color: '#fff', fontSize: 12, fontWeight: '700' },
  memberName: { fontSize: 14, fontWeight: '600', color: '#1F2937' },
  emptyText: { fontSize: 14, color: '#9CA3AF', textAlign: 'center', paddingVertical: 16 },
  deckCard: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: '#fff', borderRadius: 16, padding: 16, marginBottom: 10,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.04, shadowRadius: 8, elevation: 2,
  },
  deckInfo: { flex: 1 },
  deckName: { fontSize: 16, fontWeight: '700', color: '#1F2937' },
  deckMeta: { fontSize: 12, color: '#6B7280', marginTop: 4 },
  shareGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  shareCard: {
    flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: '#fff',
    paddingHorizontal: 14, paddingVertical: 10, borderRadius: 12,
    borderWidth: 1, borderColor: '#E5E7EB',
  },
  shareName: { fontSize: 13, fontWeight: '600' },
});
