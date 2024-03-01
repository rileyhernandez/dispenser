from Phidget22.Phidget import *
from Phidget22.Devices.DigitalOutput import *

def main():
    try:
        digitalOutput0 = DigitalOutput()
        digitalOutput0.setDeviceSerialNumber(716692)
        digitalOutput0.openWaitForAttachment(5000)
        # Your code to control the digital output goes here
    except PhidgetException as e:
        print(f"PhidgetException {e.code} ({e.description}): {e.details}")

if __name__ == "__main__":
    main()
