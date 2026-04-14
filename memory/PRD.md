# FlashCards - Application de Flashcards Gamifiée

## Description
Application mobile gamifiée de flashcards pour les étudiants de la 6ème à la Terminale avec système Leitner 3 boîtes et IA intégrée.

## Fonctionnalités

### Core (v1)
- Auth JWT email/mot de passe, 9 matières, système Leitner 3 boîtes
- Gamification : XP, niveaux, streaks, 6 badges
- Flashcards pré-remplies + personnalisées, rapport de session

### v2-v4
- Filtrage par niveau scolaire (6ème-Terminale), notifications streak
- Mode classe (créer/rejoindre/partager), export/import decks
- Leaderboard, mode quiz chronométré, stats détaillées, thème sombre
- Récompenses quotidiennes, classes privées/verrouillées

### v5
- Mode révision examen (toutes cartes, triées par faiblesse)
- Défis hebdomadaires (4 défis/semaine avec XP bonus)
- Partage social (résultats + profil via Share API)

### v6 (actuel)
- **Intégration IA Claude Sonnet** : Génération automatique de flashcards à partir de texte de cours. Bouton violet (sparkles) sur l'accueil → écran dédié avec sélection matière, nombre de cartes et zone de texte
- **Synchronisation multi-appareils** : Indicateur de sync dans le profil (cloud icon, nombre de sessions/cartes, dernière activité). Architecture server-side MongoDB = données synchronisées automatiquement
- **Version tablette optimisée** : useResponsive() hook, grille 2 colonnes sur tablette, padding adaptatif

## Architecture
- Backend: FastAPI + MongoDB + JWT + Claude Sonnet (emergentintegrations)
- Frontend: Expo SDK 54 + Expo Router + React Native + TypeScript
- Collections: users, subjects, flashcards, user_card_progress, study_sessions, classes, shared_decks, challenge_claims
- 4 onglets + 2 modals (Create Card, AI Generate)
- 3 modes d'étude: Normal, Quiz, Examen
