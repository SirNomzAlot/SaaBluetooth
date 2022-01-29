#!/usr/bin/python

import os
import can
import time
import sched
import threading
import dbus
import dbus.mainloop.glib
import gobject

# Setup and linking of can0 interface/bus

os.system('sudo ip link set can0 type can bitrate 47619')
os.system('sudo ifconfig can0 up')
os.system('sudo ifconfig can0 txqueuelen 40')

can0 = can.interface.Bus(channel = 'can0', bustype = 'socketcan_ctypes')# socketcan_native

# Basic broadcast syntax, no need tho cause i made transmit(id,data)
# msg = can.Message(arbitration_id=0x123, data=[0,1,2,3,4,5,6,7], extended_id=false)


# Variables for functions, self explanitory
carOn = False
count = 0
cdOn = False
shuffle = False
muteBool = False
prevTime = 0

noSongText = "SaaBluetooth"
letterOff = 0

songName = "UNKNOWN"
artist = ""
album = ""
playing = False
connected = False

# Because im lazy and dont want to implement it
# that or its a security thing, none shall connect!
# literally the mac address of you phones bluetooth
phoneMAC = '12:34:56:78:9a:bc'

# must be sent every second for cd changer to recognice CD changer
cdcode = [0xe0,0x00,0x3f,0x31,0xff,0xff,0xff,0xd0]
dispco = [0x1f,0x00,0xff,0x08,0x00,0x00,0x00,0x00]

# dbus insanity, dont ask me
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
# playerIface = None
# transIface = None

playerIface = bus.get_object('org.bluez', '/org/bluez/hci0/dev_58_CB_52_8F_F1_35/player0')
transIface = bus.get_object('org.bluez', '/org/bluez/hci0/dev_58_CB_52_8F_F1_35/fd0')
adaptIface = dbus.Interface(bus.get_object('org.bluez', '/org/bluez/hci0'), 'org.freedesktop.DBus.Properties')

# thanks blueplayer guy bwiggs nvm doesnt work f.
# also its not bwiggs, i cant find the og now...
# theres too many i cant tell.
def findPlayer():
	global bus
	global playerIface
	global transIface
	manager = dbus.Interface(bus.get_object("org.bluez", "/"), "org.freedesktop.DBus.ObjectManager")
	objects = manager.GetManagedObjects()

	playerPath = None
	transPath = None
	for i, interfaces in objects.iteritems():
		if 'org.bluez.MediaPlayer1' in interfaces:
			playerPath = i
		if 'org.bluez.MediaTransport1' in interfaces:
			transPath = i
	print playerPath
	print transPath
	playerIface = bus.get_object('org.bluez',playerPath)
	transIface = bus.get_object('org.bluez',transPath)


def dbusChange(interface, properties, invalidated, path):
	global bus
	global playing
	global songName
	global artist
	global album
	global letterOff
	global connected
	if interface == 'org.bluez.MediaTransport1':
		if 'State' in properties:
			state = properties['State']
			if state == 'active':
				print "active"
				playing = True
				letterOff = 0
			elif state == 'idle':
				print "idle"
				playing = False
	elif interface == 'org.bluez.MediaPlayer1':
		if 'Track' in properties:
			track = properties['Track']
			if 'Title' in track:
				# non ASCII characters go bork
				songName = track['Title'].encode("ascii", "ignore").decode()
				letterOff = 0
			if 'Artist' in track:
				artist = track['Artist'].encode("ascii", "ignore").decode()
			if 'Album' in track:
				album = track['Album'].encode("ascii", "ignore").decode()
	elif 'Device' in properties:
		print "connected: true"
		connected = True

# Utility functions

# EX: transmit(0x123,[0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00])
def transmit(idd, dat):
	can0.send(can.Message(arbitration_id=idd, data=dat, extended_id=False))

# BEEP BEEP
def beep():
	transmit(0x430, [0x80,0x04,0x00,0x00,0x00,0x00,0x00,0x00])

# Functions for head controls
# and yes most of them aren't used
def play():
	global playerIface
	print "play"
	playerIface.Play(dbus_interface='org.bluez.MediaPlayer1')

def pause():
	global playerIface
	# global connected
	# print connected
	# if connected:
	print "pause"
	playerIface.Pause(dbus_interface='org.bluez.MediaPlayer1')

def shuffle():
	global playerIface
	print "shuffle"
	playerIface.Shuffle(dbus_interface='org.bluez.MediaPlayer1')

def nxt():
	global playerIface
	print "next"
	playerIface.Next(dbus_interface='org.bluez.MediaPlayer1')

def prev():
	global playerIface
	print "previous"
	playerIface.Previous(dbus_interface='org.bluez.MediaPlayer1')

def mute():
	global playerIface
	global muteBool
	print "mute"
	muteBool = not muteBool
	if muteBool:
		os.system('amixer -q -M sset Master 0%')
	else:
		os.system('amixer -q -M sset Master 100%')

def ff():
	global playerIface
	print "fast forward"
	playerIface.FastForward(dbus_interface='org.bluez.MediaPlayer1')

def rr():
	global playerIface
	print "rewind"
	playerIface.rewind(dbus_interface='org.bluez.MediaPlayer1')

def bluetoothOn():
	global phoneMAC
	print adaptIface.Get('org.bluez.Adapter1', 'Powered')
	os.system('echo "power on" | bluetoothctl')
	os.system('echo "connect '+phoneMAC+'" | bluetoothctl')
	os.system('echo "quit" | bluetoothctl')
	print adaptIface.Get('org.bluez.Adapter1', 'Powered')

def bluetoothOff():
	global playing
	global songName
	global artist
	global album
	print adaptIface.Get('org.bluez.Adapter1', 'Powered')
	os.system('echo "power off" | bluetoothctl')
	os.system('echo "quit" | bluetoothctl')
	print adaptIface.Get('org.bluez.Adapter1', 'Powered')
	playing=False
	songName=""
	artist=""
	album=""

# Print functions that write text to the sid
def spaPrint(upper, lower):
	sent = False
	# A brutalization? Probly. Do I care? No.
	data = 	[[0x45,0x96,0x01,ord(upper[0:1]),ord(upper[1:2]),ord(upper[2:3]),ord(upper[3:4]),ord(upper[4:5])],
			[0x04,0x96,0x01,ord(upper[5:6]),ord(upper[6:7]),ord(upper[7:8]),ord(upper[8:9]),ord(upper[9:10])],
			[0x03,0x96,0x01,ord(upper[10:11]),ord(upper[11:12]),0x00,0x00,0x00],
			[0x02,0x96,0x02,ord(lower[0:1]),ord(lower[1:2]),ord(lower[2:3]),ord(lower[3:4]),ord(lower[4:5])],
			[0x01,0x96,0x02,ord(lower[5:6]),ord(lower[6:7]),ord(lower[7:8]),ord(lower[8:9]),ord(lower[9:10])],
			[0x00,0x96,0x02,ord(lower[10:11]),ord(lower[11:12]),0x00,0x00,0x00]
		]
	# Just look at that hardcoding man. Now thats hardcore.
	transmit(0x337,data[0])
	transmit(0x337,data[1])
	transmit(0x337,data[2])
	transmit(0x337,data[3])
	transmit(0x337,data[4])
	transmit(0x337,data[5])
	# Technically how the i-bus expects the spa print to function
	# Doesnt really work when your fighting things for the sid
	# if sent:
	#	# Sends keep displaying it, but is almost utterly ignored
	# 	permission = [0x1f,0x01,0x05,0x12,0x00,0x00,0x00,0x00]
	# else:
	#	# Sends an AH stuffs happend!
	# 	permission = [0x1f,0x00,0x04,0x08,0x00,0x00,0x00,0x00]
	# 	sent = True
	# transmit(0x357,permission)
	transmit(0x357,[0x1f,0x00,0x04,0x08,0x00,0x00,0x00,0x00])
	threading.Timer(1,spaPrint,[upper, lower]).start()

def spaPrintL(lower):
	sent = False
	data = 	[[0x42,0x96,0x02,ord(lower[0:1]),ord(lower[1:2]),ord(lower[2:3]),ord(lower[3:4]),ord(lower[4:5])],
			[0x01,0x96,0x02,ord(lower[5:6]),ord(lower[6:7]),ord(lower[7:8]),ord(lower[8:9]),ord(lower[9:10])],
			[0x00,0x96,0x02,ord(lower[10:11]),ord(lower[11:12]),0x00,0x00,0x00]
		]
	transmit(0x337,data[0])
	transmit(0x337,data[1])
	transmit(0x337,data[2])
	# if sent:
	# 	dispco = [0x1f,0x01,0x05,0x12,0x00,0x00,0x00,0x00]
	# else:
	# 	dispco = [0x1f,0x00,0x04,0x08,0x00,0x00,0x00,0x00]
	# 	sent = True
	# transmit(0x357,dispco)
	transmit(0x357,[0x1f,0x00,0x04,0x08,0x00,0x00,0x00,0x00])
	#threading.Timer(1,spaPrintL,[lower]).start()

def audioPrint(upper, lower):
	sent = False
	# carbon copies, Ill take your entire stock
	data = 	[[0x45,0x96,0x01,ord(upper[0:1]),ord(upper[1:2]),ord(upper[2:3]),ord(upper[3:4]),ord(upper[4:5])],
			[0x04,0x96,0x01,ord(upper[5:6]),ord(upper[6:7]),ord(upper[7:8]),ord(upper[8:9]),ord(upper[9:10])],
			[0x03,0x96,0x01,ord(upper[10:11]),ord(upper[11:12]),0x00,0x00,0x00],
			[0x02,0x96,0x02,ord(lower[0:1]),ord(lower[1:2]),ord(lower[2:3]),ord(lower[3:4]),ord(lower[4:5])],
			[0x01,0x96,0x02,ord(lower[5:6]),ord(lower[6:7]),ord(lower[7:8]),ord(lower[8:9]),ord(lower[9:10])],
			[0x00,0x96,0x02,ord(lower[10:11]),ord(lower[11:12]),0x00,0x00,0x00]
		]
	transmit(0x328,data[0])
	transmit(0x328,data[1])
	transmit(0x328,data[2])
	transmit(0x328,data[3])
	transmit(0x328,data[4])
	transmit(0x328,data[5])

	# Text priority, does it work this way i dunno
	transmit(0x368,[0x01,0xff,0x00,0x00,0x00,0x00,0x00,0x00])
	transmit(0x368,[0x02,0xff,0x00,0x00,0x00,0x00,0x00,0x00])
	threading.Timer(1,audioPrint,[upper, lower]).start()

def audioPrintL(lower):
	sent = False
	data = 	[[0x42,0x96,0x02,ord(lower[0:1]),ord(lower[1:2]),ord(lower[2:3]),ord(lower[3:4]),ord(lower[4:5])],
			[0x01,0x96,0x02,ord(lower[5:6]),ord(lower[6:7]),ord(lower[7:8]),ord(lower[8:9]),ord(lower[9:10])],
			[0x00,0x96,0x02,ord(lower[10:11]),ord(lower[11:12]),0x00,0x00,0x00]
		]
	transmit(0x328,data[0])
	transmit(0x328,data[1])
	transmit(0x328,data[2])

	transmit(0x348,[0x11,0x02,0x05,0x01,0x00,0x00,0x00,0x00])
	transmit(0x368,[0x02,0x01,0x00,0x00,0x00,0x00,0x00,0x00])
	#threading.Timer(1,spaPrintL,[lower]).start()

def display():
	global cdOn
	global songName
	global noSongText
	global playing
	global letterOff
	if not cdOn:
		letterOff=0
	elif not playing:
		spaPrintL(noSongText)
		#audioPrintL(noSongText)
	elif len(songName)<=12:
		spaPrintL(songName.ljust(12))
		#audioPrintL(songName.ljust(12))
	else:
		spaPrintL(songName.center(len(songName)+6)[letterOff:12+letterOff]+songName)
		#audioPrintL(songName.center(len(songName)+6)[letterOff:12+letterOff]+songName)
		letterOff = (letterOff+1)%(len(songName)+3)
	threading.Timer(1,display).start()


# Sends cd changer identfier so head recognizes cd changer

def cdc():
	global cdcode
	global carOn
	if carOn:
		transmit(0x3c8, cdcode)
		time.sleep(10/1000)
	threading.Timer(0.80,cdc).start()

def command():
	global cdOn
	global count
	global cdcode
	global playing
	global carOn
	global mute
	global shuffle
	global songName
	global adaptIface
	global phoneMAC
	global bus
	global connected
	msg = can0.recv(0.1)
	# Cd changer command Id and an issued command
	if msg is not None and msg.arbitration_id!=0x004:
		count=0
		if not carOn:
			print "power on! bluetooth mode"
			carOn = True
			#bluetoothOn()
		if msg.arbitration_id==0x3c0 and msg.data[0]==0x80:
			if msg.data[1]==0x24:
				cdOn = True
				bluetoothOn()
				#os.system('echo "' +phoneMAC+'  \nquit" | bluetoothctl')
				#cdcode=[0xe0,0x00,0x3f,0x71,0x01,0x04,0x04,0xd0]
				#play()
				#beep()
			elif msg.data[1]==0x14:
				cdOn = False
				bluetoothOff()
				#pause()
				transmit(0x357,[0x1f,0x00,0xff,0x00,0x00,0x00,0x00,0x00])
				#cdcode=[0xe0,0x00,0x3f,0x31,0xff,0xff,0xff,0xd0]
				#beep()

			if cdOn:
				# DISCREPENCIES DETECTED!
				# No idea if its just my car but any steering wheel commands
				# get converted to cd changer command. Oddly enought though
				# my head unit refuses to transmit its inputs through the cd
				# changer command so no clue there.

				# Through Research ive come to the conclusion that only the
				# 1-6 buttons work, annoyingly.

				# The next button on the wheel
				if msg.data[1]==0x59:
					if playing:
						pause()
					else:
						play()
				# Should be long press of CD/RDM no clue if it works
				# I should have tried at some point but i dont remember
				elif msg.data[1]==0x76:
					shuffle()
				# One of these is mute/unmute but its a singe button I
				# dont think well be getting two mute signals in a row
				elif msg.data[1]==0xb1 or msg.data[1]==0xb0:
					mute()
				# Should be seek forward never got it to work
				elif msg.data[1]==0x35:
					ff()
				# Should be seek back never got it to work too
				elif msg.data[1]==0x36:
					rr()
				# six number buttons on head unit, causes play cd1 to appear
				elif msg.data[1]==0x68:
					# button 1
					if msg.data[2]==0x01:
						mute()
		elif msg.arbitration_id==0x290 and msg.data[0]==0x80:
			print msg
			if msg.data[2]==0x10:
				nxt()
			elif msg.data[2]==0x08:
				prev()
			#src button just switches between cd changer and radio
			#elif msg.data[2]==0x01:
				#mute()
			elif msg.data[3]==0x80:
				dispOn = False
	elif msg == None and carOn:
		if count==3:
			print "Power off"
			bluetoothOff()
			carOn = False
			count = 0
			connected = False
		else:
			count+=1

	threading.Timer(0,command).start()

#start
cdc()
display()
command()

#because dbus is still so dumb

def init():
	global bus
	global songName
	global playing
	global cdOn
	global adaptIface
	bluetoothOff()
	os.system('amixer -q -M sset Master 100%')
	bus.add_signal_receiver(
		dbusChange,
		bus_name='org.bluez',
		signal_name='PropertiesChanged',
		dbus_interface='org.freedesktop.DBus.Properties',
		path_keyword='path')

	# medinterface = dbus.Interface(playerIface,'org.freedesktop.DBus.Properties')
	# track = medinterface.Get('org.bluez.MediaPlayer1', 'Track')
	# songName = track['Title']

	# print songName

	# transinterface = dbus.Interface(transIface, 'org.freedesktop.DBus.Properties')
	# status = transinterface.Get('org.bluez.MediaTransport1', 'State')
	# if status == 'active':
	# 	if not cdOn:
	# 		pause()
	# 	else:
	# 		playing = True
	# elif status == 'idle':
	# 	pass

def runMainLoop():
	mainloop.run()

if __name__ == '__main__':
	init()
	gobject.threads_init()
	mainloop = gobject.MainLoop()
	mainloopThread = threading.Thread(name='mainloop', target=runMainLoop)
	mainloopThread.setDaemon(True)
	mainloopThread.start()

