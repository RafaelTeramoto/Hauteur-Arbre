import serial
import time
import collections

# --- CONFIGURATIONS ---
SERIAL_PORT = 'COM6'   
BAUD_RATE = 2000000    
MAX_WAIT_SAMPLES = 500 

# --- PARAMÈTRES DE DÉTECTION ---
V_REF = 5.0
ADC_RES = 1023.0
BIAS_VOLTAGE = 2.5     
THRESHOLD = 0.05       # Tension au-dessus du Bias pour déclencher (Trigger)

# Stocke la valeur précédente pour l'interpolation
prev_v1 = BIAS_VOLTAGE
prev_v2 = BIAS_VOLTAGE

# --- FONCTION D'INTERPOLATION ---
def get_exact_crossing_time(prev_val, curr_val, threshold_val, current_sample_idx):
    """
    Calcule le moment exact (float) où le signal a franchi le seuil (threshold).
    Utilise l'équation de la droite entre le point précédent et l'actuel.
    """
    # Évite la division par zéro
    if curr_val == prev_val:
        return current_sample_idx
        
    # Fraction de temps où le franchissement s'est produit (0.0 à 1.0)
    # Ex : Si prev=2.4, curr=2.6, target=2.5 -> fraction = 0.5
    fraction = (threshold_val - prev_val) / (curr_val - prev_val)
    
    # Le temps exact est l'échantillon précédent + la fraction
    exact_index = (current_sample_idx - 1) + fraction
    return exact_index

# --- CALIBRAGE (Identique au précédent) ---
def calibrate_samplerate(ser_conn):
    print("--- Calibrage du Taux d'Échantillonnage (1s)... ---")
    start_time = time.time()
    count = 0
    while time.time() - start_time < 1.0:
        if ser_conn.in_waiting:
            ser_conn.readline()
            count += 1
    print(f"Taux Réel : {count} Hz | Période : {1000/count:.4f} ms")
    return count

# --- SETUP ---
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.01)
    time.sleep(2)
    ser.reset_input_buffer()
except Exception as e:
    print(e)
    exit()

FS = calibrate_samplerate(ser)

# Variables
t_sensor1 = None  # Sera désormais un FLOAT (ex : 512.43)
t_sensor2 = None
sample_counter = 0
triggered = False
trigger_level_pos = BIAS_VOLTAGE + THRESHOLD # Niveau de déclenchement positif

print(f"\n--- HAUTE PRÉCISION ACTIVÉE ---")
print(f"Trigger défini à {trigger_level_pos:.2f} V")

try:
    while True:
        if ser.in_waiting:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if ',' in line:
                    parts = line.split(',')
                    if len(parts) == 2:
                        curr_v1 = (float(parts[0]) / ADC_RES) * V_REF
                        curr_v2 = (float(parts[1]) / ADC_RES) * V_REF
                        
                        sample_counter += 1

                        # --- LOGIQUE DE DÉCLENCHEMENT (RISING EDGE / FRONT MONTANT) ---
                        # Se déclenche uniquement s'il ÉTAIT en dessous et est MAINTENANT au-dessus
                        
                        # Capteur 1
                        if t_sensor1 is None:
                            if prev_v1 < trigger_level_pos and curr_v1 >= trigger_level_pos:
                                t_sensor1 = get_exact_crossing_time(prev_v1, curr_v1, trigger_level_pos, sample_counter)

                        # Capteur 2
                        if t_sensor2 is None:
                            if prev_v2 < trigger_level_pos and curr_v2 >= trigger_level_pos:
                                t_sensor2 = get_exact_crossing_time(prev_v2, curr_v2, trigger_level_pos, sample_counter)

                        # --- CALCUL ---
                        if t_sensor1 is not None and t_sensor2 is not None and not triggered:
                            # Différence exacte en échantillons (float)
                            diff_samples = t_sensor2 - t_sensor1
                            
                            # Différence en ms
                            diff_ms = (diff_samples / FS) * 1000.0
                            
                            print(f"DELTA DÉTECTÉ :")
                            print(f"  Échantillons : {diff_samples:.4f}")
                            print(f"  Temps :        {diff_ms:.5f} ms  <--- PRÉCISION ACCRUE")
                            
                            if diff_ms == 0:
                                print("  AVERTISSEMENT : Les capteurs se sont déclenchés exactement ensemble (augmentez la distance ou le taux d'échantillonnage).")
                            
                            triggered = True

                        # Réinitialisation (Reset timeout)
                        if (t_sensor1 is not None or t_sensor2 is not None):
                            start_check = t_sensor1 if t_sensor1 else t_sensor2
                            if (sample_counter - start_check) > MAX_WAIT_SAMPLES:
                                t_sensor1 = None
                                t_sensor2 = None
                                triggered = False
                        
                        # Met à jour les valeurs précédentes pour la boucle suivante
                        prev_v1 = curr_v1
                        prev_v2 = curr_v2

            except ValueError:
                pass
except KeyboardInterrupt:
    ser.close()