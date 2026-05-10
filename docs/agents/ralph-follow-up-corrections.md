# Corrections de suivi Ralph

Cette note décrit comment corriger un bug découvert après une implémentation lancée avec `scripts/ralph-next-issue.sh`.

## Principe

`scripts/ralph-next-issue.sh` sert à sélectionner une nouvelle issue `ready-for-agent`, créer une nouvelle branche `agent/issue-<numero>-<timestamp>`, puis lancer Codex dans la sandbox Docker.

Pour corriger un bug sur une implémentation déjà poussée, ne relance pas automatiquement `scripts/ralph-next-issue.sh`.

- Si le PR est encore ouvert, reprends la branche du PR existant dans la sandbox `mirandole-001`.
- Si le PR a déjà été mergé et clôturé, crée un nouveau correctif depuis la branche cible à jour.

## Cas 1: PR encore ouvert

## Retrouver le PR et la branche

Consulte l'issue ou les PR ouverts :

```bash
gh issue view <issue> --repo mirandole/mirandole-001 --comments
gh pr list --repo mirandole/mirandole-001 --head 'agent/issue-<issue>-*'
```

Le commentaire `RALPH_STATUS: PR_OPEN` contient normalement le lien du PR.

## Ouvrir Codex sur la branche existante

Pour travailler toi-meme avec Codex ouvert dans la sandbox, lance le mode interactif en indiquant explicitement la branche du PR :

```bash
sbx run \
  --branch agent/issue-123-20260510-153000 \
  mirandole-001 \
  -- --sandbox workspace-write
```

Tu peux aussi fournir un prompt initial tout en gardant Codex ouvert :

```bash
sbx run \
  --branch agent/issue-123-20260510-153000 \
  mirandole-001 \
  -- --sandbox workspace-write \
  "Tu corriges le PR de l'issue #123.

Reprends la branche existante, ne demarre pas une nouvelle issue.
Lis AGENTS.md, CONTEXT.md et les docs agents pertinentes.

Bug observe:
- ...

Etapes de reproduction:
- ...

Resultat attendu:
- ..."
```

`codex exec` est reserve au mode non interactif. Si tu l'utilises, le prompt est obligatoire :

```bash
sbx run \
  --branch agent/issue-123-20260510-153000 \
  mirandole-001 \
  -- exec \
  --sandbox workspace-write \
  "Tu corriges le PR de l'issue #123.

Reprends la branche existante, ne demarre pas une nouvelle issue.
Lis AGENTS.md, CONTEXT.md et les docs agents pertinentes.

Bug observe:
- ...

Etapes de reproduction:
- ...

Resultat attendu:
- ...

Fais une correction minimale, ajoute ou ajuste les tests utiles, lance les checks pertinents, commit et push sur la meme branche. Ne merge pas le PR."
```

## Informations a donner a Codex

Pour une correction efficace, fournis :

- l'issue concernee ;
- le lien du PR ;
- le nom exact de la branche ;
- la commande ou le parcours qui echoue ;
- l'erreur complete ;
- le comportement attendu ;
- la contrainte de correction minimale, sans refactor hors sujet.

Exemple :

```text
Issue: #123
PR: https://github.com/mirandole/mirandole-001/pull/456
Branche: agent/issue-123-20260510-153000
Commande qui echoue: uv run pytest tests/test_example.py
Erreur complete: ...
Comportement attendu: ...
Contrainte: correction minimale, pas de refactor hors sujet.
```

## Apres correction

Codex doit pousser la correction sur la meme branche et laisser le PR ouvert :

```bash
git status
# modifier le code
# lancer les tests, le lint, le typecheck ou les checks pertinents
git commit -m "Fix issue #123 follow-up bug"
git push
gh issue comment 123 --repo mirandole/mirandole-001 --body "RALPH_STATUS: PR_OPEN

Follow-up fix pushed to the existing PR.

Checks run:
- ..."
```

Ne merge pas le PR et ne ferme pas l'issue sauf demande explicite.

## Cas 2: PR deja merge et cloture

Quand le PR a deja ete merge et que l'issue d'origine est cloturee, ne pousse pas de correction sur l'ancienne branche du PR. Elle ne represente plus le flux de travail actif.

Travaille plutot avec une nouvelle branche de correction depuis la branche cible a jour, puis ouvre un nouveau PR.

## Creer ou identifier l'issue de correction

Si le bug est mineur et deja documente dans une nouvelle issue, utilise cette issue.

Sinon, cree une issue de suivi qui reference l'issue ou le PR d'origine :

```bash
gh issue create \
  --repo mirandole/mirandole-001 \
  --title "Fix follow-up bug after issue #123" \
  --body "Follow-up bug discovered after #123 was merged.

Original issue: #123
Original PR: #456

Bug observed:
- ...

Steps to reproduce:
- ...

Expected behavior:
- ..."
```

Utilise ensuite le numero de cette nouvelle issue pour le correctif. Ne rouvre l'issue d'origine que si un humain le demande explicitement.

## Lancer Codex sur une nouvelle branche de correction

Choisis un nom de branche explicite, par exemple :

```text
agent/fix-issue-123-follow-up-20260510-153000
```

Puis ouvre Codex dans `sbx` avec cette branche :

```bash
sbx run \
  --branch agent/fix-issue-123-follow-up-20260510-153000 \
  mirandole-001 \
  -- --sandbox workspace-write
```

Pour un lancement non interactif, utilise `codex exec` avec un prompt explicite :

```bash
sbx run \
  --branch agent/fix-issue-123-follow-up-20260510-153000 \
  mirandole-001 \
  -- exec \
  --sandbox workspace-write \
  "Tu corriges un bug decouvert apres merge du PR de l'issue #123.

Le PR d'origine est deja merge et cloture. Ne modifie pas l'ancienne branche.
Pars de la branche cible a jour du repo.
Lis AGENTS.md, CONTEXT.md et les docs agents pertinentes.

Issue de suivi: #789
Issue d'origine: #123
PR d'origine: #456

Bug observe:
- ...

Etapes de reproduction:
- ...

Resultat attendu:
- ...

Fais une correction minimale, ajoute ou ajuste les tests utiles, lance les checks pertinents, commit et push sur cette nouvelle branche. Ouvre un draft PR lie a l'issue de suivi #789. Ne merge pas le PR."
```

## Apres le correctif merge-post-PR

Codex doit ouvrir un nouveau PR, lie a l'issue de suivi :

```bash
git status
# modifier le code
# lancer les tests, le lint, le typecheck ou les checks pertinents
git commit -m "Fix follow-up bug after issue #123"
git push
gh pr create \
  --repo mirandole/mirandole-001 \
  --draft \
  --title "Fix follow-up bug after issue #123" \
  --body "Fixes #789

Follow-up to #123 / #456.

Checks run:
- ..."
gh issue comment 789 --repo mirandole/mirandole-001 --body "RALPH_STATUS: PR_OPEN

Follow-up fix opened after the original PR was merged.

Checks run:
- ..."
```

Le principe important est la tracabilite : un bug decouvert apres merge devient un nouveau changement, avec sa propre branche, son propre PR et, idealement, sa propre issue de suivi.
