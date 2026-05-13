import cv2
import numpy as np


def identify_team(player_crop) -> str:
    """Classify a player crop as one of: red, yellow, white, black, background.

    Yellow is preserved as a distinct label so callers can map it to referees.
    """
    hsv = cv2.cvtColor(player_crop, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    lower_yellow = np.array([22, 150, 150])
    upper_yellow = np.array([32, 255, 255])

    lower_white = np.array([0, 0, 180])
    upper_white = np.array([180, 40, 255])

    lower_black = np.array([0, 0, 0])
    upper_black = np.array([180, 255, 60])

    mask_red = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(
        hsv, lower_red2, upper_red2
    )
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    mask_white = cv2.inRange(hsv, lower_white, upper_white)
    mask_black = cv2.inRange(hsv, lower_black, upper_black)

    counts = {
        "red": int(np.sum(mask_red > 0)),
        "yellow": int(np.sum(mask_yellow > 0)),
        "white": int(np.sum(mask_white > 0)),
        "black": int(np.sum(mask_black > 0)),
    }

    best_match = max(counts, key=counts.get)
    if counts[best_match] < 100:
        return "background"
    return best_match
