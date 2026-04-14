# FlashCards - Application de Flashcards Gamifiée

## Description
Application mobile gamifiée de flashcards pour les étudiants de la 6ème à la Terminale. Utilise le système de mémorisation Leitner à 3 boîtes pour optimiser l'apprentissage.

## Fonctionnalités principales
- **Authentification** : Inscription/connexion par email/mot de passe (JWT)
- **9 matières scolaires** : Maths, Français, Histoire-Géo, SVT, Physique-Chimie, Anglais, Philosophie, SES, Espagnol
- **Système Leitner 3 boîtes** : Révision espacée avec suivi de progression par carte
- **Flashcards alternées** : Les cartes apparaissent côté définition la première fois, puis alternent
- **Gamification** : XP, niveaux (500 XP/niveau), streaks quotidiens, 6 badges
- **Flashcards personnalisées** : Les utilisateurs peuvent créer leurs propres cartes
- **Rapport de session** : Pourcentage de réussite, XP gagnés, cartes à réviser

## Architecture technique
- **Backend** : FastAPI + MongoDB (motor async)
- **Frontend** : Expo Router (React Native) avec TypeScript
- **Auth** : JWT Bearer tokens + AsyncStorage
- **Base de données** : MongoDB avec collections users, subjects, flashcards, user_card_progress, study_sessions

## Stack
- Python 3.x / FastAPI / MongoDB / Motor
- React Native / Expo SDK 54 / Expo Router
- JWT / bcrypt / AsyncStorage
