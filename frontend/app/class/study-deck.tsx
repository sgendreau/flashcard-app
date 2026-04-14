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

export default function StudySharedDeck() {
  const { classId, deckId } = useLocalSearchParams<{ classId: string; deckId: string }>();
  const router = useRouter();
  const [cards, setCards] = useState<any[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [subjectId, setSubjectId] = useState('');
  const flipAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    api.get(`/classes/${classId}/decks/${deckId}/study`).then((data) => {
      setCards(data.session_cards || []);
      setSubjectId(data.subject_id || '');
    }).catch(console.log).finally(() => setLoading(false));
  }, [classId, deckId]);

  const flipCard = () => {
    Animated.spring(flipAnim, { toValue: isFlipped ? 0 : 1, friction: 8, tension: 10, useNativeDriver: true }).start();
    setIsFlipped(!isFlipped);
  };

  const handleAnswer = (isCorrect: boolean) => {
    const card = cards[currentIndex];
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

  const submitResults = async (finalResults: any[]) => {
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
    } catch { setSubmitting(false); }
  };

  const frontInterp = flipAnim.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '180deg'] });
  const backInterp = flipAnim.interpolate({ inputRange: [0, 1], outputRange: ['180deg', '360deg'] });

  if (loading || submitting) {
    return (
      <SafeAreaView style={s.safe}>
        <View style={s.center}>
          <ActivityIndicator size="large" color="#FF6B35" />
          {submitting && <Text style={s.loadText}>Résultats en cours...</Text>}
        </View>
      </SafeAreaView>
    );
  }

  if (cards.length === 0) {
    return (
      <SafeAreaView style={s.safe}>
        <View style={s.center}>
          <Text style={s.loadText}>Aucune carte dans ce deck</Text>
          <TouchableOpacity style={s.btn} onPress={() => router.back()}>
            <Text style={s.btnTxt}>Retour</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const card = cards[currentIndex];
  const front = card.show_side === 'question' ? card.question : card.answer;
  const back = card.show_side === 'question' ? card.answer : card.question;
  const frontLbl = card.show_side === 'question' ? 'TERME' : 'DÉFINITION';
  const backLbl = card.show_side === 'question' ? 'DÉFINITION' : 'TERME';

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} style={s.closeBtn}>
          <Ionicons name="close" size={24} color="#1F2937" />
        </TouchableOpacity>
        <Text style={s.progress}>{currentIndex + 1} / {cards.length}</Text>
        <View style={s.badge}><Text style={s.badgeTxt}>Deck partagé</Text></View>
      </View>
      <View style={s.barBg}><View style={[s.barFill, { width: `${((currentIndex + 1) / cards.length) * 100}%` }]} /></View>

      <View style={s.cardWrap}>
        <TouchableOpacity onPress={flipCard} activeOpacity={0.95}>
          <Animated.View style={[s.card, { transform: [{ rotateY: frontInterp }], backfaceVisibility: 'hidden' }]}>
            <Text style={s.lbl}>{frontLbl}</Text>
            <Text style={s.txt}>{front}</Text>
          </Animated.View>
          <Animated.View style={[s.card, s.cardBack, { transform: [{ rotateY: backInterp }], backfaceVisibility: 'hidden' }]}>
            <Text style={s.lbl}>{backLbl}</Text>
            <Text style={s.txt}>{back}</Text>
          </Animated.View>
        </TouchableOpacity>
      </View>

      {isFlipped ? (
        <View style={s.ansRow}>
          <TouchableOpacity style={[s.ansBtn, s.wrongBtn]} onPress={() => handleAnswer(false)}>
            <Ionicons name="close-circle" size={24} color="#EF4444" />
            <Text style={s.wrongTxt}>Je ne savais pas</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[s.ansBtn, s.rightBtn]} onPress={() => handleAnswer(true)}>
            <Ionicons name="checkmark-circle" size={24} color="#10B981" />
            <Text style={s.rightTxt}>Je savais !</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={s.hintWrap}><Text style={s.hintTxt}>Touche la carte pour la retourner</Text></View>
      )}
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F4F6F8' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 16 },
  loadText: { fontSize: 16, color: '#6B7280' },
  btn: { backgroundColor: '#FF6B35', borderRadius: 16, paddingHorizontal: 32, paddingVertical: 14 },
  btnTxt: { color: '#fff', fontSize: 16, fontWeight: '700' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 12 },
  closeBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center' },
  progress: { fontSize: 16, fontWeight: '700', color: '#1F2937' },
  badge: { backgroundColor: '#EEF2FF', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 12 },
  badgeTxt: { fontSize: 12, fontWeight: '700', color: '#3B82F6' },
  barBg: { height: 4, backgroundColor: '#E5E7EB', marginHorizontal: 20 },
  barFill: { height: 4, backgroundColor: '#3B82F6', borderRadius: 2 },
  cardWrap: { flex: 1, justifyContent: 'center', paddingHorizontal: 24 },
  card: {
    width: CARD_WIDTH, height: 360, backgroundColor: '#fff', borderRadius: 24,
    borderWidth: 2, borderColor: '#E5E7EB', padding: 28,
    alignItems: 'center', justifyContent: 'center',
  },
  cardBack: { position: 'absolute', top: 0, left: 0 },
  lbl: { position: 'absolute', top: 20, left: 24, fontSize: 12, fontWeight: '700', color: '#9CA3AF', letterSpacing: 1 },
  txt: { fontSize: 22, fontWeight: '700', color: '#1F2937', textAlign: 'center', lineHeight: 32 },
  ansRow: { flexDirection: 'row', paddingHorizontal: 24, paddingBottom: 24, gap: 12 },
  ansBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 18, borderRadius: 16 },
  wrongBtn: { backgroundColor: '#FEF2F2', borderWidth: 2, borderColor: '#FECACA' },
  rightBtn: { backgroundColor: '#F0FDF4', borderWidth: 2, borderColor: '#BBF7D0' },
  wrongTxt: { fontSize: 15, fontWeight: '700', color: '#EF4444' },
  rightTxt: { fontSize: 15, fontWeight: '700', color: '#10B981' },
  hintWrap: { alignItems: 'center', paddingBottom: 32 },
  hintTxt: { fontSize: 14, color: '#9CA3AF', fontWeight: '500' },
});
