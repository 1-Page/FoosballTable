#include <SPI.h>
#include <Ethernet.h>

#define LEFT_LIGHT_SENSOR A0
#define RIGHT_LIGHT_SENSOR A2

#define LEFT_LASER_LIGHT 9
#define RIGHT_LASER_LIGHT 10

#define BOARD_LIGHT 13

#define CALIBRATION_REPEATS 100
#define CALIBRATION_DELAY 10
#define CALIBRATE_EVERY_MSECONDS 1000*60*2 //2 minutes
//#define CALIBRATE_EVERY_MSECONDS 1000*10 //2 minutes

#define BALL_REFLECTION_FACTOR 50

#define MINIMUM_TIME_BETWEEN_GOALS 10000 // 10 seconds
#define MINIMUM_TIME_GAME_ON_CHECK 15000 // 15 seconds


//#define SERVER "10.4.4.161"
#define LEFT_SIDE 0
#define RIGHT_SIDE 1

byte mac[] = { 0xF0, 0x00, 0x55, 0xB0, 0x00, 0x11 };
IPAddress ip(10, 4, 4, 200);
EthernetClient client;

//IPAddress server(10,4,4,161);
char serverName[] = "10.4.4.161";
IPAddress server(10,4,4,94);
//char serverName[] = "riley";
int serverPort = 7008;
char pageNameLeft[] = "/goal/left";
char pageNameRight[] = "/goal/right";
char pageNameIsGameOn[] = "/is_game_on";


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

  
  Serial.println("Starting Ethernet");
  // start the Ethernet connection:

  if (Ethernet.begin(mac) == 0) {
    Serial.println("Failed to configure Ethernet using DHCP");
    // no point in carrying on, so do nothing forevermore:
    // try to congifure using IP address instead of DHCP:
    Ethernet.begin(mac, ip);
  }

  Serial.print("Got IP: ");
  Serial.println(Ethernet.localIP());

  
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
  char params[] = "Nothing";
  
  byte result;
  
  if (side == LEFT_SIDE) {
    result = postPage(serverName,serverPort,pageNameLeft,params); 
  } else {
    result = postPage(serverName,serverPort,pageNameRight,params); 
  }
  
  if (!result) {
    Serial.print(F("Fail "));
  } else {
    Serial.print(F("Pass "));
  }
}


byte postPage(char* domainBuffer,int thisPort,char* page,char* thisData)
{
  int inChar;
  char outBuf[64];

  Serial.print(F("Posting goal..."));

  if(client.connect(domainBuffer,thisPort) == 1)
  {
    Serial.println(F("connected"));

    // send the header
    sprintf(outBuf,"POST %s HTTP/1.1",page);
    client.println(outBuf);    
    sprintf(outBuf,"Host: %s",domainBuffer);

    client.println("User-Agent: FoosballTable/1.0");
    client.println("Connection: close");
    client.println("Content-Type: text/plain");
    client.print("Content-Length: ");
    client.println(strlen(thisData));
    client.print(thisData);
    client.stop();
    return 1;
  } 
  else
  {
    Serial.println(F("failed"));
    return 0;
  }
}


String getPage(IPAddress ipBuf,int thisPort, char *page)
{
  int inChar;
  char outBuf[128];
  String response = "";

  Serial.print(F("Check Online..."));

  if(client.connect(ipBuf,thisPort) == 1)
  {
    Serial.println(F("connected"));

    sprintf(outBuf,"GET %s HTTP/1.1",page);
    client.println(outBuf);
    sprintf(outBuf,"Host: %s",serverName);
    client.println(outBuf);
    client.println(F("Connection: close\r\n"));
  } 
  else
  {
    Serial.println(F("failed"));
    return response;
  }

  // connectLoop controls the hardware fail timeout
  int connectLoop = 0;      

  while(client.connected())
  {
    while(client.available())
    {
      inChar = client.read();
      response.concat(inChar);
      Serial.write(inChar);
      // set connectLoop to zero if a packet arrives
      connectLoop = 0;
    }

    connectLoop++;

    // if more than 10000 milliseconds since the last packet
    if(connectLoop > 10000)
    {
      // then close the connection from this end.
      Serial.println();
      Serial.println(F("Timeout"));
      client.stop();
    }
    // this is a delay for the connectLoop timing
    delay(1);
  }

  Serial.println();

  Serial.println(F("disconnecting."));
  // close client end
  client.stop();

  return response;
}


void check_game_on() {
  return;
  String response("");
  // Check server for "/is_game_on" ==> "Yes", or "No"  
  response = getPage(server,serverPort,pageNameIsGameOn);
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
