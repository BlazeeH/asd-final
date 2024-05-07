import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QFileDialog, QSlider,QLabel,QMessageBox
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import Qt, QUrl, QTimer,QPoint
from PyQt5.QtGui import QIcon
import random

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Player")
        self.setGeometry(100, 100, 550, 500)

        self.playlist = []
        self.favorites = []
        self.current_position = 0
        self.current_index = 0
        self.currently_playing_index = 0
        self.repeat_mode = False
        self.shuffle_mode = False
            
        self.is_repeated = False
        self.song_list = QListWidget()
        self.init_ui()
        self.load_favorites_from_file()

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        with open("audioplayer/style.css", 'r', encoding='utf-8') as style_file:
            self.setStyleSheet(style_file.read())
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Layout for song list
        song_list_layout = QHBoxLayout()
        main_layout.addLayout(song_list_layout)

        self.song_list = QListWidget()
        song_list_layout.addWidget(self.song_list)
        self.song_list.setMaximumWidth(700)
        self.song_list.setMaximumHeight(700)

        self.song_list.itemClicked.connect(self.select_song)
        self.current_song_label = QLabel("Playing: ")
        main_layout.addWidget(self.current_song_label)
        
        # Layout for position slider     
        position_slider_layout = QHBoxLayout()
        main_layout.addLayout(position_slider_layout)
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.sliderMoved.connect(self.set_position)
        position_slider_layout.addWidget(self.position_slider)

        # Labels for current time and total duration
        self.current_time_label = QLabel("0:00")
        self.total_duration_label = QLabel("0:00")
        position_slider_layout.addWidget(self.current_time_label)
        position_slider_layout.addWidget(self.total_duration_label)
        
        # Layout for control buttons
        control_buttons_layout = QVBoxLayout()
        main_layout.addLayout(control_buttons_layout)

        # Group 1: Play, Pause, Stop, Next, Previous, Shuffle, Loop
        control_group_1_layout = QHBoxLayout()
        control_buttons_layout.addLayout(control_group_1_layout)

        self.player = QMediaPlayer(self)
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.player.mediaStatusChanged.connect(self.handle_media_status)

        play_icon = QIcon("audioplayer/icon/play.png")
        self.play_button = QPushButton()
        self.play_button.setIcon(play_icon)
        self.play_button.clicked.connect(self.play_song)
        control_group_1_layout.addWidget(self.play_button)

        pause_icon = QIcon("audioplayer/icon/pause.png")
        self.pause_button = QPushButton("")
        self.pause_button.setIcon(pause_icon)
        self.pause_button.clicked.connect(self.pause_song)
        control_group_1_layout.addWidget(self.pause_button)

        stop_icon = QIcon("audioplayer/icon/stop.png")
        self.stop_button = QPushButton()
        self.stop_button.setIcon(stop_icon)
        self.stop_button.clicked.connect(self.stop_song)
        control_group_1_layout.addWidget(self.stop_button)

        prev_icon = QIcon("audioplayer/icon/previous.png")
        self.prev_button = QPushButton()
        self.prev_button.setIcon(prev_icon)
        self.prev_button.clicked.connect(self.prev_song)
        control_group_1_layout.addWidget(self.prev_button)

        next_icon = QIcon("audioplayer/icon/skip.png")
        self.next_button = QPushButton()
        self.next_button.setIcon(next_icon)
        self.next_button.clicked.connect(self.next_song)
        control_group_1_layout.addWidget(self.next_button)

        shuffle_icon = QIcon("audioplayer/icon/shuffle.png")
        self.shuffle_button = QPushButton()
        self.shuffle_button.setIcon(shuffle_icon)
        self.shuffle_button.clicked.connect(self.toggle_shuffle)
        control_group_1_layout.addWidget(self.shuffle_button)

        repeat_button_icon = QIcon("audioplayer/icon/loop.png")
        self.repeat_button = QPushButton()
        self.repeat_button.setIcon(repeat_button_icon)
        self.repeat_button.clicked.connect(self.toggle_repeat)
        control_group_1_layout.addWidget(self.repeat_button)

        # Group 2: Add, Remove, Add to Favorites, Show Favorites
        control_group_2_layout = QHBoxLayout()
        control_buttons_layout.addLayout(control_group_2_layout)

        add_icon = QIcon("audioplayer/icon/add-to-playlist.png")
        self.add_button = QPushButton()
        self.add_button.setIcon(add_icon)
        self.add_button.clicked.connect(self.add_songs)
        control_group_2_layout.addWidget(self.add_button)

        remove_icon = QIcon("audioplayer/icon/delete.png")
        self.remove_button = QPushButton()
        self.remove_button.setIcon(remove_icon)
        self.remove_button.clicked.connect(self.remove_song)
        control_group_2_layout.addWidget(self.remove_button)

        add_to_favorites_icon = QIcon("audioplayer/icon/heart.png")
        self.add_to_favorites_button = QPushButton()
        self.add_to_favorites_button.setIcon(add_to_favorites_icon)
        self.add_to_favorites_button.clicked.connect(self.add_to_favorites)
        control_group_2_layout.addWidget(self.add_to_favorites_button)

        self.show_favorites_button = QPushButton("Favorites")
        self.show_favorites_button.setCheckable(True)
        self.show_favorites_button.clicked.connect(self.show_favorites)
        control_group_2_layout.addWidget(self.show_favorites_button)
        self.show_favorites_button.clicked.connect(lambda: self.add_button.setVisible(not self.show_favorites_button.isChecked()))
        self.show_favorites_button.clicked.connect(self.toggle_favorite_button_text)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_end_of_media)
        
        self.volume_button = QPushButton()
        self.volume_button.setIcon(QIcon("audioplayer/icon/volume.png"))
        self.volume_button.setFixedSize(30, 30)
        self.volume_button.clicked.connect(self.toggle_volume_slider)
        control_group_2_layout.addWidget(self.volume_button)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(20)
        self.volume_slider.setFixedWidth(150)
        self.volume_slider.hide()  
        control_group_2_layout.addWidget(self.volume_slider)
        self.volume_slider.sliderMoved.connect(self.set_volume)  # Kết nối sự kiện sliderMoved của QSlider với phương thức set_volume
        self.song_list.itemDoubleClicked.connect(self.play_song) # Hàm double click để phát nhạc
        self.song_list.itemDoubleClicked.connect(self.select_song_double_click)

    def set_volume(self, value):
        self.player.setVolume(value)

    # Phương thức để hiển thị / ẩn thanh trượt âm lượng khi nhấn vào nút âm lượng
    def toggle_volume_slider(self):
        if self.volume_slider.isVisible():
            self.volume_slider.hide()
        else:
            global_pos = self.volume_button.mapToGlobal(QPoint(0, 0))
            self.volume_slider.move(global_pos.x() + self.volume_button.width(), global_pos.y())
            self.volume_slider.show()

    def toggle_favorite_button_text(self):
        if self.show_favorites_button.isChecked():
            self.show_favorites_button.setText("Song List")
        else:
            self.show_favorites_button.setText("Favorites List")

    def play_song(self):
        if self.show_favorites_button.isChecked() and self.favorites:
            song_list = self.favorites
        else:
            song_list = self.playlist
        if not song_list:  # Kiểm tra xem danh sách có rỗng không
            QMessageBox.warning(self, "Cảnh báo", "Danh sách nhạc đang chọn là rỗng")
            return  # Trả về nếu danh sách rỗng
        song = song_list[self.current_index]
        self.current_song_label.setText(f"Playing: {os.path.basename(song)}") 
        url = QUrl.fromLocalFile(song)
        content = QMediaContent(url)
        self.player.setMedia(content)
        self.player.setPosition(self.current_position)
        self.player.play()
        if self.shuffle_mode:  # Cập nhật currently_playing_index khi phát bài hát mới
            self.currently_playing_index = self.current_index
        self.play_button.setEnabled(False)   # Vô hiệu hóa nút play
        self.pause_button.setEnabled(True)   # Kích hoạt nút pause   
        self.song_list.clearSelection()

    def remove_song(self):
        selected_items = self.song_list.selectedItems()
        if not selected_items:  # Kiểm tra nếu không có bài hát nào được chọn
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn bài hát muốn xóa.")
            return
        if selected_items:
            if self.show_favorites_button.isChecked() and self.favorites:
                for item in selected_items:
                    index = self.song_list.row(item)
                    if index == self.current_index:  # Kiểm tra nếu bài hát đang phát bị remove
                        self.stop_song()  # Dừng bài hát
                        self.current_position = 0  # Reset vị trí phát
                        self.current_song_label.setText("Playing: ")  # Xóa tiêu đề trên bài hát đang phát
                    del self.favorites[index]
                    self.song_list.takeItem(index)
                self.save_favorites_to_file()
            else:
                for item in selected_items:
                    index = self.song_list.row(item)
                    if index == self.current_index:  # Kiểm tra nếu bài hát đang phát bị remove
                        self.stop_song()  # Dừng bài hát
                        self.current_position = 0  # Reset vị trí phát  
                        self.current_song_label.setText("Playing: ")  # Xóa tiêu đề trên bài hát đang phát                  
                    del self.playlist[index]
                    self.song_list.takeItem(index)

    def pause_song(self):
        self.current_position = self.player.position()
        self.player.pause()
        self.pause_button.setEnabled(False)  # Vô hiệu hóa nút pause
        self.play_button.setEnabled(True)    # Kích hoạt nút play

    def stop_song(self):
        self.current_position = 0
        self.player.stop()
        self.play_button.setEnabled(True)

    def next_song(self):
        if self.playlist or self.favorites:
            if self.show_favorites_button.isChecked():
                playlist = self.favorites
            else:
                playlist = self.playlist
            if self.is_repeated:
                self.current_index = (self.current_index + 1) % len(playlist)
            elif self.shuffle_mode:
                self.current_index = random.randint(0, len(playlist) - 1)
            elif self.current_index < len(playlist) - 1:
                self.current_index += 1
            else:
                self.current_index = 0
            self.current_position = 0
            self.play_song()
            self.song_list.clearSelection()
            if not self.shuffle_mode:
                self.song_list.setCurrentRow(self.current_index)
            else:
                self.song_list.setCurrentRow(self.currently_playing_index)  # Highlight the currently playing song

    def prev_song(self):
        if self.playlist or self.favorites:
            if self.show_favorites_button.isChecked():
                playlist = self.favorites
            else:
                playlist = self.playlist
            if self.current_index > 0:
                self.current_index -= 1
            else:
                self.current_index = len(playlist) - 1
            self.play_song()
            if not self.shuffle_mode:
                self.song_list.setCurrentRow(self.current_index)
            else:
                self.song_list.setCurrentRow(self.currently_playing_index)

    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        if self.shuffle_mode:
            self.shuffle_button.setIcon(QIcon("audioplayer/icon/shuffle (1).png"))
        else:
            self.shuffle_button.setIcon(QIcon("audioplayer/icon/shuffle.png"))

    def toggle_repeat(self):
        self.repeat_mode = not self.repeat_mode
        self.is_repeated = self.repeat_mode
        if self.repeat_mode:
            self.repeat_button.setIcon(QIcon("audioplayer/icon/repeat-once.png"))
        else:
            self.repeat_button.setIcon(QIcon("audioplayer/icon/loop.png"))

    def set_volume(self, value):
        self.player.setVolume(value)

    def set_position(self, position):
        self.current_position = position
        self.player.setPosition(position)

    def update_position(self, position):
        self.position_slider.setValue(position)
        self.update_current_time(position)

    def update_duration(self, duration):
        self.position_slider.setRange(0, duration)
        self.update_total_duration(duration)

    def update_current_time(self, position):
        minutes = position // 60000
        seconds = (position // 1000) % 60
        self.current_time_label.setText("{:d}:{:02d}".format(minutes, seconds))

    def update_total_duration(self, duration):
        minutes = duration // 60000
        seconds = (duration // 1000) % 60
        self.total_duration_label.setText("{:d}:{:02d}".format(minutes, seconds))

    def add_songs(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Music Files", "",  "Audio Files (*.mp3 *.wav)"
        )
        if files:
            for file in files:
                self.playlist.append(file)
                self.song_list.addItem(os.path.basename(file))
            QMessageBox.information(self, "Thông báo", "Đã thêm bài hát thành công")

    def save_favorites_to_file(self):
        with open("favorites.json", "w") as f:
            json.dump(self.favorites, f)

    def load_favorites_from_file(self):
        try:
            with open("favorites.json", "r") as f:
                self.favorites = json.load(f)
        except FileNotFoundError:
            pass

    def add_to_favorites(self):
        selected_item = self.song_list.currentItem()
        if selected_item:
            index = self.song_list.row(selected_item)
            song = self.playlist[index]
            if song not in self.favorites:
                self.favorites.append(song)
                self.save_favorites_to_file()
                QMessageBox.information(self, "Thông báo", "Bài hát đã được thêm vào Favorites")
            else:
                 QMessageBox.information(self, "Thông báo", "Bài hát đã có trong Favorites")

    def show_favorites(self):
        if self.show_favorites_button.isChecked():
            playlist = self.favorites
            self.add_to_favorites_button.setEnabled(False) 
        else:
            playlist = self.playlist
            self.add_to_favorites_button.setEnabled(True) 
        if playlist:
            self.song_list.clear()
            for song in playlist:
                self.song_list.addItem(os.path.basename(song))
        else:
            self.song_list.clear()

    def handle_media_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.check_end_of_media()

    def check_end_of_media(self):
        if self.player.state() == QMediaPlayer.StoppedState:
            if self.repeat_mode:
                self.player.setPosition(0)
                self.player.play()
            elif self.shuffle_mode:
                self.next_song()
            else:
                self.next_song()

    def select_song(self):
        selected_item = self.song_list.currentItem()
        if selected_item:
            index = self.song_list.row(selected_item)
            self.currently_playing_index = index
            self.current_position = 0
            self.update_buttons_state()  # Gọi hàm để cập nhật trạng thái nút

    def select_song_double_click(self):
        selected_item = self.song_list.currentItem()
        if selected_item:
            index = self.song_list.row(selected_item)
            self.current_index = index  # Cập nhật chỉ số của bài hát hiện tại
            self.current_position = 0  # Đặt vị trí hiện tại về 0
            self.play_song()  # Phát bài hát được chọn

    def update_buttons_state(self):
        if not self.player.state() == QMediaPlayer.PlayingState:
            self.play_button.setEnabled(True)
            self.pause_button.setEnabled(False)
        else:
            self.play_button.setEnabled(False)
            self.pause_button.setEnabled(True)

    def play_selected_song(self):
        if not self.player.state() == QMediaPlayer.PlayingState:
            self.play_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.play_song()
        elif self.current_index != self.currently_playing_index:  # Nếu bài hát được chọn khác với bài hát đang phát
            self.play_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.currently_playing_index = self.current_index  # Cập nhật chỉ số của bài hát đang phát
            self.play_song()
        else:
            self.play_button.setEnabled(True)
            self.pause_button.setEnabled(False)       

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MusicPlayer()
    window.show()
    sys.exit(app.exec_())
