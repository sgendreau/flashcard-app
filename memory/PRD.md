# Quikko — Product Requirements Document

> Document de référence du produit. Sert de socle stable avant toute modification du code.
> Remplace le placeholder Emergent (`memory/PRD.md`).

---

## 1. Vision

Quikko est une application mobile de révision pour les élèves français, adossée aux **programmes officiels**. L'utilisateur choisit son niveau et révise, via un système de **répétition espacée (Leitner)**, des flashcards de son niveau et des niveaux antérieurs. Il peut aussi **créer ses propres cartes** et réviser à plusieurs au sein de **classes**.

**Cibles**
- Collégiens (6e → 3e)
- Lycéens (2nde → Terminale)
- Post-bac *(phase ultérieure — voir §9)*

---

## 2. Les trois piliers

### Pilier 1 — Niveaux & programmes
- Chaque utilisateur a un **niveau** (`grade_level`).
- Règle de visibilité du contenu officiel : **« mon niveau + tous les niveaux précédents »**.
  - Ex. : un élève de 3e voit les cartes officielles taguées 6e, 5e, 4e et 3e.
- Le collège est linéaire et couvert nativement par ce modèle.
- Le lycée introduit une **2ᵉ dimension** (tronc commun + **spécialités**) à modéliser en phase ultérieure.
- Le post-bac n'est pas linéaire et n'a pas de programme national unique → traité comme des **pistes séparées**, hors v1.

### Pilier 2 — Contenu à deux étages
Deux natures de cartes, avec des règles de visibilité distinctes :

| Type | Visibilité | Propriétaire |
|------|------------|--------------|
| **Officielle** | Commune à tous (filtrée par niveau) | aucun (`source = "official"`) |
| **Perso** | Privée à son créateur | l'utilisateur (`source = "personal"`) |

- Une **session d'étude** tire : *cartes officielles de mon niveau et en dessous* **+** *mes cartes perso*.
- La **progression Leitner est par utilisateur et par carte** (collection `user_card_progress`) : même sur une carte officielle commune, chacun a sa propre avancée. ✅ *(Déjà le cas dans le code actuel.)*

### Pilier 3 — Classes (groupe persistant + sessions asynchrones)
- Une **classe** est un **groupe persistant** : code d'invitation, membres, classement. ✅ *(Existe déjà.)*
- On y **lance des sessions de révision asynchrones** :
  - Un jeu de cartes défini (une matière, un deck perso partagé, ou une sélection).
  - Une **date limite** (ex. 48 h) : chacun la fait quand il veut dans la fenêtre.
  - Un **classement propre à la session**, calculé uniquement sur les réponses de cette session.
  - Les résultats **nourrissent aussi la progression Leitner perso** de chaque élève (réviser une carte = réviser une carte).
- **Pas de sessions synchrones (temps réel)** en v1 : évite l'infra websockets et respecte les emplois du temps des élèves.

---

## 3. Modèle de données cible

### Collections existantes (réutilisées)
- **users** — profil, XP, niveau, streak, badges, `grade_level`, prefs notifications, parrainage.
- **subjects** — matières (seed).
- **flashcards** — `id`, `subject_id`, `question`, `answer`, `grade_levels[]`, `created_by`, `created_at`.
- **user_card_progress** — `user_id`, `card_id`, `subject_id`, `box`, `last_shown_side`, `last_reviewed`, `times_correct`, `times_incorrect`.
- **study_sessions** — *journal des sessions d'étude perso* (à ne pas confondre avec les sessions de classe).
- **classes** — `id`, `name`, `code`, `is_private`, `locked_grade`, `members[]`.
- **shared_decks** — embryon de partage en classe (à faire évoluer vers les sessions, §6).
- **challenge_claims** — défis hebdo.

### Évolutions à apporter
**`flashcards`** — ajouter :
- `source` : `"official" | "personal"`
- `owner_id` : identifiant du créateur pour les cartes perso (`null` pour les officielles)

**`user_card_progress`** — ajouter (couche temporelle Leitner) :
- `next_review_at` : date à laquelle la carte redevient « due »

**Nouvelle collection `class_sessions`** :
- `id`, `class_id`, `created_by`, `title`
- `card_ids[]` (ou référence à une matière / un deck)
- `opens_at`, `deadline`, `status` (`open | closed`)

**Nouvelle collection `class_session_results`** :
- `session_id`, `user_id`, `correct`, `total`, `percentage`, `completed_at`

> ⚠️ **Vocabulaire** : « session d'étude » (perso, `study_sessions`) ≠ « session de classe » (groupe, `class_sessions`). À nommer distinctement partout pour éviter la confusion.

---

## 4. Règles de visibilité (synthèse)
1. **Carte officielle** : visible si le niveau de l'utilisateur est ≥ au niveau minimum de la carte.
2. **Carte perso** : visible **uniquement** par son propriétaire…
3. …**sauf** si elle est intégrée à une session de classe : les participants la voient **le temps de la session**.
4. **Progression Leitner** : toujours strictement par utilisateur, jamais partagée.

---

## 5. Leitner / répétition espacée

**État actuel (fonctionnel) ✅**
- 3 boîtes : bonne réponse → carte montée d'une boîte ; mauvaise → retour boîte 1.
- Échantillonnage par session : toute la boîte 1, ~½ de la boîte 2, ~¼ de la boîte 3.

**À ajouter — la couche temporelle (le maillon manquant)**
- Définir un intervalle par boîte (ex. boîte 1 = quotidien, boîte 2 = ~3 j, boîte 3 = ~7 j — à calibrer).
- À chaque révision, calculer `next_review_at`.
- La sélection des cartes d'une session priorise les cartes **dues** (`next_review_at` ≤ aujourd'hui).
- Le champ `last_reviewed` existe déjà mais n'est pas exploité : c'est ici qu'il sert.

> Évolution possible plus tard : passer d'intervalles fixes par boîte à un algorithme type **SM-2** (Anki). Non prioritaire.

---

## 6. Sessions de classe (détail)
- **Création** : un membre lance une session (titre, jeu de cartes, deadline).
- **Participation** : asynchrone, dans la fenêtre de temps.
- **Classement** : agrégé à partir de `class_session_results`, figé à la deadline.
- **Effet Leitner** : chaque réponse met à jour `user_card_progress` du participant.
- **Rappels** : s'appuient sur le système de notifications **déjà présent** (`notification_enabled`, `notification_hour`) — ex. « il te reste 12 h pour la session de maths ».
- **Cartes manquées après deadline** : l'élève qui n'a pas participé n'apparaît pas au classement (comportement par défaut, à confirmer).

---

## 7. Notifications
- Champs existants : `notification_enabled`, `notification_hour`.
- Usages : rappel de révision quotidienne + rappels de deadline des sessions de classe.

---

## 8. Génération IA (scan → cartes)

### Objectif
Permettre à l'élève de **scanner une feuille de cours ou une page de manuel** et d'en extraire automatiquement des flashcards, sans avoir à les saisir une à une.

### Principe directeur : l'IA est un **assistant**, pas un nègre
Écrire ses fiches a une vraie valeur d'apprentissage (**effet de génération** : on retient mieux ce qu'on produit soi-même). Le moteur principal de mémorisation reste toutefois la **récupération espacée** (le Leitner), indépendante de qui a créé la carte. La génération IA ne tue donc pas le bénéfice principal — elle supprime un bénéfice secondaire (l'encodage). Conclusion : **garder l'élève dans la boucle cognitive** plutôt que de livrer du tout-fait.

### Deux modes assumés
- **Mode rapide** — tout est généré par l'IA, pour produire du volume vite. L'élève valide en bloc.
- **Mode actif** — l'élève reste impliqué (voir mécaniques ci-dessous). Recommandé pour un vrai apprentissage, mis en avant dans l'app comme argument pédagogique.

### Mécaniques qui gardent l'élève actif (mode actif)
- **L'IA propose, l'élève valide** : les cartes générées arrivent en **brouillon** ; l'élève relit, corrige, garde ou jette chaque carte avant qu'elle entre dans son deck.
  → Bonus : cette étape de validation est **aussi le contrôle qualité** (une carte fausse est attrapée par l'élève au moment de valider).
- **L'élève sélectionne, l'IA met en forme** : l'élève surligne les passages importants ; l'IA les transforme en cartes. Choisir ce qui compte est déjà un acte d'apprentissage.
- **L'IA pose la question, l'élève écrit la réponse** avec ses mots : on garde l'étape génératrice la plus précieuse (reformuler) en supprimant la corvée (recopier).

### Notes techniques
- Faire **lire l'image directement par un modèle multimodal** (l'app passe déjà par un LLM) plutôt qu'OCR-puis-texte : plus robuste sur des manuels mis en page.
- Le **manuscrit** (notes d'élève) est nettement plus difficile à lire que l'imprimé : à tester tôt.
- Chaque scan a un **coût d'appel réel** → bon candidat au palier payant (cf. monétisation).
- Borner le nombre de cartes générées par appel (aujourd'hui non borné).

---

## 9. Chantiers priorisés (roadmap)

### Phase 0 — Assainissement (rapide, débloque tout)
- [x] Retirer `frontend/.metro-cache` du dépôt (16k fichiers commités) + l'ajouter au `.gitignore`.
- [ ] Restreindre le CORS (`allow_origins=["*"]` + `allow_credentials=True` est insécurisé et invalide).
- [ ] Rédiger un vrai README.

### Phase 1 — Fondations du modèle (cœur de la vision)
- [ ] Champ `source` (officiel/perso) sur `flashcards` + scoping des requêtes d'étude.
- [ ] CRUD complet sur les cartes perso : **édition et suppression** (absentes aujourd'hui).
- [ ] Route `/auth/refresh` (le refresh token est généré mais jamais utilisé).
- [ ] Stockage des tokens en `expo-secure-store` plutôt qu'`AsyncStorage` (non chiffré).

### Phase 2 — Leitner complet
- [ ] Couche temporelle (`next_review_at`) + sélection des cartes dues.

### Phase 3 — Sessions de classe asynchrones
- [ ] Collections `class_sessions` + `class_session_results`.
- [ ] Deadline, classement de session, agrégation des résultats.
- [ ] Branchement sur le Leitner perso + rappels via notifications.

### Phase 4 — Extensions
- [ ] Lycée : dimension **spécialité**.
- [ ] Post-bac (pistes séparées).
- [ ] Contenu réel aligné sur les programmes officiels (chantier de contenu à part).
- [ ] **Scan multimodal (image → cartes)** + flux brouillon/validation + modes rapide/actif (cf. §8).
- [ ] Images sur les cartes (schémas SVT/maths), rate-limiting sur `/ai/generate` et `/auth`.

---

## 10. Hors-périmètre v1
- Sessions de classe **synchrones** (temps réel).
- **Post-bac** et **spécialités** lycée (phasés).
- Alignement complet sur les programmes officiels (effort de contenu distinct du code).

---

## 11. Points à trancher ultérieurement
- Calibrage exact des intervalles Leitner par boîte.
- Sort des participants qui ne terminent pas une session avant la deadline.
- Modération du contenu si des cartes perso deviennent partageables à grande échelle.
