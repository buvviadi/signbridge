import cv2
import mediapipe as mp

holistic = mp.solutions.holistic.Holistic(model_complexity=1)
drawing = mp.solutions.drawing_utils
conn = mp.solutions.holistic

cap = cv2.VideoCapture(0)
print("Webcam open. Wave your hands. Press Q in the window to quit.")

while True:
    ok, frame = cap.read()
    if not ok:
        print("Could not read from webcam")
        break
    result = holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    drawing.draw_landmarks(frame, result.pose_landmarks, conn.POSE_CONNECTIONS)
    drawing.draw_landmarks(frame, result.left_hand_landmarks, conn.HAND_CONNECTIONS)
    drawing.draw_landmarks(frame, result.right_hand_landmarks, conn.HAND_CONNECTIONS)

    cv2.imshow("Landmarks (Q to quit)", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
