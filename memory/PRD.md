# FlashCards - Application de Flashcards Gamifiée

## Description
Application mobile gamifiée de flashcards pour les étudiants de la 6ème à la Terminale avec système Leitner 3 boîtes, IA intégrée et mode offline.

## Fonctionnalités complètes

### Core (v1) — Auth, Study, Gamification
- Auth JWT email/mot de passe, 9 matières, 45+ flashcards pré-remplies
- Système Leitner 3 boîtes, flashcards alternées
- XP, niveaux, streaks, 6 badges, rapport de session

### v2 — Social & Sharing
- Filtrage par niveau scolaire (6ème-Terminale)
- Notifications streak, mode classe, export/import decks

### v3 — Competition & Stats
- Leaderboard, mode quiz chronométré, stats détaillées, thème sombre

### v4 — Rewards & Privacy
- Récompenses quotidiennes (cycle 7 jours), classes privées/verrouillées

### v5 — Exam & Challenges
- Mode révision examen, défis hebdomadaires, partage social

### v6 — AI & Responsive
- IA Claude Sonnet (génération flashcards), sync multi-appareils, tablette responsive

### v7 (actuel) — Referral & Offline
- **Système de parrainage** : Code unique par utilisateur (FC + 5 chars), 100 XP bonus pour parrain et filleul à l'inscription, stats de parrainage dans le profil avec bouton de partage
- **Mode offline** : Cache AsyncStorage (matières + flashcards), fallback local quand API indisponible, indicateur de cache dans le profil, file de résultats en attente de sync

## Architecture
- Backend: FastAPI + MongoDB + JWT + Claude Sonnet (emergentintegrations) — 35+ endpoints
- Frontend: Expo SDK 54 + Expo Router + React Native + TypeScript
- Collections: users, subjects, flashcards, user_card_progress, study_sessions, classes, shared_decks, challenge_claims
- Cache: AsyncStorage (offline), ThemeContext (dark/light), AuthContext (JWT)
- 4 onglets + 2 modals, 3 modes d'étude, responsive tablette
