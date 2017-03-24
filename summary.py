#!/usr/bin/python
# *****BatteryMonitor store summary data summary.py*****
# Copyright (C) 2014 Simon Richard Matthews
# Project loaction https://github.com/simat/BatteryMonitor
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import sys
from os import rename
import time
from shutil import copy as filecopy
from copy import deepcopy
from ast import literal_eval
from ConfigParser import SafeConfigParser
from config import config
numcells = config['battery']['numcells']


class Summary:
  """Handles battery summary data""" 

  def __init__(self):
    self.currenttime = time.localtime()
    printtime = time.strftime("%Y%m%d%H%M%S ", self.currenttime)
    self.logfile = open(config['files']['logfile'],'a',0)
    self.sampletime = time.time()
    self.prevtime = time.localtime()

    try:
      self.summaryfile = SafeConfigParser()
      self.summaryfile.read(config['files']['summaryfile'])
      self.summary = {}
      for section in self.summaryfile.sections():
        self.summary[section] = {}
        for key, val in self.summaryfile.items(section):
          self.summary[section][key] = literal_eval(val)
#      daysummaryfile = open('/media/75cc9171-4331-4f88-ac3f-0278d132fae9/daysummary','r')
#      self.daydata = literal_eval(daysummaryfile.read())
#      daysummaryfile.close()
    except IOError:
      pass
#      summary = open('/media/75cc9171-4331-4f88-ac3f-0278d132fae9/summary','w')
#      pickle.dump(hivolts, summary)
#      pickle.dump(lowvolts, summary)
#      summary.close()
    if self.summary['hour']['timestamp'][0:10] != printtime[0:10]:
      self.summary['hour'] = deepcopy(self.summary['current'])
    if self.summary['currentday']['timestamp'][0:8] != printtime[0:8]:
      self.summary['currentday'] = deepcopy(self.summary['current'])
    if self.summary['monthtodate']['timestamp'][0:6] != printtime[0:6]:
      self.summary['monthtodate'] = deepcopy(self.summary['current'])
    if self.summary['yeartodate']['timestamp'][0:4] != printtime[0:4]:
      self.summary['yeartodate'] = deepcopy(self.summary['current'])



  def update(self, summary, batdata):
    """ Update 'current' section of summary data with 'batdata' and write realtime log """
    
    summary['current']['maxvoltages'][numcells] = round(batdata.batvoltsav[numcells],2)
    summary['current']['minvoltages'][numcells] = summary['current']['maxvoltages'][numcells]
    if batdata.currentav[0] > -config['battery']['ilowcurrent']:
      summary['current']['maxnocharge'][numcells] = summary['current']['maxvoltages'][numcells]
    if batdata.currentav[0] < config['battery']['ilowcurrent']:
      summary['current']['minnoload'][numcells] = summary['current']['minvoltages'][numcells]
    summary['current']['ah'][2] = round(batdata.soc,2)
    summary['current']['ah'][0] = summary['current']['ah'][2]
    summary['current']['ah'][1] = summary['current']['ah'][2]
    summary['current']['ah'][6] = round(batdata.inahtot,2)  # current from solar etc
    summary['current']['dod'][2] = round(batdata.socadj,2)
    summary['current']['dod'][0] = summary['current']['dod'][2]
    summary['current']['dod'][1] = summary['current']['dod'][2]
#    summary['current']['amps'][1] = round(batdata.currentav[0], 1)
#    summary['current']['amps'][0] = summary['current']['amps'][1]
#    summary['current']['amps'][2] = round(batdata.currentav[1], 1)
    if batdata.ah > 0.0:
      summary['current']['ah'][5] = round(batdata.ah,2)
      summary['current']['ah'][4] = 0.0      
    else:
      summary['current']['ah'][4] = round(batdata.ah,2)
      summary['current']['ah'][5] = 0.0      
    if batdata.pwrbat > 0.0:
      summary['current']['power'][1] = round(batdata.pwrbattot,6)
      summary['current']['power'][0] = 0.0      
    else:
      summary['current']['power'][0] = round(batdata.pwrbattot,6)
      summary['current']['power'][1] = 0.0      
    summary['current']['power'][2] = round(batdata.pwrintot,6)     
    summary['current']['power'][3] = round(summary['current']['power'][0] - \
                                     summary['current']['power'][2] + \
                                     summary['current']['power'][1] ,6 )  # current to loads     

    vprint=''
    maxmaxvoltage = 0.0
    minmaxvoltage = 5.0    
    for i in range(numcells):
      summary['current']['maxvoltages'][i] = round(batdata.deltav[i+1],3)
      maxmaxvoltage = max(maxmaxvoltage, summary['current']['maxvoltages'][i])
      minmaxvoltage = min(minmaxvoltage, summary['current']['maxvoltages'][i])
      summary['current']['minvoltages'][i] = summary['current']['maxvoltages'][i]
      if batdata.currentav[0] > -config['battery']['ilowcurrent']:
        summary['current']['maxnocharge'][i] = summary['current']['maxvoltages'][i]  
      if batdata.currentav[0] < config['battery']['ilowcurrent']:
        summary['current']['minnoload'][i] = summary['current']['minvoltages'][i]     
      vprint=vprint + str(round(batdata.deltav[i+1],3)).ljust(5,'0') + ' '
    summary['current']['deltav'][0] = round(maxmaxvoltage - minmaxvoltage, 3)
    if batdata.currentav[0] < config['battery']['ilowcurrent']:
      summary['current']['deltav'][1] = summary['current']['deltav'][0]
    summary['current']['deltav'][2] = summary['current']['deltav'][0]
    vprint = vprint + str(round(batdata.batvoltsav[numcells],2)).ljust(5,'0') + ' '
    vprint = vprint + str(summary['current']['deltav'][0]) + ' '

    for i in range(batdata.numiins):
      summary['current']['currentmax'][i] = round(batdata.currentav[i],1)
      summary['current']['currentmin'][i] = round(batdata.currentav[i],1)
      vprint = vprint + str(round(batdata.currentav[i],1)) + ' '
      summary['current']['powermax'][i] = round(batdata.currentav[i]*batdata.batvoltsav[numcells],0)
      summary['current']['powermin'][i] = summary['current']['powermax'][i]
     
    logdata = vprint + str(round(batdata.soc,2)).ljust(5,'0') + \
              ' ' + str(round(batdata.socadj,2)).ljust(5,'0') + '\n'  #  + '\033[1A'    
    sys.stdout.write(logdata)  #  + '\033[1A'
    self.prevtime = self.currenttime
    self.currenttime = time.localtime()
    self.printtime = time.strftime("%Y%m%d%H%M%S ", self.currenttime)
    summary['current']['timestamp'] = "'" + self.printtime + "'"
    currentdata = self.printtime + logdata

#      currentdata = currentdata + '               '
#      for i in range(numcells):
#        currentdata = currentdata + str(round(batdata.uncalvolts[i+1]-batdata.uncalvolts[i],3)) + ' ' 
#      currentdata = currentdata + '\n'
    self.logfile.write(currentdata)

  def updatesection(self, summary, section, source):
    """ Update 'summary' section 'section' with data from 'source' """
    
    section = summary[section]
    source = summary[source]
    section['deltav'][1] = max(section['deltav'][1], source['deltav'][1])
    section['deltav'][2] = max(section['deltav'][2], source['deltav'][2])
    section['deltav'][0] = min(section['deltav'][0], source['deltav'][0])
    section['ah'][2] = max(section['ah'][2], source['ah'][2])
    section['ah'][0] = min(section['ah'][0], source['ah'][0])
    section['ah'][1] = (section['ah'][1]*section['ah'][3] + source['ah'][1])
    section['ah'][4] = round(section['ah'][4]+source['ah'][4], 2)
    section['ah'][5] = round(section['ah'][5]+source['ah'][5], 2)
    section['ah'][6] = round(section['ah'][6]+source['ah'][6], 2)
    section['power'][0] = round(section['power'][0]+source['power'][0], 6)
    section['power'][1] = round(section['power'][1]+source['power'][1], 6)
    section['power'][2] = round(section['power'][2]+source['power'][2], 6)
    section['power'][3] = round(section['power'][3]+source['power'][3], 6) 
    section['dod'][2] = max(section['dod'][2], source['dod'][2])
    section['dod'][0] = min(section['dod'][0], source['dod'][0])
    section['dod'][1] = (section['dod'][1]*section['ah'][3] + source['dod'][1])
    section['ah'][3] += 1
    section['ah'][1] = round(section['ah'][1]/section['ah'][3], 6)
    section['dod'][1] = round(section['dod'][1]/section['ah'][3], 6)
    section['dod'][3] = max(section['dod'][3], source['dod'][3])
#    section['amps'][1] = max(section['amps'][1], source['amps'][1])
#    section['amps'][0] = min(section['amps'][0], source['amps'][0])     
#    section['amps'][2] = min(section['amps'][2], source['amps'][2])
    for i in range(len(config['CurrentInputs'])):
      section['currentmax'][i] = max(section['currentmax'][i], source['currentmax'][i])
      section['currentmin'][i] = min(section['currentmin'][i], source['currentmin'][i])
      section['powermax'][i] = max(section['powermax'][i], source['powermax'][i])
      section['powermin'][i] = min(section['powermin'][i], source['powermin'][i])
    for i in range(numcells+1):
      section['maxvoltages'][i] = max(section['maxvoltages'][i], source['maxvoltages'][i])
      section['minvoltages'][i] = min(section['minvoltages'][i], source['minvoltages'][i])
      section['maxnocharge'][i] = max(section['maxnocharge'][i], source['maxnocharge'][i])
      section['minnoload'][i] = min(section['minnoload'][i], source['minnoload'][i])
    section['timestamp'] = summary['current']['timestamp']

  def writesummary(self):
    """ Write summary file """
    
    for section in self.summaryfile.sections():
      for option in self.summaryfile.options(section):
        self.summaryfile.set(section, option, str(self.summary[section][option]))
    of = open(config['files']['summaryfile'],'w')
    self.summaryfile.write(of)
    of.close()

#  def writehour(self, data):
#    hoursummaryfile=open('/media/75cc9171-4331-4f88-ac3f-0278d132fae9/hoursummary','a')
#    hoursummaryfile.write(data)
#    hoursummaryfile.close()
#    logsummary.set('alltime', 'maxvoltages') = round(max(literal_eval(logsummary.get('currentday','maxvoltages')),literal_eval(logsummary.get(),2)
#    logsummary.set('alltime', 'minvoltages') = round(min(literal_eval(logsummary.get('currentday','minvoltages')),batdata.batvoltsav[8]),2)
#    logsummary.set('alltime', 'ah') = round(max(literal_eval(logsummary.get('currentday','ah'))[1], batdata.soc/1000),2)
#    logsummary.set('alltime', 'ah') = round(min(literal_eval(logsummary.get('currentday','ah'))[0], batdata.soc/1000),2)
#    logsummary.set('alltime', 'current') = round(max(literal_eval(logsummary.get('alltime','current'))[1], batdata.batcurrentav/1000),2)
#    logsummary.set('alltime', 'current') = round(min(literal_eval(logsummary.get('alltime','current'))[0], batdata.batcurrentav/1000),2)


  def writeperiod(self, file, data):
    """ Append 'data' to 'file' for previous period """
    periodfile=open(config['files'][file],'a')
    writestr=''
    y = self.summaryfile.items(data)
    for i in y:
      writestr = writestr + str(i) +"\n"
    writestr = writestr + "\n"
    periodfile.write(writestr)
    periodfile.close()
 
  def starthour(self, summary):
    """ Start new hour """
    self.writeperiod('hoursummaryfile', 'hour')
    summary['hour']['ah'][3] = 0 # zero # of samples for av  
    summary['hour'] = deepcopy(summary['current'])

  def startday(self, summary):
    """ Start new Day """
    
    self.writeperiod('daysummaryfile', 'currentday')
    summary['prevday'] = deepcopy(summary['currentday'])
    summary['currentday']['ah'][3] = 0 # zero number of samples for av
    summary['current']['dod'][3] += 1 
    summary['currentday'] = deepcopy(summary['current'])

  def startmonth(self, summary):
    """ Start new month """
    
    self.writeperiod('monthsummaryfile', 'monthtodate')
    summary['monthtodate']['ah'][3] = 0  # zero number of samples for av 
    summary['monthtodate'] = deepcopy(summary['current'])
    filecopy(config['files']['summaryfile'],config['files']['summaryfile']+ self.printtime[0:8])

  def startyear(self, summary):
    """ Start new year """
    
    self.writeperiod('yearsummaryfile', 'yeartodate')
    summary['yeartodate']['ah'][3] = 0  # zero number of samples for av 
    summary['yeartodate'] = deepcopy(summary['current'])
    self.logfile.close()
    rename(config['files']['logfile'],config['files']['logfile']+str(int(self.printtime[0:4])-1))
    self.logfile = open(config['files']['logfile'],'a')

  def close(self):
    """ Close logging file ready for exit """
    
    self.logfile.close()


