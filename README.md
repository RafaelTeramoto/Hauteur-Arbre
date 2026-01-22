# Hauteur-Arbre 🌳

Ce projet est dédié à la mesure dendrométrique par analyse vibratoire. Il utilise des accéléromètres (ADXL1002Z) couplés à un Arduino pour capturer des ondes mécaniques à haute fréquence. Le système permet de visualiser les signaux en temps réel, de détecter des échos et de mesurer le temps de propagation entre deux capteurs avec une précision de l'ordre de la microseconde.

---

## 🚀 Ordre d'Exécution

Pour assurer le bon fonctionnement du système, respectez scrupuleusement cet ordre :

1.  **Matériel** : Connectez votre Arduino et les capteurs aux broches analogiques **A0** et **A1**.
2.  **Firmware** : Ouvrez `pythonsetup.ino` dans l'IDE Arduino et téléversez-le sur la carte. **Cette étape est indispensable** car elle configure la vitesse de communication (2 000 000 bauds) et le formatage des données.
3.  **Analyse** : Une fois le téléversement terminé, fermez l'IDE Arduino et lancez l'un des scripts Python fournis.

---

## 📂 Description des Fichiers

* **`pythonsetup.ino`** : Code source pour l'Arduino. Il gère l'acquisition de données sur deux canaux et applique un lissage par filtre passe-bas.
* **`graphiques.py`** : Permet de visualiser les tensions réelles des deux capteurs en temps réel sous forme de graphique dynamique.
* **`diffcapteurs.py`** : Outil de haute précision pour mesurer le délai (Delta T) entre le passage d'une onde sur le premier capteur et le second.
* **`allerretour.py`** : Spécialisé dans la détection d'échos (onde incidente et réfléchie) sur un seul capteur pour mesurer le temps de trajet.

---

## 🛠️ Mode d'Emploi

1.  **Configuration du port** : Dans chaque fichier Python, vérifiez que la variable `SERIAL_PORT` correspond à votre port (ex: `'COM6'` sur Windows ou `'/dev/ttyUSB0'` sur Linux).
2.  **Prérequis** : Installez les bibliothèques nécessaires via votre terminal :
    ```bash
    pip install pyserial matplotlib numpy scipy
    ```
3.  **Exécution** :
    * Lancez le script : `python diffcapteurs.py`
    * Le script effectuera d'abord un **calibrage automatique** pendant 1 seconde pour mesurer la fréquence d'échantillonnage réelle.
    * Les résultats s'afficheront dans la console ou sur l'interface graphique.

---

## 📈 Détails Techniques

### Acquisition et Transmission
* **Vitesse de transmission** : 2 000 000 bauds pour minimiser la latence de transfert.
* **Filtre numérique** : Un filtre passe-bas (facteur de lissage de 0.5) est intégré au firmware pour atténuer le bruit électronique avant l'envoi.

### Précision du Signal
* **Interpolation Linéaire** : Le script `diffcapteurs.py` utilise une interpolation entre deux points de mesure pour estimer l'instant exact du franchissement du seuil (Trigger). Cela permet une précision temporelle supérieure à la simple période d'échantillonnage.
* **Seuil Dynamique** : Le système utilise un `BIAS_VOLTAGE` de 2.5V (zéro G pour l'ADXL) et un seuil de déclenchement réglable (`THRESHOLD`) pour filtrer les vibrations parasites.

---
*Développé pour des projets d'instrumentation scientifique et de traitement du signal.*
