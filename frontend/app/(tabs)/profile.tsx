import React, { useState, useCallback } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView, RefreshControl,
  ActivityIndicator, Alert, Switch, Share,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/context/AuthContext';
import { useTheme } from '../../src/context/ThemeContext';
import { api } from '../../src/utils/api';
import { getOfflineStatus } from '../../src/utils/offlineCache';

let Notifications: any = null;
try { Notifications = require('expo-notifications'); } catch {}

const GRADE_LABELS: Record<string, string> = {
  '6eme': '6ème', '5eme': '5ème', '4eme': '4ème', '3eme': '3ème',
  '2nde': '2nde', '1ere': '1ère', 'terminale': 'Terminale',
};
const ALL_GRADES = ['6eme', '5eme', '4eme', '3eme', '2nde', '1ere', 'terminale'];

export default function ProfileScreen() {
  const { user, logout, refreshUser } = useAuth();
  const { colors, isDark, toggleTheme } = useTheme();
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [notifEnabled, setNotifEnabled] = useState(user?.notification_enabled ?? true);
  const [syncStatus, setSyncStatus] = useState<any>(null);
  const [referralStats, setReferralStats] = useState<any>(null);
  const [offlineInfo, setOfflineInfo] = useState<any>(null);

  const fetchStats = async () => {
    try {
      await refreshUser();
      const [statsData, syncData, refData] = await Promise.all([
        api.get('/progress/stats'),
        api.get('/sync/status'),
        api.get('/referral/stats'),
      ]);
      setStats(statsData);
      setSyncStatus(syncData);
      setReferralStats(refData);
      try { const offData = await getOfflineStatus(); setOfflineInfo(offData); } catch {}
    } catch (e) { console.log('Error:', e); }
    finally { setLoading(false); setRefreshing(false); }
  };

  useFocusEffect(useCallback(() => { fetchStats(); setNotifEnabled(user?.notification_enabled ?? true); }, []));

  const handleLogout = async () => { await logout(); router.replace('/(auth)/login'); };

  const setGrade = async (g: string | null) => {
    try { await api.put('/user/grade', { grade_level: g }); await refreshUser(); }
    catch (e: any) { Alert.alert('Erreur', e.message); }
  };

  const handleToggleTheme = async () => {
    const newTheme = isDark ? 'light' : 'dark';
    toggleTheme();
    try { await api.put('/user/theme', { theme: newTheme }); await refreshUser(); } catch {}
  };

  const toggleNotifications = async (value: boolean) => {
    setNotifEnabled(value);
    try {
      if (!Notifications) { await api.put('/user/notifications', { notification_enabled: value, notification_hour: 18 }); return; }
      if (value) {
        const { status } = await Notifications.requestPermissionsAsync();
        if (status !== 'granted') { Alert.alert('Permission refusée'); setNotifEnabled(false); return; }
        await Notifications.cancelAllScheduledNotificationsAsync();
        await Notifications.scheduleNotificationAsync({
          content: { title: "N'oublie pas de réviser !", body: 'Maintiens ton streak !' },
          trigger: { type: Notifications.SchedulableTriggerInputTypes?.DAILY || 'daily', hour: 18, minute: 0 },
        });
      } else {
        await Notifications.cancelAllScheduledNotificationsAsync();
      }
      await api.put('/user/notifications', { notification_enabled: value, notification_hour: 18 });
    } catch { /* Notification not supported in this env */ }
  };

  if (loading) return <SafeAreaView style={[st.safe, { backgroundColor: colors.bg }]}><View style={st.center}><ActivityIndicator size="large" color={colors.primary} /></View></SafeAreaView>;

  const xpProg = ((user?.xp || 0) % 500) / 5;

  return (
    <SafeAreaView style={[st.safe, { backgroundColor: colors.bg }]}>
      <ScrollView contentContainerStyle={st.scroll}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchStats(); }} tintColor={colors.primary} />}>
        <View style={st.profileHeader}>
          <View style={[st.avatar, { backgroundColor: colors.primary }]}><Text style={st.avatarText}>{(user?.name || 'U').charAt(0).toUpperCase()}</Text></View>
          <Text style={[st.name, { color: colors.text }]} testID="profile-name">{user?.name}</Text>
          <Text style={[st.email, { color: colors.textSecondary }]}>{user?.email}</Text>
        </View>

        <View style={st.statsRow}>
          {[
            { icon: 'star', color: '#FBBF24', val: user?.xp || 0, label: 'XP Total', tid: 'profile-xp' },
            { icon: 'trophy', color: '#3B82F6', val: user?.level || 1, label: 'Niveau', tid: 'profile-level' },
            { icon: 'flame', color: '#FF5A00', val: user?.streak_count || 0, label: 'Streak', tid: 'profile-streak' },
          ].map((s, i) => (
            <View key={i} style={[st.statCard, { backgroundColor: colors.surface }]}>
              <Ionicons name={s.icon as any} size={24} color={s.color} />
              <Text style={[st.statValue, { color: colors.text }]} testID={s.tid}>{s.val}</Text>
              <Text style={[st.statLabel, { color: colors.textSecondary }]}>{s.label}</Text>
            </View>
          ))}
        </View>

        {/* Level */}
        <View style={[st.card, { backgroundColor: colors.surface }]}>
          <Text style={[st.cardTitle, { color: colors.text }]}>Progression niveau {(user?.level || 1) + 1}</Text>
          <View style={[st.progressBg, { backgroundColor: colors.border }]}>
            <View style={[st.progressFill, { width: `${xpProg}%` }]} />
          </View>
          <Text style={[st.progressText, { color: colors.textSecondary }]}>{(user?.xp || 0) % 500} / 500 XP</Text>
        </View>

        {/* Theme Toggle */}
        <View style={[st.card, { backgroundColor: colors.surface }]}>
          <View style={st.settingRow}>
            <View style={{ flex: 1 }}>
              <Text style={[st.cardTitle, { color: colors.text }]}>Thème sombre</Text>
              <Text style={[st.settingDesc, { color: colors.textSecondary }]}>{isDark ? 'Mode sombre activé' : 'Mode clair activé'}</Text>
            </View>
            <Switch testID="theme-toggle" value={isDark} onValueChange={handleToggleTheme}
              trackColor={{ false: colors.border, true: colors.primary }} thumbColor="#fff" />
          </View>
        </View>

        {/* Grade */}
        <View style={[st.card, { backgroundColor: colors.surface }]}>
          <Text style={[st.cardTitle, { color: colors.text }]}>Mon niveau scolaire</Text>
          <View style={st.gradeGrid}>
            <TouchableOpacity testID="grade-none" style={[st.gradeBtn, { borderColor: colors.border, backgroundColor: colors.surfaceAlt }, !user?.grade_level && { backgroundColor: colors.primary, borderColor: colors.primary }]} onPress={() => setGrade(null)}>
              <Text style={[st.gradeBtnText, { color: colors.text }, !user?.grade_level && { color: '#fff' }]}>Tous</Text>
            </TouchableOpacity>
            {ALL_GRADES.map((g) => (
              <TouchableOpacity key={g} testID={`grade-select-${g}`} style={[st.gradeBtn, { borderColor: colors.border, backgroundColor: colors.surfaceAlt }, user?.grade_level === g && { backgroundColor: colors.primary, borderColor: colors.primary }]} onPress={() => setGrade(g)}>
                <Text style={[st.gradeBtnText, { color: colors.text }, user?.grade_level === g && { color: '#fff' }]}>{GRADE_LABELS[g]}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Notif */}
        <View style={[st.card, { backgroundColor: colors.surface }]}>
          <View style={st.settingRow}>
            <View style={{ flex: 1 }}><Text style={[st.cardTitle, { color: colors.text }]}>Rappels de streak</Text><Text style={[st.settingDesc, { color: colors.textSecondary }]}>Notification quotidienne à 18h</Text></View>
            <Switch testID="notif-toggle" value={notifEnabled} onValueChange={toggleNotifications} trackColor={{ false: colors.border, true: colors.primary }} thumbColor="#fff" />
          </View>
        </View>

        {/* Leitner */}
        {stats?.box_counts && (
          <View style={[st.card, { backgroundColor: colors.surface }]}>
            <Text style={[st.cardTitle, { color: colors.text }]}>Boîtes Leitner</Text>
            <View style={st.boxesRow}>
              {[
                { bg: colors.errorBg, color: colors.error, val: stats.box_counts.box_1 || 0, lbl: 'B1' },
                { bg: colors.warningBg, color: colors.warning, val: stats.box_counts.box_2 || 0, lbl: 'B2' },
                { bg: colors.successBg, color: colors.success, val: stats.box_counts.box_3 || 0, lbl: 'B3' },
              ].map((b, i) => (
                <View key={i} style={[st.leitnerBox, { backgroundColor: b.bg }]}>
                  <Text style={[st.boxCount, { color: b.color }]}>{b.val}</Text>
                  <Text style={[st.boxLabel, { color: colors.textMuted }]}>{b.lbl}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Badges */}
        <View style={[st.card, { backgroundColor: colors.surface }]}>
          <Text style={[st.cardTitle, { color: colors.text }]}>Badges ({(user?.badges || []).length})</Text>
          {(user?.badges || []).length === 0 ? (
            <Text style={[st.emptyText, { color: colors.textMuted }]}>Complète des sessions pour gagner des badges !</Text>
          ) : (
            <View style={st.badgesGrid}>
              {(user?.badges || []).map((badge: any, i: number) => (
                <View key={i} style={st.badgeItem}>
                  <View style={[st.badgeIcon, { backgroundColor: colors.primaryBg }]}>
                    <Ionicons name={badge.icon as any} size={24} color={colors.primary} />
                  </View>
                  <Text style={[st.badgeName, { color: colors.text }]}>{badge.name}</Text>
                </View>
              ))}
            </View>
          )}
        </View>

        {/* Referral */}
        {referralStats && (
          <View style={[st.card, { backgroundColor: colors.surface }]}>
            <Text style={[st.cardTitle, { color: colors.text }]}>Parrainage</Text>
            <View style={[st.referralCodeBox, { backgroundColor: colors.primaryBg, borderColor: colors.primary }]}>
              <Text style={[st.referralLabel, { color: colors.textSecondary }]}>Ton code</Text>
              <Text style={[st.referralCode, { color: colors.primary }]} testID="referral-code">{referralStats.referral_code}</Text>
            </View>
            <TouchableOpacity testID="share-referral-btn" style={[st.shareBtn, { marginTop: 12 }]}
              onPress={async () => {
                const msg = `Rejoins-moi sur Quikko ! Utilise mon code ${referralStats.referral_code} à l'inscription et on gagne chacun 100 XP ! ⚡📚`;
                try { await Share.share({ message: msg }); } catch {}
              }}>
              <Ionicons name="gift-outline" size={18} color="#3B82F6" />
              <Text style={st.shareBtnText}>Inviter un ami (+100 XP chacun)</Text>
            </TouchableOpacity>
            <Text style={[st.settingDesc, { color: colors.textSecondary, marginTop: 8 }]}>
              {referralStats.referral_count} ami(s) parrainé(s) • +{referralStats.xp_earned_from_referrals} XP gagnés
            </Text>
          </View>
        )}

        {/* Offline Cache */}
        {offlineInfo && (
          <View style={[st.card, { backgroundColor: colors.surface }]}>
            <View style={st.settingRow}>
              <View style={{ flex: 1 }}>
                <Text style={[st.cardTitle, { color: colors.text }]}>Mode hors-ligne</Text>
                <Text style={[st.settingDesc, { color: colors.textSecondary }]}>
                  {offlineInfo.hasCache ? `${offlineInfo.subjectCount} matières en cache` : 'Aucun cache local'}
                </Text>
                {offlineInfo.pendingCount > 0 && (
                  <Text style={[st.settingDesc, { color: colors.warning, marginTop: 4 }]}>
                    {offlineInfo.pendingCount} résultat(s) en attente de sync
                  </Text>
                )}
              </View>
              <Ionicons name={offlineInfo.hasCache ? 'phone-portrait-outline' : 'cloud-offline-outline'} size={24} color={offlineInfo.hasCache ? colors.success : colors.textMuted} />
            </View>
          </View>
        )}

        {/* Sync Status */}
        {syncStatus && (
          <View style={[st.card, { backgroundColor: colors.surface }]}>
            <View style={st.settingRow}>
              <View style={{ flex: 1 }}>
                <Text style={[st.cardTitle, { color: colors.text }]}>Synchronisation</Text>
                <Text style={[st.settingDesc, { color: colors.textSecondary }]}>
                  {syncStatus.session_count} sessions • {syncStatus.card_progress_count} cartes suivies
                </Text>
                {syncStatus.last_activity && (
                  <Text style={[st.settingDesc, { color: colors.textMuted, marginTop: 4 }]}>
                    Dernière activité: {new Date(syncStatus.last_activity).toLocaleDateString('fr-FR')}
                  </Text>
                )}
              </View>
              <Ionicons name="cloud-done-outline" size={24} color={colors.success} />
            </View>
          </View>
        )}

        <TouchableOpacity testID="share-profile-btn" style={st.shareBtn} onPress={async () => {
          try { const d = await api.get('/share/profile'); await Share.share({ message: d.share_text }); } catch {}
        }}>
          <Ionicons name="share-social-outline" size={20} color="#3B82F6" />
          <Text style={st.shareBtnText}>Partager mon profil</Text>
        </TouchableOpacity>

        <TouchableOpacity testID="logout-btn" style={st.logoutBtn} onPress={handleLogout} activeOpacity={0.8}>
          <Ionicons name="log-out-outline" size={20} color={colors.error} />
          <Text style={[st.logoutText, { color: colors.error }]}>Se déconnecter</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const st = StyleSheet.create({
  safe: { flex: 1 }, center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { padding: 20, paddingBottom: 40 },
  profileHeader: { alignItems: 'center', marginBottom: 24 },
  avatar: { width: 80, height: 80, borderRadius: 40, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  avatarText: { fontSize: 32, fontWeight: '900', color: '#fff' },
  name: { fontSize: 24, fontWeight: '800' }, email: { fontSize: 14, marginTop: 4 },
  statsRow: { flexDirection: 'row', gap: 12, marginBottom: 16 },
  statCard: { flex: 1, borderRadius: 16, padding: 16, alignItems: 'center', gap: 4 },
  statValue: { fontSize: 24, fontWeight: '900' }, statLabel: { fontSize: 12, fontWeight: '600' },
  card: { borderRadius: 20, padding: 20, marginBottom: 16 },
  cardTitle: { fontSize: 18, fontWeight: '700', marginBottom: 12 },
  progressBg: { height: 10, borderRadius: 5 },
  progressFill: { height: 10, backgroundColor: '#FF6B35', borderRadius: 5 },
  progressText: { fontSize: 13, marginTop: 8, textAlign: 'right' },
  settingRow: { flexDirection: 'row', alignItems: 'center' },
  settingDesc: { fontSize: 13, marginTop: -8 },
  gradeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  gradeBtn: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 14, borderWidth: 2 },
  gradeBtnText: { fontSize: 14, fontWeight: '600' },
  boxesRow: { flexDirection: 'row', gap: 10 },
  leitnerBox: { flex: 1, borderRadius: 14, padding: 14, alignItems: 'center', gap: 4 },
  boxCount: { fontSize: 22, fontWeight: '900' }, boxLabel: { fontSize: 11, fontWeight: '600' },
  badgesGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  badgeItem: { width: '30%', alignItems: 'center' },
  badgeIcon: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', marginBottom: 6 },
  badgeName: { fontSize: 12, fontWeight: '700', textAlign: 'center' },
  emptyText: { fontSize: 14, textAlign: 'center', paddingVertical: 16 },
  logoutBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 16, marginTop: 8 },
  logoutText: { fontSize: 16, fontWeight: '600' },
  shareBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 14, marginTop: 8, backgroundColor: '#EEF2FF', borderRadius: 16, borderWidth: 2, borderColor: '#BFDBFE' },
  shareBtnText: { fontSize: 15, fontWeight: '700', color: '#3B82F6' },
  referralCodeBox: { borderRadius: 14, padding: 14, borderWidth: 2, borderStyle: 'dashed', alignItems: 'center' },
  referralLabel: { fontSize: 11, fontWeight: '600' },
  referralCode: { fontSize: 28, fontWeight: '900', letterSpacing: 3, marginTop: 4 },
});
