#include <Stepper.h>

const int STEPS = 2048; // Number of steps per revolution of your motor
const int MOTOR_RPM = 6; // Speed in revolutions per minute
const int INIT_POS = 240;  // Initial position of the motor
const int NUM_STEPS = 15;  // Number of steps per cycle

Stepper stepper(STEPS, 8, 10, 9, 11);
bool programExecuted = false;

void setup() {
  Serial.begin(9600); // Initialize serial communication at 9600 baud
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    if (command == 'S') {
      programExecuted = true;
    }
  }

  if (programExecuted) {
    // Perform 15 steps to the right
    for (int i = 0; i < NUM_STEPS; i++) {
      stepper.setSpeed(MOTOR_RPM);
      stepper.step(16); // Perform a step to the right
      delay(2000);
      Serial.println("Step performed to the right");
    }
    // Send a return message indicating that the movement to the right is complete
    Serial.println("A");

    // Return to the initial position
    stepper.setSpeed(MOTOR_RPM);
    stepper.step(-INIT_POS); // Return to the initial position
    delay(2000); // Wait a bit before changing direction

    // Perform 15 steps to the left
    for (int i = 0; i < NUM_STEPS; i++) {
      stepper.setSpeed(MOTOR_RPM);
      stepper.step(-16); // Perform a step to the left
      delay(2000);
      Serial.println("Step performed to the left");
    }
    // Send a return message indicating that the movement to the left is complete
    Serial.println("B");

    // Return to the initial position
    stepper.setSpeed(MOTOR_RPM);
    stepper.step(INIT_POS); // Return to the initial position
    delay(2000); // Wait a bit before restarting the cycle

    programExecuted = false; // Update the control variable to indicate that the program has been executed
  }
}