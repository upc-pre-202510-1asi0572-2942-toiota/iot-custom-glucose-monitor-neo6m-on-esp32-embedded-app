#include "wokwi-api.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>  // Para fabsf()

typedef struct {
  pin_t pin_a0;               // Salida analógica de glucosa
  pin_t pin_out;              // Salida digital de alerta
  uint32_t glucose_attr;      // Atributo de glucosa
  uint32_t temp_attr;         // Atributo de temperatura
  float last_glucose;         // Último valor de glucosa
  float last_temp;            // Último valor de temperatura
  timer_t timer;              // Timer para verificación
} chip_state_t;

void check_values_change(void *user_data);

void chip_init() {
  chip_state_t *chip = malloc(sizeof(chip_state_t));
  
  // Inicializar pines
  chip->pin_a0 = pin_init("A0", ANALOG);
  chip->pin_out = pin_init("OUT", OUTPUT);
  
  // Inicializar atributos
  chip->glucose_attr = attr_init("glucose", 100);
  chip->temp_attr = attr_init("temp", 36);
  
  // Valores iniciales
  chip->last_glucose = 100.0f;
  chip->last_temp = 36.0f;
  
  // Configurar timer (500ms)
  timer_config_t timer_config = {
    .callback = check_values_change,
    .user_data = chip,
  };
  chip->timer = timer_init(&timer_config);
  timer_start(chip->timer, 500000, true);
  
  printf("Chip de diabetes inicializado\n");
}

void check_values_change(void *user_data) {
  chip_state_t *chip = (chip_state_t*)user_data;
  float current_glucose = attr_read_float(chip->glucose_attr);
  float current_temp = attr_read_float(chip->temp_attr);
  bool glucose_changed = fabsf(current_glucose - chip->last_glucose) > 0.1f;
  bool temp_changed = fabsf(current_temp - chip->last_temp) > 0.1f;

  if (glucose_changed || temp_changed) {
    chip->last_glucose = current_glucose;
    chip->last_temp = current_temp;
    
    // Actualizar salida analógica (50-300mg/dL → 0-3.3V)
    float voltage = (current_glucose - 50) * (3.3f / 250.0f);
    pin_dac_write(chip->pin_a0, voltage);
    
    // Actualizar alerta digital
    pin_write(chip->pin_out, current_glucose > 180 ? HIGH : LOW);
    
    printf("Actualizado: Glucosa=%.1f mg/dL, Temp=%.1f°C\n", current_glucose, current_temp);
  }
}