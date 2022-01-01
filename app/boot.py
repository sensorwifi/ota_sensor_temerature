print("z1.03")
import esp32
import os
import time
from time import sleep
import dht
import machine
import network
import _thread as th
import utime
import urequests
import config

try:
  import usocket as socket
except:
  import socket

from app.sgp40 import SGP40
import sht40
i2c = machine.I2C(1, scl = machine.Pin(22), sda = machine.Pin(21), freq = 400000)
sgp40 = SGP40(i2c, 0x59)
sht=sht40.SHT40(i2c)

blink_running = True
led = machine.Pin(0, machine.Pin.OUT)
token='a28e01a320c3aa3e608bed62df9ec1b10ea2c9a5'
influxdb = 'http://51.68.139.56:8086/write?db=sht_40_test'
location='pokoj'
position='biurko'

led.on()

timer = machine.Timer(0)

p13 = machine.Pin(34, machine.Pin.IN)

def callback(p):
 print('pin change', p)
 
p13.irq(trigger=machine.Pin.IRQ_FALLING, handler=callback)
print("PIN ",p13.value())


def handleInterrupt(timer):
  print("Reset ====================after 50sek")
  machine.reset()
  
def blink():
  while blink_running:
         led.off()
         time.sleep(0.1)
         led.on()
         time.sleep(0.1)         
          


def startApp():
    import app.git

    
  
T_COLOR = '#f5b041'
H_COLOR = '#85c1e9'
ERR_COLOR = '#444444'

T_VPIN = 3
H_VPIN = 4

dht22 = dht.DHT22(machine.Pin(32, machine.Pin.IN, machine.Pin.PULL_UP))
try:
 dht22.measure()
 print("TEMPERATURA: ",dht22.temperature())
except:
 print("No DHT22")
timer.init(period=100000, mode=machine.Timer.PERIODIC, callback=handleInterrupt)

state = machine.disable_irq()
machine.enable_irq(state)

def do_connect():
 print("conect") 
 sta_if = network.WLAN(network.STA_IF)
 if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(config.wifi_config['ssid'], config.wifi_config['password'])
        while not sta_if.isconnected():
            pass
 print('network config:', sta_if.ifconfig())

if machine.reset_cause() == machine.DEEPSLEEP_RESET:
    print('woke from a deep sleep')
    
    #f=open('wifi.dat')
    #wifidat=f.read()
    #ssid, password, api = wifidat.strip("\n").split(";")
    #ssid, password = wifidat.strip("\n").split(";")
    do_connect()
    print("+++TYLO WIFI++++") 
      
else:
    print('power on or hard reset')
    import app.wifimgr as wifimgr
    wlan = wifimgr.get_connection()
    if wlan is None:
         print("Could not initialize the network connection.")
         while True:
             pass
              
    print("ESP OK")
    try:
      from ntptime import settime
      
      settime()
      rtc=machine.RTC()

      # for time convert to second
      tampon1=utime.time() 
          
      # for gmt. For me gmt+3. 
      # 1 hour = 3600 seconds
      # 3 hours = 10800 seconds
      tampon2=tampon1+3600

      # for second to convert time
      (year, month, mday, hour, minute, second, weekday, yearday)=utime.localtime(tampon2)

      # first 0 = week of year
      # second 0 = milisecond
      rtc.datetime((year, month, mday, 0, hour, minute, second, 0))
      print("Local time after synchronization：%s" %str(time.localtime()))
    except:
      print("no time-----------")
      
    
#958903C06C9AF5185C7092627E
def ota():
 try:
   print("tring ota")
   from app.ota_updater import OTAUpdater
   o = OTAUpdater('https://github.com/sensorwifi/ota_sensor_temerature', main_dir='app') # headers={'Authorization': 'token {}'.format(token)})
   
   th.start_new_thread(blink, ())
   #o.install_update_if_available()
   old,now=o._check_for_new_version()
   #sleep(5)
   
   if old==now:
    
    print("Version newest ",now)
       
    blink_running = False
    led.on()
    
    machine.reset()
   else:  
    print(old," Update for new version ",now)
    
    o.install_update_if_available()
    blink_running = False
    
    led.on()
    print("go reset")
    
    machine.reset()
     
 except:
   print("no github")
   blink_running = False
   led.on()
   startApp()
 
def hall_100(hall):
  print("Alert 100 - default - reset wifi and blynk")
  #machine.reset()
    #os.remove("wifi.dat")
  ota() 

def hall_10():
  #import webrepl_setup
  print("Alert 10  - ota()")
  # webrepl.start()
  ota()
  #webrepl.start(password='wifisensor')
  #o = OTAUpdater('https://github.com/sensorwifi/ota_door', github_src_dir='app', main_dir='app')
 # o._get.
  #o.install_update_if_available_after_boot()
  
  #download_and_install_update_if_available()

def read_handler(vpin):
    temperature = 0.0
    humidity = 0.0

    # read sensor data
    try:
        dht22.measure()
        temperature = dht22.temperature()
        humidity = dht22.humidity()
    except OSError as o_err:
        print("Unable to get DHT22 sensor data: '{}'".format(o_err))

    # change widget values and colors according read results
    if temperature != 0.0 and humidity != 0.0:
        blynk.set_property(T_VPIN, 'color', T_COLOR)
        blynk.set_property(H_VPIN, 'color', H_COLOR)
        blynk.virtual_write(T_VPIN, temperature)
        blynk.virtual_write(H_VPIN, humidity)
    else:
        # show widgets aka 'disabled' that mean we had errors during read sensor operation
        blynk.set_property(T_VPIN, 'color', ERR_COLOR)
        blynk.set_property(H_VPIN, 'color', ERR_COLOR)

def influx():
  temperature,humidity=sht.measure_temp_rh()
  print("dhtok",temperature)
 # try:
  #  try:
  #  temperature , humidity = sht.measure_temp_rh_raw()
   # print("dhtok",temperature)
   # except OSError as o_err:
    #    print("Unable to get DHT22 sensor data: '{}'".format(o_err))
  fields = (u'sensors,',
                  u'location={location}'.format(location=location),
                  u',position={position}'.format(position=position),
                  u' ',
                  u'temperature={temp}'.format(temp=temperature),
                  u',humidity={humidity}'.format(humidity=humidity))
  point = ''.join(fields)
  print(point)
  response = urequests.post(influxdb,
                                  data=point)
  response.close()
  print('Submitted :{}'.format(point))
  #except:
   #     print('no minflux') 
        
def conect_blynk():
  try:
      
      f=open('wifi.dat')
      wifidat=f.read()
      ssid, password, api = wifidat.strip("\n").split(";")
      
      if len(api)>10:
       print(api)
       print("Connecting to Blynk server...",api)
       import app.blynk_mp as blynklib
       print("API ok: ",api)
       try:
        blynk = blynklib.Blynk(api)
       # return  wlan_sta if connected else None
        print("blynk ready")
        blynk.run()
        print("blunk run")
        if alarm:
            blynk.notify('Otwarte')
        read_handler(4)
        print("synchro blynk")
       except:
         print("BAD BLYNK no API")
  except:
      print("no blynk import")
  
  
#do_connect() 
  
while True:
 #print(p13)
 #temperature,humidity = sht.measure_temp_rh_raw()
 #print(temperature)
 if p13.value()==1:
  alarm=True
 else:
  alarm=False 
 
 (year, month, mday, hour, minute, second, weekday, yearday)=utime.localtime()
 print("minute :",minute)
 #if (hour==19 && minute==33):
  # print("OTA Time zone",minute)
  # ota()
 try: 
  influx()
  print('in')
 except:
  print('nic')
 hall = esp32.hall_sensor()
 print("HALL ",hall)
 if hall > 100 : hall_100(hall)
 if hall < 10 : hall_10()
 #time.sleep_ms(180)
 try:
  print("try to blynk")
  conect_blynk()
 except:
   print("NO BLYNK")
 alarm=True
 #reed = machine.Pin(13, mode = machine.Pin.IN, pull = machine.Pin.PULL_DOWN)
 #reed.irq(trigger=machine.Pin.WAKE_LOW, wake=machine.DEEPSLEEP) 

 print("I go slepp")
 
 print(alarm)
 if alarm: 
  print("deepsleep for 30s")
  machine.deepsleep(30000)
 else:
  pass
  
 print(sgp40.measure_raw())
 #break
 alarm=True
#machine.enable_irq(state)
