import React, { useState, useEffect } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/utils/api';
import { useTheme } from '../../src/context/ThemeContext';
import * as Clipboard from 'expo-clipboard';

export default function ClassDetailScreen() {
  const { classId } = useLocalSearchParams<{ classId: string }>();
  const { colors } = useTheme();
  const router = useRouter();
  const [classData, setClassData] = useState<any>(null);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAll = async () => {
    try {
      const [cls, subj, lb] = await Promise.all([
        api.get(`/classes/${classId}`),
        api.get('/subjects'),
        api.get(`/classes/${classId}/leaderboard`),
      ]);
      setClassData(cls.class);
      setSubjects(subj.subjects || []);
      setLeaderboard(lb.leaderboard || []);
    } catch (e: any) { Alert.alert('Erreur', e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, [classId]);

  const copyCode = async () => {
    if (classData?.code) { await Clipboard.setStringAsync(classData.code); Alert.alert('Copié !', `Code: ${classData.code}`); }
  };

  const shareDeck = async (sid: string, sname: string) => {
    try {
      await api.post(`/classes/${classId}/share`, { subject_id: sid, name: `${sname} — Deck partagé` });
      Alert.alert('Partagé !');
      fetchAll();
    } catch (e: any) { Alert.alert('Erreur', e.message); }
  };

  if (loading) return <SafeAreaView style={[s.safe, { backgroundColor: colors.bg }]}><View style={s.center}><ActivityIndicator size="large" color={colors.primary} /></View></SafeAreaView>;
  if (!classData) return null;

  const MEDAL_COLORS = ['#FFD700', '#C0C0C0', '#CD7F32'];

  return (
    <SafeAreaView style={[s.safe, { backgroundColor: colors.bg }]}>
      <ScrollView contentContainerStyle={s.scroll}>
        <View style={s.headerRow}>
          <TouchableOpacity testID="class-back-btn" onPress={() => router.back()} style={[s.backBtn, { backgroundColor: colors.surface }]}>
            <Ionicons name="arrow-back" size={24} color={colors.text} />
          </TouchableOpacity>
          <Text style={[s.title, { color: colors.text }]} numberOfLines={1}>{classData.name}</Text>
          <View style={{ width: 40 }} />
        </View>

        {/* Code */}
        <TouchableOpacity testID="copy-code-btn" style={[s.codeCard, { backgroundColor: colors.primaryBg, borderColor: colors.primary }]} onPress={copyCode}>
          <View><Text style={[s.codeLabel, { color: colors.textSecondary }]}>Code</Text><Text style={[s.codeValue, { color: colors.primary }]}>{classData.code}</Text></View>
          <Ionicons name="copy-outline" size={22} color={colors.primary} />
        </TouchableOpacity>

        {/* Leaderboard */}
        <Text style={[s.sectionTitle, { color: colors.text }]}>Classement</Text>
        <View style={[s.leaderCard, { backgroundColor: colors.surface }]}>
          {leaderboard.map((entry, i) => (
            <View key={i} style={[s.lbRow, i < leaderboard.length - 1 && { borderBottomWidth: 1, borderBottomColor: colors.borderLight }]}>
              <View style={[s.rankCircle, { backgroundColor: i < 3 ? MEDAL_COLORS[i] + '30' : colors.surfaceAlt }]}>
                <Text style={[s.rankText, { color: i < 3 ? MEDAL_COLORS[i] : colors.textSecondary }]}>
                  {i < 3 ? ['🥇', '🥈', '🥉'][i] : `${entry.rank}`}
                </Text>
              </View>
              <View style={s.lbInfo}>
                <Text style={[s.lbName, { color: colors.text }]}>{entry.name}</Text>
                <Text style={[s.lbMeta, { color: colors.textSecondary }]}>
                  Niv. {entry.level} • {entry.sessions} sessions • Moy. {entry.avg_score}%
                </Text>
              </View>
              <View style={{ alignItems: 'flex-end' }}>
                <Text style={[s.lbXP, { color: colors.primary }]}>{entry.xp} XP</Text>
                {entry.streak > 0 && (
                  <View style={s.streakBadge}>
                    <Ionicons name="flame" size={12} color="#FF5A00" />
                    <Text style={s.streakText}>{entry.streak}</Text>
                  </View>
                )}
              </View>
            </View>
          ))}
          {leaderboard.length === 0 && <Text style={[s.empty, { color: colors.textMuted }]}>Pas encore de données</Text>}
        </View>

        {/* Members */}
        <Text style={[s.sectionTitle, { color: colors.text }]}>Membres ({classData.members?.length || 0})</Text>
        <View style={s.membersRow}>
          {(classData.members || []).map((m: any, i: number) => (
            <View key={i} style={[s.memberChip, { backgroundColor: colors.surface }]}>
              <View style={[s.memberAvatar, { backgroundColor: '#3B82F6' }]}><Text style={s.memberAvatarText}>{m.name?.charAt(0)?.toUpperCase()}</Text></View>
              <Text style={[s.memberName, { color: colors.text }]}>{m.name}</Text>
              {m.role === 'admin' && <Ionicons name="shield-checkmark" size={14} color={colors.primary} />}
            </View>
          ))}
        </View>

        {/* Shared Decks */}
        <Text style={[s.sectionTitle, { color: colors.text }]}>Decks partagés</Text>
        {(classData.shared_decks || []).length === 0 ? (
          <Text style={[s.empty, { color: colors.textMuted }]}>Aucun deck partagé</Text>
        ) : (
          (classData.shared_decks || []).map((deck: any) => (
            <TouchableOpacity key={deck.id} testID={`shared-deck-${deck.id}`} style={[s.deckCard, { backgroundColor: colors.surface }]}
              onPress={() => router.push(`/class/study-deck?classId=${classId}&deckId=${deck.id}`)}>
              <View style={s.deckInfo}><Text style={[s.deckName, { color: colors.text }]}>{deck.name}</Text><Text style={[s.deckMeta, { color: colors.textSecondary }]}>Par {deck.shared_by_name} • {deck.card_count} cartes</Text></View>
              <Ionicons name="play-circle" size={28} color={colors.primary} />
            </TouchableOpacity>
          ))
        )}

        {/* Share */}
        <Text style={[s.sectionTitle, { color: colors.text, marginTop: 24 }]}>Partager un deck</Text>
        <View style={s.shareGrid}>
          {subjects.map((subj: any) => (
            <TouchableOpacity key={subj.id} testID={`share-subject-${subj.id}`}
              style={[s.shareCard, { backgroundColor: colors.surface, borderColor: colors.border }]}
              onPress={() => shareDeck(subj.id, subj.name)}>
              <Text style={[s.shareName, { color: subj.color }]}>{subj.name}</Text>
              <Ionicons name="share-outline" size={16} color={subj.color} />
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1 }, center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { padding: 20, paddingBottom: 40 },
  headerRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 },
  backBtn: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 22, fontWeight: '900', flex: 1, textAlign: 'center' },
  codeCard: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderRadius: 16, padding: 16, marginBottom: 24, borderWidth: 2, borderStyle: 'dashed' },
  codeLabel: { fontSize: 12, fontWeight: '600' },
  codeValue: { fontSize: 28, fontWeight: '900', letterSpacing: 4 },
  sectionTitle: { fontSize: 18, fontWeight: '700', marginBottom: 12 },
  leaderCard: { borderRadius: 20, padding: 16, marginBottom: 20 },
  lbRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12, gap: 12 },
  rankCircle: { width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
  rankText: { fontSize: 16, fontWeight: '800' },
  lbInfo: { flex: 1 },
  lbName: { fontSize: 15, fontWeight: '700' },
  lbMeta: { fontSize: 11, marginTop: 2 },
  lbXP: { fontSize: 15, fontWeight: '800' },
  streakBadge: { flexDirection: 'row', alignItems: 'center', gap: 2, marginTop: 2 },
  streakText: { fontSize: 11, fontWeight: '700', color: '#FF5A00' },
  membersRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 24 },
  memberChip: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20 },
  memberAvatar: { width: 28, height: 28, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  memberAvatarText: { color: '#fff', fontSize: 12, fontWeight: '700' },
  memberName: { fontSize: 14, fontWeight: '600' },
  empty: { fontSize: 14, textAlign: 'center', paddingVertical: 16 },
  deckCard: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderRadius: 16, padding: 16, marginBottom: 10 },
  deckInfo: { flex: 1 }, deckName: { fontSize: 16, fontWeight: '700' }, deckMeta: { fontSize: 12, marginTop: 4 },
  shareGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  shareCard: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 12, borderWidth: 1 },
  shareName: { fontSize: 13, fontWeight: '600' },
});
