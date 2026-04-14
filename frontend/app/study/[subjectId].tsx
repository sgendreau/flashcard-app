import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Animated, ActivityIndicator, Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/utils/api';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const CARD_WIDTH = SCREEN_WIDTH - 48;

interface StudyCard {
  card_id: string;
  question: string;
  answer: string;
  show_side: 'question' | 'answer';
  box: number;
}

export default function StudySession() {
  const { subjectId } = useLocalSearchParams<{ subjectId: string }>();
  const router = useRouter();

  const [cards, setCards] = useState<StudyCard[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [results, setResults] = useState<{ card_id: string; is_correct: boolean }[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const flipAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    loadCards();
  }, [subjectId]);

  const loadCards = async () => {
    try {
      const data = await api.get(`/study/start/${subjectId}`);
      setCards(data.session_cards || []);
    } catch (e: any) {
      setError(e.message || 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  const flipCard = () => {
    Animated.spring(flipAnim, {
      toValue: isFlipped ? 0 : 1,
      friction: 8,
      tension: 10,
      useNativeDriver: true,
    }).start();
    setIsFlipped(!isFlipped);
  };

  const handleAnswer = (isCorrect: boolean) => {
    const card = cards[currentIndex];
    const newResults = [...results, { card_id: card.card_id, is_correct: isCorrect }];
    setResults(newResults);

    if (currentIndex < cards.length - 1) {
      // Reset flip and go to next card
      flipAnim.setValue(0);
      setIsFlipped(false);
      setCurrentIndex(currentIndex + 1);
    } else {
      // Submit results
      submitResults(newResults);
    }
  };

  const submitResults = async (finalResults: typeof results) => {
    setSubmitting(true);
    try {
      const data = await api.post('/study/submit', {
        subject_id: subjectId,
        results: finalResults,
      });
      router.replace({
        pathname: '/study/report',
        params: {
          percentage: String(data.percentage),
          correct: String(data.correct_count),
          total: String(data.total_cards),
          xpEarned: String(data.xp_earned),
          streak: String(data.streak_count),
          level: String(data.new_level),
          totalXp: String(data.total_xp),
          newBadges: JSON.stringify(data.new_badges || []),
          cardsToReview: JSON.stringify(data.cards_to_review || []),
        },
      });
    } catch (e: any) {
      setError(e.message || 'Erreur de soumission');
      setSubmitting(false);
    }
  };

  const frontInterpolate = flipAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '180deg'],
  });
  const backInterpolate = flipAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['180deg', '360deg'],
  });

  if (loading) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.center}><ActivityIndicator size="large" color="#FF6B35" /></View>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.center}>
          <Ionicons name="alert-circle" size={48} color="#EF4444" />
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity testID="study-back-btn" style={styles.backBtn} onPress={() => router.back()}>
            <Text style={styles.backBtnText}>Retour</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  if (submitting) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#FF6B35" />
          <Text style={styles.submittingText}>Calcul de tes résultats...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (cards.length === 0) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.center}>
          <Ionicons name="checkmark-circle" size={48} color="#10B981" />
          <Text style={styles.emptyTitle}>Toutes les cartes sont maîtrisées !</Text>
          <TouchableOpacity testID="study-back-btn" style={styles.backBtn} onPress={() => router.back()}>
            <Text style={styles.backBtnText}>Retour</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const card = cards[currentIndex];
  const showSide = card.show_side;
  const frontContent = showSide === 'question' ? card.question : card.answer;
  const backContent = showSide === 'question' ? card.answer : card.question;
  const frontLabel = showSide === 'question' ? 'TERME' : 'DÉFINITION';
  const backLabel = showSide === 'question' ? 'DÉFINITION' : 'TERME';

  const boxColors = ['#EF4444', '#F59E0B', '#10B981'];

  return (
    <SafeAreaView style={styles.safe}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity testID="study-close-btn" onPress={() => router.back()} style={styles.closeBtn}>
          <Ionicons name="close" size={24} color="#1F2937" />
        </TouchableOpacity>
        <Text style={styles.progress}>{currentIndex + 1} / {cards.length}</Text>
        <View style={[styles.boxBadge, { backgroundColor: boxColors[card.box - 1] + '20' }]}>
          <Text style={[styles.boxText, { color: boxColors[card.box - 1] }]}>Boîte {card.box}</Text>
        </View>
      </View>

      {/* Progress Bar */}
      <View style={styles.progressBarBg}>
        <View style={[styles.progressBarFill, { width: `${((currentIndex + 1) / cards.length) * 100}%` }]} />
      </View>

      {/* Flashcard */}
      <View style={styles.cardContainer}>
        <TouchableOpacity testID="flashcard-flip-btn" onPress={flipCard} activeOpacity={0.95}>
          {/* Front */}
          <Animated.View style={[styles.flashcard, { transform: [{ rotateY: frontInterpolate }], backfaceVisibility: 'hidden' }]}>
            <Text style={styles.sideLabel}>{frontLabel}</Text>
            <Text style={styles.cardText}>{frontContent}</Text>
            <View style={styles.flipHint}>
              <Ionicons name="refresh-outline" size={16} color="#9CA3AF" />
              <Text style={styles.flipHintText}>Toucher pour retourner</Text>
            </View>
          </Animated.View>

          {/* Back */}
          <Animated.View style={[styles.flashcard, styles.flashcardBack, { transform: [{ rotateY: backInterpolate }], backfaceVisibility: 'hidden' }]}>
            <Text style={styles.sideLabel}>{backLabel}</Text>
            <Text style={styles.cardText}>{backContent}</Text>
            <View style={styles.flipHint}>
              <Ionicons name="refresh-outline" size={16} color="#9CA3AF" />
              <Text style={styles.flipHintText}>Toucher pour retourner</Text>
            </View>
          </Animated.View>
        </TouchableOpacity>
      </View>

      {/* Answer Buttons */}
      {isFlipped && (
        <View style={styles.answerRow}>
          <TouchableOpacity
            testID="answer-incorrect-btn"
            style={[styles.answerBtn, styles.incorrectBtn]}
            onPress={() => handleAnswer(false)}
            activeOpacity={0.8}
          >
            <Ionicons name="close-circle" size={24} color="#EF4444" />
            <Text style={styles.incorrectText}>Je ne savais pas</Text>
          </TouchableOpacity>
          <TouchableOpacity
            testID="answer-correct-btn"
            style={[styles.answerBtn, styles.correctBtn]}
            onPress={() => handleAnswer(true)}
            activeOpacity={0.8}
          >
            <Ionicons name="checkmark-circle" size={24} color="#10B981" />
            <Text style={styles.correctText}>Je savais !</Text>
          </TouchableOpacity>
        </View>
      )}

      {!isFlipped && (
        <View style={styles.tapHintContainer}>
          <Text style={styles.tapHintText}>Retourne la carte puis évalue-toi</Text>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F4F6F8' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24, gap: 16 },
  errorText: { fontSize: 16, color: '#EF4444', textAlign: 'center', fontWeight: '600' },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: '#1F2937', textAlign: 'center' },
  submittingText: { fontSize: 16, color: '#6B7280', marginTop: 16 },
  backBtn: { backgroundColor: '#FF6B35', borderRadius: 16, paddingHorizontal: 32, paddingVertical: 14 },
  backBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 12 },
  closeBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center' },
  progress: { fontSize: 16, fontWeight: '700', color: '#1F2937' },
  boxBadge: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 12 },
  boxText: { fontSize: 12, fontWeight: '700' },
  progressBarBg: { height: 4, backgroundColor: '#E5E7EB', marginHorizontal: 20 },
  progressBarFill: { height: 4, backgroundColor: '#FF6B35', borderRadius: 2 },
  cardContainer: { flex: 1, justifyContent: 'center', paddingHorizontal: 24 },
  flashcard: {
    width: CARD_WIDTH, height: 380, backgroundColor: '#fff', borderRadius: 24,
    borderWidth: 2, borderColor: '#E5E7EB', padding: 28,
    alignItems: 'center', justifyContent: 'center',
    shadowColor: '#000', shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.08, shadowRadius: 16, elevation: 4,
  },
  flashcardBack: { position: 'absolute', top: 0, left: 0 },
  sideLabel: { position: 'absolute', top: 20, left: 24, fontSize: 12, fontWeight: '700', color: '#9CA3AF', letterSpacing: 1, textTransform: 'uppercase' },
  cardText: { fontSize: 22, fontWeight: '700', color: '#1F2937', textAlign: 'center', lineHeight: 32 },
  flipHint: { position: 'absolute', bottom: 20, flexDirection: 'row', alignItems: 'center', gap: 6 },
  flipHintText: { fontSize: 12, color: '#9CA3AF' },
  answerRow: { flexDirection: 'row', paddingHorizontal: 24, paddingBottom: 24, gap: 12 },
  answerBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 18, borderRadius: 16 },
  incorrectBtn: { backgroundColor: '#FEF2F2', borderWidth: 2, borderColor: '#FECACA' },
  correctBtn: { backgroundColor: '#F0FDF4', borderWidth: 2, borderColor: '#BBF7D0' },
  incorrectText: { fontSize: 15, fontWeight: '700', color: '#EF4444' },
  correctText: { fontSize: 15, fontWeight: '700', color: '#10B981' },
  tapHintContainer: { alignItems: 'center', paddingBottom: 32 },
  tapHintText: { fontSize: 14, color: '#9CA3AF', fontWeight: '500' },
});
