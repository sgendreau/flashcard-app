import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Quikko brand colors derived from logo
// Primary: Coral red from the Q logo
// Dark: #1A1A2E (user preference)
export const BRAND = {
  primary: '#E8594D',
  primaryLight: '#FF7B6F',
  primaryDark: '#C9403A',
  dark: '#1A1A2E',
  darkAlt: '#16213E',
  darkSurface: '#1E2A45',
};

export const THEMES = {
  light: {
    bg: '#F5F5FA', surface: '#FFFFFF', surfaceAlt: '#F0F0F8',
    text: '#1A1A2E', textSecondary: '#5C5C7A', textMuted: '#9696AD',
    border: '#E0E0EF', borderLight: '#F0F0F8',
    primary: BRAND.primary, primaryBg: '#FFF0EE', primaryLight: BRAND.primaryLight,
    error: '#EF4444', errorBg: '#FEF2F2',
    success: '#10B981', successBg: '#F0FDF4',
    warning: '#F59E0B', warningBg: '#FFF8E1',
    tabBar: '#FFFFFF', tabBorder: '#E0E0EF',
    cardShadow: 0.06,
  },
  dark: {
    bg: BRAND.dark, surface: BRAND.darkSurface, surfaceAlt: '#263352',
    text: '#F0F0F8', textSecondary: '#A0A0C0', textMuted: '#6B6B8D',
    border: '#2A3555', borderLight: '#1E2A45',
    primary: BRAND.primaryLight, primaryBg: '#3A1F1D', primaryLight: BRAND.primary,
    error: '#F87171', errorBg: '#450A0A',
    success: '#34D399', successBg: '#052E16',
    warning: '#FBBF24', warningBg: '#451A03',
    tabBar: BRAND.darkSurface, tabBorder: '#2A3555',
    cardShadow: 0,
  },
};

type ThemeColors = typeof THEMES.light;
type ThemeName = 'light' | 'dark';

interface ThemeContextType {
  isDark: boolean;
  theme: ThemeName;
  colors: ThemeColors;
  toggleTheme: () => void;
  setTheme: (t: ThemeName) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children, initialTheme }: { children: ReactNode; initialTheme?: ThemeName }) {
  const [theme, setThemeState] = useState<ThemeName>(initialTheme || 'light');

  useEffect(() => {
    AsyncStorage.getItem('app_theme').then((v) => {
      if (v === 'dark' || v === 'light') setThemeState(v);
    });
  }, []);

  useEffect(() => { if (initialTheme) setThemeState(initialTheme); }, [initialTheme]);

  const setTheme = (t: ThemeName) => { setThemeState(t); AsyncStorage.setItem('app_theme', t); };
  const toggleTheme = () => setTheme(theme === 'light' ? 'dark' : 'light');

  return (
    <ThemeContext.Provider value={{ isDark: theme === 'dark', theme, colors: THEMES[theme], toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
