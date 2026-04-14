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
- Notifications de rappel de streak
- Mode classe (créer/rejoindre, partager des decks)
- Export/Import de decks (JSON presse-papier)

### v3
- Leaderboard par classe
- Mode quiz chronométré (15s/carte)
- Statistiques détaillées par matière (onglet Stats)
- Thème sombre (toggle persisté)

### v4
- Récompenses quotidiennes (cycle 7 jours, 25→300 XP)
- Classes privées + verrouillées par niveau
- Bug fix: async-storage (3.0.2→2.2.0)

### v5 (actuel)
- **Mode révision avant examen** : Toutes les cartes d'une matière (jusqu'à 30), triées par faiblesse (boîte 1 d'abord), sans filtre de niveau
- **Défis hebdomadaires** : 4 défis/semaine (Marathonien 5 sessions, Sans faute 2×100%, Touche-à-tout 3 matières, Maître absolu 5 cartes en B3) avec suivi de progression et XP bonus
- **Système de partage social** : Partager ses résultats de session et son profil via l'API Share native (texte formaté avec emojis et stats)

## Architecture
- Backend: FastAPI + MongoDB + JWT + 30+ endpoints
- Frontend: Expo SDK 54 + Expo Router + React Native + TypeScript
- Collections: users, subjects, flashcards, user_card_progress, study_sessions, classes, shared_decks, challenge_claims
- 4 onglets: Accueil, Stats, Classe, Profil
- 3 modes d'étude: Normal, Quiz chronométré, Révision examen
