import depthai as dai
from src.face_detection import FaceDetector
from src.display import Display
from src.performance_monitor import PerformanceMonitor

def main():
    pipeline = dai.Pipeline()
    detector = FaceDetector(pipeline)
    display = Display()
    performance_monitor = PerformanceMonitor(pipeline)

    with dai.Device(pipeline) as device:
        q_rgb = device.getOutputQueue("rgb")
        q_nn = device.getOutputQueue("nn")
        system_queue = device.getOutputQueue("system_logger")

        while True:
            frame = detector.get_frame(q_rgb)
            detections = detector.get_detections(q_nn)

            if frame is not None:
                eyes_bounding_boxes = detector.process_detections(frame, detections)
                
                # Sort eyes left to right to avoid duplication issues
                eyes_bounding_boxes.sort(key=lambda eye: eye[0])

                output_screen = display.create_output_screen(eyes_bounding_boxes, frame)

                # Get performance data and overlay it
                perf_data = performance_monitor.get_performance_data(system_queue)
                display.overlay_performance_data(output_screen, perf_data)
                
                display.show_output_screen(output_screen)

            if display.check_exit_condition():
                break
            
if __name__ == "__main__":
    main()
