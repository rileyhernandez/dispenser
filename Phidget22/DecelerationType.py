import sys
import ctypes
class DecelerationType:
	# Configures the motor for coasting deceleration
	DECELERATION_TYPE_COAST = 1
	# Configures the motor for forced deceleration
	DECELERATION_TYPE_FORCED = 2

	@classmethod
	def getName(self, val):
		if val == self.DECELERATION_TYPE_COAST:
			return "DECELERATION_TYPE_COAST"
		if val == self.DECELERATION_TYPE_FORCED:
			return "DECELERATION_TYPE_FORCED"
		return "<invalid enumeration value>"
