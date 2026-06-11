import sys
import sqlite3
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QRadioButton, QButtonGroup, QLabel, QMenuBar,
    QAction, QMessageBox, QInputDialog, QDialog, QComboBox,
    QPushButton, QGroupBox, QFrame, QSplitter, QStatusBar, QProgressBar
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "fantasy_cricket.db")

# ── Point rules ───────────────────────────────────────────────────────────────
def calculate_batting_points(scored, faced, fours, sixes):
    pts = scored // 2
    if scored >= 100: pts += 10
    elif scored >= 50: pts += 5
    if fours > 0: pts += fours
    if sixes > 0: pts += sixes * 2
    if faced > 0:
        sr = (scored / faced) * 100
        if sr > 100:   pts += 6
        elif sr >= 80: pts += 2
    return pts

def calculate_bowling_points(bowled, maiden, given, wkts):
    pts = wkts * 10
    if wkts >= 5:    pts += 10
    elif wkts >= 3:  pts += 5
    pts += maiden * 4
    if bowled > 0:
        economy = given / bowled
        if economy < 2:      pts += 10
        elif economy <= 3.5: pts += 7
        elif economy <= 4.5: pts += 4
    return pts

def calculate_fielding_points(catches, stumping, run_out):
    return (catches + stumping + run_out) * 10

# ── DB helpers ────────────────────────────────────────────────────────────────
def get_connection():
    return sqlite3.connect(DB_PATH)

def get_players_by_category(category):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT player, value FROM stats WHERE ctg=?", (category,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_match_names():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT match_name FROM match")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows

def get_player_match_stats(player, match_name):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""SELECT scored, faced, fours, sixes, bowled, maiden, given, wkts,
                          catches, stumping, run_out
                   FROM match WHERE player=? AND match_name=?""", (player, match_name))
    row = cur.fetchone()
    conn.close()
    return row

def get_player_category(player_name):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT ctg FROM stats WHERE player=?", (player_name,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else ""

def save_team_to_db(name, players_list, score):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO teams (name, players, value) VALUES (?,?,?)",
                (name, ",".join(players_list), score))
    conn.commit()
    conn.close()

def load_team_from_db(name):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT players FROM teams WHERE name=?", (name,))
    row = cur.fetchone()
    conn.close()
    return row[0].split(",") if row else []

def get_saved_team_names():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT name FROM teams")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows

def rename_team_in_db(old_name, new_name):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("UPDATE teams SET name=? WHERE name=?", (new_name, old_name))
    conn.commit()
    conn.close()

def get_player_value(player_name):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT value, ctg FROM stats WHERE player=?", (player_name,))
    row = cur.fetchone()
    conn.close()
    return (row[0], row[1]) if row else (0, "")

# ── Selection rules ───────────────────────────────────────────────────────────
MAX_TEAM_SIZE   = 11
TOTAL_POINTS    = 100
CATEGORY_LIMITS = {
    "Batsman":       4,
    "Bowler":        4,
    "All-Rounder":   3,
    "Wicket-Keeper": 2,
}

CATEGORY_COLORS = {
    "Batsman":       "#1565C0",
    "Bowler":        "#2E7D32",
    "All-Rounder":   "#E65100",
    "Wicket-Keeper": "#6A1B9A",
}

CATEGORY_ICONS = {
    "Batsman":       "🏏",
    "Bowler":        "🎯",
    "All-Rounder":   "⭐",
    "Wicket-Keeper": "🧤",
}

# ── Score dialog ──────────────────────────────────────────────────────────────
class ScoreDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🏆 Evaluate Score")
        self.setMinimumWidth(420)
        self.setMinimumHeight(300)
        self.setStyleSheet("""
            QDialog { background: #1a1a2e; color: #eee; }
            QLabel  { color: #eee; font-size: 13px; }
            QComboBox {
                background: #16213e; color: #eee; border: 1px solid #0f3460;
                border-radius: 6px; padding: 6px; font-size: 13px;
            }
            QComboBox QAbstractItemView { background: #16213e; color: #eee; }
            QPushButton {
                background: #0f3460; color: white; border: none;
                border-radius: 8px; padding: 10px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: #e94560; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🏆 Score Evaluator")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #f5c518; margin-bottom: 10px;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Select your saved team:"))
        self.team_combo = QComboBox()
        self.team_combo.addItems(get_saved_team_names())
        layout.addWidget(self.team_combo)

        layout.addWidget(QLabel("Select match:"))
        self.match_combo = QComboBox()
        self.match_combo.addItems(get_match_names())
        layout.addWidget(self.match_combo)

        btn = QPushButton("⚡ Calculate Score")
        btn.clicked.connect(self.calculate)
        layout.addWidget(btn)

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setFont(QFont("Arial", 15, QFont.Bold))
        self.result_label.setStyleSheet("color: #f5c518; margin-top: 10px;")
        layout.addWidget(self.result_label)

    def calculate(self):
        team_name  = self.team_combo.currentText()
        match_name = self.match_combo.currentText()
        if not team_name or not match_name:
            QMessageBox.warning(self, "Warning", "Please select both team and match.")
            return
        players = load_team_from_db(team_name)
        total   = 0
        breakdown = []
        for player in players:
            player = player.strip()
            stats  = get_player_match_stats(player, match_name)
            if stats:
                scored, faced, fours, sixes, bowled, maiden, given, wkts, catches, stump, ro = stats
                pts  = calculate_batting_points(scored, faced, fours, sixes)
                pts += calculate_bowling_points(bowled, maiden, given, wkts)
                pts += calculate_fielding_points(catches, stump, ro)
                total += pts
                breakdown.append(f"  {player}: {pts} pts")
            else:
                breakdown.append(f"  {player}: 0 pts (no data)")

        detail = "\n".join(breakdown)
        msg = QMessageBox(self)
        msg.setWindowTitle("Score Breakdown")
        msg.setText(
            f"<b>Team:</b> {team_name}<br>"
            f"<b>Match:</b> {match_name}<br><br>"
            f"<pre>{detail}</pre>"
            f"<hr><b style='font-size:15px'>Total Score: {total} pts</b>"
        )
        msg.setStyleSheet("QLabel { color: black; min-width: 320px; }")
        msg.exec_()
        self.result_label.setText(f"🏆 Total Score: {total} pts")

# ── Main window ───────────────────────────────────────────────────────────────
class FantasyCricketApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏏 Fantasy Cricket")
        self.setMinimumSize(980, 640)
        self.team_name         = None
        self.selected_players  = []
        self.used_points       = 0
        self.selection_enabled = False

        self._apply_stylesheet()
        self._build_menu()
        self._build_ui()

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0d1117; }

            QMenuBar {
                background-color: #161b22;
                color: #c9d1d9;
                font-size: 13px;
                padding: 4px;
                border-bottom: 1px solid #30363d;
            }
            QMenuBar::item:selected { background-color: #388bfd; border-radius: 4px; }
            QMenu {
                background-color: #161b22; color: #c9d1d9;
                border: 1px solid #30363d;
            }
            QMenu::item:selected { background-color: #388bfd; }

            QGroupBox {
                color: #58a6ff;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #30363d;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: #161b22;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }

            QListWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item { padding: 7px 10px; border-bottom: 1px solid #21262d; }
            QListWidget::item:selected { background-color: #1f6feb; color: white; border-radius: 4px; }
            QListWidget::item:hover { background-color: #21262d; }

            QRadioButton {
                color: #c9d1d9;
                font-size: 12px;
                spacing: 6px;
                padding: 4px 8px;
                border-radius: 6px;
            }
            QRadioButton:checked { color: #58a6ff; font-weight: bold; }
            QRadioButton::indicator { width: 14px; height: 14px; }
            QRadioButton::indicator:checked { background: #388bfd; border-radius: 7px; border: 2px solid #58a6ff; }
            QRadioButton::indicator:unchecked { background: #21262d; border-radius: 7px; border: 2px solid #30363d; }

            QLabel { color: #8b949e; font-size: 12px; }

            QStatusBar {
                background-color: #161b22;
                color: #8b949e;
                border-top: 1px solid #30363d;
                font-size: 12px;
            }
        """)

    # ── Menu bar ──────────────────────────────────────────────────────────────
    def _build_menu(self):
        menubar  = self.menuBar()
        manage   = menubar.addMenu("🏏 Manage Teams")

        new_act    = QAction("➕  New Team",      self); new_act.triggered.connect(self.new_team)
        open_act   = QAction("📂  Open Team",     self); open_act.triggered.connect(self.open_team)
        save_act   = QAction("💾  Save Team",     self); save_act.triggered.connect(self.save_team)
        rename_act = QAction("✏️   Rename Team",  self); rename_act.triggered.connect(self.rename_team)
        eval_act   = QAction("🏆  Evaluate Score",self); eval_act.triggered.connect(self.evaluate_score)

        manage.addAction(new_act)
        manage.addAction(open_act)
        manage.addAction(save_act)
        manage.addAction(rename_act)
        manage.addSeparator()
        manage.addAction(eval_act)

    # ── Central widget ────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Header banner ────────────────────────────────────────────────────
        header = QLabel("🏏  Fantasy Cricket")
        header.setAlignment(Qt.AlignCenter)
        header.setFixedHeight(56)
        header.setFont(QFont("Arial", 20, QFont.Bold))
        header.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #0d47a1, stop:0.5 #1565c0, stop:1 #0d47a1);
            color: white;
            letter-spacing: 2px;
        """)
        root.addWidget(header)

        # ── Main content area ─────────────────────────────────────────────────
        content = QWidget()
        content.setStyleSheet("background: #0d1117;")
        content_layout = QHBoxLayout(content)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(16, 16, 16, 16)

        # ── LEFT panel ────────────────────────────────────────────────────────
        left_group = QGroupBox("Available Players")
        left_layout = QVBoxLayout(left_group)
        left_layout.setSpacing(10)

        # Category radio buttons in a styled row
        cat_frame = QFrame()
        cat_frame.setStyleSheet("background: #21262d; border-radius: 8px; padding: 2px;")
        cat_layout = QHBoxLayout(cat_frame)
        cat_layout.setSpacing(4)
        cat_layout.setContentsMargins(8, 4, 8, 4)

        self.btn_group = QButtonGroup()
        self.categories = ["Batsman", "Bowler", "All-Rounder", "Wicket-Keeper"]
        self.radio_btns = []
        for i, cat in enumerate(self.categories):
            icon = CATEGORY_ICONS[cat]
            rb   = QRadioButton(f"{icon} {cat}")
            rb.setEnabled(False)
            rb.toggled.connect(self.on_category_changed)
            self.btn_group.addButton(rb, i)
            cat_layout.addWidget(rb)
            self.radio_btns.append(rb)
        left_layout.addWidget(cat_frame)

        # Player count label
        self.avail_count_label = QLabel("Select a category to view players")
        self.avail_count_label.setAlignment(Qt.AlignCenter)
        self.avail_count_label.setStyleSheet("color: #58a6ff; font-size: 12px;")
        left_layout.addWidget(self.avail_count_label)

        self.players_list = QListWidget()
        self.players_list.itemDoubleClicked.connect(self.add_player)
        left_layout.addWidget(self.players_list)

        hint = QLabel("💡 Double-click a player to add them")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #484f58; font-size: 11px; padding: 4px;")
        left_layout.addWidget(hint)

        # ── RIGHT panel ───────────────────────────────────────────────────────
        right_group = QGroupBox("Selected Players")
        right_layout = QVBoxLayout(right_group)
        right_layout.setSpacing(10)

        # Points & progress dashboard
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background: #21262d; border-radius: 8px; padding: 2px;")
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setSpacing(6)
        stats_layout.setContentsMargins(12, 8, 12, 8)

        top_row = QHBoxLayout()
        self.team_name_label = QLabel("No team loaded")
        self.team_name_label.setFont(QFont("Arial", 13, QFont.Bold))
        self.team_name_label.setStyleSheet("color: #f5c518;")
        self.count_label = QLabel("0 / 11 players")
        self.count_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        self.count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top_row.addWidget(self.team_name_label)
        top_row.addWidget(self.count_label)
        stats_layout.addLayout(top_row)

        pts_row = QHBoxLayout()
        self.avail_label = QLabel("Points Available: 100")
        self.avail_label.setStyleSheet("color: #3fb950; font-weight: bold; font-size: 12px;")
        self.used_label  = QLabel("Points Used: 0")
        self.used_label.setStyleSheet("color: #f78166; font-weight: bold; font-size: 12px;")
        pts_row.addWidget(self.avail_label)
        pts_row.addWidget(self.used_label)
        stats_layout.addLayout(pts_row)

        self.points_bar = QProgressBar()
        self.points_bar.setMaximum(TOTAL_POINTS)
        self.points_bar.setValue(0)
        self.points_bar.setTextVisible(False)
        self.points_bar.setFixedHeight(8)
        self.points_bar.setStyleSheet("""
            QProgressBar { background: #30363d; border-radius: 4px; border: none; }
            QProgressBar::chunk { background: #1f6feb; border-radius: 4px; }
        """)
        stats_layout.addWidget(self.points_bar)

        right_layout.addWidget(stats_frame)

        self.selected_list = QListWidget()
        self.selected_list.itemDoubleClicked.connect(self.remove_player)
        right_layout.addWidget(self.selected_list)

        hint2 = QLabel("💡 Double-click a player to remove them")
        hint2.setAlignment(Qt.AlignCenter)
        hint2.setStyleSheet("color: #484f58; font-size: 11px; padding: 4px;")
        right_layout.addWidget(hint2)

        # Category breakdown
        self.breakdown_label = QLabel("BAT: 0  |  BWL: 0  |  AR: 0  |  WK: 0")
        self.breakdown_label.setAlignment(Qt.AlignCenter)
        self.breakdown_label.setStyleSheet(
            "color: #8b949e; font-size: 11px; background: #21262d; "
            "border-radius: 6px; padding: 5px;"
        )
        right_layout.addWidget(self.breakdown_label)

        content_layout.addWidget(left_group, 1)
        content_layout.addWidget(right_group, 1)
        root.addWidget(content, 1)

        # Status bar
        self.statusBar().showMessage("📢  Create a new team from 🏏 Manage Teams to begin.")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _update_points_display(self):
        avail = TOTAL_POINTS - self.used_points
        self.avail_label.setText(f"Points Available: {avail}")
        self.used_label.setText(f"Points Used: {self.used_points}")
        self.count_label.setText(f"{len(self.selected_players)} / {MAX_TEAM_SIZE} players")
        self.points_bar.setValue(self.used_points)

        # Update progress bar color based on usage
        if self.used_points > 85:
            chunk_color = "#f78166"
        elif self.used_points > 60:
            chunk_color = "#f5c518"
        else:
            chunk_color = "#1f6feb"
        self.points_bar.setStyleSheet(f"""
            QProgressBar {{ background: #30363d; border-radius: 4px; border: none; }}
            QProgressBar::chunk {{ background: {chunk_color}; border-radius: 4px; }}
        """)

        # Category breakdown
        bat = sum(1 for p in self.selected_players if p[2] == "Batsman")
        bwl = sum(1 for p in self.selected_players if p[2] == "Bowler")
        ar  = sum(1 for p in self.selected_players if p[2] == "All-Rounder")
        wk  = sum(1 for p in self.selected_players if p[2] == "Wicket-Keeper")
        self.breakdown_label.setText(
            f"🏏 BAT: {bat}/4   🎯 BWL: {bwl}/4   ⭐ AR: {ar}/3   🧤 WK: {wk}/2"
        )

    def _refresh_players_list(self):
        if not self.selection_enabled:
            return
        checked = self.btn_group.checkedButton()
        if not checked:
            return
        category = checked.text().split(" ", 1)[1]   # strip emoji
        rows = get_players_by_category(category)
        selected_names = {p[0] for p in self.selected_players}
        self.players_list.clear()
        color = CATEGORY_COLORS.get(category, "#58a6ff")
        for player, value in rows:
            if player not in selected_names:
                item_text = f"  {player}   —   {value} pts"
                self.players_list.addItem(item_text)
        self.avail_count_label.setText(
            f"{self.players_list.count()} players available in {category}"
        )

    # ── Actions ───────────────────────────────────────────────────────────────
    def new_team(self):
        name, ok = QInputDialog.getText(self, "New Team", "Enter team name:")
        if not ok or not name.strip():
            return
        self.team_name         = name.strip()
        self.selected_players  = []
        self.used_points       = 0
        self.selection_enabled = True
        self.selected_list.clear()
        self.team_name_label.setText(f"🏆 {self.team_name}")
        for rb in self.radio_btns:
            rb.setEnabled(True)
        self.radio_btns[0].setChecked(True)
        self._update_points_display()
        self.statusBar().showMessage(
            f"✅  Team '{self.team_name}' created. Double-click players to add them!"
        )

    def open_team(self):
        names = get_saved_team_names()
        if not names:
            QMessageBox.information(self, "Open Team", "No saved teams found.")
            return
        name, ok = QInputDialog.getItem(self, "Open Team", "Select a team:", names, 0, False)
        if not ok:
            return
        self.team_name         = name
        self.selected_players  = []
        self.used_points       = 0
        self.selection_enabled = True
        self.selected_list.clear()
        players = load_team_from_db(name)
        for pname in players:
            pname = pname.strip()
            value, ctg = get_player_value(pname)
            self.selected_players.append((pname, value, ctg))
            self.used_points += value
            icon = CATEGORY_ICONS.get(ctg, "")
            self.selected_list.addItem(f"  {icon} {pname}   —   {ctg}   —   {value} pts")
        self.team_name_label.setText(f"🏆 {self.team_name}")
        for rb in self.radio_btns:
            rb.setEnabled(True)
        self.radio_btns[0].setChecked(True)
        self._update_points_display()
        self._refresh_players_list()
        self.statusBar().showMessage(f"📂  Team '{self.team_name}' loaded.")

    def save_team(self):
        if not self.team_name:
            QMessageBox.warning(self, "Save", "Create or open a team first.")
            return
        if not self.selected_players:
            QMessageBox.warning(self, "Save", "No players selected yet.")
            return
        names = [p[0] for p in self.selected_players]
        save_team_to_db(self.team_name, names, self.used_points)
        QMessageBox.information(self, "Saved ✅",
                                f"Team '{self.team_name}' saved successfully with "
                                f"{len(names)} players!")
        self.statusBar().showMessage(f"💾  Team '{self.team_name}' saved.")

    def rename_team(self):
        names = get_saved_team_names()
        if not names:
            QMessageBox.information(self, "Rename Team", "No saved teams found.")
            return
        old_name, ok = QInputDialog.getItem(self, "Rename Team",
                                            "Select team to rename:", names, 0, False)
        if not ok:
            return
        new_name, ok2 = QInputDialog.getText(self, "Rename Team",
                                             f"New name for '{old_name}':")
        if not ok2 or not new_name.strip():
            return
        new_name = new_name.strip()
        if new_name in names:
            QMessageBox.warning(self, "Error", f"'{new_name}' already exists.")
            return
        rename_team_in_db(old_name, new_name)
        if self.team_name == old_name:
            self.team_name = new_name
            self.team_name_label.setText(f"🏆 {self.team_name}")
        QMessageBox.information(self, "Renamed ✅",
                                f"Renamed '{old_name}' → '{new_name}'!")
        self.statusBar().showMessage(f"✏️  Team renamed to '{new_name}'.")

    def evaluate_score(self):
        dlg = ScoreDialog(self)
        dlg.exec_()

    def on_category_changed(self):
        self._refresh_players_list()

    def add_player(self, item):
        if not self.selection_enabled:
            return
        text   = item.text().strip()
        player = text.split("   —")[0].strip()
        value, ctg = get_player_value(player)

        if len(self.selected_players) >= MAX_TEAM_SIZE:
            QMessageBox.warning(self, "Team Full ❌",
                                f"Maximum {MAX_TEAM_SIZE} players allowed!")
            return
        if self.used_points + value > TOTAL_POINTS:
            QMessageBox.warning(self, "Insufficient Points ❌",
                                f"Not enough points!\n"
                                f"Available: {TOTAL_POINTS - self.used_points}  |  "
                                f"Player costs: {value}")
            return
        cat_count = sum(1 for p in self.selected_players if p[2] == ctg)
        if cat_count >= CATEGORY_LIMITS.get(ctg, 99):
            QMessageBox.warning(self, "Category Limit ❌",
                                f"Max {CATEGORY_LIMITS[ctg]} {ctg}s allowed in a team!")
            return

        self.selected_players.append((player, value, ctg))
        self.used_points += value
        icon = CATEGORY_ICONS.get(ctg, "")
        self.selected_list.addItem(f"  {icon} {player}   —   {ctg}   —   {value} pts")
        self._update_points_display()
        self._refresh_players_list()
        self.statusBar().showMessage(f"✅  Added {player} to {self.team_name}")

    def remove_player(self, item):
        text   = item.text().strip()
        player = text.split("   —")[0].strip()
        # strip any leading emoji+space
        for icon in CATEGORY_ICONS.values():
            player = player.replace(icon, "").strip()
        value, _ = get_player_value(player)
        self.selected_players = [p for p in self.selected_players if p[0] != player]
        self.used_points = max(0, self.used_points - value)
        row = self.selected_list.row(item)
        self.selected_list.takeItem(row)
        self._update_points_display()
        self._refresh_players_list()
        self.statusBar().showMessage(f"🗑️  Removed {player} from {self.team_name}")

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app    = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = FantasyCricketApp()
    window.show()
    sys.exit(app.exec_())
