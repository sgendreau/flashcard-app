import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Share, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/utils/api';

export default function ReportScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{
    percentage: string;
    correct: string;
    total: string;
    xpEarned: string;
    streak: string;
    level: string;
    totalXp: string;
    newBadges: string;
    cardsToReview: string;
  }>();

  const percentage = parseInt(params.percentage || '0');
  const correct = parseInt(params.correct || '0');
  const total = parseInt(params.total || '0');
  const xpEarned = parseInt(params.xpEarned || '0');
  const streak = parseInt(params.streak || '0');
  const level = parseInt(params.level || '1');
  const newBadges = JSON.parse(params.newBadges || '[]');
  const cardsToReview = JSON.parse(params.cardsToReview || '[]');

  const getScoreColor = () => {
    if (percentage >= 80) return '#10B981';
    if (percentage >= 50) return '#F59E0B';
    return '#EF4444';
  };

  const getScoreEmoji = () => {
    if (percentage >= 80) return 'trophy';
    if (percentage >= 50) return 'thumbs-up';
    return 'fitness';
  };

  const getScoreMessage = () => {
    if (percentage === 100) return 'Parfait ! Tu es au top !';
    if (percentage >= 80) return 'Excellent travail !';
    if (percentage >= 50) return 'Bien joué, continue !';
    return 'Continue de réviser, tu vas y arriver !';
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Score Circle */}
        <View style={styles.scoreSection}>
          <View style={[styles.scoreCircle, { borderColor: getScoreColor() }]}>
            <Ionicons name={getScoreEmoji() as any} size={32} color={getScoreColor()} />
            <Text style={[styles.scorePercentage, { color: getScoreColor() }]} testID="report-percentage">
              {percentage}%
            </Text>
          </View>
          <Text style={styles.scoreMessage}>{getScoreMessage()}</Text>
          <Text style={styles.scoreDetail} testID="report-correct-count">
            {correct} / {total} bonnes réponses
          </Text>
        </View>

        {/* Stats Row */}
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Ionicons name="star" size={20} color="#FBBF24" />
            <Text style={styles.statValue} testID="report-xp">+{xpEarned}</Text>
            <Text style={styles.statLabel}>XP gagnés</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Ionicons name="flame" size={20} color="#FF5A00" />
            <Text style={styles.statValue}>{streak}</Text>
            <Text style={styles.statLabel}>Jours streak</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Ionicons name="trophy" size={20} color="#3B82F6" />
            <Text style={styles.statValue}>{level}</Text>
            <Text style={styles.statLabel}>Niveau</Text>
          </View>
        </View>

        {/* New Badges */}
        {newBadges.length > 0 && (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="ribbon" size={20} color="#8B5CF6" />
              <Text style={styles.cardTitle}>Nouveaux badges !</Text>
            </View>
            {newBadges.map((badge: any, i: number) => (
              <View key={i} style={styles.badgeRow}>
                <View style={styles.badgeIconWrap}>
                  <Ionicons name={badge.icon as any} size={24} color="#8B5CF6" />
                </View>
                <View>
                  <Text style={styles.badgeName}>{badge.name}</Text>
                  <Text style={styles.badgeDesc}>{badge.description}</Text>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Cards to Review */}
        {cardsToReview.length > 0 && (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="book" size={20} color="#EF4444" />
              <Text style={styles.cardTitle}>À réviser ({cardsToReview.length})</Text>
            </View>
            {cardsToReview.map((card: any, i: number) => (
              <View key={i} style={styles.reviewItem}>
                <Text style={styles.reviewQuestion}>{card.question}</Text>
                <Text style={styles.reviewAnswer}>{card.answer}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Share Button */}
        <TouchableOpacity
          testID="report-share-btn"
          style={styles.shareBtn}
          onPress={async () => {
            try {
              const data = await api.post('/share/session', {
                percentage, correct, total, xp_earned: xpEarned,
              });
              await Share.share({ message: data.share_text });
            } catch { Alert.alert('Erreur', 'Partage indisponible'); }
          }}
          activeOpacity={0.8}
        >
          <Ionicons name="share-social" size={20} color="#3B82F6" />
          <Text style={styles.shareBtnText}>Partager mon résultat</Text>
        </TouchableOpacity>

        {/* Back Button */}
        <TouchableOpacity
          testID="report-home-btn"
          style={styles.homeBtn}
          onPress={() => router.replace('/(tabs)/home')}
          activeOpacity={0.8}
        >
          <Ionicons name="home" size={20} color="#fff" />
          <Text style={styles.homeBtnText}>Retour à l'accueil</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F4F6F8' },
  scroll: { padding: 24, paddingBottom: 40 },
  scoreSection: { alignItems: 'center', marginTop: 20, marginBottom: 32 },
  scoreCircle: {
    width: 140, height: 140, borderRadius: 70, borderWidth: 6,
    backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center', marginBottom: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.08, shadowRadius: 12, elevation: 4,
  },
  scorePercentage: { fontSize: 36, fontWeight: '900', marginTop: 4 },
  scoreMessage: { fontSize: 22, fontWeight: '800', color: '#1F2937', textAlign: 'center' },
  scoreDetail: { fontSize: 16, color: '#6B7280', marginTop: 4 },
  statsRow: {
    flexDirection: 'row', backgroundColor: '#fff', borderRadius: 20, padding: 20, marginBottom: 20,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.04, shadowRadius: 8, elevation: 2,
  },
  statItem: { flex: 1, alignItems: 'center', gap: 4 },
  statDivider: { width: 1, backgroundColor: '#E5E7EB' },
  statValue: { fontSize: 22, fontWeight: '900', color: '#1F2937' },
  statLabel: { fontSize: 12, color: '#6B7280', fontWeight: '500' },
  card: {
    backgroundColor: '#fff', borderRadius: 20, padding: 20, marginBottom: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.04, shadowRadius: 8, elevation: 2,
  },
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 14 },
  cardTitle: { fontSize: 18, fontWeight: '700', color: '#1F2937' },
  badgeRow: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 8 },
  badgeIconWrap: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#F3E8FF', alignItems: 'center', justifyContent: 'center' },
  badgeName: { fontSize: 15, fontWeight: '700', color: '#1F2937' },
  badgeDesc: { fontSize: 13, color: '#6B7280' },
  reviewItem: { paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#F3F4F6' },
  reviewQuestion: { fontSize: 15, fontWeight: '700', color: '#1F2937' },
  reviewAnswer: { fontSize: 13, color: '#6B7280', marginTop: 4 },
  homeBtn: {
    flexDirection: 'row', backgroundColor: '#E8594D', borderRadius: 16, paddingVertical: 18,
    alignItems: 'center', justifyContent: 'center', gap: 10, marginTop: 8,
  },
  homeBtnText: { color: '#fff', fontSize: 17, fontWeight: '700' },
  shareBtn: {
    flexDirection: 'row', backgroundColor: '#EEF2FF', borderRadius: 16, paddingVertical: 16,
    alignItems: 'center', justifyContent: 'center', gap: 10, marginTop: 16, borderWidth: 2, borderColor: '#BFDBFE',
  },
  shareBtnText: { color: '#3B82F6', fontSize: 16, fontWeight: '700' },
});
