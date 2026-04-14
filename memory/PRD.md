# FlashCards - Application de Flashcards Gamifiée

## Description
Application mobile gamifiée de flashcards pour les étudiants de la 6ème à la Terminale avec système Leitner 3 boîtes.

## Fonctionnalités
### Core (v1)
- Auth JWT (inscription/connexion email/mot de passe)
- 9 matières scolaires avec 45+ flashcards pré-remplies
- Système Leitner 3 boîtes (révision espacée)
- Flashcards alternées (définition d'abord, puis alternance)
- Gamification : XP, niveaux, streaks, 6 badges
- Création de flashcards personnalisées
- Rapport de session (%, XP, cartes à réviser)

### v2
- Filtrage par niveau scolaire (6ème-Terminale)
- Notifications de rappel de streak (expo-notifications)
- Mode classe (créer/rejoindre, partager des decks)
- Export/Import de decks (JSON via presse-papier)

### v3
- Leaderboard par classe (classement par XP avec médailles)
- Mode quiz chronométré (15s/carte)
- Statistiques détaillées par matière (onglet Stats)
- Thème sombre (toggle persisté)

### v4 (actuel)
- **Récompenses quotidiennes** : Cycle de 7 jours (25→300 XP), nécessite 1 session d'étude
- **Classes privées** : Toggle privé + verrouillage sur un niveau scolaire
- **Bug fix** : async-storage 3.0.2→2.2.0 (corrige "Native module is null" sur mobile)

## Architecture
- Backend: FastAPI + MongoDB + JWT
- Frontend: Expo SDK 54 + Expo Router + React Native
- Collections: users, subjects, flashcards, user_card_progress, study_sessions, classes, shared_decks
- 4 onglets: Accueil, Stats, Classe, Profil
