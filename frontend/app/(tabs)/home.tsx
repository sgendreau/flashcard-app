import React, { useState, useCallback } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView, RefreshControl,
  ActivityIndicator, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/context/AuthContext';
import { useTheme } from '../../src/context/ThemeContext';
import { api } from '../../src/utils/api';
import * as Clipboard from 'expo-clipboard';

const SUBJECT_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  'calculator-outline': 'calculator-outline', 'book-outline': 'book-outline',
  'earth-outline': 'earth-outline', 'leaf-outline': 'leaf-outline',
  'flask-outline': 'flask-outline', 'language-outline': 'language-outline',
  'bulb-outline': 'bulb-outline', 'trending-up-outline': 'trending-up-outline',
  'sunny-outline': 'sunny-outline',
};

const GRADE_LABELS: Record<string, string> = {
  '6eme': '6ème', '5eme': '5ème', '4eme': '4ème', '3eme': '3ème',
  '2nde': '2nde', '1ere': '1ère', 'terminale': 'Term.',
};

interface Subject { id: string; name: string; icon: string; color: string; description: string; card_count: number; }

export default function HomeScreen() {
  const { user, refreshUser } = useAuth();
  const { colors } = useTheme();
  const router = useRouter();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [gradeFilter, setGradeFilter] = useState<string | null>(null);
  const [allGrades, setAllGrades] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async (grade?: string | null) => {
    try {
      const g = grade !== undefined ? grade : gradeFilter;
      const url = g ? `/subjects?grade=${g}` : '/subjects';
      const data = await api.get(url);
      setSubjects(data.subjects || []);
      if (data.grade_levels) setAllGrades(data.grade_levels);
      await refreshUser();
    } catch (e) { console.log('Error:', e); }
    finally { setLoading(false); setRefreshing(false); }
  };

  useFocusEffect(useCallback(() => {
    setGradeFilter(user?.grade_level || null);
    fetchData(user?.grade_level || null);
  }, [user?.grade_level]));

  const toggleGrade = (g: string) => {
    const n = gradeFilter === g ? null : g;
    setGradeFilter(n);
    setLoading(true);
    fetchData(n);
  };

  const handleExport = async (sid: string, name: string) => {
    try {
      const data = await api.get(`/export/${sid}`);
      await Clipboard.setStringAsync(JSON.stringify(data.export, null, 2));
      Alert.alert('Exporté !', `"${name}" copié dans le presse-papier.`);
    } catch (e: any) { Alert.alert('Erreur', e.message); }
  };

  const handleImport = async () => {
    try {
      const text = await Clipboard.getStringAsync();
      if (!text) { Alert.alert('Erreur', 'Presse-papier vide'); return; }
      const parsed = JSON.parse(text);
      if (!parsed.cards || !parsed.subject_id) { Alert.alert('Erreur', 'Format invalide'); return; }
      const data = await api.post('/import', { subject_id: parsed.subject_id, cards: parsed.cards });
      Alert.alert('Importé !', `${data.imported} cartes importées.`);
      fetchData();
    } catch { Alert.alert('Erreur', 'JSON invalide'); }
  };

  if (loading) {
    return <SafeAreaView style={[styles.safe, { backgroundColor: colors.bg }]}><View style={styles.center}><ActivityIndicator size="large" color={colors.primary} /></View></SafeAreaView>;
  }

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.bg }]}>
      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchData(); }} tintColor={colors.primary} />}>
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={[styles.greeting, { color: colors.textSecondary }]}>Bonjour,</Text>
            <Text style={[styles.userName, { color: colors.text }]} testID="home-user-name">{user?.name || 'Étudiant'}</Text>
          </View>
          <View style={styles.statsRow}>
            <View style={[styles.statBadge, { backgroundColor: colors.primaryBg }]}>
              <Ionicons name="flame" size={18} color="#FF5A00" />
              <Text style={[styles.statText, { color: colors.text }]} testID="home-streak">{user?.streak_count || 0}</Text>
            </View>
            <View style={[styles.statBadge, { backgroundColor: colors.warningBg }]}>
              <Ionicons name="star" size={18} color="#FBBF24" />
              <Text style={[styles.statText, { color: colors.text }]} testID="home-xp">{user?.xp || 0} XP</Text>
            </View>
          </View>
        </View>

        {/* Level */}
        <View style={[styles.levelCard, { backgroundColor: colors.surface }]}>
          <View style={styles.levelRow}>
            <Text style={[styles.levelLabel, { color: colors.text }]}>Niveau {user?.level || 1}</Text>
            <Text style={[styles.levelXP, { color: colors.textSecondary }]}>{(user?.xp || 0) % 500} / 500 XP</Text>
          </View>
          <View style={[styles.progressBg, { backgroundColor: colors.border }]}>
            <View style={[styles.progressFill, { width: `${((user?.xp || 0) % 500) / 5}%` }]} />
          </View>
        </View>

        {/* Grade chips */}
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Filtre par niveau</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.gradeScroll}>
          {allGrades.map((g) => (
            <TouchableOpacity key={g} testID={`grade-filter-${g}`}
              style={[styles.gradeChip, { borderColor: colors.border, backgroundColor: colors.surface }, gradeFilter === g && { backgroundColor: colors.primary, borderColor: colors.primary }]}
              onPress={() => toggleGrade(g)}>
              <Text style={[styles.gradeText, { color: colors.text }, gradeFilter === g && { color: '#fff' }]}>{GRADE_LABELS[g] || g}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Import */}
        <TouchableOpacity testID="import-deck-btn" style={[styles.importBtn, { backgroundColor: colors.primaryBg }]} onPress={handleImport}>
          <Ionicons name="download-outline" size={18} color={colors.primary} />
          <Text style={[styles.importBtnText, { color: colors.primary }]}>Importer un deck</Text>
        </TouchableOpacity>

        {/* Subjects */}
        <Text style={[styles.sectionTitle, { color: colors.text, marginTop: 16 }]}>
          {gradeFilter ? `Matières (${GRADE_LABELS[gradeFilter]})` : 'Toutes les matières'}
        </Text>
        <View style={styles.subjectsGrid}>
          {subjects.map((subject) => (
            <View key={subject.id} style={[styles.subjectCard, { backgroundColor: colors.surface, borderLeftColor: subject.color }]}>
              <TouchableOpacity testID={`subject-card-${subject.id}`} style={styles.subjectTouch}
                onPress={() => router.push(`/study/${subject.id}`)} activeOpacity={0.7}>
                <View style={[styles.subjectIcon, { backgroundColor: subject.color + '18' }]}>
                  <Ionicons name={(SUBJECT_ICONS[subject.icon] || 'book-outline') as any} size={28} color={subject.color} />
                </View>
                <View style={styles.subjectInfo}>
                  <Text style={[styles.subjectName, { color: colors.text }]}>{subject.name}</Text>
                  <Text style={[styles.subjectDesc, { color: colors.textSecondary }]} numberOfLines={1}>{subject.description}</Text>
                  <Text style={[styles.cardCount, { color: colors.primary }]}>{subject.card_count} cartes</Text>
                </View>
                <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
              </TouchableOpacity>
              {/* Quiz mode button */}
              <TouchableOpacity testID={`quiz-btn-${subject.id}`}
                style={[styles.quizBtn, { backgroundColor: colors.warningBg }]}
                onPress={() => router.push(`/study/${subject.id}?mode=quiz`)}>
                <Ionicons name="timer-outline" size={14} color={colors.warning} />
                <Text style={[styles.quizBtnText, { color: colors.warning }]}>Quiz</Text>
              </TouchableOpacity>
              <TouchableOpacity testID={`export-btn-${subject.id}`} style={[styles.exportSmallBtn, { backgroundColor: colors.surfaceAlt }]}
                onPress={() => handleExport(subject.id, subject.name)}>
                <Ionicons name="share-outline" size={16} color={colors.textSecondary} />
              </TouchableOpacity>
            </View>
          ))}
          {subjects.length === 0 && <Text style={[styles.emptyText, { color: colors.textMuted }]}>Aucune matière pour ce niveau</Text>}
        </View>
      </ScrollView>

      <TouchableOpacity testID="create-card-fab" style={[styles.fab, { backgroundColor: colors.primary }]} onPress={() => router.push('/create-card')} activeOpacity={0.8}>
        <Ionicons name="add" size={28} color="#fff" />
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { flex: 1 },
  scrollContent: { padding: 20, paddingBottom: 100 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 },
  greeting: { fontSize: 16, fontWeight: '500' },
  userName: { fontSize: 28, fontWeight: '900', marginTop: 2 },
  statsRow: { flexDirection: 'row', gap: 8, marginTop: 4 },
  statBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20 },
  statText: { fontSize: 14, fontWeight: '700' },
  levelCard: { borderRadius: 20, padding: 16, marginBottom: 20 },
  levelRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 },
  levelLabel: { fontSize: 16, fontWeight: '700' },
  levelXP: { fontSize: 14, fontWeight: '600' },
  progressBg: { height: 10, borderRadius: 5 },
  progressFill: { height: 10, backgroundColor: '#FF6B35', borderRadius: 5 },
  sectionTitle: { fontSize: 20, fontWeight: '800', marginBottom: 12 },
  gradeScroll: { marginBottom: 12 },
  gradeChip: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 20, borderWidth: 2, marginRight: 8 },
  gradeText: { fontSize: 14, fontWeight: '600' },
  importBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 10, paddingHorizontal: 16, borderRadius: 12, alignSelf: 'flex-start' },
  importBtnText: { fontSize: 13, fontWeight: '600' },
  subjectsGrid: { gap: 12 },
  subjectCard: { borderRadius: 16, borderLeftWidth: 4 },
  subjectTouch: { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 14 },
  subjectIcon: { width: 52, height: 52, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  subjectInfo: { flex: 1 },
  subjectName: { fontSize: 17, fontWeight: '700' },
  subjectDesc: { fontSize: 13, marginTop: 2 },
  cardCount: { fontSize: 12, fontWeight: '600', marginTop: 4 },
  quizBtn: { position: 'absolute', bottom: 12, right: 50, flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 10, paddingVertical: 5, borderRadius: 10 },
  quizBtnText: { fontSize: 11, fontWeight: '700' },
  exportSmallBtn: { position: 'absolute', top: 12, right: 12, width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  emptyText: { fontSize: 15, textAlign: 'center', paddingVertical: 32 },
  fab: {
    position: 'absolute', bottom: 24, right: 24, width: 60, height: 60, borderRadius: 30,
    alignItems: 'center', justifyContent: 'center',
    shadowColor: '#FF6B35', shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.35, shadowRadius: 8, elevation: 6,
  },
});
