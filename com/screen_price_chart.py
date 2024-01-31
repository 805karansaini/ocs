"""
Created on 05-Apr-2023

@author: Karan
"""

from com import *
from com.variables import *
from com.combination_helper import *


class PriceChart(tk.Toplevel):
    """
    classdocs
    """

    def __init__(self, unique_id):

        # Create a popup window
        self.chart_window_master = tk.Toplevel()
        self.chart_window_master.title(f"Price Chart, Unique ID: {unique_id}")

        # Geometry
        self.chart_window_master.geometry("830x720")

        # Frame
        chart_popup_window = ttk.Frame(self.chart_window_master)
        chart_popup_window.pack(fill="both", expand=True)

        # Create a frame for the input fields
        chart_popup_input_frame = ttk.Frame(
            self.chart_window_master,
            height=150,
        )
        chart_popup_input_frame.pack(fill="both", expand=True)

        # # Create second frame with remaining area
        chart_popup_chart_frame = ttk.Frame(
            self.chart_window_master,
        )
        chart_popup_chart_frame.pack(expand=True)

        # Add a label and entry field for the user to enter an integer
        # Add labels and entry fields for each column in the table
        ttk.Label(
            chart_popup_input_frame,
            text="Bar Size",
            width=16,
            anchor="center",
        ).grid(column=0, row=0, padx=5, pady=5)
        ttk.Label(
            chart_popup_input_frame,
            text="Chart Duration",
            width=16,
            anchor="center",
        ).grid(column=1, row=0, padx=5, pady=5)
        ttk.Label(
            chart_popup_input_frame,
            text="Auto Update(Sec)",
            width=16,
            anchor="center",
        ).grid(column=2, row=0, padx=5, pady=5)

        bar_size_options = [
            "1 min",
            "2 mins",
            "3 mins",
            "5 mins",
            "10 mins",
            "15 mins",
            "20 mins",
            "30 mins",
            "1 hour",
            "2 hours",
            "3 hours",
            "4 hours",
            "8 hours",
            "1 day",
            "1 week",
        ]
        chart_duration_options = [
            "1 Day",
            "2 Day",
            "3 Day",
            "4 Day",
            "1 Week",
            "2 Weeks",
            "3 Weeks",
            "1 Month",
            "2 Months",
            "3 Months",
            "4 Months",
            "5 Months",
            "6 Months",
            "12 Months",
        ]

        # Create a custom style for the Combobox widget
        custom_style = ttk.Style()
        custom_style.map(
            "Custom.TCombobox",
            fieldbackground=[
                ("readonly", "white"),
                ("!disabled", "white"),
                ("disabled", "lightgray"),
            ],
        )

        bar_size_combo_box = ttk.Combobox(
            chart_popup_input_frame, width=12, values=bar_size_options, state="readonly"
        )
        bar_size_combo_box.current(0)
        bar_size_combo_box.grid(column=0, row=1, padx=5, pady=5)

        chart_duration_combo_box = ttk.Combobox(
            chart_popup_input_frame,
            width=12,
            values=chart_duration_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        chart_duration_combo_box.current(0)
        chart_duration_combo_box.grid(column=1, row=1, padx=5, pady=5)

        update_frequency_entry = ttk.Entry(
            chart_popup_input_frame,
            width=14,
        )
        update_frequency_entry.grid(column=2, row=1, padx=5, pady=5)

        # Place in center
        chart_popup_input_frame.place(relx=0.5, anchor=tk.CENTER)
        chart_popup_input_frame.place(y=30)

        chart_popup_chart_frame.place(relx=0.5, anchor=tk.CENTER)
        chart_popup_chart_frame.place(y=390)

        ####### CHART ###########
        # Figure
        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)

        # Create Canvas
        canvas = FigureCanvasTkAgg(fig, master=chart_popup_chart_frame)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Green Color For UP, Red for Down
        mc = mpf.make_marketcolors(up="g", down="r")

        # Create Canvas
        canvas.draw()

        # Create toolbar
        toolbar = NavigationToolbar2Tk(canvas, chart_popup_chart_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # create a flag variable to check if the window is closed
        self.window_closed = False

        # bind the close event to stop the thread
        self.chart_window_master.protocol("WM_DELETE_WINDOW", self.on_close)

        self.plot_chart_button = ttk.Button(
            chart_popup_input_frame,
            text="Plot Chart",
            # width=16,
            command=lambda: self.on_plot_chart_button_click(
                ax,
                fig,
                canvas,
                unique_id,
                bar_size_combo_box,
                chart_duration_combo_box,
                update_frequency_entry,
            ),
        )
        self.plot_chart_button.grid(column=3, row=1, padx=5, pady=5)

    # Method to draw graph
    def draw_chart(
        self,
        ax,
        fig,
        canvas,
        unique_id,
        bar_size_combo_box,
        chart_duration_combo_box,
        update_frequency_entry,
    ):

        # User Given Values
        bar_size = bar_size_combo_box.get().strip()
        chart_size = chart_duration_combo_box.get().strip()
        update_time = update_frequency_entry.get().strip()

        # Get title of Plot
        combination_object_unique_id = variables.unique_id_to_combo_obj[unique_id]
        info_string = make_informative_combo_string(combination_object_unique_id)
        info_string = " \n".join(
            [info_string[cx : cx + 85] for cx in range(0, len(info_string), 85)]
        )

        # Update Time in Seconds
        if update_time == "":
            update_time = None
        else:
            try:
                update_time = int(update_time)
            except:
                update_time = 600

        if update_time != None:
            flag_keep_updating = True
        else:
            flag_keep_updating = False

        while not self.window_closed:

            # Request Historical Data for the unique Id
            ohlc_data = request_historical_price_data_of_combination_for_chart(
                unique_id, bar_size, chart_size
            )

            # If ohlc_data is None, Zero Length, Empty DataFrame
            if ohlc_data is None or len(ohlc_data.index) == 0 or ohlc_data.empty:
                print(f"Unable to get Data for Unique ID: {unique_id}")
                self.plot_chart_button.config(state="normal")
                return

            # data = pd.read_csv(r"sample_csv_og.csv",parse_dates=True, index_col=0)
            ohlc_data.index.name = "Time"

            # Clear the Canvas
            ax.clear()

            # Figure Title
            fig.suptitle(info_string, size="small", weight="semibold")

            # Plot candlestick chart
            mpf.plot(
                ohlc_data,
                ax=ax,
                style="yahoo",
                type="candle",
                xrotation=20,
            )  # mav=(10, 20),)

            # Draw the canvas in tkinter
            canvas.draw()

            # Keep Updating The Chart
            if flag_keep_updating:
                # print(f"Sleep {update_time}")

                counter = 1
                while (
                    int(update_time / (variables.sleep_iteration_price_chart * counter))
                    > 0
                ):
                    time.sleep(variables.sleep_iteration_price_chart)
                    counter += 1

                    # Break from this Loop then main While Loop will also be breaked
                    if self.window_closed:
                        break

            else:
                # Enable the button now.
                self.plot_chart_button.config(state="normal")
                break
        else:
            print("Breaked")

    # Method to invoke when window get destroy
    def on_close(self):
        # set the flag to True to stop the update thread
        self.window_closed = True

        # Destory the ScreenWindow
        self.chart_window_master.destroy()

    # Method to perform action when plot chart button click
    def on_plot_chart_button_click(
        self,
        ax,
        fig,
        canvas,
        unique_id,
        bar_size_combo_box,
        chart_duration_combo_box,
        update_frequency_entry,
    ):
        self.plot_chart_button.config(state="disabled")
        self.draw_chart_thread = threading.Thread(
            target=self.draw_chart,
            args=(
                ax,
                fig,
                canvas,
                unique_id,
                bar_size_combo_box,
                chart_duration_combo_box,
                update_frequency_entry,
            ),
        )
        self.draw_chart_thread.start()
