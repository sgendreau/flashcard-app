# FlashCards - Application de Flashcards Gamifiée

## Description
Application mobile gamifiée de flashcards pour les étudiants de la 6ème à la Terminale avec système Leitner 3 boîtes.

## Fonctionnalités
### Core
- Auth JWT (inscription/connexion email/mot de passe)
- 9 matières scolaires avec 45+ flashcards pré-remplies
- Système Leitner 3 boîtes (révision espacée)
- Flashcards alternées (définition d'abord, puis alternance)
- Gamification : XP, niveaux, streaks, 6 badges
- Création de flashcards personnalisées
- Rapport de session (%, XP, cartes à réviser)

### v2 - Fonctionnalités avancées
- Filtrage par niveau scolaire (6ème-Terminale)
- Notifications de rappel de streak (expo-notifications)
- Mode classe (créer/rejoindre, partager des decks, code 6 chars)
- Export/Import de decks (JSON via presse-papier)

### v3 - Fonctionnalités récentes
- **Leaderboard par classe** : Classement des membres par XP avec médailles 🥇🥈🥉
- **Mode quiz chronométré** : 15 secondes par carte, auto-incorrect si timeout
- **Statistiques détaillées** : Onglet Stats avec breakdown par matière (sessions, moyenne, maîtrise %, distribution boîtes)
- **Thème sombre** : Toggle dark/light persisté côté backend et AsyncStorage

## Architecture
- Backend: FastAPI + MongoDB (motor) + JWT
- Frontend: Expo SDK 54 + Expo Router + React Native
- Collections: users, subjects, flashcards, user_card_progress, study_sessions, classes, shared_decks
- 4 onglets: Accueil, Stats, Classe, Profil
