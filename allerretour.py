import serial
import time
import collections
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from scipy.signal import find_peaks

# --- CONFIGURATIONS ---
SERIAL_PORT = 'COM6'   # <--- VÉRIFIEZ VOTRE PORT
BAUD_RATE = 2000000    
MAX_SAMPLES = 2000     # Fenêtre de visualisation sur le graphique

# --- PARAMÈTRES PHYSIQUES DU CAPTEUR ---
V_REF = 5.0            
ADC_RES = 1023.0       
BIAS = 2.5             # Tension de repos (Zéro G)

# --- CONFIGURATION DE DÉTECTION D'ÉCHO (RÉGLAGE PRÉCIS) ---
# Tension minimale (au-dessus ou en dessous du Bias) pour considérer qu'il y a eu un impact
THRESHOLD_VOLTAGE = 0.15  

# Distance minimale entre les pics pour considérer qu'il s'agit d'ondes différentes (et non du bruit de la même onde)
# Si le retour est TRÈS proche, diminuez cette valeur. Si vous détectez des faux positifs, augmentez-la.
MIN_DISTANCE_MS = 2.0  # En millisecondes (ex : n'accepte pas d'échos inférieurs à 2ms)

# --- CALIBRAGE AUTOMATIQUE DU TEMPS ---
def calibrate_samplerate(ser_conn):
    print("--- Calibrage du Taux d'Échantillonnage (Attendez 1s)... ---")
    # Nettoyage du buffer
    ser_conn.reset_input_buffer()
    start_time = time.time()
    count = 0
    # Lecture pendant exactement 1 seconde
    while time.time() - start_time < 1.0:
        if ser_conn.in_waiting:
            ser_conn.readline()
            count += 1
    
    real_fs = count
    if real_fs == 0:
        print("ERREUR : Aucune donnée reçue. Vérifiez les connexions.")
        exit()
        
    print(f"Taux d'Échantillonnage Mesuré : {real_fs} Hz")
    print(f"Résolution temporelle : {1000/real_fs:.4f} ms par échantillon")
    print("-------------------------------------------------------")
    return real_fs

# --- INITIALISATION SÉRIE ---
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.01)
    time.sleep(2)
    ser.reset_input_buffer()
except Exception as e:
    print(f"Erreur lors de la connexion : {e}")
    exit()

# Calibrage FS
FS = calibrate_samplerate(ser)
SAMPLES_TO_MS = 1000.0 / FS
MIN_DISTANCE_SAMPLES = int(MIN_DISTANCE_MS / SAMPLES_TO_MS)

# --- PRÉPARATION DES DONNÉES ---
# Buffer circulaire pour le graphique
data_buffer = collections.deque([BIAS] * MAX_SAMPLES, maxlen=MAX_SAMPLES)
time_buffer = np.linspace(-MAX_SAMPLES * SAMPLES_TO_MS, 0, MAX_SAMPLES) # Axe X en ms

# Variable pour éviter le flood de prints du même événement
last_event_time = 0 

# --- CONFIGURATION DU GRAPHIQUE ---
fig, ax = plt.subplots(figsize=(10, 5))
line, = ax.plot(time_buffer, data_buffer, color='#00ff00', lw=1.5)

# Configurations visuelles précises
ax.set_title(f"Détection d'Onde et de Retour (FS : {FS}Hz)")
ax.set_ylabel("Tension (V)")
ax.set_xlabel("Temps (ms)")
ax.set_ylim(1.5, 3.5) # Focus sur la zone d'intérêt
ax.grid(True, which='both', linestyle='--', alpha=0.7)
ax.axhline(y=BIAS, color='gray', linestyle='-', alpha=0.3) # Ligne centrale
# Lignes de seuil (threshold) visuel
ax.axhline(y=BIAS + THRESHOLD_VOLTAGE, color='red', linestyle=':', alpha=0.5, label='Seuil (Threshold)')
ax.axhline(y=BIAS - THRESHOLD_VOLTAGE, color='red', linestyle=':', alpha=0.5)
ax.legend(loc='upper right')

# --- FONCTION DE MISE À JOUR ---
def update(frame):
    global last_event_time
    
    # 1. Lecture Rapide de la Série
    while ser.in_waiting:
        try:
            line_bytes = ser.readline()
            line_str = line_bytes.decode('utf-8', errors='ignore').strip()
            
            # Supporte aussi bien "val1" que "val1,val2" (ne prend que le premier)
            if ',' in line_str:
                val_raw = float(line_str.split(',')[0])
            else:
                val_raw = float(line_str)
                
            # Conversion en Volts
            volts = (val_raw / ADC_RES) * V_REF
            data_buffer.append(volts)
            
        except ValueError:
            pass

    # 2. Mise à jour du Graphique
    line.set_ydata(data_buffer)

    # 3. ANALYSE DES DONNÉES (Détection de Pic et de Retour)
    # Conversion du deque en numpy array pour une analyse mathématique rapide
    arr_data = np.array(data_buffer)
    
    # Se concentre sur le signal "absolu - bias" pour capturer les pics positifs ET négatifs
    signal_abs = np.abs(arr_data - BIAS)
    
    # Vérifie s'il y a quelque chose au-dessus du seuil dans le buffer
    if np.max(signal_abs) > THRESHOLD_VOLTAGE:
        
        # Trouve les pics. 
        # height : hauteur minimale
        # distance : distance minimale entre pics (crucial pour séparer l'onde du retour)
        peaks, properties = find_peaks(signal_abs, height=THRESHOLD_VOLTAGE, distance=MIN_DISTANCE_SAMPLES)
        
        # Nous avons besoin d'au moins 2 pics (Aller et Retour)
        if len(peaks) >= 2:
            # Nous prenons les deux derniers pics détectés dans le buffer (événement le plus récent)
            
            # Simple : Prend le pic 1 et le pic 2 détectés dans l'ordre temporel
            p1_idx = peaks[-2] # Avant-dernier (Onde Originale)
            p2_idx = peaks[-1] # Dernier (Retour)
            
            # Vérifie s'il s'agit d'un nouvel événement (pour ne pas afficher 100x le même écho)
            # Utilisation de time.time() pour limiter les affichages à 1 par demi-seconde par exemple.
            if time.time() - last_event_time > 0.5: # 500ms de "cooldown"
                
                # CALCUL PRÉCIS
                delta_samples = p2_idx - p1_idx
                delta_ms = delta_samples * SAMPLES_TO_MS
                
                # Affiche uniquement si le delta est positif et cohérent
                if delta_ms > 0:
                    print(f"=== DÉTECTION ===")
                    print(f"Pic 1 : {properties['peak_heights'][-2]:.2f}V (relatif)")
                    print(f"Pic 2 : {properties['peak_heights'][-1]:.2f}V (relatif)")
                    print(f"DELTA T (Retour) : {delta_ms:.4f} ms")
                    print("================")
                    last_event_time = time.time()

    return line,

# Lancement de l'animation
ani = animation.FuncAnimation(fig, update, interval=20, blit=True, cache_frame_data=False)
plt.show()

# Fermeture du port série en quittant
ser.close()