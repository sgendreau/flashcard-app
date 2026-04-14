import React, { useState, useCallback } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView, RefreshControl, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/context/AuthContext';
import { api } from '../../src/utils/api';

const BADGE_COLORS: Record<string, string> = {
  'rocket-outline': '#3B82F6',
  'star-outline': '#FBBF24',
  'flame-outline': '#FF5A00',
  'medal-outline': '#10B981',
  'trophy-outline': '#8B5CF6',
  'school-outline': '#EC4899',
};

export default function ProfileScreen() {
  const { user, logout, refreshUser } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStats = async () => {
    try {
      await refreshUser();
      const data = await api.get('/progress/stats');
      setStats(data);
    } catch (e) {
      console.log('Error:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useFocusEffect(useCallback(() => { fetchStats(); }, []));

  const onRefresh = () => { setRefreshing(true); fetchStats(); };

  const handleLogout = async () => {
    await logout();
    router.replace('/(auth)/login');
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.center}><ActivityIndicator size="large" color="#FF6B35" /></View>
      </SafeAreaView>
    );
  }

  const xpProgress = ((user?.xp || 0) % 500) / 5;

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#FF6B35" />}
      >
        {/* Profile Header */}
        <View style={styles.profileHeader}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{(user?.name || 'U').charAt(0).toUpperCase()}</Text>
          </View>
          <Text style={styles.name} testID="profile-name">{user?.name}</Text>
          <Text style={styles.email} testID="profile-email">{user?.email}</Text>
        </View>

        {/* Stats Cards */}
        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <Ionicons name="star" size={24} color="#FBBF24" />
            <Text style={styles.statValue} testID="profile-xp">{user?.xp || 0}</Text>
            <Text style={styles.statLabel}>XP Total</Text>
          </View>
          <View style={styles.statCard}>
            <Ionicons name="trophy" size={24} color="#3B82F6" />
            <Text style={styles.statValue} testID="profile-level">{user?.level || 1}</Text>
            <Text style={styles.statLabel}>Niveau</Text>
          </View>
          <View style={styles.statCard}>
            <Ionicons name="flame" size={24} color="#FF5A00" />
            <Text style={styles.statValue} testID="profile-streak">{user?.streak_count || 0}</Text>
            <Text style={styles.statLabel}>Streak</Text>
          </View>
        </View>

        {/* Level Progress */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Progression vers le niveau {(user?.level || 1) + 1}</Text>
          <View style={styles.progressBg}>
            <View style={[styles.progressFill, { width: `${xpProgress}%` }]} />
          </View>
          <Text style={styles.progressText}>{(user?.xp || 0) % 500} / 500 XP</Text>
        </View>

        {/* Leitner Boxes */}
        {stats?.box_counts && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Boîtes Leitner</Text>
            <View style={styles.boxesRow}>
              <View style={[styles.leitnerBox, { backgroundColor: '#FEF2F2' }]}>
                <Ionicons name="cube-outline" size={20} color="#EF4444" />
                <Text style={styles.boxCount}>{stats.box_counts.box_1 || 0}</Text>
                <Text style={styles.boxLabel}>Boîte 1</Text>
              </View>
              <View style={[styles.leitnerBox, { backgroundColor: '#FFF8E1' }]}>
                <Ionicons name="cube-outline" size={20} color="#F59E0B" />
                <Text style={styles.boxCount}>{stats.box_counts.box_2 || 0}</Text>
                <Text style={styles.boxLabel}>Boîte 2</Text>
              </View>
              <View style={[styles.leitnerBox, { backgroundColor: '#F0FDF4' }]}>
                <Ionicons name="cube-outline" size={20} color="#10B981" />
                <Text style={styles.boxCount}>{stats.box_counts.box_3 || 0}</Text>
                <Text style={styles.boxLabel}>Boîte 3</Text>
              </View>
            </View>
          </View>
        )}

        {/* Badges */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Badges ({(user?.badges || []).length})</Text>
          {(user?.badges || []).length === 0 ? (
            <Text style={styles.emptyText}>Complète des sessions pour gagner des badges !</Text>
          ) : (
            <View style={styles.badgesGrid}>
              {(user?.badges || []).map((badge: any, i: number) => (
                <View key={i} style={styles.badgeItem}>
                  <View style={[styles.badgeIcon, { backgroundColor: (BADGE_COLORS[badge.icon] || '#3B82F6') + '20' }]}>
                    <Ionicons name={badge.icon as any} size={24} color={BADGE_COLORS[badge.icon] || '#3B82F6'} />
                  </View>
                  <Text style={styles.badgeName}>{badge.name}</Text>
                  <Text style={styles.badgeDesc}>{badge.description}</Text>
                </View>
              ))}
            </View>
          )}
        </View>

        {/* Sessions History */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Sessions récentes</Text>
          {(stats?.sessions || []).length === 0 ? (
            <Text style={styles.emptyText}>Aucune session pour l'instant</Text>
          ) : (
            (stats?.sessions || []).slice(0, 5).map((s: any, i: number) => (
              <View key={i} style={styles.sessionItem}>
                <View style={styles.sessionLeft}>
                  <Text style={styles.sessionPerc}>{s.percentage}%</Text>
                  <Text style={styles.sessionDetail}>{s.correct_count}/{s.total_cards} correct</Text>
                </View>
                <Text style={styles.sessionXP}>+{s.xp_earned} XP</Text>
              </View>
            ))
          )}
        </View>

        {/* Logout */}
        <TouchableOpacity testID="logout-btn" style={styles.logoutBtn} onPress={handleLogout} activeOpacity={0.8}>
          <Ionicons name="log-out-outline" size={20} color="#EF4444" />
          <Text style={styles.logoutText}>Se déconnecter</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F4F6F8' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { padding: 20, paddingBottom: 40 },
  profileHeader: { alignItems: 'center', marginBottom: 24 },
  avatar: {
    width: 80, height: 80, borderRadius: 40, backgroundColor: '#FF6B35',
    alignItems: 'center', justifyContent: 'center', marginBottom: 12,
  },
  avatarText: { fontSize: 32, fontWeight: '900', color: '#fff' },
  name: { fontSize: 24, fontWeight: '800', color: '#1F2937' },
  email: { fontSize: 14, color: '#6B7280', marginTop: 4 },
  statsRow: { flexDirection: 'row', gap: 12, marginBottom: 16 },
  statCard: {
    flex: 1, backgroundColor: '#fff', borderRadius: 16, padding: 16, alignItems: 'center', gap: 4,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.04, shadowRadius: 8, elevation: 2,
  },
  statValue: { fontSize: 24, fontWeight: '900', color: '#1F2937' },
  statLabel: { fontSize: 12, color: '#6B7280', fontWeight: '600' },
  card: {
    backgroundColor: '#fff', borderRadius: 20, padding: 20, marginBottom: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.04, shadowRadius: 8, elevation: 2,
  },
  cardTitle: { fontSize: 18, fontWeight: '700', color: '#1F2937', marginBottom: 12 },
  progressBg: { height: 10, backgroundColor: '#E5E7EB', borderRadius: 5 },
  progressFill: { height: 10, backgroundColor: '#FF6B35', borderRadius: 5 },
  progressText: { fontSize: 13, color: '#6B7280', marginTop: 8, textAlign: 'right' },
  boxesRow: { flexDirection: 'row', gap: 10 },
  leitnerBox: { flex: 1, borderRadius: 14, padding: 14, alignItems: 'center', gap: 4 },
  boxCount: { fontSize: 22, fontWeight: '900', color: '#1F2937' },
  boxLabel: { fontSize: 11, color: '#6B7280', fontWeight: '600' },
  badgesGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  badgeItem: { width: '30%', alignItems: 'center' },
  badgeIcon: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', marginBottom: 6 },
  badgeName: { fontSize: 12, fontWeight: '700', color: '#1F2937', textAlign: 'center' },
  badgeDesc: { fontSize: 10, color: '#6B7280', textAlign: 'center' },
  emptyText: { fontSize: 14, color: '#9CA3AF', textAlign: 'center', paddingVertical: 16 },
  sessionItem: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#F3F4F6',
  },
  sessionLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  sessionPerc: { fontSize: 18, fontWeight: '800', color: '#1F2937' },
  sessionDetail: { fontSize: 13, color: '#6B7280' },
  sessionXP: { fontSize: 14, fontWeight: '700', color: '#10B981' },
  logoutBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    paddingVertical: 16, marginTop: 8,
  },
  logoutText: { fontSize: 16, fontWeight: '600', color: '#EF4444' },
});
