import sys
import ctypes
class PositionType:
	# Configures the controller to use the encoder as a position source
	POSITION_TYPE_ENCODER = 1
	# Configures the controller to use the hall-effect sensor as a position source
	POSITION_TYPE_HALL_SENSOR = 2

	@classmethod
	def getName(self, val):
		if val == self.POSITION_TYPE_ENCODER:
			return "POSITION_TYPE_ENCODER"
		if val == self.POSITION_TYPE_HALL_SENSOR:
			return "POSITION_TYPE_HALL_SENSOR"
		return "<invalid enumeration value>"
