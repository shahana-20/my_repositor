import sys
import os
import shutil
import vlc
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QFileDialog, QListWidget, QInputDialog, QLabel, QMessageBox, QCompleter,
)
from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtWidgets import QSizePolicy

class MediaPlayer(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Netflix Clone")
        self.setGeometry(100, 100, 1100, 600)

        # List to store movie details (each movie is a dict with keys: 'name', 'genre', 'file_path')
        self.movies_file = "movies.json"
        self.movies = []
        self.load_movies_from_file()

        # --- Left Panel: Search, Upload, Movie List, Download ---
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search movie by name or genre...")
        self.search_bar.textChanged.connect(self.filter_movies)

        # Set up QCompleter for auto-suggestions:
        self.completer = QCompleter()
        self.model = QStringListModel()
        self.completer.setModel(self.model)
        self.search_bar.setCompleter(self.completer)

        self.upload_button = QPushButton("Upload Movie")
        self.upload_button.clicked.connect(self.upload_movie)

        self.movie_list = QListWidget()
        self.movie_list.itemDoubleClicked.connect(self.load_movie_from_list)

        self.download_button = QPushButton("Download Movie")
        self.download_button.clicked.connect(self.download_movie)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.search_bar)
        left_layout.addWidget(self.upload_button)
        left_layout.addWidget(QLabel("Movies:"))
        left_layout.addWidget(self.movie_list)
        left_layout.addWidget(self.download_button)

        # --- Right Panel: Video Display and VLC Controls ---
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()

        # Using a plain QWidget as the video display area
        self.video_widget = QWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


        self.load_button = QPushButton("Load Movie")
        self.load_button.clicked.connect(self.load_movie)
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_movie)
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_movie)
        self.skip_button = QPushButton("Skip 10s")
        self.skip_button.clicked.connect(self.skip_forward)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.load_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.skip_button)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.video_widget, stretch=1)
        right_layout.addLayout(controls_layout)

        # --- Main Layout: Combine Left and Right Panels ---
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, stretch=1)
        main_layout.addLayout(right_layout, stretch=2)

        self.setLayout(main_layout)
    
    def load_movies_from_file(self):
        """Load movies from a JSON file, if it exists."""
        self.movies_file = "movies.json"
        if os.path.exists(self.movies_file):
            try:
                with open(self.movies_file, "r") as f:
                  self.movies = json.load(f)
                # Update the movie list widget
                self.movie_list.clear()
                for movie in self.movies:
                    self.movie_list.addItem(f"{movie['name']} - {movie['genre']}")
                # Also update the completer suggestions if you use one
                self.update_completer()
                print("Movies loaded from file.")
            except Exception as e:
              print("Error loading movies:", e)
        else:
            self.movies = []

    def save_movies_to_file(self):
        """Save the current list of movies to a JSON file."""
        try:
            with open(self.movies_file, "w") as f:
              json.dump(self.movies, f, indent=4)
            print("Movies saved to file.")
        except Exception as e:
          print("Error saving movies:", e)


    def upload_movie(self):
        """Upload a movie and add its details to the list."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload a Movie", "", "Videos (*.mp4 *.avi *.mkv)")
        if file_path:
            default_name = os.path.basename(file_path)
            name, ok = QInputDialog.getText(self, "Movie Name", "Enter movie name:", text=default_name)
            if not ok or not name:
                return
            genre, ok = QInputDialog.getText(self, "Movie Genre", "Enter movie genre:")
            if not ok or not genre:
                return
            # Store movie details and add to the list widget
            movie = {"name": name, "genre": genre, "file_path": file_path}
            self.movies.append(movie)
            self.movie_list.addItem(f"{name} - {genre}")
            print(f"Uploaded movie: {file_path}")
            # Update completer suggestions
            self.update_completer()
            self.save_movies_to_file()

    def update_completer(self):
        """Update the QCompleter model based on the current movie list."""
        suggestions = [f"{movie['name']} - {movie['genre']}" for movie in self.movies]
        self.model.setStringList(suggestions)
    
    def closeEvent(self, event):
        """Save movies on exit."""
        self.save_movies_to_file()
        event.accept()

    def filter_movies(self):
        """Filter the movie list based on the search bar text."""
        query = self.search_bar.text().lower()
        self.movie_list.clear()
        for movie in self.movies:
            movie_entry = f"{movie['name']} - {movie['genre']}"
            if query in movie['name'].lower() or query in movie['genre'].lower():
                self.movie_list.addItem(movie_entry)

    def load_movie_from_list(self, item):
        """Load a movie when double-clicked in the movie list and play it."""
        text = item.text()
        for movie in self.movies:
            if f"{movie['name']} - {movie['genre']}" == text:
                self.load_movie_file(movie["file_path"])
                self.play_movie()  # Automatically start playing the movie
                break

    def load_movie(self):
        """Manually load a movie using a file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a Movie", "", "Videos (*.mp4 *.avi *.mkv)")
        if file_path:
            self.load_movie_file(file_path)

    def load_movie_file(self, file_path):
        """Load the selected movie file into VLC and set the video output."""
        media = self.instance.media_new(file_path)
        self.media_player.set_media(media)
        if sys.platform.startswith("win"):
            self.media_player.set_hwnd(int(self.video_widget.winId()))
        elif sys.platform.startswith("linux"):
            self.media_player.set_xwindow(int(self.video_widget.winId()))
        else:  # macOS
            self.media_player.set_nsobject(int(self.video_widget.winId()))
        print(f"Loaded: {file_path}")

    def play_movie(self):
        """Play the loaded movie."""
        if self.media_player.get_media():
            self.media_player.play()
        else:
            print("No movie loaded!")

    def pause_movie(self):
        """Pause the movie."""
        self.media_player.pause()

    def skip_forward(self):
        """Skip forward 10 seconds (10,000 ms)."""
        current_time = self.media_player.get_time()
        self.media_player.set_time(current_time + 10000)

    def download_movie(self):
        """Download (copy) the selected movie to a folder chosen by the user."""
        selected_items = self.movie_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Download Movie", "Please select a movie from the list to download.")
            return

        selected_text = selected_items[0].text()
        for movie in self.movies:
            if f"{movie['name']} - {movie['genre']}" == selected_text:
                source_path = movie["file_path"]
                break
        else:
            QMessageBox.warning(self, "Download Movie", "Movie not found!")
            return

        dest_folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if dest_folder:
            try:
                dest_path = os.path.join(dest_folder, os.path.basename(source_path))
                shutil.copy(source_path, dest_path)
                QMessageBox.information(self, "Download Movie", f"Movie downloaded to:\n{dest_path}")
                print(f"Downloaded to: {dest_path}")
            except Exception as e:
                QMessageBox.critical(self, "Download Movie", f"Error downloading movie:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = MediaPlayer()
    player.show()
    sys.exit(app.exec())



        
 


    