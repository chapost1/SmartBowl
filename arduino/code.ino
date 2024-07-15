// Include the Servo library
#include <Servo.h>

#include <string.h>

#define HIGH_SERVO_DEG 90
#define LOW_SERVO_DEG 0

#define SERVO_RAW_PIN_INDEX 9

#define RED_CHANNEL_INDEX 2
#define RED_PIN (1 << DDB3)
#define RED_DIRECTION_PORT DDRB
#define RED_PWM_REGISTER OCR2A

#define GREEN_CHANNEL_INDEX 1
#define GREEN_PIN (1 << DDD3)
#define GREEN_DIRECTION_PORT DDRD
#define GREEN_PWM_REGISTER OCR2B

#define BLUE_CHANNEL_INDEX 0
#define BLUE_PIN (1 << DDD5)
#define BLUE_DIRECTION_PORT DDRD
#define BLUE_PWM_REGISTER OCR0B

#define FORCE_SENSOR_ANALOG_PIN (1 << DDC0)
#define FORCE_SENSOR_DIRECTION_PORT DDRC
#define FORCE_SENSOR_ANALOG_PIN_ADC_INDEX 0

#define FORCE_MAX 466.0
#define RGB_MAX 255.0

#define FORCE_TO_RGB_RATIO RGB_MAX / FORCE_MAX

#define MAX_MESSAGE_CHARS 128
#define START_MARKER '<'
#define END_MARKER '>'

#define REFILL_STATE_OFF 0
#define REFILL_STATE_ON 1

#define TARGET_WEIGHT_MIN 1

const char * OUTPUT_TYPE_BOWL_CAPACITY = "BOWL_CAPACITY";
const char * OUTPUT_TYPE_BOWL_WEIGHT = "BOWL_WEIGHT";
const char * OUTPUT_TYPE_TARGET_WEIGHT_UPDATE = "TARGET_WEIGHT_UPDATE";
const char * OUTPUT_TYPE_REFILL_STATE_UPDATE = "REFILL_STATE_UPDATE";
const char * OUTPUT_TYPE_EMPTY_BOWL_ALERT = "EMPTY_BOWL_ALERT";
const char * OUTPUT_TYPE_GENERAL_ERROR_ALERT = "GENERAL_ERROR_ALERT";
const char * INPUT_TYPE_REFILL_COMMAND = "REFILL";
const char * INPUT_TYPE_NEW_TARGET_WEIGHT_COMMAND = "NEW_TARGET_WEIGHT";

// settings
const uint16_t bowl_capacity = (uint16_t) FORCE_MAX;

// Create a Servo object
Servo food_blocker_servo;
// Init read sm message vars
char received_chars[MAX_MESSAGE_CHARS];
uint8_t partial = 0;

// Init refill flags
uint8_t refill = 0;
uint8_t user_notified_for_empty_bowl = 0;
uint16_t user_target_weight = FORCE_MAX; // default

void pwm_timers_setup() {
  // Configure Timer0 to generate the PWM signal for D3 (OC0B)
  TCCR0A = (1 << WGM00) | (1 << WGM01) | (1 << COM0B1);
  TCCR0B = (1 << CS01);

  // Configure Timer2 to generate the PWM signal for D11 (OC2A) and D5 (OC2B)
  TCCR2A = (1 << WGM21) | (1 << WGM20) | (1 << COM2A1) | (1 << COM2B1);
  TCCR2B = (1 << CS21);
}

void adc_setup() {
  // Set the ADC reference to AVcc (5V)
  // It provides power to the ADC circuitry on the chip
  ADMUX = (1 << REFS0);

  // Set the ADC prescaler to 128 (for a 16 MHz clock, this will give 125 KHz ADC clock)
  ADCSRA = (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);

  // Enable ADC
  ADCSRA |= (1 << ADEN);
}

void setup() {
  Serial.begin(115200);
  // Set RGB led pins as output
  RED_DIRECTION_PORT |= RED_PIN;
  GREEN_DIRECTION_PORT |= GREEN_PIN;
  BLUE_DIRECTION_PORT |= BLUE_PIN;
  // Set Force sensor pin as input
  FORCE_SENSOR_DIRECTION_PORT &= ~FORCE_SENSOR_ANALOG_PIN;

  // Init pwm timers for led
  pwm_timers_setup();
  // Init ADC Setup for analog read
  adc_setup();
  //update_color(BLUE_CHANNEL_INDEX, RGB_MAX);

  // Attach the servo to relevant analog pin
  food_blocker_servo.attach(SERVO_RAW_PIN_INDEX);
  food_blocker_servo.write(LOW_SERVO_DEG);
  // output base settings
  update(OUTPUT_TYPE_TARGET_WEIGHT_UPDATE, NULL, & user_target_weight);
  update(OUTPUT_TYPE_BOWL_CAPACITY, NULL, & bowl_capacity);
}

void update_color(uint8_t channel, uint8_t value) {
  switch (channel) {
  case BLUE_CHANNEL_INDEX:
    BLUE_PWM_REGISTER = value;
    break;
  case GREEN_CHANNEL_INDEX:
    GREEN_PWM_REGISTER = value;
    break;
  case RED_CHANNEL_INDEX:
    RED_PWM_REGISTER = value;
    break;
  default:
    break;
  }
}

uint16_t readAnalog(uint8_t channel) {
  // Select the ADC channel, clear the previous channel selection
  ADMUX = (ADMUX & 0xF0) | (channel & 0x0F);

  // Start the conversion
  ADCSRA |= (1 << ADSC);

  // Wait for the conversion to complete
  while (ADCSRA & (1 << ADSC));

  // Return the ADC value
  return ADC;
}

uint16_t measure_weight() {
  return readAnalog(FORCE_SENSOR_ANALOG_PIN_ADC_INDEX);
}

// i have the real max weight which is weight
// i have desired max which is user_target_blah
// i have rgb value that should reflect weight / desired
void update_led_color_based_on_weight(uint16_t weight) {
  //float factor = RGB_MAX / FORCE_MAX;
  float normalized_weight = (float) weight / (float) user_target_weight;
  if (normalized_weight > 1) {
    normalized_weight = 1.0;
  }
  uint8_t rgb_value = RGB_MAX * normalized_weight;
  update_color(GREEN_CHANNEL_INDEX, rgb_value);
  update_color(RED_CHANNEL_INDEX, RGB_MAX - rgb_value);
}

char get_food_blocker_rotation_direction(uint8_t source, uint8_t dest) {
  if (source == dest) {
    return 0;
  }
  return source < dest ? 1 : -1;
}

void rotate_food_blocker(uint8_t finalDeg) {
  uint8_t currDeg;
  char direction;

  do {
    currDeg = food_blocker_servo.read();
    direction = get_food_blocker_rotation_direction(currDeg, finalDeg);
    food_blocker_servo.write(currDeg + direction);
    delay(10);
  } while (direction);
}

void update(const char * type,
  const char * error,
    const uint16_t * value) {
  unsigned long now_ms = millis();
  Serial.print("{\"time_ms\":");
  Serial.print(now_ms);

  Serial.print(", \"type\":");
  Serial.print("\"");
  Serial.print(type);
  Serial.print("\"");

  Serial.print(", \"error\":");
  Serial.print("\"");
  if (error != NULL) {
    Serial.print(error);
  }
  Serial.print("\"");
  
  Serial.print(", \"value\":");
  if (value != NULL) {
    Serial.print(* value);
  } else {
    Serial.print(0);
  }

  Serial.print("}\n");
}

uint8_t read_serial_chunk() {
  uint8_t has_new_data = 0;
  static uint8_t receive_in_progress = 0;
  static uint8_t next_index = 0;

  char rc;

  while (Serial.available() > 0 && has_new_data == 0) {
    if (next_index + 1 >= MAX_MESSAGE_CHARS) {
      received_chars[next_index] = '\0';
      has_new_data = 1;
      next_index = 0;
      partial = 1;
      break;
    }
    partial = 0;

    rc = Serial.read();

    if (receive_in_progress == 1) {
      if (rc == END_MARKER) {
        // terminate the string
        received_chars[next_index] = '\0';
        has_new_data = 1;
        receive_in_progress = 0;
        next_index = 0;
        break;
      } else {
        received_chars[next_index] = rc;
        next_index += 1;
      }
    } else if (rc == START_MARKER) {
      receive_in_progress = 1;
    }
  }

  return has_new_data;
}

void set_refill_value(uint16_t new_value) {
  if (refill == new_value) {
    return;
  }
  refill = new_value;
  update(OUTPUT_TYPE_REFILL_STATE_UPDATE, NULL, & new_value);
}

void on_refill_command() {
  set_refill_value(REFILL_STATE_ON);
}

void on_new_target_weight_command(uint16_t value) {
  if (value > FORCE_MAX) {
    char error[60];
    sprintf(error, "target weight exceeded maximum value - %d", (int) FORCE_MAX);
    update(OUTPUT_TYPE_TARGET_WEIGHT_UPDATE, error, NULL);
  } else if (value < TARGET_WEIGHT_MIN) {
    char error[60];
    sprintf(error, "target weight is below minimum value - %d", TARGET_WEIGHT_MIN);
    update(OUTPUT_TYPE_TARGET_WEIGHT_UPDATE, error, NULL);
  } else {
    user_target_weight = value;
    update(OUTPUT_TYPE_TARGET_WEIGHT_UPDATE, NULL, & user_target_weight);
  }
}

void process_serial_chunk() {
  // <value=something command=something>
  int value;
  char command[16];
  sscanf(
    received_chars,
    "value=%i command=%[^\t\n]", &
    value,
    command
  );
  // handle commands
  if (strcmp(command, INPUT_TYPE_REFILL_COMMAND) == 0) {
    on_refill_command();
  } else if (strcmp(command, INPUT_TYPE_NEW_TARGET_WEIGHT_COMMAND) == 0) {
    on_new_target_weight_command(value);
  } else {
    char error[60];
    sprintf(error, "unknown command - %s", command);
    update(OUTPUT_TYPE_GENERAL_ERROR_ALERT, error, NULL);
  }
}

void output_bowl_weight(uint16_t weight) {
  unsigned long now_ms = millis();
  static unsigned long latest_emit_ms = 0;
  if (now_ms - latest_emit_ms > 150) {
    update(OUTPUT_TYPE_BOWL_WEIGHT, NULL, & weight);
    latest_emit_ms = millis();
  }
}

void empty_bowl_alert() {
  update(OUTPUT_TYPE_EMPTY_BOWL_ALERT, NULL, NULL);
}

uint16_t dispenser_weight_loop() {
  uint16_t weight;

  weight = measure_weight();
  update_led_color_based_on_weight(weight);
  output_bowl_weight(weight);
  return weight;
}

void dispenser_loop() {
  uint16_t weight;

  weight = dispenser_weight_loop();

  // release rate limit once user refill detected
  if (weight > 0 && user_notified_for_empty_bowl) {
    user_notified_for_empty_bowl = 0;
  }

  switch(refill) {
    case REFILL_STATE_OFF: {
      if (weight > 0) {
        break;
      }
      if (user_notified_for_empty_bowl == 0) {
        // notify user
        empty_bowl_alert();
        // avoid throttle user until refill starts
        user_notified_for_empty_bowl = 1;
      }
      break;
    }
    case REFILL_STATE_ON: {
      if (weight < user_target_weight) {
        rotate_food_blocker(HIGH_SERVO_DEG);
      } else {
        rotate_food_blocker(LOW_SERVO_DEG);
        set_refill_value(REFILL_STATE_OFF);
      }
      break;
    }
  }
}

void handle_input() {
  uint8_t has_new_data = read_serial_chunk();
  if (has_new_data == 1) {
    process_serial_chunk();
  }
}

void loop() {
  handle_input();
  dispenser_loop();
  delay(300);
}
