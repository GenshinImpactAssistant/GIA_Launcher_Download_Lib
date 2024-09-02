from ultralytics import YOLO
import random

from source.util import *
from source.funclib.movement import view_to_position
from source.funclib import movement
from source.interaction.interaction_core import itt

COMBAT_MODEL = YOLO(f"{ROOT_PATH}\\assets\\YoloxModels\\combat.pt")

def predict_img(img:np.ndarray):
    r_json = COMBAT_MODEL.predict(img, show=DEBUG_MODE)[0].tojson()
    r_dict = json.loads(r_json)
    possible_points = {
        "ball":[],
        "beam": [],
        "flicker": [],
    }
    MIN_CONFIDENCE = 0.3
    if len(r_dict) > 0:
        for i in r_dict:
            bbox = i['box']
            possible_points[i['name']].append([(bbox['x1'] + bbox['x2'])/2, (bbox['y1'] + bbox['y2'])/2])
        return possible_points
    else:
        return None

def find_possible_spoils():
    movement.reset_view()
    for i in range(10):
        movement.cview(45)
        movement.cview(random.randint(-3,3)*90, mode=movement.VERTICALLY)
        itt.delay(0.2)
        if predict_img(itt.capture()):
            return True
    return False

def move_to_possible_spoils():
    spoil_exist_flag = False
    find_ball_only = False
    giveup_times = 0
    while 1:
        predict_result = predict_img(itt.capture())

        if predict_result is not None:
            spoil_exist_flag = True
            if len(predict_result['ball']) > 0:
                pos = predict_result['ball']
                for i in range(len(pos)):
                    pos[i][1]+=200
                r = view_to_position(pos)
                giveup_times = 0
                find_ball_only = True

            if not find_ball_only:
                if len(predict_result['flicker']) > 0:
                    r = view_to_position(predict_result['flicker'])
                elif len(predict_result['beam']) > 0:
                    r = view_to_position(predict_result['beam'])
                else:
                    continue
            movement.move(movement.MOVE_AHEAD, 1)

        else:
            if not spoil_exist_flag:
                logger.info(f"no spoil exist, break")
                return False
            elif giveup_times > 5:
                logger.info(f"fail many times, break")
                return False
            else:
                giveup_times += 1
                logger.info(f"giveup_times+=1")
                itt.move_to(0,200,relative=True)
                movement.move(movement.MOVE_AHEAD,1)


if __name__ == '__main__' and True:

    while 1:
        img = itt.capture()
        r = COMBAT_MODEL.predict(img, show=True)
        #print(r)

if __name__ == '__main__':
    while 1:

        r = find_possible_spoils()
        if r:
            move_to_possible_spoils()