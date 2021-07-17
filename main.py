#
# Debug client for monitoring/debugging the achatina examples
#
# Written by Glen Darling, October 2019.
#

import json
import os
import subprocess
import threading
import time
from datetime import datetime
import base64

from flask.helpers import url_for
from flask.templating import render_template
from werkzeug.utils import redirect

# Configuration constants
MQTT_SUB_COMMAND = 'mosquitto_sub -h 172.17.0.1 -p 1883 -C 1 '
MQTT_DETECT_TOPIC = '/stt'
FLASK_BIND_ADDRESS = '0.0.0.0'
FLASK_PORT = 5200
DUMMY_DETECT_IMAGE='/dummy_detect.jpg'

# Globals for the cached JSON data (last messages on these MQTT topics)
last_detect = None
stt_log = []
table_str = ''
time_origin = time.time()

#funcs
def tbl_to_html(tbl):
  global table_str
  table_str = ''
  for log in tbl:
        print(log['content'])
        name_str = '       <tr><td>' + log['time'] + '</td>\n'
        result_str = '       <td>' +  log['content'] + '</td></tr>\n'
        full_str = name_str + result_str
        table_str += full_str

def result_to_str(stt_obj):
  final_str = ''
  for result in stt_obj['results']:
    final_str += result['alternatives'][0]['transcript'] + ' '
  return final_str


if __name__ == '__main__':

  from io import BytesIO
  import flask
  from flask import Flask
  from flask import send_file
  webapp = Flask('monitor')                             
  #with webapp.app_context():
  #  url = url_for('stuff')
  
  webapp.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

  # Loop forever collecting object detection / classification data from MQTT
  class DetectThread(threading.Thread):
    def run(self):
      global last_detect
      print("\nMQTT \"" + MQTT_DETECT_TOPIC + "\" topic monitor thread started!")
      DETECT_COMMAND = MQTT_SUB_COMMAND + '-t ' + MQTT_DETECT_TOPIC
      while True:
        last_detect = subprocess.check_output(DETECT_COMMAND, shell=True)

        if last_detect:
            detect_json = json.loads(last_detect)
            new_log = {
              "time": str(round(time.time()-time_origin,1)),
              "content": result_to_str(detect_json)
            }
            stt_log.append(new_log)
        #print("\n\nMessage received on detect topic...\n")
        #print(last_detect)

  @webapp.route("/")
  def get_results():
    if None == last_detect:
      now = datetime.now().strftime("%Y/%m/%d %-I:%M%p")
      return '{"error":"' + now + ' -- No data yet."}'
    j = json.loads(last_detect)

    n = j['name']
    tbl_to_html(stt_log)

    OUT = \
        '<html>\n' + \
        ' <head>\n' + \
        '   <title>Monitor</title>\n' + \
        '   <style>table, th, td {border: 1px solid black;border-collapse: collapse;}</style>\n' + \
        ' </head>\n' + \
        ' <body bgcolor="#c0b1ce">\n' + \
        '   <div>\n' + \
        '   <table style="width:50%">\n' + \
        '     <tr>\n' + \
        '       <th>' + 'Timestamp' + '</th>\n' + \
        '       <th>' + 'Result' + '</th>\n' + \
        '     </tr>\n' + table_str + \
        '   </table>\n' + \
        '   </div>\n' + \
        '   <script>\n' + \
        '     function refresh() {\n' + \
        '       var t = 500;\n' + \
        '       (async function startRefresh() {\n' + \
        '         console.log("startRefresh");\n' + \
        '         setTimeout(startRefresh, t);\n' + \
        '       })();\n' + \
        '     }\n' + \
        '     window.onload = function() {\n' + \
        '       console.log("Refreshing");\n' + \
        '       refresh();\n' + \
        '     }\n' + \
        '   </script>\n' + \
        ' </body>\n' + \
        '</html>\n'
    print('Success')
    return (OUT)

  @webapp.route('/stuff', methods = ['GET'])
  def stuff():
      tbl_to_html(stt_log)
      time_now = time.time()
      return render_template("notmain.html", time_stamp=time_now)

  @webapp.route('/json')
  def get_json():
    if last_detect:
      tbl_to_html(stt_log)
      table_obj = {
        "html": table_str
      }
      table_json = json.dumps(table_obj)
      return  table_json + '\n'
    else:
      return '{}\n'

  # Prevent caching everywhere
  @webapp.after_request
  def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

  # Main program (instantiates and starts monitor thread and then web server)
  monitor_detect = DetectThread()
  monitor_detect.start()
  webapp.run(host=FLASK_BIND_ADDRESS, port=FLASK_PORT)
