#include <SPI.h>
#include <Ethernet.h>
#include "RestClient.h"


#define LEFT_LIGHT_SENSOR A0
#define RIGHT_LIGHT_SENSOR A2

#define LEFT_LASER_LIGHT 9
#define RIGHT_LASER_LIGHT 10

#define BOARD_LIGHT 13

#define CALIBRATION_REPEATS 100
#define CALIBRATION_DELAY 10
#define CALIBRATE_EVERY_MSECONDS 1000*60*2 //2 minutes

#define BALL_REFLECTION_FACTOR 50

#define MINIMUM_TIME_BETWEEN_GOALS 10000 // 10 seconds
#define MINIMUM_TIME_GAME_ON_CHECK 15000 // 15 seconds


#define LEFT_SIDE 0
#define RIGHT_SIDE 1

byte mac[] = { 0xF0, 0x00, 0x55, 0xB0, 0x00, 0x11 };
IPAddress ip(10, 4, 4, 200);
char serverName[] = "riley";
int serverPort = 7008;
const char pageNameLeft[] = "/goal/left";
const char pageNameRight[] = "/goal/right";
const char pageNameIsGameOn[] = "/is_game_on";

RestClient client = RestClient(serverName, serverPort);





int leftCurrentLightLevel; 
int rightCurrentLightLevel;

int leftLightLevelMax;
int rightLightLevelMax;

unsigned int last_goal_time;
unsigned int last_game_on_check;
unsigned int last_calibration;

void all_laser_control(uint8_t power) {
  digitalWrite(LEFT_LASER_LIGHT, power);   
  digitalWrite(RIGHT_LASER_LIGHT, power);  
}

void calibrate() {
  Serial.print("Calibrating ...");
  int leftLevelMax = 0;
  int rightLevelMax = 0;  

  all_laser_control(HIGH);
  for (int i=0; i<CALIBRATION_REPEATS; i++) {
    delay(CALIBRATION_DELAY);
    int level = analogRead(LEFT_LIGHT_SENSOR);
    if (level > leftLevelMax) {
      leftLevelMax = level;
    }
    
    level = analogRead(RIGHT_LIGHT_SENSOR);
    if (level > leftLevelMax) {
      rightLevelMax = level;
    }
  }

  leftLightLevelMax = leftLevelMax;
  rightLightLevelMax = rightLevelMax;
  Serial.println("Done ...");
}


void setup()
{
  Serial.begin(38400);

  Serial.println("Connecting to network");
  client.dhcp();
/*
  // Can still fall back to manual config:
  byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
  //the IP address for the shield:
  byte ip[] = { 192, 168, 2, 11 };
  Ethernet.begin(mac,ip);
*/

  pinMode(BOARD_LIGHT, OUTPUT);
  pinMode(LEFT_LASER_LIGHT, OUTPUT);
  
  calibrate();
  last_calibration = millis();
  Serial.print("Left:");
  Serial.print(leftLightLevelMax, DEC);
  Serial.print("Right:");
  Serial.print(rightLightLevelMax, DEC);
  all_laser_control(HIGH);
}

void send_goal(int side) {
  String response = "";
  int statusCode;
  
  if (side == LEFT_SIDE) {
    statusCode = client.post(pageNameLeft, "", &response);
  } else {
    statusCode = client.post(pageNameRight, "", &response);
  }

  Serial.print("Status code from server: ");
  Serial.println(statusCode);
  Serial.print("Response body from server: ");
  Serial.println(response);
  
}





void check_game_on() {

  String response = "";
  int statusCode = client.get(pageNameIsGameOn, &response);
  Serial.print("Status code from server: ");
  Serial.println(statusCode);
  Serial.print("Response body from server: ");
  Serial.println(response);

  if (response == String("Yes")) {
    Serial.println(F("LASER ON."));
    all_laser_control(HIGH);
  } else {
    Serial.println(F("LASER OFF."));
    all_laser_control(LOW);
  }
}





byte check_goal() {
  byte left_goal = 0;
  byte right_goal = 0;

  if (leftCurrentLightLevel > (leftLightLevelMax + BALL_REFLECTION_FACTOR)) {
    left_goal = 1;
  }

  if (rightCurrentLightLevel > (rightLightLevelMax + BALL_REFLECTION_FACTOR)) {
    right_goal = 1;
  }

  if (left_goal && right_goal) {
    Serial.println(" Something wrong (maybe suddent sunlight level increased) ");
    Serial.println(" No goal! ");    
    return 0;
  } else if (left_goal) {
     Serial.println(" GOAL LEFT ");
     send_goal(LEFT_SIDE);         
     return 1;
  } else if (right_goal) {
     Serial.println(" GOAL RIGHT ");
     send_goal(RIGHT_SIDE);    
     return 1;
  }
  return 0;
}




void loop() 
{
  leftCurrentLightLevel = analogRead(LEFT_LIGHT_SENSOR);
  rightCurrentLightLevel = analogRead(RIGHT_LIGHT_SENSOR);

  unsigned now = millis();

  if ((now - last_goal_time) > MINIMUM_TIME_BETWEEN_GOALS) {
    if (check_goal()) {
      last_goal_time = now;
    }
  }
  
  if ((now - last_calibration) > CALIBRATE_EVERY_MSECONDS) {    
    calibrate();
    last_calibration = now;
  }

  if ((now - last_game_on_check) > MINIMUM_TIME_GAME_ON_CHECK) {
    check_game_on();
    last_game_on_check = now;
  } 

  
}

void loop_test() 
{
  all_laser_control(HIGH);  
  //delay(200);
  leftCurrentLightLevel = analogRead(LEFT_LIGHT_SENSOR);
  rightCurrentLightLevel = analogRead(RIGHT_LIGHT_SENSOR);
  Serial.print("Left: ");
  Serial.print(leftCurrentLightLevel, DEC);
  Serial.print("\tRight: ");
  Serial.println(rightCurrentLightLevel, DEC);

}
