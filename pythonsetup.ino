const int brocheCapteur1 = A0;
const int brocheCapteur2 = A1;

const unsigned long periodeEchantillonnage = 500; 
unsigned long tempsPrecedent = 0;

float filtre1 = 0;
float filtre2 = 0;
float facteurLissage = 0.5;

void setup() {
  Serial.begin(2000000); 

  filtre1 = analogRead(brocheCapteur1);
  filtre2 = analogRead(brocheCapteur2);
}

void loop() {
  unsigned long tempsActuel = micros();

  if (tempsActuel - tempsPrecedent >= periodeEchantillonnage) {
    tempsPrecedent = tempsActuel;

    int lecture1 = analogRead(brocheCapteur1);
    int lecture2 = analogRead(brocheCapteur2);

    // Application du filtre passe-bas (lissage)
    filtre1 = (lecture1 * facteurLissage) + (filtre1 * (1.0 - facteurLissage));
    filtre2 = (lecture2 * facteurLissage) + (filtre2 * (1.0 - facteurLissage));

    // Envoi des données formatées pour le script Python
    Serial.print(filtre1, 1);
    Serial.print(",");
    Serial.println(filtre2, 1);
  }
}