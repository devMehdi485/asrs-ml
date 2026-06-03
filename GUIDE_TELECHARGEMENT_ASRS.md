# Guide pas-à-pas — Télécharger le dataset NASA ASRS (CSV)

Objectif : exporter un fichier `ASRS_export.csv` depuis l'outil officiel **ASRS Database Online**
et le placer dans le projet pour que le pipeline NLP l'utilise.

⏱️ Durée : ~3 à 5 minutes. Aucun compte requis.

📁 Destination finale du fichier :
```
C:\Users\LENOVO\Documents\Licorne\ASRS ML\data\ASRS_export.csv
```

---

## 0. Préparation (important)

- **Désactive le bloqueur de pop-up** pour le site, sinon les fenêtres de sélection ne s'ouvriront pas.
  - Dans Chrome : pendant que tu es sur la page ASRS, clique l'icône 🔒 (ou ⚙️) à gauche de la barre
    d'adresse → **Paramètres du site** → **Pop-up et redirections** → **Autoriser**.
  - Ou, quand une pop-up est bloquée, une petite icône apparaît à droite de la barre d'adresse :
    clique-la et choisis **« Toujours autoriser les pop-up de ce site »**.

---

## 1. Ouvrir l'outil de recherche

1. Va sur **https://asrs.arc.nasa.gov/search/database.html**
2. Clique le bouton **« Start Search »** (au centre de la page).
3. Une nouvelle fenêtre/onglet s'ouvre : **« ASRS Database Online - Query Filter »**
   (URL commençant par `akama.arc.nasa.gov/ASRSDBOnline/`). C'est l'assistant de requête.

> L'assistant a 3 étapes en haut : **Begin → Results → View**. On part de **Begin**.

---

## 2. Ajouter un critère de date (pour borner le volume)

L'export est limité à **10 000 rapports**. On borne donc par une plage de dates.

1. Dans la section **« Date & Report Number »**, repère la ligne
   **« Date of Incident was between [date] and [date] »**.
2. Clique le petit **⊕** (icône verte ronde) juste à gauche de cette ligne.
   → La ligne s'ajoute en bas dans **« Current Search Items »** sous la forme :
   *« Date of Incident was between **Click Here** and **Click Here** »*.

---

## 3. Choisir la plage de dates

1. Dans **« Current Search Items »**, clique le **premier « Click Here »**.
   → Une petite fenêtre **« Add values from the list below »** s'ouvre avec :
   - **Begin Date** : deux menus déroulants (année, mois)
   - **End Date** : deux menus déroulants (année, mois)
2. Règle par exemple :
   - **Begin Date** : `2023` / `January`
   - **End Date** : `2024` / `December`
3. Clique **Save** (bouton bleu dans la fenêtre).
   → La fenêtre se ferme et les dates remplacent les « Click Here ».

> 📌 Note ASRS : « un rapport n'est généralement consultable qu'au moins 60 jours après sa réception ».
> Évite donc les 2-3 derniers mois (peu ou pas de données récentes).

> 💡 Tu peux choisir une autre plage. Plus elle est large, plus il y a de rapports
> (et plus le risque de dépasser 10 000). Une plage de **1 à 2 ans** est un bon point de départ.

---

## 4. Lancer la recherche

1. Clique **« Run Search »** (bouton bleu en bas à droite de l'assistant).
2. Tu arrives sur l'étape **Results** : le **nombre de rapports trouvés** s'affiche.

### ⚠️ Si le nombre dépasse 10 000
- Clique **« Back »** et **réduis la plage** de dates (ex. une seule année, ou 6 mois),
  puis relance **Run Search**. Recommence jusqu'à passer **sous 10 000**.

### Si le nombre est très faible (quelques dizaines)
- La plage est probablement trop récente (règle des 60 jours) ou trop étroite :
  élargis vers des années antérieures (2022, 2021…).

---

## 5. Exporter en CSV

1. Passe à l'étape **« View »** (en haut) **ou** repère sur la page Results la zone
   **téléchargement / export** (intitulé proche de *Download*, *Export*, ou une icône d'enregistrement).
2. Choisis le format **CSV** (l'outil propose aussi Word `.doc` et Excel `.xls` — prends **CSV**).
3. Si on te propose de **choisir les champs (colonnes)** à inclure, garde **au minimum** :
   - **Narrative** (Reporter 1) — *indispensable*
   - **Narrative** (Reporter 2) — si disponible
   - **Synopsis**
   - **Date** (Time / Date)
   - **Anomaly** (Events)
   - **Flight Phase** (Aircraft)
   - **Make/Model** (Aircraft)
   - **Flight Conditions / Weather**, **Detector**, **Primary Problem** — utiles, optionnels

   > Tu peux aussi laisser **tous les champs cochés** : le pipeline repère automatiquement
   > les colonnes dont il a besoin. Garde simplement les narratives et la date.
4. Valide → le navigateur **télécharge un fichier** (souvent nommé `ASRSdbonline...csv`
   ou similaire, dans ton dossier **Téléchargements**).

---

## 6. Placer le fichier dans le projet

1. Ouvre l'Explorateur de fichiers sur ton dossier **Téléchargements**.
2. **Renomme** le fichier téléchargé en `ASRS_export.csv`.
3. **Déplace-le** vers :
   ```
   C:\Users\LENOVO\Documents\Licorne\ASRS ML\data\
   ```
   Il doit **remplacer** le fichier `ASRS_export.csv` synthétique déjà présent
   (réponds « Remplacer » si Windows le demande).

---

## 7. Me prévenir

Reviens dans la conversation et écris simplement **« c'est fait »**.

Je reprends alors **automatiquement**, sans action de ta part :
- chargement du vrai CSV (le double en-tête ASRS est déjà géré) ;
- vérification du mapping des colonnes (j'affiche ce qui a été détecté) ;
- ré-exécution complète du notebook (`asrs_nlp_analysis.ipynb`) ;
- régénération des artefacts + contrôle des 5 pages du dashboard.

---

## Dépannage rapide

| Problème | Solution |
|---|---|
| La fenêtre de dates ne s'ouvre pas | Bloqueur de pop-up actif → autorise les pop-up (voir §0), puis reclique « Click Here ». |
| « Run Search » ne fait rien | Vérifie qu'une plage de dates est bien affichée (pas « Click Here ») dans Current Search Items. |
| Plus de 10 000 résultats | Back → réduire la plage de dates → Run Search. |
| Pas d'option CSV visible | Cherche un bouton/menu *Download* ou *Export* sur la page Results/View ; le format CSV y est proposé. |
| Fichier .xls téléchargé par erreur | Recommence l'export en sélectionnant bien **CSV** (Comma Separated Value). |
| Le CSV s'ouvre bizarrement dans Excel | C'est normal (Excel interprète mal le double en-tête) ; le pipeline, lui, le lit correctement. Ne le ré-enregistre pas depuis Excel. |
```
