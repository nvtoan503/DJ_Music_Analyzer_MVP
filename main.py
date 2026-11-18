"""Cross-platform local DJ library analyzer (Windows / macOS)."""
from __future__ import annotations

import json
import os
import shutil
import sys
import uuid
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt, QUrl, QStandardPaths, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QComboBox,
    QMessageBox, QProgressBar, QHeaderView, QAbstractItemView, QFrame,
    QSplitter, QSlider, QCheckBox
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from analyzer import analyze_file

GENRES = ['Vinahouse', 'House Lắc', 'EDM', 'Chưa xác định']
EXTENSIONS = {'.mp3', '.wav', '.flac', '.m4a', '.aiff', '.aif', '.ogg'}


def time_str(seconds):
    seconds = max(0, int(seconds or 0))
    return f'{seconds // 60:02}:{seconds % 60:02}'


def library_path():
    root = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
    root.mkdir(parents=True, exist_ok=True)
    return root / 'library.json'


class AnalyzeThread(QThread):
    done = Signal(str, dict)
    failed = Signal(str, str)
    progress = Signal(int, int)

    def __init__(self, paths, parent=None):
        super().__init__(parent)
        self.paths = paths

    def run(self):
        for idx, path in enumerate(self.paths, 1):
            try:
                result = analyze_file(path)
                self.done.emit(path, result)
            except Exception as exc:
                self.failed.emit(path, str(exc))
            self.progress.emit(idx, len(self.paths))


class WaveformWidget(QWidget):
    seek_requested = Signal(float)

    def __init__(self):
        super().__init__()
        self.values = []
        self.play_ratio = 0.0
        self.setMinimumHeight(165)
        self.setToolTip('Nhấp vào waveform để chuyển tới vị trí tương ứng')

    def set_data(self, values):
        self.values = values or []
        self.play_ratio = 0.0
        self.update()

    def set_position(self, ratio):
        self.play_ratio = max(0, min(1, ratio))
        self.update()

    def mousePressEvent(self, event):
        if self.values and self.width() > 0:
            self.seek_requested.emit(max(0, min(1, event.position().x() / self.width())))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        p.fillRect(self.rect(), QColor('#171e30'))
        w, h = self.width(), self.height()
        if not self.values:
            p.setPen(QColor('#8693b1'))
            p.drawText(self.rect(), Qt.AlignCenter, 'Chọn bài nhạc để xem waveform')
            return
        n = len(self.values)
        step = max(1, int(n / max(1, w)))
        for i in range(0, n, step):
            x = int(i / n * w)
            val = max(self.values[i:i+step])
            half = int((val / max(0.01, max(self.values))) * (h * 0.45))
            half = max(1, min(half, int(h * 0.46)))
            p.setPen(QPen(QColor('#a78bfa') if i / n <= self.play_ratio else QColor('#27c6e8'), 1.3))
            p.drawLine(x, h//2-half, x, h//2+half)
        x = int(self.play_ratio * w)
        p.setPen(QPen(QColor('#ffffff'), 2))
        p.drawLine(x, 0, x, h)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('DJ Music Analyzer — MVP')
        self.resize(1180, 760)
        self.tracks = self.load_library()
        self.thread = None
        self.selected_path = None
        self.audio = QAudioOutput(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio)
        self.audio.setVolume(0.75)
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_position)
        self.setup_ui()
        self.refresh_table()

    def load_library(self):
        try:
            with library_path().open('r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (FileNotFoundError, ValueError, OSError):
            return []

    def save_library(self):
        path = library_path()
        tmp = path.with_suffix('.tmp')
        with tmp.open('w', encoding='utf-8') as f:
            json.dump(self.tracks, f, ensure_ascii=False)
        tmp.replace(path)

    def setup_ui(self):
        self.setStyleSheet('''
            QMainWindow,QWidget {background:#0f1421; color:#eaf0ff; font-size:13px;}
            QLabel#heading {font-size:24px; font-weight:bold; color:#ffffff;}
            QLabel#muted {color:#96a3c2;}
            QPushButton {background:#29334c; border:1px solid #3a4864; padding:10px 15px;
                         border-radius:8px; font-weight:600;}
            QPushButton:hover {background:#384664;}
            QPushButton#primary {background:#7455de; border-color:#967df4;}
            QPushButton#primary:hover {background:#876cf5;}
            QPushButton:disabled {color:#62708c; background:#20283b;}
            QComboBox {background:#202a40; border:1px solid #3c4965; border-radius:6px; padding:7px;}
            QComboBox QAbstractItemView {background:#202a40; selection-background-color:#7056c9;}
            QTableWidget {background:#151c2c; alternate-background-color:#1a2335;
                         gridline-color:#303d54; border:1px solid #354058;}
            QHeaderView::section {background:#29334b; padding:9px; border:0; font-weight:bold;}
            QTableWidget::item:selected {background:#4a467c;}
            QProgressBar {background:#1d273b; border:0; border-radius:5px; height:10px;}
            QProgressBar::chunk {background:#8b6aef; border-radius:5px;}
            QSlider::groove:horizontal {height:5px; background:#3b4562;}
            QSlider::handle:horizontal {width:13px; background:#a78bfa; margin:-5px 0; border-radius:6px;}
        ''')
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        title = QLabel('♫  DJ MUSIC ANALYZER')
        title.setObjectName('heading')
        root.addWidget(title)
        subtitle = QLabel('Waveform • BPM • Gợi ý thể loại • Thư viện nhạc offline')
        subtitle.setObjectName('muted')
        root.addWidget(subtitle)

        bar = QHBoxLayout()
        self.import_btn = QPushButton('＋  Thêm file nhạc')
        self.import_btn.setObjectName('primary')
        self.import_btn.clicked.connect(self.import_files)
        bar.addWidget(self.import_btn)
        self.folder_btn = QPushButton('＋  Nhập cả thư mục')
        self.folder_btn.clicked.connect(self.import_folder)
        bar.addWidget(self.folder_btn)
        self.export_btn = QPushButton('⇩  Xuất thư mục theo thể loại')
        self.export_btn.clicked.connect(self.export_genres)
        bar.addWidget(self.export_btn)
        bar.addStretch()
        bar.addWidget(QLabel('Lọc:'))
        self.filter = QComboBox()
        self.filter.addItems(['Tất cả'] + GENRES)
        self.filter.currentTextChanged.connect(self.refresh_table)
        bar.addWidget(self.filter)
        root.addLayout(bar)

        self.progress_label = QLabel('Sẵn sàng. Chọn file MP3/WAV/FLAC để phân tích.')
        self.progress_label.setObjectName('muted')
        root.addWidget(self.progress_label)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        root.addWidget(self.progress)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(['Tên file', 'BPM', 'Thể loại', 'Thời lượng', 'Trạng thái'])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 5):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.itemSelectionChanged.connect(self.select_track)
        root.addWidget(self.table, 4)

        info = QHBoxLayout()
        self.now_playing = QLabel('Chưa chọn bài')
        self.now_playing.setStyleSheet('font-weight:bold; font-size:16px;')
        info.addWidget(self.now_playing, 1)
        info.addWidget(QLabel('Sửa thể loại:'))
        self.genre_edit = QComboBox()
        self.genre_edit.addItems(GENRES)
        self.genre_edit.currentTextChanged.connect(self.change_genre)
        info.addWidget(self.genre_edit)
        root.addLayout(info)
        self.waveform = WaveformWidget()
        self.waveform.seek_requested.connect(self.seek_ratio)
        root.addWidget(self.waveform, 2)
        controls = QHBoxLayout()
        self.play_btn = QPushButton('▶  Phát')
        self.play_btn.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_btn)
        self.stop_btn = QPushButton('■  Dừng')
        self.stop_btn.clicked.connect(self.player.stop)
        controls.addWidget(self.stop_btn)
        self.clock = QLabel('00:00 / 00:00')
        controls.addWidget(self.clock)
        self.timeline = QSlider(Qt.Horizontal)
        self.timeline.setRange(0, 1000)
        self.timeline.sliderReleased.connect(self.seek_slider)
        controls.addWidget(self.timeline, 1)
        root.addLayout(controls)
        self.note = QLabel('⚠ Phân loại bằng quy tắc âm thanh, không phải AI đã huấn luyện. Hãy nghe và sửa nhãn khi cần.')
        self.note.setObjectName('muted')
        self.note.setWordWrap(True)
        root.addWidget(self.note)
        self.player.playbackStateChanged.connect(self.set_play_label)
        self.player.errorOccurred.connect(self.player_error)

    def import_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, 'Chọn nhạc', '', 'Audio (*.mp3 *.wav *.flac *.m4a *.ogg *.aiff *.aif)')
        self.start_analysis(files)

    def import_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Chọn thư mục nhạc')
        if not folder:
            return
        paths = [str(p) for p in Path(folder).rglob('*') if p.is_file() and p.suffix.lower() in EXTENSIONS]
        self.start_analysis(paths)

    def start_analysis(self, files):
        if self.thread and self.thread.isRunning():
            QMessageBox.information(self, 'Đang phân tích', 'Vui lòng hoàn tất lượt đang chạy trước.')
            return
        known = {os.path.normcase(os.path.abspath(t['path'])) for t in self.tracks}
        new = []
        for p in files:
            normalized = os.path.normcase(os.path.abspath(p))
            if normalized not in known and os.path.isfile(p):
                new.append(os.path.abspath(p))
                known.add(normalized)
        if not new:
            self.progress_label.setText('Không có file mới (hoặc đã nhập thư viện).')
            return
        self.import_btn.setEnabled(False)
        self.folder_btn.setEnabled(False)
        self.progress.setValue(0)
        self.progress_label.setText(f'Đang phân tích {len(new)} file...')
        self.thread = AnalyzeThread(new, self)
        self.thread.done.connect(self.analysis_done)
        self.thread.failed.connect(self.analysis_failed)
        self.thread.progress.connect(self.analysis_progress)
        self.thread.finished.connect(self.analysis_finished)
        self.thread.start()

    def analysis_done(self, path, result):
        result['id'] = uuid.uuid4().hex
        self.tracks.append(result)
        self.save_library()
        self.refresh_table()

    def analysis_failed(self, path, error):
        self.tracks.append({'id': uuid.uuid4().hex, 'path': path,
                            'name': os.path.basename(path), 'error': error,
                            'genre': 'Chưa xác định', 'bpm': 0, 'duration': 0, 'waveform': []})
        self.save_library()
        self.refresh_table()

    def analysis_progress(self, idx, total):
        self.progress.setValue(round(idx * 100 / max(1, total)))
        self.progress_label.setText(f'Đã xử lý {idx}/{total} file')

    def analysis_finished(self):
        self.import_btn.setEnabled(True)
        self.folder_btn.setEnabled(True)
        errors = sum('error' in t for t in self.tracks)
        self.progress_label.setText(f'Thư viện: {len(self.tracks)} file • {errors} file lỗi')

    def refresh_table(self, *_):
        selected_id = self.selected_track().get('id') if self.selected_track() else None
        self.table.blockSignals(True)
        filtered = [t for t in self.tracks if self.filter.currentText() == 'Tất cả' or
                    t.get('genre') == self.filter.currentText()]
        self.table.setRowCount(len(filtered))
        for row, t in enumerate(filtered):
            vals = [t.get('name', ''), str(t.get('bpm', 0)) if not t.get('error') else '—',
                    t.get('genre', ''), time_str(t.get('duration', 0)),
                    ('Lỗi: ' + t['error'][:55]) if t.get('error') else 'Đã phân tích']
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, t['id'])
                item.setToolTip(t.get('path', ''))
                self.table.setItem(row, col, item)
            if t['id'] == selected_id:
                self.table.selectRow(row)
        self.table.blockSignals(False)

    def selected_track(self):
        row = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        if not item:
            return None
        ident = item.data(Qt.UserRole)
        return next((t for t in self.tracks if t['id'] == ident), None)

    def select_track(self):
        track = self.selected_track()
        if not track:
            return
        self.selected_path = track['path']
        self.now_playing.setText(track.get('name', ''))
        self.waveform.set_data(track.get('waveform', []))
        self.genre_edit.blockSignals(True)
        self.genre_edit.setCurrentText(track.get('genre', 'Chưa xác định'))
        self.genre_edit.blockSignals(False)
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(track['path']))
        self.progress_label.setText('Gợi ý: ' + track.get('reason', 'Chưa phân tích') +
                                    (' • BPM gốc: ' + str(track.get('raw_bpm', '?')) if not track.get('error') else ''))

    def change_genre(self, new_genre):
        track = self.selected_track()
        if track:
            track['genre'] = new_genre
            track['manual_label'] = True
            self.save_library()
            self.refresh_table()

    def toggle_play(self):
        if not self.selected_track():
            return
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def set_play_label(self, state):
        self.play_btn.setText('❚❚  Tạm dừng' if state == QMediaPlayer.PlayingState else '▶  Phát')

    def player_error(self, error, error_string):
        if error != QMediaPlayer.NoError:
            self.progress_label.setText('Lỗi phát audio: ' + error_string)

    def update_position(self, *_):
        duration = self.player.duration()
        pos = self.player.position()
        if not self.timeline.isSliderDown():
            self.timeline.setValue(round(pos / duration * 1000) if duration > 0 else 0)
        track = self.selected_track()
        analyzed_ms = 1000 * track.get('analyzed_seconds', 0) if track else 0
        self.waveform.set_position(min(1, pos / analyzed_ms) if analyzed_ms > 0 else 0)
        self.clock.setText(f'{time_str(pos / 1000)} / {time_str(duration / 1000)}')

    def seek_slider(self):
        if self.player.duration() > 0:
            self.player.setPosition(int(self.player.duration() * self.timeline.value() / 1000))

    def seek_ratio(self, ratio):
        if self.player.duration() > 0:
            track = self.selected_track()
            analyzed_ms = 1000 * track.get('analyzed_seconds', 0) if track else 0
            self.player.setPosition(int(min(self.player.duration(), analyzed_ms) * ratio) if analyzed_ms else int(self.player.duration() * ratio))

    def export_genres(self):
        valid = [t for t in self.tracks if not t.get('error') and os.path.isfile(t['path'])]
        if not valid:
            QMessageBox.information(self, 'Chưa có nhạc', 'Không có file hợp lệ để xuất.')
            return
        folder = QFileDialog.getExistingDirectory(self, 'Chọn nơi xuất thư mục nhạc')
        if not folder:
            return
        count, errors = 0, []
        for track in valid:
            subfolder = Path(folder) / track.get('genre', 'Chưa xác định')
            subfolder.mkdir(parents=True, exist_ok=True)
            original = Path(track['path'])
            dst = subfolder / original.name
            if dst.exists():
                try:
                    if dst.samefile(original):
                        continue
                except OSError:
                    pass
                suffix_num = 2
                while dst.exists():
                    dst = subfolder / f'{original.stem} ({suffix_num}){original.suffix}'
                    suffix_num += 1
            try:
                shutil.copy2(original, dst)
                count += 1
            except OSError as exc:
                errors.append(f'{original.name}: {exc}')
        summary = f'Đã sao chép {count} file vào các thư mục thể loại.\nFile gốc không bị thay đổi.'
        if errors:
            summary += f'\nCó {len(errors)} lỗi. Ví dụ: {errors[0]}'
        QMessageBox.information(self, 'Xuất thư viện', summary)

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            QMessageBox.warning(self, 'Đang phân tích', 'Vui lòng hoàn tất phân tích trước khi thoát.')
            event.ignore()
            return
        self.player.stop()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('DJ Music Analyzer')
    app.setOrganizationName('DJ Music Analyzer')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
