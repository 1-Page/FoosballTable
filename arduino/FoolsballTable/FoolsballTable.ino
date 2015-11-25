#include <SPI.h>
#include <Ethernet.h>
#include "RestClient.h"


#define LEFT_PROXIMITY_SENSOR 2
#define RIGHT_PROXIMITY_SENSOR 4

#define BOARD_LIGHT 13

#define MINIMUM_TIME_BETWEEN_GOALS 5000 // 5 seconds
#define MINIMUM_TIME_GAME_ON_CHECK 15000 // 15 seconds
#define MINIMUM_TIME_GAME_OFF_CHECK 120000 // 2 minutes

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

unsigned long last_goal_time = 0;
unsigned long last_game_on_check = 0;

byte game_is_on = 1;


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
  
  unsigned long now = millis();

  check_game_on();
  last_game_on_check = now;

  last_goal_time = now - MINIMUM_TIME_BETWEEN_GOALS;  
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
    game_is_on = 1;
  } else {
    game_is_on = 0;
  }
}





byte check_goal() {
  byte left_goal = 0;
  byte right_goal = 0;

  if (digitalRead (LEFT_PROXIMITY_SENSOR) == LOW) {
    left_goal = 1;
  }

  if (digitalRead (RIGHT_PROXIMITY_SENSOR) == LOW) {
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
  unsigned long now = millis();

  if (game_is_on) {
    /*
    Serial.print("now: ");
    Serial.print(now);
    Serial.print(" - ");
    Serial.print(last_game_on_check);
    Serial.print(" = ");
    Serial.print((now - last_game_on_check));
    Serial.print(" > ");
    Serial.print(MINIMUM_TIME_GAME_OFF_CHECK);
    Serial.print(" : ");
    Serial.println(((now - last_game_on_check) > MINIMUM_TIME_GAME_OFF_CHECK));
    */
    
     if (abs(now - last_game_on_check) > MINIMUM_TIME_GAME_OFF_CHECK) {
      check_game_on();
      last_game_on_check = now;
    }        
   
  
    if (abs(now - last_goal_time) > MINIMUM_TIME_BETWEEN_GOALS) {
      if (check_goal()) {
        last_goal_time = now;
      }
    }
  } else {
    if (abs(now - last_game_on_check) > MINIMUM_TIME_GAME_ON_CHECK) {
      check_game_on();
      last_game_on_check = now;      
    }
    
  }

  
}

void loop_test() 
{
  byte leftProxValue = digitalRead (LEFT_PROXIMITY_SENSOR);
  byte rightProxValue = digitalRead (RIGHT_PROXIMITY_SENSOR);
  Serial.print("Left: ");
  Serial.print(leftProxValue == LOW);
  Serial.print("\tRight: ");
  Serial.println(rightProxValue == LOW);

}
