import cv2
import numpy as np
import time
from src.config import RGB_RESOLUTION

class Display:
    def __init__(self): 
        self.width, self.height = RGB_RESOLUTION
        self.fullscreen = False
        self.color = True

    def create_output_screen(self, eyes_bounding_boxes, frame):
        output_screen = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        if not self.color:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert frame to grayscale
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)  # Keep 3 channels for compatibility

        if not eyes_bounding_boxes:
            self._display_no_eyes(output_screen)
        else:
            self._display_eyes(eyes_bounding_boxes, frame, output_screen)

        return output_screen

    def show_output_screen(self, output_screen):
        """Show the processed eye detection output in a separate window and resize it to fit more space on screen."""
        cv2.namedWindow('Eye Detection', cv2.WINDOW_NORMAL)
        self._apply_window_state('Eye Detection')
        cv2.imshow('Eye Detection', output_screen)
    def check_keyboard_interaction(self, frame):
        key = cv2.waitKey(1) & 0xFF
        if key == ord('v'):
            self.fullscreen = not self.fullscreen
        if key == ord('c'):
            self.color = not self.color
        if key == ord('s'):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"snap_{timestamp}.png"
            cv2.imwrite(filename, frame)
            print(f"Image saved: {filename}")
        if key == ord('q'):
            return True

    def check_exit_condition(self):
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return True
    
    def destroy_all_windows(self):
        cv2.destroyAllWindows()

    def _display_no_eyes(self, output_screen):
        lines = [
            "WATCHING YOU LOOKING",
            "AT EVERYTHING BUT ME",
        ]
        
        font = cv2.FONT_HERSHEY_DUPLEX
        font_scale = 2.5
        font_thickness = 5
        text_color = (255, 255, 255)
        line_spacing = 20  # Space between lines
        
        # Calculate the total text block height
        text_sizes = [cv2.getTextSize(line, font, font_scale, font_thickness)[0] for line in lines]
        total_text_height = sum(h for w, h in text_sizes) + (len(lines) - 1) * line_spacing
        
        # Start position for the first line (centered vertically)
        start_y = (self.height - total_text_height) // 2

        for i, line in enumerate(lines):
            text_size = text_sizes[i]
            text_x = (self.width - text_size[0]) // 2  # Centered horizontally
            text_y = start_y + sum(text_sizes[j][1] for j in range(i)) + i * line_spacing  # Move down each line
            
            cv2.putText(output_screen, line, (text_x, text_y), font, font_scale, text_color, font_thickness)

    def _display_eyes(self, eyes_bounding_boxes, frame, output_screen):
        num_eyes = len(eyes_bounding_boxes)
        rows, cols, black_splits = self._determine_grid_layout(num_eyes)
        split_width, split_height = self._calculate_split_size(rows, cols)

        idx = 0
        for row in range(rows):
            for col in range(cols):
                if idx >= num_eyes or idx >= (rows * cols - black_splits):
                    break  # Skip extra splits for black padding
                x1, y1, x2, y2 = eyes_bounding_boxes[idx]
                eye_img = frame[y1:y2, x1:x2]
                if eye_img.size == 0:
                    continue
                resized_eye = cv2.resize(eye_img, (split_width, split_height))
                
                start_x = col * split_width + (self.width - cols * split_width) // 2
                start_y = row * split_height + (self.height - rows * split_height) // 2

                output_screen[start_y:start_y + split_height, start_x:start_x + split_width] = resized_eye
                idx += 1

    def _determine_grid_layout(self, num_eyes):
        grid_map = {
            **{i: (2, 2, 4 - i) for i in range(1, 5)},
            **{i: (3, 3, 9 - i) for i in range(5, 10)},
            **{i: (4, 4, 16 - i) for i in range(10, 17)},
            **{i: (5, 5, 25 - i) for i in range(17, 26)}
        }
        return grid_map.get(num_eyes, (3, 3, 0))

    def _calculate_split_size(self, rows, cols):
        aspect_ratio = 16 / 9
        split_height = self.height // rows
        split_width = int(split_height * aspect_ratio)
        if split_width * cols > self.width:
            split_width = self.width // cols
            split_height = int(split_width / aspect_ratio)
        return split_width, split_height

    def _apply_window_state(self, window_name):
        if self.fullscreen:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            self.width, self.height = RGB_RESOLUTION
            cv2.resizeWindow(window_name, self.width, self.height)
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)


class DebugDisplay:
    def __init__(self, fps=5):
        self.width, self.height = RGB_RESOLUTION
        self.fps = fps
        self.frame_interval = 1.0 / fps  # Time per frame in seconds
        self.last_update_time = time.time()

    def create_debug_screen(self, frame, eyes_bounding_boxes):
        debug_frame = frame.copy()
        debug_frame = cv2.cvtColor(debug_frame, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
        debug_frame = cv2.cvtColor(debug_frame, cv2.COLOR_GRAY2BGR)  # Maintain 3 channels

        # Draw bounding boxes on the debug frame
        for (x1, y1, x2, y2) in eyes_bounding_boxes:
            cv2.rectangle(debug_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

        debug_resized = cv2.resize(debug_frame, (self.width, self.height))
        return debug_resized

    def show_debug_screen(self, debug_screen):
        """Show the debug screen only if enough time has passed (throttle FPS)."""
        current_time = time.time()
        if current_time - self.last_update_time >= self.frame_interval:
            cv2.namedWindow('Debug View - Full Frame', cv2.WINDOW_NORMAL)
            cv2.imshow('Debug View - Full Frame', debug_screen)
            self.last_update_time = current_time  # Update timestamp

    def overlay_performance_data(self, frame, perf_data):
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = .9
        font_thickness = 2
        text_color = (0, 0, 255)  # White text
        bg_color = (0, 0, 0)  # Black background
        padding = 10  # Padding around text
        y_offset = 30  # Initial Y position

        # Calculate background rectangle size
        text_lines = [f"{key}: {value}" for key, value in perf_data.items()]
        text_sizes = [cv2.getTextSize(text, font, font_scale, font_thickness)[0] for text in text_lines]
        
        max_text_width = max(w for w, h in text_sizes) + 2 * padding
        total_text_height = sum(h for w, h in text_sizes) + (len(text_sizes) - 1) * padding + 2 * padding

        # Draw background rectangle
        cv2.rectangle(frame, (5, 5), (5 + max_text_width, 5 + total_text_height), bg_color, -1)

        # Overlay performance text
        for text in text_lines:
            text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
            cv2.putText(frame, text, (10, y_offset), font, font_scale, text_color, font_thickness)
            y_offset += text_size[1] + padding  # Move down for next line
