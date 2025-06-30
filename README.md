# Introduction 

Base = logiciel isChecker de Safety Data
Projet = tester la faisabilité du développement d'un moteur d'analyse linguistique hybride combinant :
- des règles basées sur des expressions régulières (RegEx) pour les vérifications simples ;
- des requêtes à un LLM (Large Language Model) pour les règles contextuelles ou complexes.

# Mise en place

1.	Installation

```
git clone https://mydavi@dev.azure.com/mydavi/BU%20Recherche/_git/isChecker_tests
cd isChecker_tests
pip install -r requirements.txt
```

2.	Dépendences

- SpaCy : segmentation de texte, détection des entités
- openai 

# Structure

## 1. Upload des données

- Chargement d'un texte brut
- Sélection de la langue d’analyse ⇒ permet de sélectionner les règles spécifiques à cette langue

## 2. Nettoyage et préparation des données

Normalisation du texte :
    - uniformisation des guillemets (simples + doubles), espaces, ponctuation…

Segmentation : 
    - en phrases ⇒ `SpaCy` est plus robuste que `nltk` , notamment pour de l’analyse de textes techniques. Il offre une meilleure détection des entités ;
    - en blocs selon le type (titres, listes à puces, paragraphes, tableaux…) ⇒ permet de prioriser ou d’exclure certains types

## 3. Système des règles linguistiques

Chargement des règles linguistiques définies par catégorie :
    - Alerte/Warning
    - Nombre/Number
    - Liste/List
    - Note/Note
    - Paragraphe/Paragraph
    - Phrase/Sentence
    - Ponctuation/Punctuation
    - Titre/Title
    - Unité/Unit
    - Verbe/Verb
    - Vocabulaire/Vocabulary

Chaque règle contient :
    - Langue de la règle
    - Nom de la règle
    - Sévérité
    - Catégorie de la règle
    - ID de la règle
    - Détail de la règle dans sa langue
    - Message d’erreur dans sa langue
    - Expression régulière (si applicable)
    - Exceptions éventuelles
    - Exemples positifs/négatifs ⇒ *prompt tuning ? fine-tuning ?*
    - Champs llm_required true (si l'analyse nécessite un LLM) ou false
    - RegEx si champs llm_required = false (sinon null)

## 4. Analyse RegEx/LLM hybride

**Règles vérifiées par RegEx**
    - Règles simples comme la vérification de la présence d’une majuscule, d’une ponctuation, etc.

**Règles vérifiées par LLM (requêtes directes à une API) :**
    - Rédaction d’un prompt spécifique pour des analyses plus complexes :
        - *Exemple simplifié : “Voici une règle linguistique : [règle]. Analyse cette phrase : [texte]. Si la règle n'est pas respectée, indique la partie fautive et affiche ce message : [message d'erreur].”*
    - A privilégier pour les règles difficiles à exprimer en RegEx ou nécessitant la prise en compte du contexte (ex : tournures ambigües, mauvaise concordance, temps mal choisis, etc.)
    - Permet d’inclure des ressources

## 5. Rapport d’analyse

Affichage des erreurs détectées avec :
- ligne/position de l'erreur
- élément de texte comportant l'erreur
- règle enfreinte
- message d’erreur
- sévérité de l’erreur

# Evolutions considérées

- Import de documents structurés (DOC(X)/ODT, TXT) ⇒ `python-docx` et `odfpy` / `pypandoc` / `docxcompose`
- Extraction des blocs avec conservation des styles et de la hiérarchie 
    - Titres = début d'une section ou sous-section
    - Paragraphes, listes, tableaux = blocs de contenu
    - Styles typographiques = indicateurs d'importance
    - Balises XML ou métadonnées = informations utiles comme langue, auteur, statut du texte, etc.
- Segmentation en blocs avec tag de chaque bloc par un label (`TITLE`, `PARAGRAPH`, `LIST`, `TABLE`, etc.) pour faciliter l’application conditionnelle des règles
- Option d'activation/désactivation des règles (par profil, catégorie, etc.)
- Format d’export de rapport : `.tsv`
- Document annoté avec les erreurs (dans une copie du document d'origine).
- Calcul d’un score global ou par catégorie, utile pour créer des tableaux de bord.