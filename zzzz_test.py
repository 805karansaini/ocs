import tkinter as tk
from tkinter import ttk


def add_row():
    # Get data from entry fields
    name = name_entry.get()
    age = age_entry.get()

    # Insert data into table
    table.insert('', 'end', values=(name, age))

    # Clear entry fields
    name_entry.delete(0, 'end')
    age_entry.delete(0, 'end')


# Create main window
root = tk.Tk()
root.title("Table Example")

# Create table
columns = ('Name', 'Age')
table = ttk.Treeview(root, columns=columns, show='headings')
for col in columns:
    table.heading(col, text=col)
table.pack()

# Create entry fields for adding data
name_label = tk.Label(root, text="Name:")
name_label.pack()
name_entry = tk.Entry(root)
name_entry.pack()

age_label = tk.Label(root, text="Age:")
age_label.pack()
age_entry = tk.Entry(root)
age_entry.pack()

# Button to add row
add_button = tk.Button(root, text="Add Row", command=add_row)
add_button.pack()

root.mainloop()
