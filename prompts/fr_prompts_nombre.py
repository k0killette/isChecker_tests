PROMPTS_NOMBRE = {
    "SD-08.01": 
        """
        CONSIGNE : 
            Analyse le texte et identifie les cas suivants :
                - Une quantité écrite en lettres, comme "vingt-trois", "quatre-vingts" ;
                - Une date écrite en toutes lettres, comme "huit janvier", "quatorze juillet" ;
                - Une valeur ordinale écrite en lettres, comme "cinquième", "premier".
            Pour chaque cas renvoie le message d'erreur en remplaçant `X` par l’un des trois types :
                - `"quantité"` si c’est une quantité ;
                - `"date"` si c’est une date ;
                - `"valeur ordinale"` si c’est un ordinal.
            Ignore les nombres déjà écrits en chiffres, même s’ils ne comportent pas d’espace ou de séparation.
        EXEMPLES : 
            - "quatorze" → "Une quantité est écrite en lettres." ;
            - "premier janvier" → "Une date est écrite en lettres." ;
            - "cinquième" → "Une valeur ordinale est écrite en lettres.".
        """
    ,
    "SD-08.04": 
        """
        CONSIGNE : 
            Vérifie que les grands nombres (à partir de 4 chiffres) sont écrits correctement = utilisation d’une espace insécable tous les 3 chiffres.
            Considère comme erreurs les cas suivants :
                - Le nombre ne contient aucun espace (ex. : "1000", "2000000") ;
                - Le nombre est mal segmenté (ex. : "12 3456", "1 00 000").
            Pour chaque nombre incorrect, renvoie le message d’erreur fourni via `error_mesg`.
        EXEMPLES : 
            - "1000" → erreur ;
            - "12 3456" → erreur ;
            - "1 000" → correct.
        """
}

