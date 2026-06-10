**Code testé pour les versions suivantes :**  
Python      : 3.9.21  
PyQt5       : 5.15.9  
PyQt5-Qt5   : 5.15.2  
PyQt5-sip   : 12.13.0  
pygame      : 2.2.0  

→ pip install PyQt5==5.15.9 PyQt5-Qt5==5.15.2 PyQt5-sip==12.13.0 pygame==2.2.0
(pygame==2.6.1 si erreur d'installation avec versions récentes de python)

Pour expérience de jeu normale, mettre la variable DEBUG dans game.config.py sur False, puis lancer le main.py (s'il y a des messages dans la console, alors le débug mode est activé).

Concernant la repartition du travail : Un nom d'auteur est indiqué au debut des codes si jamais il est considéré comme codé grandement (idées et implémentation principale) par l'un des membres du groupe. Une attribution stricte est difficile, étant donne que chacun a été amené à modifier, ajouter ou supprimer le code de l'autre.
Si pas d'auteur precisé: ou bien le code est trop court, ou bien il est trop important et modifié pour donner un auteur clair.

# Fait:
- scene générale avec déplacements
- systeme d’entités - ennemis + joueur
- systeme de salles dans .json
- collisions
- transition de piece
- fonts (polices)
- music
- sfx
- hitboxes
- armes/items
- loi de move pour ennemis + pathfinding
- ecran titre
- ecran de game over
- quelques items (boomerang)
- biomes pour mieux gérer sprites de tiles
- clignotement blanc si invulnérable
- animation de stun
- sauvegarde
- pnj
- boites de dialogues
- systeme d'items + inventaire
- boomerang pickup items
- update de tiles de selon action (explosion, ouverture de porte etc.)
- settings
- hud scene generale
- interrupteur & tiles reagissant a flag
- salles et reste du jeu

# En cours:
- boss final
- quelques ennemis
- quelques quêtes
- équilibrage


# À faire:

- ~~(.exe) - pas obligatoire~~

