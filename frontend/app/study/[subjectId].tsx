import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Animated, ActivityIndicator, Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/utils/api';
import { useTheme } from '../../src/context/ThemeContext';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const CARD_WIDTH = SCREEN_WIDTH - 48;
const QUIZ_TIME = 15; // seconds per card

interface StudyCard { card_id: string; question: string; answer: string; show_side: 'question' | 'answer'; box: number; }

export default function StudySession() {
  const { subjectId, mode } = useLocalSearchParams<{ subjectId: string; mode?: string }>();
  const isQuiz = mode === 'quiz';
  const isExam = mode === 'exam';
  const { colors } = useTheme();
  const router = useRouter();

  const [cards, setCards] = useState<StudyCard[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [results, setResults] = useState<{ card_id: string; is_correct: boolean }[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [timer, setTimer] = useState(QUIZ_TIME);

  const flipAnim = useRef(new Animated.Value(0)).current;
  const timerRef = useRef<any>(null);

  useEffect(() => { loadCards(); return () => clearInterval(timerRef.current); }, [subjectId]);

  useEffect(() => {
    if (!isQuiz || loading || cards.length === 0 || submitting) return;
    clearInterval(timerRef.current);
    setTimer(QUIZ_TIME);
    timerRef.current = setInterval(() => {
      setTimer((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current);
          handleAnswer(false); // Time's up = incorrect
          return QUIZ_TIME;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [currentIndex, loading, isQuiz, submitting]);

  const loadCards = async () => {
    try {
      const endpoint = isExam ? `/study/exam/${subjectId}` : `/study/start/${subjectId}`;
      const data = await api.get(endpoint);
      setCards(data.session_cards || []);
    } catch (e: any) { setError(e.message || 'Erreur'); }
    finally { setLoading(false); }
  };

  const flipCard = () => {
    Animated.spring(flipAnim, { toValue: isFlipped ? 0 : 1, friction: 8, tension: 10, useNativeDriver: true }).start();
    setIsFlipped(!isFlipped);
  };

  const handleAnswer = (isCorrect: boolean) => {
    clearInterval(timerRef.current);
    const card = cards[currentIndex];
    if (!card) return;
    const newResults = [...results, { card_id: card.card_id, is_correct: isCorrect }];
    setResults(newResults);
    if (currentIndex < cards.length - 1) {
      flipAnim.setValue(0);
      setIsFlipped(false);
      setCurrentIndex(currentIndex + 1);
    } else {
      submitResults(newResults);
    }
  };

  const submitResults = async (finalResults: typeof results) => {
    setSubmitting(true);
    try {
      const data = await api.post('/study/submit', { subject_id: subjectId, results: finalResults });
      router.replace({
        pathname: '/study/report',
        params: {
          percentage: String(data.percentage), correct: String(data.correct_count),
          total: String(data.total_cards), xpEarned: String(data.xp_earned),
          streak: String(data.streak_count), level: String(data.new_level),
          totalXp: String(data.total_xp), newBadges: JSON.stringify(data.new_badges || []),
          cardsToReview: JSON.stringify(data.cards_to_review || []),
        },
      });
    } catch (e: any) { setError(e.message); setSubmitting(false); }
  };

  const frontInterp = flipAnim.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '180deg'] });
  const backInterp = flipAnim.interpolate({ inputRange: [0, 1], outputRange: ['180deg', '360deg'] });

  if (loading) return <SafeAreaView style={[s.safe, { backgroundColor: colors.bg }]}><View style={s.center}><ActivityIndicator size="large" color={colors.primary} /></View></SafeAreaView>;

  if (error) return (
    <SafeAreaView style={[s.safe, { backgroundColor: colors.bg }]}>
      <View style={s.center}>
        <Ionicons name="alert-circle" size={48} color={colors.error} />
        <Text style={[s.errText, { color: colors.error }]}>{error}</Text>
        <TouchableOpacity testID="study-back-btn" style={[s.btn, { backgroundColor: colors.primary }]} onPress={() => router.back()}>
          <Text style={s.btnTxt}>Retour</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );

  if (submitting) return <SafeAreaView style={[s.safe, { backgroundColor: colors.bg }]}><View style={s.center}><ActivityIndicator size="large" color={colors.primary} /><Text style={[s.subTxt, { color: colors.textSecondary }]}>Résultats...</Text></View></SafeAreaView>;

  if (cards.length === 0) return (
    <SafeAreaView style={[s.safe, { backgroundColor: colors.bg }]}>
      <View style={s.center}>
        <Ionicons name="checkmark-circle" size={48} color={colors.success} />
        <Text style={[s.emptyTitle, { color: colors.text }]}>Toutes les cartes maîtrisées !</Text>
        <TouchableOpacity testID="study-back-btn" style={[s.btn, { backgroundColor: colors.primary }]} onPress={() => router.back()}>
          <Text style={s.btnTxt}>Retour</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );

  const card = cards[currentIndex];
  const front = card.show_side === 'question' ? card.question : card.answer;
  const back = card.show_side === 'question' ? card.answer : card.question;
  const frontLbl = card.show_side === 'question' ? 'TERME' : 'DÉFINITION';
  const backLbl = card.show_side === 'question' ? 'DÉFINITION' : 'TERME';
  const boxColors = ['#EF4444', '#F59E0B', '#10B981'];
  const timerColor = timer <= 5 ? colors.error : timer <= 10 ? colors.warning : colors.success;

  return (
    <SafeAreaView style={[s.safe, { backgroundColor: colors.bg }]}>
      <View style={s.header}>
        <TouchableOpacity testID="study-close-btn" onPress={() => { clearInterval(timerRef.current); router.back(); }} style={[s.closeBtn, { backgroundColor: colors.surface }]}>
          <Ionicons name="close" size={24} color={colors.text} />
        </TouchableOpacity>
        <View style={{ alignItems: 'center' }}>
          <Text style={[s.progress, { color: colors.text }]}>{currentIndex + 1} / {cards.length}</Text>
          {isQuiz && <Text style={[s.modeBadge, { color: colors.warning }]}>QUIZ</Text>}
          {isExam && <Text style={[s.modeBadge, { color: colors.error }]}>EXAMEN</Text>}
        </View>
        <View style={[s.boxBadge, { backgroundColor: boxColors[card.box - 1] + '20' }]}>
          <Text style={[s.boxText, { color: boxColors[card.box - 1] }]}>Boîte {card.box}</Text>
        </View>
      </View>

      {/* Timer bar for quiz */}
      {isQuiz && (
        <View style={[s.timerWrap, { backgroundColor: colors.border }]}>
          <View style={[s.timerBar, { width: `${(timer / QUIZ_TIME) * 100}%`, backgroundColor: timerColor }]} />
          <Text style={[s.timerText, { color: timerColor }]}>{timer}s</Text>
        </View>
      )}

      <View style={[s.barBg, { backgroundColor: colors.border }]}>
        <View style={[s.barFill, { width: `${((currentIndex + 1) / cards.length) * 100}%`, backgroundColor: colors.primary }]} />
      </View>

      <View style={s.cardWrap}>
        <TouchableOpacity testID="flashcard-flip-btn" onPress={flipCard} activeOpacity={0.95}>
          <Animated.View style={[s.card, { backgroundColor: colors.surface, borderColor: colors.border }, { transform: [{ rotateY: frontInterp }], backfaceVisibility: 'hidden' }]}>
            <Text style={[s.lbl, { color: colors.textMuted }]}>{frontLbl}</Text>
            <Text style={[s.txt, { color: colors.text }]}>{front}</Text>
            <View style={s.flipHint}><Ionicons name="refresh-outline" size={16} color={colors.textMuted} /><Text style={[s.flipHintTxt, { color: colors.textMuted }]}>Toucher pour retourner</Text></View>
          </Animated.View>
          <Animated.View style={[s.card, s.cardBack, { backgroundColor: colors.surface, borderColor: colors.border }, { transform: [{ rotateY: backInterp }], backfaceVisibility: 'hidden' }]}>
            <Text style={[s.lbl, { color: colors.textMuted }]}>{backLbl}</Text>
            <Text style={[s.txt, { color: colors.text }]}>{back}</Text>
          </Animated.View>
        </TouchableOpacity>
      </View>

      {isFlipped ? (
        <View style={s.ansRow}>
          <TouchableOpacity testID="answer-incorrect-btn" style={[s.ansBtn, { backgroundColor: colors.errorBg, borderColor: colors.error + '40' }]} onPress={() => handleAnswer(false)}>
            <Ionicons name="close-circle" size={24} color={colors.error} />
            <Text style={[s.ansTxt, { color: colors.error }]}>Je ne savais pas</Text>
          </TouchableOpacity>
          <TouchableOpacity testID="answer-correct-btn" style={[s.ansBtn, { backgroundColor: colors.successBg, borderColor: colors.success + '40' }]} onPress={() => handleAnswer(true)}>
            <Ionicons name="checkmark-circle" size={24} color={colors.success} />
            <Text style={[s.ansTxt, { color: colors.success }]}>Je savais !</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={s.hintWrap}><Text style={[s.hintTxt, { color: colors.textMuted }]}>Retourne la carte puis évalue-toi</Text></View>
      )}
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24, gap: 16 },
  errText: { fontSize: 16, textAlign: 'center', fontWeight: '600' },
  emptyTitle: { fontSize: 18, fontWeight: '700', textAlign: 'center' },
  subTxt: { fontSize: 16, marginTop: 16 },
  btn: { borderRadius: 16, paddingHorizontal: 32, paddingVertical: 14 },
  btnTxt: { color: '#fff', fontSize: 16, fontWeight: '700' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 12 },
  closeBtn: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  progress: { fontSize: 16, fontWeight: '700' },
  modeBadge: { fontSize: 10, fontWeight: '800', letterSpacing: 2, marginTop: 2 },
  boxBadge: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 12 },
  boxText: { fontSize: 12, fontWeight: '700' },
  timerWrap: { marginHorizontal: 20, borderRadius: 8, height: 28, marginBottom: 8, justifyContent: 'center', overflow: 'hidden' },
  timerBar: { position: 'absolute', left: 0, top: 0, bottom: 0, borderRadius: 8 },
  timerText: { textAlign: 'center', fontSize: 14, fontWeight: '800', zIndex: 1 },
  barBg: { height: 4, marginHorizontal: 20 },
  barFill: { height: 4, borderRadius: 2 },
  cardWrap: { flex: 1, justifyContent: 'center', paddingHorizontal: 24 },
  card: {
    width: CARD_WIDTH, height: 360, borderRadius: 24, borderWidth: 2, padding: 28,
    alignItems: 'center', justifyContent: 'center',
  },
  cardBack: { position: 'absolute', top: 0, left: 0 },
  lbl: { position: 'absolute', top: 20, left: 24, fontSize: 12, fontWeight: '700', letterSpacing: 1, textTransform: 'uppercase' },
  txt: { fontSize: 22, fontWeight: '700', textAlign: 'center', lineHeight: 32 },
  flipHint: { position: 'absolute', bottom: 20, flexDirection: 'row', alignItems: 'center', gap: 6 },
  flipHintTxt: { fontSize: 12 },
  ansRow: { flexDirection: 'row', paddingHorizontal: 24, paddingBottom: 24, gap: 12 },
  ansBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 18, borderRadius: 16, borderWidth: 2 },
  ansTxt: { fontSize: 15, fontWeight: '700' },
  hintWrap: { alignItems: 'center', paddingBottom: 32 },
  hintTxt: { fontSize: 14, fontWeight: '500' },
});
