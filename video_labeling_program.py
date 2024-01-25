import cv2, os
import json

'''
    프로그램을 실행하면, 지정된 영상(sample.mp4)이 실행됩니다.
    
    기능
        - 'p' 키를 입력하면 영상을 재생 및 멈출 수 있습니다
        - 정지된 상태에서 영역을 드래그 하면 사각형 영역을 선택할 수 있습니다
            - 여러 영역을 선택한 후 's'키를 누르면 json 파일 및 이미지.png를 저장합니다
        - 'q' 키를 입력하면 영상을 종료합니다.
    
'''

class VideoLabelingTool:
    def __init__(self, video_path):
        self.video_path = video_path # 동영상 경로
        self.video_capture = cv2.VideoCapture(video_path)
        self.rect_start_point = None # 좌표 초기화
        self.rect_end_point = None # 좌표 초기화
        self.start_point_save = [] # 드래그 시작 좌표를 저장히기 위한 리스트
        self.end_point_save = [] # 드래그 끝 좌표를 저장하기 위한 리스트
        self.drawing = False # 그리기 상태를 추적하기 위한 변수
        self.labels = [] # 좌표 및 이미지 경로를 저장하기 위한 리스트
        self.nums = 0 # 이미지 및 데이터를 저장하기 위한 변수
        self.paused = False  # 동영상 정지 상태를 추적하기 위한 변수
        self.ready = False # 캡처 준비 상태를 추적하기 위한 변수
        self.image_folder = "captured_images"  # 캡쳐된 이미지를 저장할 폴더
        os.makedirs(self.image_folder, exist_ok=True)  # 폴더가 없으면 생성

    def mouse_callback(self, event, x, y, flags, param):
        if self.paused:  # 정지 상태에서만 사각형 그리기를 수행합니다.
            if event == cv2.EVENT_LBUTTONDOWN:
                self.drawing = True
                self.ready = True
                self.rect_start_point = (x, y)

            elif event == cv2.EVENT_MOUSEMOVE:
                if self.drawing:
                    self.rect_end_point = (x, y)

            elif event == cv2.EVENT_LBUTTONUP:
                self.drawing = False
                self.ready = False
                self.rect_end_point = (x, y)

    def run(self):
        cv2.namedWindow("Video")
        cv2.setMouseCallback("Video", self.mouse_callback)

        while self.video_capture.isOpened():
            if not self.paused:  # 정지 상태가 아니면 동영상을 계속 재생합니다.
                ret, self.current_frame = self.video_capture.read()
                if not ret:
                    break

            if self.rect_start_point and self.rect_end_point and self.ready is False and self.paused:
                # 시작 좌표와 정지 좌표, 그리기 준비 상태가 아니며, 영상이 멈춰 있는 경우
                cv2.rectangle(self.current_frame, self.rect_start_point, self.rect_end_point, (0, 255, 0), 2)
                # 초록색 사각형 그리기
                # 좌측 상단에서 우측 상단 그리기 외 작업시 좌표점 표준화
                x1, y1 = self.rect_start_point
                x2, y2 = self.rect_end_point
                top_left = (min(x1, x2), min(y1, y2))
                bottom_right = (max(x1, x2), max(y1, y2))

                self.start_point_save.append(top_left)
                self.end_point_save.append(bottom_right)
                # 하나의 사각형을 그리면 새로운 사각형을 그리는 상태로 변경
                self.ready = True


            cv2.imshow("Video", self.current_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                # q 버튼을 클릭시 동영상을 종료
                break
            elif key == ord('p'):
                # 'p' 키를 누르면 동영상 재생/정지를 토글합니다.
                self.paused = not self.paused
                # 동영상 정지 / 재생시 그리는 사각형 데이터를 초기화
                self.rect_start_point = None
                self.rect_end_point = None
                self.start_point_save = []
                self.end_point_save = []
                self.labels = []
            elif key == ord('s'):
                # 's'키를 누르면 지정된 영역들을 저장합니다.
                self.capture_and_save_area()  # 영역 캡쳐 및 저장 메소드 호출

        self.video_capture.release()
        cv2.destroyAllWindows()

    def capture_and_save_area(self):

        # 저장된 영역들이 없는 경우 저장하지 않음
        if not len(self.start_point_save) or not len(self.end_point_save):
            return
        # 저장된 영역들을 순환하면서 저장합니다.
        for idx in range(len(self.start_point_save)):

            p1 = self.start_point_save[idx]
            p2 = self.end_point_save[idx]

            x1, y1 = p1[0], p1[1]
            x2, y2 = p2[0], p2[1]

            captured_image = self.current_frame[y1:y2, x1:x2]  # 영역 캡쳐

            image_path = os.path.join(self.image_folder, f"image_{self.nums}.png")
            cv2.imwrite(image_path, captured_image)  # 이미지 저장

            self.labels.append({
                'start_point': p1,
                'end_point': p2,
                'image_path': image_path  # JSON에 이미지 경로 저장
            })

            file_name = f'labels_{self.nums}.json'

            with open(file_name, 'w') as file:
                json.dump(self.labels, file, indent=4)

            self.nums += 1
            self.labels = []

if __name__ == "__main__":
    tool = VideoLabelingTool("./sample.mp4")
    tool.run()