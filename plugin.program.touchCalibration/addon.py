import calendar
import sys
import os
import xbmc
import xbmcgui
import xbmcaddon

SWAP_AXES_THRESHOLD = 10
ACTION_PREVIOUS_MENU = 10
ACTION_SELECT_ITEM = 7
ACTION_BACKSPACE = 92

TEXT_ALIGN_LEFT = 0
TEXT_ALIGN_RIGHT = 1
TEXT_ALIGN_CENTER_X = 2
TEXT_ALIGN_CENTER_Y = 4
TEXT_ALIGN_RIGHT_CENTER_Y = 5
TEXT_ALIGN_LEFT_CENTER_X_CENTER_Y = 6

class touchCalibration(xbmcgui.WindowDialog):

	def __init__(self):
		# Go to a new window to see animations from Home
		# TODO: - Create a new empty window instead of using Programs
		#       - Add text with "You don't have the radio module or the radio server was not
		#         started"
		xbmc.executebuiltin("XBMC.ActivateWindow(Programs)")
		self.retval=0
		self.clientScript=os.path.join(addon.getAddonInfo('path'),'resources','radio_client.py')
		self.stations=os.path.join(addon.getAddonInfo('path'),'resources','stations')
		self.mediaPath=os.path.join(addon.getAddonInfo('path'),'resources','media') + '/'

		# Background
		#self.w = self.getWidth()
		#self.h = self.getHeight()
		self.w = 1280
		self.h = 720
		self.background = xbmcgui.ControlImage(0,0,self.w,self.h,self.mediaPath + 'background.jpg',
		colorDiffuse = '0xffffffff')
		self.addControl(self.background)

		self.calibrationFile = "/home/pi/touchscreen_calibration_log"
		self.touchAxesCalib = "/home/pi/touchscreen_axes_calib"

		# Target
		self.targetW = 50
		self.targetH = 50
		self.x1 = 0
		self.y1 = 0
		self.x2 = self.w - self.targetW
		self.y2 = 0
		self.x3 = self.w - self.targetW
		self.y3 = self.h - self.targetH
		self.x4 = 0
		self.y4 = self.h - self.targetH
		self.targetImagePath = self.mediaPath + 'target.png'
		self.currentTarget = 1 # initial target index
		# Values used for calibration
		self.p1x = 0
		self.p1y = 0
		self.p2x = 0
		self.p2y = 0
		self.p3x = 0
		self.p3y = 0
		self.p4x = 0
		self.p4y = 0

		# First target
		self.targetImage = xbmcgui.ControlImage(self.x1, self.y1,
			self.targetW, self.targetH,
			self.targetImagePath, colorDiffuse='0xffffffff')
		self.addControl(self.targetImage)

		# Menu button
		#self.home_button=xbmcgui.ControlImage(0,0,70,70,
		#										self.mediaPath + 'textures/icon_home.png',
		#										colorDiffuse='0xffffffff')
		#self.button_menu=xbmcgui.ControlButton(0,0,70,70,
		#										"",
		#										self.mediaPath + 'textures/floor_buttonfo.png',
		#										self.mediaPath + 'textures/floor_button.png',
		#										0,
		#										0)
		#self.addControl(self.button_menu)
		#self.setFocus(self.button_menu)
		#self.addControl(self.home_button)

		# Mouse Position label
		self.mouse_pos = xbmcgui.ControlLabel(
			10, self.h/2 - 70,
			500, 40,
			"",
			textColor='0xffffffff',
			font='font30',
			alignment=TEXT_ALIGN_LEFT)
		self.addControl(self.mouse_pos)
		#self.mouse_pos.setLabel(str(self.w) + "x" + str(self.h))
		
		# Informational text label
		self.info = xbmcgui.ControlLabel(
			10, self.h/2 - 40,
			1000, 400,
			"",
			textColor='0xffffffff',
			font='font30',
			alignment=TEXT_ALIGN_LEFT)
		self.addControl(self.info)
		self.info.setLabel("Touch the top left point and then press ENTER")

	def onControl(self, controlID):
		if controlID == self.button_menu:
			# Go to Home Window
			xbmc.executebuiltin("XBMC.ActivateWindow(Home)")
			self.retval=0
			self.close()

	def onAction(self, action):
		if action == ACTION_SELECT_ITEM:
			pos = xbmcgui.getMouseRawPosition()
			pos_string ="x:%i y:%i" % (pos/10000, pos%10000)
			self.mouse_pos.setLabel(pos_string)
			self.removeControl(self.targetImage)
			self.currentTarget = self.currentTarget + 1

			if self.currentTarget == 2:
				self.info.setLabel("Touch the top right point and then press ENTER")
				self.p1x = xbmcgui.getMouseRawPosition()/10000
				self.p1y = xbmcgui.getMouseRawPosition()%10000
				# Second target
				self.targetImage = xbmcgui.ControlImage(self.x2, self.y2,
					self.targetW, self.targetH,
					self.targetImagePath, colorDiffuse='0xffffffff')
				self.addControl(self.targetImage)

			if self.currentTarget == 3:
				self.info.setLabel("Touch the bottom right point and then press ENTER")
				self.p2x = xbmcgui.getMouseRawPosition()/10000
				self.p2y = xbmcgui.getMouseRawPosition()%10000
				# Third target
				self.targetImage = xbmcgui.ControlImage(self.x3, self.y3,
					self.targetW, self.targetH,
					self.targetImagePath, colorDiffuse='0xffffffff')
				self.addControl(self.targetImage)

			if self.currentTarget == 4:
				self.info.setLabel("Touch the bottom left point and then press ENTER")
				self.p3x = xbmcgui.getMouseRawPosition()/10000
				self.p3y = xbmcgui.getMouseRawPosition()%10000
				# Fourth target
				self.targetImage = xbmcgui.ControlImage(self.x4, self.y4,
					self.targetW, self.targetH,
					self.targetImagePath, colorDiffuse='0xffffffff')
				self.addControl(self.targetImage)

			if self.currentTarget == 5:
				self.p4x = xbmcgui.getMouseRawPosition()/10000
				self.p4y = xbmcgui.getMouseRawPosition()%10000
				# Compute values and write them in the file
				doCalibration(self)

		if action == ACTION_PREVIOUS_MENU or action == ACTION_BACKSPACE:
			self.retval=0
			self.close()

DELTA = 10

'''
Compute the calibration values and write them in the file
'''
def doCalibration(self):
	# Predefined values
	x1 = self.x1 + 25
	x2 = self.x2 + 25
	x3 = self.x3 + 25
	x4 = self.x4 + 25
	y1 = self.y1 + 25
	y2 = self.y2 + 25
	y3 = self.y3 + 25
	y4 = self.y4 + 25

	# Read values
	px1 = self.p1x
	px2 = self.p2x
	px3 = self.p3x
	px4 = self.p4x
	py1 = self.p1y
	py2 = self.p2y
	py3 = self.p3y
	py4 = self.p4y
	
	fd = open(self.calibrationFile,'w')
	
	fd.write(str(self.w) + "x" + str(self.h) + "\n")
	fd.write("Touch screen calibration plugin\n")
	fd.write("Predefined points:\n")
	fd.write(str(x1) + "," + str(y1) + '\n')
	fd.write(str(x2) + "," + str(y2) + '\n')
	fd.write(str(x3) + "," + str(y3) + '\n')
	fd.write(str(x4) + "," + str(y4) + '\n')
	fd.write("\nObtained points:\n")
	fd.write(str(px1) + "," + str(py1) + '\n')
	fd.write(str(px2) + "," + str(py2) + '\n')
	fd.write(str(px3) + "," + str(py3) + '\n')
	fd.write(str(px4) + "," + str(py4) + '\n')

	# Final values
	calib_x_fact = 1.0
	calib_y_fact = 1.0
	calib_x_d = 0
	calib_y_d = 0
	swap_axes = 0
	click_confines = 8
	touch_mouse = 1

	case1 = 0
	case2 = 0
	startx = 0
	starty = 0
	rev = 0

	if px2 > px1 + DELTA or px1 > px2 + DELTA:
		# Compute the ratio between the big screen(touch) and the visible screen(the ratio can
		# be negative)
		calib_x_fact = float(x2 - x1) / float(px2 - px1)
		calib_y_fact = float(y4 - y1) / float(py4 - py1)

		tmp_calib_x_fact = calib_x_fact
		if calib_x_fact < 0.0:
			tmp_calib_x_fact *= -1.0

		tmp_calib_y_fact = calib_y_fact
		if calib_y_fact < 0.0:
			tmp_calib_y_fact *= -1.0

		# whichever point is the left one decides the x offset of the touch frame
		if px2 > px1 + DELTA:
			# cases 1 & 4
			case1 = 14
			calib_px = float(px1) * tmp_calib_x_fact
			calib_px_i = int(calib_px)

			if x1 > calib_px_i:
				calib_x_d = x1 - calib_px_i
			else:
				calib_x_d = calib_px_i - x1
		if px1 > px2 + DELTA:
			# cases 5 & 8
			case1 = 58

			# take the left margin as reference
			calib_px = float(px2) * tmp_calib_x_fact
			calib_px_i = int(calib_px) - 25
			
			if x1 > calib_px_i:
				calib_x_d = self.w + (x1 - calib_px_i)
			else:
				calib_x_d = self.w + (calib_px_i - x1)
			
			'''
			# take the right margin as reference
			calib_px = float(px1) * tmp_calib_x_fact
			calib_px_i = int(calib_px)
			fd.write(str(calib_px_i)+'\n')
			if x2 > calib_px_i:
				calib_x_d = self.w - (x2 - calib_px_i)
			else:
				calib_x_d = self.w - (calib_px_i - x2)
			'''
		if py4 > py1 + DELTA or py1 > py4 + DELTA:
			# whichever point is the top one decides the y offset of the touch frame
			if py4 > py1 + DELTA:
				# cases 1 & 8
				case2 = 18
				calib_py = float(py1) * tmp_calib_y_fact
				calib_py_i = int(calib_py)

				if y1 > calib_py_i:
					calib_y_d = y1 - calib_py_i
				else:
					calib_y_d = calib_py_i - y1
				'''
				if y1 > py1:
					calib_y_d = y1 - py1
				else:
					calib_y_d = py1 - y1
				'''
			if py1 > py4 + DELTA:
				# cases 4 & 5
				case2 = 45
				calib_py = float(py4) * tmp_calib_y_fact
				calib_py_i = int(calib_py)

				if y1 > calib_py_i:
					calib_y_d = self.h + (y1 - calib_py_i)
				else:
					calib_y_d = self.h + (calib_py_i - y1)
				#calib_y_d = self.h - int(float(y1 - py4) * tmp_calib_y_fact)
	else:
		rev = 1

	'''
	if px4 > px1 + DELTA or px1 > px4 + DELTA:
		# whichever point is the left one decides the x offset of the touch frame
		if px4 > px1 + DELTA:
			# cases 2 & 7
			case1 = 27
			if x1 > px1:
				calib_x_d = x1 - px1
			else:
				calib_x_d = px1 - x1
		if px1 > px4 + DELTA:
			# cases 3 & 6
			case1 = 36
			if x4 > px4:
				calib_x_d = self.w - (x4 - px4)
			else:
				calib_x_d = self.w - (px4 - x4)
		if py2 > py1 + DELTA or py1 > py2 + DELTA:
			# whichever point is the top one decides the y offset of the touch frame
			if py2 > py1 + DELTA:
				# cases 2 & 3
				case2 = 23
				if y1 > py1:
					calib_y_d = y1 - py1
				else:
					calib_y_d = py1 - y1
			if py1 > py2 + DELTA:
				# cases 6 & 7
				case2 = 67
				if y2 > py2:
					calib_y_d = self.h - (y2 - py2)
				else:
					calib_y_d = self.h - (py2 - y2)

			# Compute the ratio between the big screen(touch) and the visible screen(the ratio can
			# be negative)
			calib_x_fact = float(x2 - x1) / float(px4 - px1)
			calib_y_fact = float(y4 - y1) / float(py2 - py1)
	'''

	if rev == 1:
		xbmcgui.Dialog().ok("Please reverse touch screen cable","Please reverse the touch screen cable comming from the \nscreen and going into the usb controller and then try \nagain")
		fd.write("Please reverse the touch screen cable comming from the screen and going into the usb controller")
		fd.close()

		# Restart with the first target
		self.currentTarget = 1 # initial target index
		self.targetImage = xbmcgui.ControlImage(self.x1, self.y1,
			self.targetW, self.targetH,
			self.targetImagePath, colorDiffuse='0xffffffff')
		self.addControl(self.targetImage)
	else:
		# Compute the main case
		case = 0

		if case1 / 10 == case2 / 10:
			case = case1 / 10
		if case1 % 10 == case2 % 10:
			case = case1 % 10
		if case1 / 10 == case2 % 10:
			case = case1 / 10
		if case1 % 10 == case2 / 10:
			case = case1 % 10
		if case == 2 or case == 3 or case == 6 or case == 7:
			swap_axes = 1

		# Debug values
		fd.write("\n")
		#fd.write("startx=" + str(startx) + "  starty=" + str(starty) + '\n')
		fd.write("case=" + str(case))
		fd.write("\n")
		fd.write("calib_x_d=" + str(calib_x_d) + ';')
		fd.write("calib_x_fact=" + str(calib_x_fact) + ';')
		fd.write("calib_y_d=" + str(calib_y_d) + ';')
		fd.write("calib_y_fact=" + str(calib_y_fact) + ';')
		fd.write("swap_axes=" + str(swap_axes) + ';')
		fd.write("click_confines=" + str(click_confines) + ';')
		fd.write("touch_mouse=" + str(touch_mouse))
		fd.close()

		# Calibration values
		fd = open(self.touchAxesCalib, 'w')
		fd.write("calib_x_d=" + str(calib_x_d) + ';')
		fd.write("calib_x_fact=" + str(calib_x_fact) + ';')
		fd.write("calib_y_d=" + str(calib_y_d) + ';')
		fd.write("calib_y_fact=" + str(calib_y_fact) + ';')
		fd.write("swap_axes=" + str(swap_axes) + ';')
		fd.write("click_confines=" + str(click_confines) + ';')
		fd.write("touch_mouse=" + str(touch_mouse))
		fd.close()

		self.retval=0
		self.close()

addon = xbmcaddon.Addon(id='plugin.program.touchCalibration')
finished=0
counter=0

while finished == 0:
	dialog=touchCalibration()
	dialog.doModal()

	if dialog.retval == 0:
		finished = 1
	del dialog
del addon
