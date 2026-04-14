import React, { useState, useCallback } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView, RefreshControl, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/utils/api';
import { useTheme } from '../../src/context/ThemeContext';

const ICONS: Record<string, string> = {
  'calculator-outline': 'calculator-outline', 'book-outline': 'book-outline',
  'earth-outline': 'earth-outline', 'leaf-outline': 'leaf-outline',
  'flask-outline': 'flask-outline', 'language-outline': 'language-outline',
  'bulb-outline': 'bulb-outline', 'trending-up-outline': 'trending-up-outline',
  'sunny-outline': 'sunny-outline',
};

export default function StatsScreen() {
  const { colors } = useTheme();
  const [stats, setStats] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStats = async () => {
    try {
      const data = await api.get('/progress/subject-stats');
      setStats(data.subject_stats || []);
    } catch (e) { console.log('Stats error:', e); }
    finally { setLoading(false); setRefreshing(false); }
  };

  useFocusEffect(useCallback(() => { fetchStats(); }, []));

  if (loading) {
    return (
      <SafeAreaView style={[styles.safe, { backgroundColor: colors.bg }]}>
        <View style={styles.center}><ActivityIndicator size="large" color={colors.primary} /></View>
      </SafeAreaView>
    );
  }

  const totalSessions = stats.reduce((a, s) => a + s.total_sessions, 0);
  const totalXP = stats.reduce((a, s) => a + s.total_xp, 0);
  const globalAvg = stats.length ? Math.round(stats.reduce((a, s) => a + s.avg_percentage, 0) / stats.length) : 0;

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.bg }]}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchStats(); }} tintColor={colors.primary} />}
      >
        <Text style={[styles.title, { color: colors.text }]}>Statistiques</Text>
        <Text style={[styles.subtitle, { color: colors.textSecondary }]}>Détail par matière</Text>

        {/* Summary cards */}
        <View style={styles.summaryRow}>
          <View style={[styles.sumCard, { backgroundColor: colors.surface }]}>
            <Ionicons name="albums-outline" size={22} color={colors.primary} />
            <Text style={[styles.sumVal, { color: colors.text }]}>{totalSessions}</Text>
            <Text style={[styles.sumLabel, { color: colors.textSecondary }]}>Sessions</Text>
          </View>
          <View style={[styles.sumCard, { backgroundColor: colors.surface }]}>
            <Ionicons name="star" size={22} color="#FBBF24" />
            <Text style={[styles.sumVal, { color: colors.text }]}>{totalXP}</Text>
            <Text style={[styles.sumLabel, { color: colors.textSecondary }]}>XP Total</Text>
          </View>
          <View style={[styles.sumCard, { backgroundColor: colors.surface }]}>
            <Ionicons name="checkmark-circle" size={22} color={colors.success} />
            <Text style={[styles.sumVal, { color: colors.text }]}>{globalAvg}%</Text>
            <Text style={[styles.sumLabel, { color: colors.textSecondary }]}>Moyenne</Text>
          </View>
        </View>

        {stats.length === 0 ? (
          <View style={styles.emptyWrap}>
            <Ionicons name="bar-chart-outline" size={64} color={colors.textMuted} />
            <Text style={[styles.emptyTitle, { color: colors.textSecondary }]}>Pas encore de stats</Text>
            <Text style={[styles.emptyDesc, { color: colors.textMuted }]}>Complète des sessions pour voir tes statistiques</Text>
          </View>
        ) : (
          stats.map((s) => (
            <View key={s.subject_id} style={[styles.subjectCard, { backgroundColor: colors.surface }]}>
              <View style={styles.subjectHeader}>
                <View style={[styles.subjectIconWrap, { backgroundColor: s.color + '18' }]}>
                  <Ionicons name={(ICONS[s.icon] || 'book-outline') as any} size={24} color={s.color} />
                </View>
                <View style={styles.subjectHeaderInfo}>
                  <Text style={[styles.subjectName, { color: colors.text }]}>{s.name}</Text>
                  <Text style={[styles.subjectMeta, { color: colors.textSecondary }]}>
                    {s.total_sessions} sessions • {s.total_cards_reviewed} cartes révisées
                  </Text>
                </View>
                <View style={[styles.avgBadge, { backgroundColor: s.avg_percentage >= 70 ? colors.successBg : colors.warningBg }]}>
                  <Text style={[styles.avgText, { color: s.avg_percentage >= 70 ? colors.success : colors.warning }]}>
                    {s.avg_percentage}%
                  </Text>
                </View>
              </View>

              {/* Progress bar - mastery */}
              <View style={{ marginTop: 12 }}>
                <View style={styles.masteryLabelRow}>
                  <Text style={[styles.masteryLabel, { color: colors.textSecondary }]}>Maîtrise</Text>
                  <Text style={[styles.masteryValue, { color: colors.text }]}>{s.mastered}/{s.total_cards} ({s.mastery_pct}%)</Text>
                </View>
                <View style={[styles.barBg, { backgroundColor: colors.border }]}>
                  <View style={[styles.barFill, { width: `${s.mastery_pct}%`, backgroundColor: s.color }]} />
                </View>
              </View>

              {/* Box distribution */}
              <View style={styles.boxRow}>
                <View style={[styles.miniBox, { backgroundColor: colors.errorBg }]}>
                  <Text style={[styles.miniBoxVal, { color: colors.error }]}>{s.box_distribution.box_1}</Text>
                  <Text style={[styles.miniBoxLabel, { color: colors.textMuted }]}>B1</Text>
                </View>
                <View style={[styles.miniBox, { backgroundColor: colors.warningBg }]}>
                  <Text style={[styles.miniBoxVal, { color: colors.warning }]}>{s.box_distribution.box_2}</Text>
                  <Text style={[styles.miniBoxLabel, { color: colors.textMuted }]}>B2</Text>
                </View>
                <View style={[styles.miniBox, { backgroundColor: colors.successBg }]}>
                  <Text style={[styles.miniBoxVal, { color: colors.success }]}>{s.box_distribution.box_3}</Text>
                  <Text style={[styles.miniBoxLabel, { color: colors.textMuted }]}>B3</Text>
                </View>
                <View style={{ flex: 1, alignItems: 'flex-end' }}>
                  <Text style={[styles.xpEarned, { color: colors.primary }]}>+{s.total_xp} XP</Text>
                </View>
              </View>
            </View>
          ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { padding: 20, paddingBottom: 40 },
  title: { fontSize: 28, fontWeight: '900' },
  subtitle: { fontSize: 15, marginTop: 4, marginBottom: 20 },
  summaryRow: { flexDirection: 'row', gap: 10, marginBottom: 24 },
  sumCard: { flex: 1, borderRadius: 16, padding: 14, alignItems: 'center', gap: 4 },
  sumVal: { fontSize: 22, fontWeight: '900' },
  sumLabel: { fontSize: 11, fontWeight: '600' },
  emptyWrap: { alignItems: 'center', paddingTop: 60, gap: 12 },
  emptyTitle: { fontSize: 20, fontWeight: '700' },
  emptyDesc: { fontSize: 14, textAlign: 'center' },
  subjectCard: { borderRadius: 20, padding: 18, marginBottom: 14 },
  subjectHeader: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  subjectIconWrap: { width: 44, height: 44, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  subjectHeaderInfo: { flex: 1 },
  subjectName: { fontSize: 17, fontWeight: '700' },
  subjectMeta: { fontSize: 12, marginTop: 2 },
  avgBadge: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 10 },
  avgText: { fontSize: 14, fontWeight: '800' },
  masteryLabelRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  masteryLabel: { fontSize: 12, fontWeight: '600' },
  masteryValue: { fontSize: 12, fontWeight: '700' },
  barBg: { height: 8, borderRadius: 4 },
  barFill: { height: 8, borderRadius: 4 },
  boxRow: { flexDirection: 'row', gap: 8, marginTop: 12, alignItems: 'center' },
  miniBox: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 10, alignItems: 'center', minWidth: 50 },
  miniBoxVal: { fontSize: 16, fontWeight: '800' },
  miniBoxLabel: { fontSize: 10, fontWeight: '600' },
  xpEarned: { fontSize: 14, fontWeight: '700' },
});
