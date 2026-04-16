import React, { useRef, useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Animated, Dimensions, Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';
import { QUIKKO_LOGO } from '../assets/logo-base64';

const { width: SW } = Dimensions.get('window');

const SLIDES = [
  {
    icon: 'flash-outline' as const,
    title: 'Révise en un éclair',
    description: 'Quikko utilise la méthode Leitner à 3 boîtes pour maximiser ta mémorisation. Les cartes que tu ne connais pas reviennent plus souvent.',
    color: '#E8594D',
  },
  {
    icon: 'trophy-outline' as const,
    title: 'Gagne des XP et des badges',
    description: 'Chaque session te rapporte des XP. Monte de niveau, débloque des badges et maintiens ton streak quotidien pour progresser !',
    color: '#FBBF24',
  },
  {
    icon: 'people-outline' as const,
    title: 'Révise avec ta classe',
    description: "Crée ou rejoins une classe, partage tes decks et compare-toi dans le classement. L'IA peut même générer des flashcards à partir de tes cours !",
    color: '#10B981',
  },
];

export default function OnboardingScreen() {
  const router = useRouter();
  const [currentSlide, setCurrentSlide] = useState(0);
  const slideAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(1)).current;

  const goToSlide = (index: number) => {
    Animated.timing(fadeAnim, { toValue: 0, duration: 150, useNativeDriver: true }).start(() => {
      setCurrentSlide(index);
      slideAnim.setValue(0);
      Animated.parallel([
        Animated.timing(fadeAnim, { toValue: 1, duration: 300, useNativeDriver: true }),
        Animated.spring(slideAnim, { toValue: 1, friction: 6, useNativeDriver: true }),
      ]).start();
    });
  };

  const handleNext = () => {
    if (currentSlide < SLIDES.length - 1) {
      goToSlide(currentSlide + 1);
    } else {
      finishOnboarding();
    }
  };

  const finishOnboarding = async () => {
    await AsyncStorage.setItem('onboarding_done', 'true');
    router.replace('/(auth)/login');
  };

  const slide = SLIDES[currentSlide];
  const translateY = slideAnim.interpolate({ inputRange: [0, 1], outputRange: [30, 0] });

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.container}>
        {/* Skip */}
        {currentSlide < SLIDES.length - 1 && (
          <TouchableOpacity testID="onboarding-skip" style={s.skipBtn} onPress={finishOnboarding}>
            <Text style={s.skipText}>Passer</Text>
          </TouchableOpacity>
        )}

        {/* Logo */}
        <Image source={{ uri: QUIKKO_LOGO }} style={s.logo} />

        {/* Slide content */}
        <Animated.View style={[s.slideContent, { opacity: fadeAnim, transform: [{ translateY }] }]}>
          <View style={[s.iconCircle, { backgroundColor: slide.color + '20' }]}>
            <Ionicons name={slide.icon} size={48} color={slide.color} />
          </View>
          <Text style={s.slideTitle}>{slide.title}</Text>
          <Text style={s.slideDesc}>{slide.description}</Text>
        </Animated.View>

        {/* Dots */}
        <View style={s.dotsRow}>
          {SLIDES.map((_, i) => (
            <View
              key={i}
              style={[s.dot, i === currentSlide ? s.dotActive : s.dotInactive]}
            />
          ))}
        </View>

        {/* Button */}
        <TouchableOpacity
          testID={currentSlide < SLIDES.length - 1 ? 'onboarding-next' : 'onboarding-start'}
          style={[s.nextBtn, { backgroundColor: slide.color }]}
          onPress={handleNext}
          activeOpacity={0.8}
        >
          <Text style={s.nextText}>
            {currentSlide < SLIDES.length - 1 ? 'Suivant' : "C'est parti !"}
          </Text>
          <Ionicons
            name={currentSlide < SLIDES.length - 1 ? 'arrow-forward' : 'rocket'}
            size={20}
            color="#fff"
          />
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#1A1A2E' },
  container: { flex: 1, padding: 24, alignItems: 'center', justifyContent: 'center' },
  skipBtn: { position: 'absolute', top: 16, right: 24, paddingVertical: 8, paddingHorizontal: 16 },
  skipText: { color: '#A0A0C0', fontSize: 15, fontWeight: '600' },
  logo: { width: 140, height: 76, borderRadius: 14, marginBottom: 40 },
  slideContent: { alignItems: 'center', paddingHorizontal: 16, marginBottom: 40 },
  iconCircle: {
    width: 96, height: 96, borderRadius: 48, alignItems: 'center', justifyContent: 'center', marginBottom: 24,
  },
  slideTitle: { fontSize: 28, fontWeight: '900', color: '#F0F0F8', textAlign: 'center', marginBottom: 12 },
  slideDesc: { fontSize: 16, color: '#A0A0C0', textAlign: 'center', lineHeight: 24, maxWidth: 340 },
  dotsRow: { flexDirection: 'row', gap: 10, marginBottom: 32 },
  dot: { height: 8, borderRadius: 4 },
  dotActive: { width: 28, backgroundColor: '#E8594D' },
  dotInactive: { width: 8, backgroundColor: '#2A3555' },
  nextBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10,
    paddingVertical: 18, paddingHorizontal: 40, borderRadius: 20, width: '100%', maxWidth: 340,
  },
  nextText: { color: '#fff', fontSize: 18, fontWeight: '700' },
});
