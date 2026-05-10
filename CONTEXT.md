# Recherche d'offres d'emploi

Application d'agregation d'offres d'emploi issues de plusieurs sources, afin de comparer des annonces normalisees a partir d'une meme recherche.

## Language

**Offre d'emploi**:
Une annonce individuelle publiee par une organisation pour recruter sur un poste.
_Avoid_: Job, annonce

**Source d'offres**:
Un site ou service depuis lequel l'application recupere des offres d'emploi.
_Avoid_: Moteur de recherche, plateforme

**Source maintenable**:
Une source d'offres que l'application peut interroger via un acces autorise et techniquement stable.
_Avoid_: Source scrapable, source disponible

**Source prioritaire MVP**:
Une source maintenable candidate a l'integration dans la premiere version utile de l'application.
_Avoid_: Source MVP, source principale

**Source candidate phase 2**:
Une source d'offres pertinente mais non prioritaire pour le MVP, a evaluer apres les sources prioritaires.
_Avoid_: Source secondaire, source plus tard

**Perimetre geographique MVP**:
La limite du MVP aux offres d'emploi en France recherchees par localisation et rayon.
_Avoid_: France, recherche locale

**Recherche d'offres**:
Une demande composee d'un intitule de poste, d'une localisation et d'un rayon geographique.
_Avoid_: Requete, filtre

**Session de recherche**:
Une execution ponctuelle d'une recherche d'offres lancee a la demande.
_Avoid_: Alerte, recherche sauvegardee

**Resultat d'offre**:
La version normalisee d'une offre d'emploi affichee dans l'application apres recuperation depuis une source d'offres.
_Avoid_: Resultat, job card

**Identite de resultat**:
La cle qui reconnait un resultat d'offre comme le meme entre deux sessions, fondee sur sa source d'offres et son URL canonique ou identifiant source.
_Avoid_: Identite d'offre, cle de deduplication globale

**Date de publication**:
La date a laquelle une offre d'emploi a ete publiee, normalisee quand la source la fournit ou permet de la deduire.
_Avoid_: Date, date de mise a jour

**Entreprise**:
L'organisation qui recrute ou publie l'offre d'emploi, telle qu'elle est indiquee par la source d'offres.
_Avoid_: Recruteur, client

**Remuneration indiquee**:
Le salaire ou la fourchette de salaire publie par la source d'offres pour une offre d'emploi.
_Avoid_: Salaire, package

**Offre nouvelle**:
Un resultat d'offre absent de la session precedente pour la meme recherche d'offres.
_Avoid_: Nouvelle annonce, nouveaute

**Offre consultee**:
Un resultat d'offre dont le lien source a ete ouvert depuis l'application.
_Avoid_: Offre vue, offre lue

**Offre favorite**:
Un resultat d'offre que l'utilisateur a marque pour le retrouver facilement.
_Avoid_: Offre etoilee, offre cochee

**Offre inactive**:
Un resultat d'offre deja connu qui n'apparait plus dans les sessions recentes ou n'est plus retourne par sa source d'offres.
_Avoid_: Offre expiree, offre supprimee

**Vue favoris**:
L'ecran qui regroupe les resultats d'offre marques comme favoris par l'utilisateur principal.
_Avoid_: Liste etoilee, favoris

**Tri des favoris**:
L'ordre choisi par l'utilisateur pour afficher la vue favoris.
_Avoid_: Tri favoris, ordre des etoiles

**Recherche recente**:
Une recherche d'offres deja utilisee que l'utilisateur peut relancer depuis l'application.
_Avoid_: Historique, session sauvegardee

**Stockage applicatif**:
La persistance cote application des recherches, resultats et etats utilisateur du MVP.
_Avoid_: Cache navigateur, stockage local

**Application deployee**:
L'application web installee sur un VPS pour etre accessible a distance par l'utilisateur principal.
_Avoid_: Application locale, script local

**Acces protege**:
La protection de l'application deployee par exposition reseau limitee et mot de passe utilisateur.
_Avoid_: Authentification multi-utilisateur, compte

**Connecteur de source**:
Le composant qui interroge une source d'offres et retourne des resultats d'offre normalises.
_Avoid_: Scraper, client API

**Echec de source**:
L'indisponibilite ou l'erreur d'une source d'offres pendant une session de recherche.
_Avoid_: Erreur, panne

**Niveau d'experience demande**:
La classe d'experience attendue pour un resultat d'offre, deduite ou fournie par la source.
_Avoid_: Seniorite, experience

**Niveau de diplome demande**:
Le niveau de diplome attendu pour un resultat d'offre, deduit ou fourni par la source.
_Avoid_: Diplome, formation

**Tag de competence**:
Une competence informatique detectee dans une offre d'emploi a partir d'un dictionnaire configurable.
_Avoid_: Resume de competence, skill

**Description source**:
Le descriptif d'une offre d'emploi tel qu'il est fourni par la source d'offres.
_Avoid_: Resume, description generee

**Filtre de resultats**:
Un critere applique apres aggregation sur les resultats d'offre normalises.
_Avoid_: Critere de recherche, filtre source

**Type de contrat recherche**:
La categorie contractuelle d'une offre d'emploi incluse ou exclue dans les resultats du MVP.
_Avoid_: Contrat, condition

**Rayon demande**:
La distance autour de la localisation choisie par l'utilisateur pour une recherche d'offres.
_Avoid_: Distance, perimetre

**Rayon source**:
Le rayon effectivement envoye a une source d'offres selon les valeurs qu'elle supporte.
_Avoid_: Rayon utilise, distance source

**Tri par fraicheur**:
L'ordre d'affichage qui place les resultats d'offre les plus recents en premier.
_Avoid_: Tri par defaut, tri chronologique

**Utilisateur principal**:
La personne unique qui utilise l'application dans le MVP.
_Avoid_: Compte, profil

## Relationships

- Une **Recherche d'offres** interroge une ou plusieurs **Sources d'offres**
- Une **Recherche d'offres** utilise l'intitule du poste, la localisation et le rayon pour interroger les **Sources d'offres**
- Le **Rayon source** est le **Rayon demande** quand la source le supporte, sinon le plus petit rayon superieur supporte par cette source
- Une **Recherche d'offres** produit une **Session de recherche** lorsqu'elle est lancee
- Une **Recherche recente** represente une **Recherche d'offres** relancable, pas une session individuelle
- Une **Source d'offres** doit etre une **Source maintenable** pour etre integree
- Une **Source prioritaire MVP** est evaluee avant les autres sources candidates
- Une **Source candidate phase 2** est evaluee apres validation du MVP
- Une **Source d'offres** integree possede un **Connecteur de source**
- Un **Echec de source** n'empeche pas une **Session de recherche** de retourner les resultats des autres sources
- Le **Perimetre geographique MVP** limite les recherches aux offres en France avec localisation et rayon
- Une **Source d'offres** peut produire zero, une ou plusieurs **Offres d'emploi**
- Une **Session de recherche** contient zero, un ou plusieurs **Resultats d'offre**
- Le **Stockage applicatif** conserve les **Sessions de recherche**, **Resultats d'offre**, **Offres consultees**, **Offres favorites** et **Recherches recentes**
- Une **Application deployee** heberge le **Stockage applicatif** et l'interface web du MVP
- Une **Application deployee** utilise un **Acces protege**
- Un **Filtre de resultats** s'applique apres aggregation sur les **Resultats d'offre**
- Le **Tri par fraicheur** est l'ordre d'affichage par defaut des **Resultats d'offre**
- Une **Offre d'emploi** devient un **Resultat d'offre** lorsqu'elle est normalisee pour l'affichage
- Un **Resultat d'offre** possede une **Identite de resultat**
- Un **Resultat d'offre** peut avoir une **Date de publication**
- Un **Resultat d'offre** peut avoir une **Entreprise**
- Un **Resultat d'offre** peut avoir une **Remuneration indiquee**
- Un **Resultat d'offre** peut avoir un **Type de contrat recherche**
- Un **Resultat d'offre** peut etre une **Offre nouvelle**
- Un **Resultat d'offre** peut etre une **Offre consultee**
- Un **Resultat d'offre** peut etre une **Offre favorite**
- Un **Resultat d'offre** peut devenir une **Offre inactive**
- La **Vue favoris** affiche les **Offres favorites** de l'**Utilisateur principal**
- La **Vue favoris** utilise un **Tri des favoris** choisi par l'utilisateur
- Un **Resultat d'offre** peut avoir un **Niveau d'experience demande**
- Un **Resultat d'offre** peut avoir un **Niveau de diplome demande**
- Un **Resultat d'offre** peut afficher des **Tags de competence**
- Un **Resultat d'offre** ouvre son lien source lorsque l'utilisateur le selectionne
- L'**Utilisateur principal** possede les **Offres consultees** et les **Offres favorites** du MVP

## Example dialogue

> **Dev:** "Quand l'utilisateur lance une **Recherche d'offres**, est-ce qu'on affiche les annonces separement par **Source d'offres** ?"
> **Domain expert:** "Non, l'objectif est une liste agregee de **Resultats d'offre** comparables, quelle que soit la source."
> **Dev:** "Est-ce qu'on doit integrer LinkedIn meme si l'acces automatise est fragile ?"
> **Domain expert:** "Non, une **Source d'offres** n'est integree que si elle est une **Source maintenable**."
> **Dev:** "Est-ce qu'une **Recherche d'offres** tourne automatiquement tous les jours ?"
> **Domain expert:** "Non, pour le MVP elle produit une **Session de recherche** uniquement quand l'utilisateur la lance."
> **Dev:** "Est-ce qu'une etoile veut dire que l'utilisateur a postule ?"
> **Domain expert:** "Non, l'etoile marque seulement une **Offre favorite**."
> **Dev:** "Quand l'utilisateur ouvre l'annonce complete sur la source, est-ce que le **Resultat d'offre** devient une **Offre consultee** ?"
> **Domain expert:** "Oui, consulter une offre signifie ouvrir son lien source depuis l'application."
> **Dev:** "Si la meme annonce apparait sur deux sources, est-ce qu'elle partage automatiquement ses favoris et son statut consulte ?"
> **Domain expert:** "Non, pour le MVP ces etats suivent l'**Identite de resultat**, donc la source et l'URL ou identifiant source."
> **Dev:** "Faut-il isoler les favoris par compte utilisateur ?"
> **Domain expert:** "Non, le MVP a un seul **Utilisateur principal** et ne gere pas de comptes."
> **Dev:** "Si une annonce ne precise pas l'experience attendue, est-elle exclue des filtres ?"
> **Domain expert:** "Non, son **Niveau d'experience demande** est 'Non precise'."
> **Dev:** "Est-ce qu'on filtre par type de formation comme ecole d'ingenieur ou cybersecurite ?"
> **Domain expert:** "Non, pour le MVP on filtre par **Niveau de diplome demande**; le type de formation reste dans le resume."
> **Dev:** "Est-ce que l'experience et le diplome sont envoyes aux sources comme criteres de recherche ?"
> **Domain expert:** "Non, ce sont des **Filtres de resultats** appliques apres aggregation."
> **Dev:** "Si une source ne supporte pas le **Rayon demande**, faut-il ignorer cette source ?"
> **Domain expert:** "Non, on utilise le plus petit **Rayon source** superieur supporte par la source."
> **Dev:** "Quelles sources faut-il evaluer en premier ?"
> **Domain expert:** "Les **Sources prioritaires MVP** sont France Travail, Adzuna, Jooble, Careerjet / Optioncarriere et Jobijoba."
> **Dev:** "Faut-il bloquer le MVP sur Glassdoor ou Monster ?"
> **Domain expert:** "Non, Glassdoor et Monster sont des **Sources candidates phase 2**."
> **Dev:** "Une offre full remote Europe doit-elle apparaitre dans une recherche Nantes + 30 km ?"
> **Domain expert:** "Non, le MVP respecte le **Perimetre geographique MVP**; le remote international viendra plus tard."
> **Dev:** "Les stages et alternances sont-ils affiches par defaut ?"
> **Domain expert:** "Non, le MVP inclut CDI, CDD, Freelance et Interim; il exclut Stage et Alternance."
> **Dev:** "Faut-il generer un resume de l'offre avec l'IA ?"
> **Domain expert:** "Non, la liste affiche des **Tags de competence** detectes; selectionner l'offre ouvre directement son lien source."
> **Dev:** "Les **Offres nouvelles** passent-elles avant les offres plus recentes ?"
> **Domain expert:** "Non, l'affichage par defaut utilise le **Tri par fraicheur**."
> **Dev:** "Si la source affiche 'hier', faut-il stocker le texte brut ?"
> **Domain expert:** "Non, on le convertit en **Date de publication** quand c'est possible; sinon la date reste non precisee."
> **Dev:** "Si une offre est publiee par un cabinet de recrutement, quelle **Entreprise** affiche-t-on ?"
> **Domain expert:** "On affiche l'organisation indiquee publiquement par la source, qu'il s'agisse du cabinet ou du client final."
> **Dev:** "Faut-il filtrer les offres par salaire dans le MVP ?"
> **Domain expert:** "Non, la **Remuneration indiquee** est seulement affichee quand elle est disponible."
> **Dev:** "Une offre favorite disparait-elle si elle n'est plus retournee par la source ?"
> **Domain expert:** "Non, elle reste une **Offre favorite** et peut devenir une **Offre inactive**."
> **Dev:** "L'etoile sert-elle seulement dans la liste de recherche courante ?"
> **Domain expert:** "Non, la **Vue favoris** permet de retrouver les **Offres favorites**."
> **Dev:** "La **Vue favoris** est-elle toujours triee par date de publication ?"
> **Domain expert:** "Non, l'utilisateur choisit le **Tri des favoris** entre date d'ajout en favori et date de publication."
> **Dev:** "Faut-il afficher toutes les anciennes **Sessions de recherche** ?"
> **Domain expert:** "Non, le MVP affiche des **Recherches recentes** que l'utilisateur peut relancer."
> **Dev:** "Les favoris peuvent-ils etre stockes seulement dans le navigateur ?"
> **Domain expert:** "Non, le MVP utilise un **Stockage applicatif** persistant cote application."
> **Dev:** "L'application est-elle seulement un outil local lance sur l'ordinateur ?"
> **Domain expert:** "Non, c'est une **Application deployee** sur un VPS pour l'utilisateur principal."
> **Dev:** "Le VPN WireGuard suffit-il a remplacer le mot de passe ?"
> **Domain expert:** "Non, le MVP utilise un **Acces protege** avec exposition initiale sur l'interface WireGuard et mot de passe."
> **Dev:** "Chaque source doit-elle appliquer elle-meme les tags et niveaux demandes ?"
> **Domain expert:** "Non, chaque **Connecteur de source** retourne des resultats normalises; les enrichissements communs sont appliques ensuite."
> **Dev:** "Si Jobijoba ne repond pas, faut-il annuler toute la **Session de recherche** ?"
> **Domain expert:** "Non, on affiche les resultats disponibles et on signale l'**Echec de source**."

## Flagged ambiguities

- "moteur de recherche d'emploi" designe ici une **Source d'offres**, pas un moteur de recherche generaliste.
- "recherche" designe les criteres saisis; une execution concrete est une **Session de recherche**.
- "etoile" designe le marquage d'une **Offre favorite**, pas un statut de candidature.
- "nouvelle depuis ma derniere visite" se mesure par rapport a la session precedente de la meme **Recherche d'offres**, pas par rapport a la derniere ouverture globale de l'application.
- La reconnaissance d'une offre entre sessions repose d'abord sur l'**Identite de resultat**, pas sur une deduplication globale entre sources.
- "utilisateur" designe l'**Utilisateur principal** du MVP, pas un compte authentifie.
- Le **Niveau d'experience demande** utilise les valeurs Debutant (0-1 an), Confirme (1-3 ans), Avance (3-5 ans), Senior (5+ ans) et Non precise.
- Le **Niveau de diplome demande** utilise les valeurs Non precise, Aucun diplome requis, Bac, Bac+2, Bac+3, Bac+5 et Doctorat.
- "filtre" designe un **Filtre de resultats** quand il porte sur l'experience ou le diplome; les criteres envoyes aux sources restent l'intitule, la localisation et le rayon.
- Le rayon transmis a une source peut etre superieur au **Rayon demande** si la source ne supporte pas exactement la valeur demandee.
- Le **Rayon demande** utilise une liste fixe: 10 km, 20 km, 30 km, 50 km et 100 km.
- Les **Sources prioritaires MVP** sont France Travail, Adzuna, Jooble, Careerjet / Optioncarriere et Jobijoba.
- Les **Sources candidates phase 2** incluent Hellowork, Meteojob, Apec, LesJeudis, Talent.com, Welcome to the Jungle, Glassdoor et Monster.
- Le MVP exclut les sources purement remote Europe ou internationales sauf si elles peuvent respecter le **Perimetre geographique MVP**.
- Les **Types de contrat recherche** inclus par defaut sont CDI, CDD, Freelance et Interim; Stage et Alternance sont exclus du MVP par defaut.
- Le teletravail peut etre affiche si une source le fournit, mais il n'est pas un **Filtre de resultats** du MVP.
- Les competences affichees dans la liste sont des **Tags de competence** detectes par dictionnaire; le MVP ne cree pas de page detail interne et ouvre directement l'offre sur sa source.
- La **Description source** n'est pas stockee par defaut dans le MVP, sauf si elle est deja fournie dans la reponse de recherche sans appel supplementaire.
- "tri par defaut" designe le **Tri par fraicheur**, c'est-a-dire la date de publication la plus recente d'abord.
- Une **Date de publication** inconnue est affichee comme non precisee et triee apres les resultats dates.
- L'**Entreprise** est affichee quand elle est disponible; si la source ne revele qu'un cabinet de recrutement, ce cabinet est l'entreprise affichee.
- La **Remuneration indiquee** est facultative et n'est pas un **Filtre de resultats** du MVP.
- Les etats **Offre favorite** et **Offre consultee** sont conserves meme si le resultat devient une **Offre inactive**.
- Le MVP inclut une **Vue favoris** dediee.
- Le **Tri des favoris** permet de trier par date d'ajout en favori la plus recente d'abord ou par date de publication la plus recente d'abord.
- Le **Tri des favoris** par defaut est la date d'ajout en favori la plus recente d'abord.
- Le MVP inclut des **Recherches recentes** relancables, mais pas une vue detaillee de toutes les **Sessions de recherche**.
- Le MVP affiche au maximum 10 **Recherches recentes**, triees par derniere utilisation; relancer une recherche identique la remonte sans creer de doublon.
- Le MVP utilise un **Stockage applicatif** persistant, pas uniquement un cache ou stockage navigateur.
- Le MVP est une **Application deployee** sur un VPS, tout en restant mono-utilisateur.
- L'**Acces protege** du MVP combine une exposition initiale sur l'interface VPN WireGuard du VPS et un mot de passe unique.
- Chaque source integree est isolee dans un **Connecteur de source** qui retourne un format commun de **Resultat d'offre**.
- Un **Echec de source** est signale a l'utilisateur et ne rend pas inactives les offres deja connues de cette source.
