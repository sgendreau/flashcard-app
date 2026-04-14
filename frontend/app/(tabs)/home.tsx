import React, { useState, useCallback } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView, RefreshControl, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/context/AuthContext';
import { api } from '../../src/utils/api';

const SUBJECT_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  'calculator-outline': 'calculator-outline',
  'book-outline': 'book-outline',
  'earth-outline': 'earth-outline',
  'leaf-outline': 'leaf-outline',
  'flask-outline': 'flask-outline',
  'language-outline': 'language-outline',
  'bulb-outline': 'bulb-outline',
  'trending-up-outline': 'trending-up-outline',
  'sunny-outline': 'sunny-outline',
};

interface Subject {
  id: string;
  name: string;
  icon: string;
  color: string;
  description: string;
  card_count: number;
}

export default function HomeScreen() {
  const { user, refreshUser } = useAuth();
  const router = useRouter();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const data = await api.get('/subjects');
      setSubjects(data.subjects || []);
      await refreshUser();
    } catch (e) {
      console.log('Error fetching subjects:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useFocusEffect(useCallback(() => { fetchData(); }, []));

  const onRefresh = () => { setRefreshing(true); fetchData(); };

  if (loading) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.center}><ActivityIndicator size="large" color="#FF6B35" /></View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#FF6B35" />}
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>Bonjour,</Text>
            <Text style={styles.userName} testID="home-user-name">{user?.name || 'Étudiant'}</Text>
          </View>
          <View style={styles.statsRow}>
            <View style={styles.statBadge}>
              <Ionicons name="flame" size={18} color="#FF5A00" />
              <Text style={styles.statText} testID="home-streak">{user?.streak_count || 0}</Text>
            </View>
            <View style={[styles.statBadge, { backgroundColor: '#FFF8E1' }]}>
              <Ionicons name="star" size={18} color="#FBBF24" />
              <Text style={styles.statText} testID="home-xp">{user?.xp || 0} XP</Text>
            </View>
          </View>
        </View>

        {/* Level bar */}
        <View style={styles.levelCard}>
          <View style={styles.levelRow}>
            <Text style={styles.levelLabel}>Niveau {user?.level || 1}</Text>
            <Text style={styles.levelXP}>{(user?.xp || 0) % 500} / 500 XP</Text>
          </View>
          <View style={styles.progressBg}>
            <View style={[styles.progressFill, { width: `${((user?.xp || 0) % 500) / 5}%` }]} />
          </View>
        </View>

        {/* Subjects */}
        <Text style={styles.sectionTitle}>Choisis ta matière</Text>
        <View style={styles.subjectsGrid}>
          {subjects.map((subject) => (
            <TouchableOpacity
              key={subject.id}
              testID={`subject-card-${subject.id}`}
              style={[styles.subjectCard, { borderLeftColor: subject.color, borderLeftWidth: 4 }]}
              onPress={() => router.push(`/study/${subject.id}`)}
              activeOpacity={0.7}
            >
              <View style={[styles.subjectIcon, { backgroundColor: subject.color + '18' }]}>
                <Ionicons
                  name={(SUBJECT_ICONS[subject.icon] || 'book-outline') as any}
                  size={28}
                  color={subject.color}
                />
              </View>
              <View style={styles.subjectInfo}>
                <Text style={styles.subjectName}>{subject.name}</Text>
                <Text style={styles.subjectDesc} numberOfLines={1}>{subject.description}</Text>
                <Text style={styles.cardCount}>{subject.card_count} cartes</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#9CA3AF" />
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      {/* FAB - Create Card */}
      <TouchableOpacity
        testID="create-card-fab"
        style={styles.fab}
        onPress={() => router.push('/create-card')}
        activeOpacity={0.8}
      >
        <Ionicons name="add" size={28} color="#fff" />
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F4F6F8' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { flex: 1 },
  scrollContent: { padding: 20, paddingBottom: 100 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 },
  greeting: { fontSize: 16, color: '#6B7280', fontWeight: '500' },
  userName: { fontSize: 28, fontWeight: '900', color: '#1F2937', marginTop: 2 },
  statsRow: { flexDirection: 'row', gap: 8, marginTop: 4 },
  statBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: '#FFF3ED',
    paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20,
  },
  statText: { fontSize: 14, fontWeight: '700', color: '#1F2937' },
  levelCard: {
    backgroundColor: '#fff', borderRadius: 20, padding: 16, marginBottom: 24,
    shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.05, shadowRadius: 12, elevation: 3,
  },
  levelRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 },
  levelLabel: { fontSize: 16, fontWeight: '700', color: '#1F2937' },
  levelXP: { fontSize: 14, color: '#6B7280', fontWeight: '600' },
  progressBg: { height: 10, backgroundColor: '#E5E7EB', borderRadius: 5 },
  progressFill: { height: 10, backgroundColor: '#FF6B35', borderRadius: 5 },
  sectionTitle: { fontSize: 22, fontWeight: '800', color: '#1F2937', marginBottom: 16 },
  subjectsGrid: { gap: 12 },
  subjectCard: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff', borderRadius: 16,
    padding: 16, gap: 14,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.04, shadowRadius: 8, elevation: 2,
  },
  subjectIcon: { width: 52, height: 52, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  subjectInfo: { flex: 1 },
  subjectName: { fontSize: 17, fontWeight: '700', color: '#1F2937' },
  subjectDesc: { fontSize: 13, color: '#6B7280', marginTop: 2 },
  cardCount: { fontSize: 12, color: '#FF6B35', fontWeight: '600', marginTop: 4 },
  fab: {
    position: 'absolute', bottom: 24, right: 24,
    width: 60, height: 60, borderRadius: 30, backgroundColor: '#FF6B35',
    alignItems: 'center', justifyContent: 'center',
    shadowColor: '#FF6B35', shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.35, shadowRadius: 8, elevation: 6,
  },
});
