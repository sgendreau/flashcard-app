# Quikko - Application de Flashcards Gamifiée

## Description
Application mobile gamifiée de flashcards pour les étudiants de la 6ème à la Terminale. Système Leitner 3 boîtes, IA intégrée, mode offline.

## Branding
- **Nom** : Quikko
- **Logo** : Q rouge avec éclair (quikko-logo.png)
- **Couleurs** : Primary #E8594D (coral rouge), Dark #1A1A2E, Dark Surface #1E2A45
- **Slogan** : "Révise vite, retiens tout"
- **Theme** : Dark par défaut avec palette deep navy + coral red

## Fonctionnalités complètes (v1-v8)
- Auth JWT, 9 matières, 45+ flashcards, système Leitner 3 boîtes
- Gamification: XP, niveaux, streaks, 6 badges, récompenses quotidiennes (7j cycle)
- Filtrage par niveau scolaire minimum (6ème-Terminale)
- Mode classe (créer/rejoindre/partager), leaderboard
- 3 modes d'étude: Normal, Quiz chronométré (15s), Révision examen
- Défis hebdomadaires (4 défis/semaine)
- IA Claude Sonnet (génération de flashcards)
- Partage social (résultats + profil)
- Parrainage (+100 XP chacun)
- Mode offline (AsyncStorage cache)
- Thème sombre/clair, responsive tablette
- Export/Import de decks

## Architecture
- Backend: FastAPI + MongoDB + JWT + Claude Sonnet
- Frontend: Expo SDK 54 + Expo Router + React Native + TypeScript
- 4 onglets: Accueil, Stats, Classe, Profil
