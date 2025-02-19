import threading
import time
import tkinter
import tkinter as tk
from tkinter import Scrollbar, ttk

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.option_indicator_tab import OptionIndicator
from option_combo_scanner.gui.scanner_combination_tab import ScannerCombinationTab
from option_combo_scanner.gui.scanner_inputs_tab import ScannerInputsTab

logger = CustomLogger.logger


class IsScreenRunning:
    flag_is_screen_running = False


class ScreenGUI(threading.Thread):
    def __init__(self):
        # Setted in the main whne the app is closed
        self.flag_stopped_all_task = False

        self.window = tk.Tk()
        self.window.title("Option Combo Scanner")
        self.window.geometry("1600x800")  # Set the window size

        # Create the notebook widget with three tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill="both")
        # Create the Scanner Inputs Tab
        self.scanner_inputs_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.scanner_inputs_tab_frame, text=" Scanner Inputs ")
        self.scanner_inputs_tab_object = ScannerInputsTab(self.scanner_inputs_tab_frame)

        # Create the Scanner Combination Tab
        self.combination_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.combination_tab_frame, text=" Scanned Combo ")
        self.combination_tab_object = ScannerCombinationTab(self.combination_tab_frame)

        # Create the Option Indicator tab
        self.option_indicator_data_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(
            self.option_indicator_data_tab_frame, text=" Option Indicator "
        )
        self.option_indicator_data_tab_object = OptionIndicator(
            self.option_indicator_data_tab_frame
        )

        # # Bind the event to the Trading Rules tab
        # self.notebook.bind(
        #     "<Button-1>", self.trading_rules_tab_object.update_trading_rules
        # )

        # Bind the closing event to the handler
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Mark that the screen is running
        IsScreenRunning.flag_is_screen_running = True

        self.close_button_clicked_lock = threading.Lock()

    def run(self):
        # Create and configure your GUI here...
        self.window.mainloop()

    def on_close(self):
        # if lock is acquired, return
        if self.close_button_clicked_lock.locked():
            return

        # if screen is waiting to be closed, return
        if not IsScreenRunning.flag_is_screen_running:
            return

        logger.info("Close GUI button clicked")

        t = threading.Thread(target=self.exit_gracefully)
        t.start()

    def exit_gracefully(self):
        # if lock is acquired, return
        if self.close_button_clicked_lock.locked():
            return

        # if screen is waiting to be closed, return
        if not IsScreenRunning.flag_is_screen_running:
            return

        with self.close_button_clicked_lock:
            # Mark that the screen is running
            IsScreenRunning.flag_is_screen_running = False

            logger.info("Exiting Gracefully")

            while not self.flag_stopped_all_task:
                time.sleep(0.2)
                logger.info("Waiting for the all the tasks to be stopped")
            else:
                logger.info("All the tasks stopped, Closing the window")
                try:
                    self.window.destroy()
                except Exception as exp:
                    pass

    # Method to dispaly error pop up
    def display_error_popup(self, error_title, error_string):
        # Create a error popup window
        error_popup = tk.Toplevel()
        error_popup.title(error_title)

        error_popup.geometry("400x100")

        # Create a frame for the input fields
        error_frame = ttk.Frame(error_popup, padding=20)
        error_frame.pack(fill="both", expand=True)

        # Add labels and entry fields for each column in the table
        error_label = ttk.Label(
            error_frame, text=error_string, width=80, anchor="center"
        )
        error_label.place(relx=0.5, rely=0.5, anchor="center")


if __name__ == "__main__":
    screen_gui_app = ScreenGUI()
    screen_gui_app.window.mainloop()
