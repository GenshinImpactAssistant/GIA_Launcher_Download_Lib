import cv2
import time
from source.interaction.interaction_core import itt
from source.util import *
while 1:
    input('enter to capture')
    cap = itt.capture(jpgmode=NORMAL_CHANNELS)
    cv2.imwrite(ROOT_PATH + '\\' + "tools\\snapshot\\" + str(time.time()) + ".png", cap) # type: ignore

