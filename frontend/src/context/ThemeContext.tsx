import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const THEMES = {
  light: {
    bg: '#F4F6F8', surface: '#FFFFFF', surfaceAlt: '#F9FAFB',
    text: '#1F2937', textSecondary: '#6B7280', textMuted: '#9CA3AF',
    border: '#E5E7EB', borderLight: '#F3F4F6',
    primary: '#FF6B35', primaryBg: '#FFF3ED',
    error: '#EF4444', errorBg: '#FEF2F2',
    success: '#10B981', successBg: '#F0FDF4',
    warning: '#F59E0B', warningBg: '#FFF8E1',
    tabBar: '#FFFFFF', tabBorder: '#E5E7EB',
    cardShadow: 0.05,
  },
  dark: {
    bg: '#0F172A', surface: '#1E293B', surfaceAlt: '#334155',
    text: '#F1F5F9', textSecondary: '#94A3B8', textMuted: '#64748B',
    border: '#334155', borderLight: '#1E293B',
    primary: '#FF8A5C', primaryBg: '#3B1F10',
    error: '#F87171', errorBg: '#450A0A',
    success: '#34D399', successBg: '#052E16',
    warning: '#FBBF24', warningBg: '#451A03',
    tabBar: '#1E293B', tabBorder: '#334155',
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

  useEffect(() => {
    if (initialTheme) setThemeState(initialTheme);
  }, [initialTheme]);

  const setTheme = (t: ThemeName) => {
    setThemeState(t);
    AsyncStorage.setItem('app_theme', t);
  };

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
