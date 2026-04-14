import React, { useState, useCallback } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView, RefreshControl,
  ActivityIndicator, TextInput, Alert, KeyboardAvoidingView, Platform, Switch,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../src/context/ThemeContext';
import { api } from '../../src/utils/api';

const GRADE_LABELS: Record<string, string> = {
  '6eme': '6ème', '5eme': '5ème', '4eme': '4ème', '3eme': '3ème',
  '2nde': '2nde', '1ere': '1ère', 'terminale': 'Term.',
};
const ALL_GRADES = ['6eme', '5eme', '4eme', '3eme', '2nde', '1ere', 'terminale'];

export default function ClassesScreen() {
  const { colors } = useTheme();
  const router = useRouter();
  const [classes, setClasses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [showJoin, setShowJoin] = useState(false);
  const [className, setClassName] = useState('');
  const [isPrivate, setIsPrivate] = useState(false);
  const [lockedGrade, setLockedGrade] = useState<string | null>(null);
  const [joinCode, setJoinCode] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const fetchClasses = async () => {
    try { const d = await api.get('/classes'); setClasses(d.classes || []); }
    catch (e) { console.log('Error:', e); }
    finally { setLoading(false); setRefreshing(false); }
  };

  useFocusEffect(useCallback(() => { fetchClasses(); }, []));

  const handleCreate = async () => {
    if (!className.trim()) return;
    setActionLoading(true);
    try {
      await api.post('/classes', {
        name: className.trim(),
        is_private: isPrivate,
        locked_grade: lockedGrade,
      });
      setClassName(''); setIsPrivate(false); setLockedGrade(null); setShowCreate(false);
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
      setJoinCode(''); setShowJoin(false);
      fetchClasses();
      Alert.alert('Rejoint !', 'Tu fais partie de la classe.');
    } catch (e: any) { Alert.alert('Erreur', e.message); }
    finally { setActionLoading(false); }
  };

  if (loading) return <SafeAreaView style={[s.safe, { backgroundColor: colors.bg }]}><View style={s.center}><ActivityIndicator size="large" color={colors.primary} /></View></SafeAreaView>;

  return (
    <SafeAreaView style={[s.safe, { backgroundColor: colors.bg }]}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={s.scroll}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchClasses(); }} tintColor={colors.primary} />}>
          <Text style={[s.title, { color: colors.text }]}>Mes classes</Text>
          <Text style={[s.subtitle, { color: colors.textSecondary }]}>Partage et étudie avec ta classe</Text>

          <View style={s.actionsRow}>
            <TouchableOpacity testID="create-class-btn" style={[s.actionBtn, { backgroundColor: colors.primaryBg }]}
              onPress={() => { setShowCreate(!showCreate); setShowJoin(false); }}>
              <Ionicons name="add-circle-outline" size={22} color={colors.primary} />
              <Text style={[s.actionText, { color: colors.primary }]}>Créer</Text>
            </TouchableOpacity>
            <TouchableOpacity testID="join-class-btn" style={[s.actionBtn, { backgroundColor: colors.surfaceAlt }]}
              onPress={() => { setShowJoin(!showJoin); setShowCreate(false); }}>
              <Ionicons name="enter-outline" size={22} color="#3B82F6" />
              <Text style={[s.actionText, { color: '#3B82F6' }]}>Rejoindre</Text>
            </TouchableOpacity>
          </View>

          {showCreate && (
            <View style={[s.formCard, { backgroundColor: colors.surface }]}>
              <Text style={[s.formTitle, { color: colors.text }]}>Nouvelle classe</Text>
              <TextInput testID="create-class-name-input" style={[s.input, { backgroundColor: colors.surfaceAlt, borderColor: colors.border, color: colors.text }]}
                placeholder="Nom de la classe" placeholderTextColor={colors.textMuted}
                value={className} onChangeText={setClassName} />

              {/* Private toggle */}
              <View style={s.toggleRow}>
                <View style={{ flex: 1 }}>
                  <Text style={[s.toggleLabel, { color: colors.text }]}>Classe privée</Text>
                  <Text style={[s.toggleDesc, { color: colors.textSecondary }]}>Visible uniquement avec le code</Text>
                </View>
                <Switch testID="class-private-toggle" value={isPrivate} onValueChange={setIsPrivate}
                  trackColor={{ false: colors.border, true: colors.primary }} thumbColor="#fff" />
              </View>

              {/* Grade lock */}
              <Text style={[s.lockLabel, { color: colors.text }]}>Verrouiller sur un niveau</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.gradeScroll}>
                <TouchableOpacity testID="grade-lock-none"
                  style={[s.gradeChip, { borderColor: colors.border, backgroundColor: colors.surfaceAlt }, !lockedGrade && { backgroundColor: colors.primary, borderColor: colors.primary }]}
                  onPress={() => setLockedGrade(null)}>
                  <Text style={[s.gradeText, { color: colors.text }, !lockedGrade && { color: '#fff' }]}>Aucun</Text>
                </TouchableOpacity>
                {ALL_GRADES.map((g) => (
                  <TouchableOpacity key={g} testID={`grade-lock-${g}`}
                    style={[s.gradeChip, { borderColor: colors.border, backgroundColor: colors.surfaceAlt }, lockedGrade === g && { backgroundColor: colors.primary, borderColor: colors.primary }]}
                    onPress={() => setLockedGrade(g)}>
                    <Text style={[s.gradeText, { color: colors.text }, lockedGrade === g && { color: '#fff' }]}>{GRADE_LABELS[g]}</Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>

              <TouchableOpacity testID="create-class-submit"
                style={[s.submitBtn, { backgroundColor: colors.primary }, actionLoading && { opacity: 0.7 }]}
                onPress={handleCreate} disabled={actionLoading}>
                {actionLoading ? <ActivityIndicator color="#fff" /> : <Text style={s.submitText}>Créer</Text>}
              </TouchableOpacity>
            </View>
          )}

          {showJoin && (
            <View style={[s.formCard, { backgroundColor: colors.surface }]}>
              <Text style={[s.formTitle, { color: colors.text }]}>Rejoindre</Text>
              <TextInput testID="join-class-code-input" style={[s.input, { backgroundColor: colors.surfaceAlt, borderColor: colors.border, color: colors.text }]}
                placeholder="Code (6 caractères)" placeholderTextColor={colors.textMuted}
                value={joinCode} onChangeText={setJoinCode} autoCapitalize="characters" maxLength={6} />
              <TouchableOpacity testID="join-class-submit"
                style={[s.submitBtn, { backgroundColor: '#3B82F6' }, actionLoading && { opacity: 0.7 }]}
                onPress={handleJoin} disabled={actionLoading}>
                {actionLoading ? <ActivityIndicator color="#fff" /> : <Text style={s.submitText}>Rejoindre</Text>}
              </TouchableOpacity>
            </View>
          )}

          {classes.length === 0 ? (
            <View style={s.emptyWrap}>
              <Ionicons name="people-outline" size={64} color={colors.textMuted} />
              <Text style={[s.emptyTitle, { color: colors.textSecondary }]}>Aucune classe</Text>
            </View>
          ) : (
            <View style={s.classList}>
              {classes.map((cls) => (
                <TouchableOpacity key={cls.id} testID={`class-card-${cls.id}`}
                  style={[s.classCard, { backgroundColor: colors.surface }]}
                  onPress={() => router.push(`/class/${cls.id}`)} activeOpacity={0.7}>
                  <View style={[s.classIconWrap, { backgroundColor: colors.primaryBg }]}>
                    <Ionicons name="school-outline" size={28} color={colors.primary} />
                  </View>
                  <View style={s.classInfo}>
                    <View style={s.classNameRow}>
                      <Text style={[s.classCardName, { color: colors.text }]}>{cls.name}</Text>
                      {cls.is_private && <Ionicons name="lock-closed" size={14} color={colors.textMuted} />}
                    </View>
                    <View style={s.classMetaRow}>
                      <View style={s.classMeta}>
                        <Ionicons name="people-outline" size={14} color={colors.textSecondary} />
                        <Text style={[s.classMetaText, { color: colors.textSecondary }]}>{cls.member_count}</Text>
                      </View>
                      <View style={s.classMeta}>
                        <Ionicons name="layers-outline" size={14} color={colors.textSecondary} />
                        <Text style={[s.classMetaText, { color: colors.textSecondary }]}>{cls.deck_count} decks</Text>
                      </View>
                      {cls.locked_grade && (
                        <View style={[s.gradeBadge, { backgroundColor: colors.warningBg }]}>
                          <Text style={[s.gradeBadgeText, { color: colors.warning }]}>{GRADE_LABELS[cls.locked_grade] || cls.locked_grade}</Text>
                        </View>
                      )}
                    </View>
                  </View>
                  <View style={[s.codeBadge, { backgroundColor: colors.surfaceAlt }]}>
                    <Text style={[s.codeText, { color: colors.textSecondary }]}>{cls.code}</Text>
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

const s = StyleSheet.create({
  safe: { flex: 1 }, center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { padding: 20, paddingBottom: 40 },
  title: { fontSize: 28, fontWeight: '900' },
  subtitle: { fontSize: 15, marginTop: 4, marginBottom: 20 },
  actionsRow: { flexDirection: 'row', gap: 12, marginBottom: 16 },
  actionBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 14, borderRadius: 16 },
  actionText: { fontSize: 14, fontWeight: '700' },
  formCard: { borderRadius: 20, padding: 20, marginBottom: 16 },
  formTitle: { fontSize: 18, fontWeight: '700', marginBottom: 12 },
  input: { borderRadius: 14, borderWidth: 2, paddingHorizontal: 16, paddingVertical: 14, fontSize: 16, marginBottom: 12 },
  toggleRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  toggleLabel: { fontSize: 15, fontWeight: '600' },
  toggleDesc: { fontSize: 12, marginTop: 2 },
  lockLabel: { fontSize: 14, fontWeight: '600', marginBottom: 8 },
  gradeScroll: { marginBottom: 16 },
  gradeChip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 14, borderWidth: 2, marginRight: 8 },
  gradeText: { fontSize: 13, fontWeight: '600' },
  submitBtn: { borderRadius: 14, paddingVertical: 14, alignItems: 'center' },
  submitText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  emptyWrap: { alignItems: 'center', paddingTop: 60, gap: 12 },
  emptyTitle: { fontSize: 20, fontWeight: '700' },
  classList: { gap: 12 },
  classCard: { flexDirection: 'row', alignItems: 'center', borderRadius: 16, padding: 16, gap: 14 },
  classIconWrap: { width: 52, height: 52, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  classInfo: { flex: 1 },
  classNameRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  classCardName: { fontSize: 17, fontWeight: '700' },
  classMetaRow: { flexDirection: 'row', gap: 12, marginTop: 4, alignItems: 'center' },
  classMeta: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  classMetaText: { fontSize: 12 },
  gradeBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  gradeBadgeText: { fontSize: 10, fontWeight: '700' },
  codeBadge: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8 },
  codeText: { fontSize: 12, fontWeight: '800', letterSpacing: 1 },
});
