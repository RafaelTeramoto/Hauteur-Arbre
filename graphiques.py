import serial
import time
import collections
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# --- CONFIGURATIONS ---
SERIAL_PORT = 'COM6'   # <--- VÉRIFIEZ SI LE PORT EST CORRECT
BAUD_RATE = 2000000    # Doit être identique à celui de l'Arduino
MAX_SAMPLES = 4000     

# --- PARAMÈTRES DE CONVERSION (ADXL1002Z + ARDUINO) ---
V_REF = 5.0            # Tension de référence
ADC_RES = 1023.0       # Résolution 10 bits

# Estimation du taux d'échantillonnage
FS_ESTIMEE = 1600      # Hz
DURATION = MAX_SAMPLES / FS_ESTIMEE 

# --- PRÉPARATION DES DONNÉES ---
# Axe de temps relatif
time_axis = np.linspace(-DURATION, 0, MAX_SAMPLES)

# Buffers pour stocker la TENSION
data_1 = collections.deque([0.0] * MAX_SAMPLES, maxlen=MAX_SAMPLES)
data_2 = collections.deque([0.0] * MAX_SAMPLES, maxlen=MAX_SAMPLES)

# Connexion Série
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.01)
    print(f"Connecté à {BAUD_RATE} baud sur le port {SERIAL_PORT} ! En attente de données...")
    time.sleep(2) 
    ser.reset_input_buffer()
except serial.SerialException:
    print(f"ERREUR : Impossible d'ouvrir le port {SERIAL_PORT}.")
    print("Vérifiez que l'Arduino est connecté et que le Moniteur Série de l'IDE est FERMÉ.")
    exit()

# --- GRAPHIQUE ---
fig, ax = plt.subplots(figsize=(12, 6))

# Lignes du graphique
line1, = ax.plot(time_axis, data_1, color='#00ff00', linewidth=1, label='Capteur 1 (Haut)')
line2, = ax.plot(time_axis, data_2, color='#ff6600', linewidth=1, label='Capteur 2 (Bas)')

ax.set_title(f"Signal Accélérométrique (Tension Réelle - ADXL1002Z)")
ax.set_ylabel("Tension (Volts)")
ax.set_xlabel("Temps (secondes)")
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(loc='upper right')

# --- LIMITES DE L'AXE Y ---
ax.set_ylim(2.25, 2.75) 

# --- FONCTION DE MISE À JOUR ---
def update(frame):
    # Lit tout ce qui est accumulé dans le buffer série
    while ser.in_waiting:
        try:
            line_bytes = ser.readline()
            # Décode et supprime les espaces
            line_str = line_bytes.decode('utf-8', errors='ignore').strip()
            
            # Vérifie si la ligne a le format "val1,val2"
            if ',' in line_str:
                parts = line_str.split(',')
                if len(parts) == 2:
                    # --- CORRECTION APPLIQUÉE ICI ---
                    # Nous accédons à parts[0] pour la première valeur
                    raw_1 = float(parts[0]) 
                    raw_2 = float(parts[1])
                    
                    # CONVERSION EN VOLTS
                    volt_1 = (raw_1 / ADC_RES) * V_REF
                    volt_2 = (raw_2 / ADC_RES) * V_REF
                    
                    # Ajoute aux buffers
                    data_1.append(volt_1)
                    data_2.append(volt_2)
                    
        except ValueError:
            pass # Ignore les lignes incomplètes ou les erreurs de conversion

    # Met à jour les lignes sur le graphique
    line1.set_data(time_axis, data_1)
    line2.set_data(time_axis, data_2)
    
    return line1, line2

# Lance l'animation
ani = animation.FuncAnimation(fig, update, interval=30, blit=True, cache_frame_data=False)

try:
    plt.show()
except AttributeError:
    # Capture l'erreur de fermeture brusque si elle survient
    pass
finally:
    if ser.is_open:
        ser.close()
        print("Connexion série fermée.")