import { useEffect, useRef, useState } from 'react';
import { View, Animated, StyleSheet, Image, Text } from 'react-native';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAuth } from '../src/context/AuthContext';
import { QUIKKO_LOGO } from '../assets/logo-base64';

export default function Index() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [showSplash, setShowSplash] = useState(true);

  // Animations
  const logoScale = useRef(new Animated.Value(0.3)).current;
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const titleOpacity = useRef(new Animated.Value(0)).current;
  const titleTranslateY = useRef(new Animated.Value(20)).current;
  const sloganOpacity = useRef(new Animated.Value(0)).current;
  const bgFlash = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // 1. Logo fade in + scale up with bounce
    Animated.sequence([
      Animated.parallel([
        Animated.spring(logoScale, { toValue: 1, friction: 4, tension: 50, useNativeDriver: true }),
        Animated.timing(logoOpacity, { toValue: 1, duration: 600, useNativeDriver: true }),
      ]),
      // 2. Flash effect
      Animated.sequence([
        Animated.timing(bgFlash, { toValue: 1, duration: 150, useNativeDriver: false }),
        Animated.timing(bgFlash, { toValue: 0, duration: 300, useNativeDriver: false }),
      ]),
      // 3. Title slides up + fades in
      Animated.parallel([
        Animated.timing(titleOpacity, { toValue: 1, duration: 400, useNativeDriver: true }),
        Animated.spring(titleTranslateY, { toValue: 0, friction: 6, useNativeDriver: true }),
      ]),
      // 4. Slogan fade in
      Animated.timing(sloganOpacity, { toValue: 1, duration: 400, useNativeDriver: true }),
      // 5. Wait then navigate
      Animated.delay(600),
    ]).start(() => setShowSplash(false));
  }, []);

  useEffect(() => {
    if (showSplash || loading) return;
    const navigate = async () => {
      const seen = await AsyncStorage.getItem('onboarding_done');
      if (!seen) {
        router.replace('/onboarding');
      } else if (user) {
        router.replace('/(tabs)/home');
      } else {
        router.replace('/(auth)/login');
      }
    };
    navigate();
  }, [showSplash, user, loading]);

  const bgColor = bgFlash.interpolate({
    inputRange: [0, 1],
    outputRange: ['#1A1A2E', '#2A2040'],
  });

  return (
    <Animated.View style={[styles.container, { backgroundColor: bgColor }]}>
      <Animated.View style={{ transform: [{ scale: logoScale }], opacity: logoOpacity }}>
        <Image source={{ uri: QUIKKO_LOGO }} style={styles.logo} />
      </Animated.View>
      <Animated.Text style={[styles.title, { opacity: titleOpacity, transform: [{ translateY: titleTranslateY }] }]}>
        quikko
      </Animated.Text>
      <Animated.Text style={[styles.slogan, { opacity: sloganOpacity }]}>
        Révise vite, retiens tout
      </Animated.Text>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  logo: { width: 220, height: 120, borderRadius: 20 },
  title: { fontSize: 42, fontWeight: '900', color: '#E8594D', letterSpacing: 2, marginTop: 16 },
  slogan: { fontSize: 16, color: '#A0A0C0', marginTop: 8, fontWeight: '500' },
});
