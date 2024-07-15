import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from typing import Callable
import random
import math
from models import RefillState

# Set up the constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700

SCREEN_TITLE = "Smart Bowl"
BG_COLOR = "#222"
TEXT_COLOR = "#FFFFFF"
EMPTY_TEXT_COLOR = "red"

CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2

WEIGHT_UNIT = "g"

BOWL_WIDTH = 300
BOWL_HEIGHT = 150
FOOD_COLOR = "#8B4513"  # Brown
BOWL_COLOR = "#A9A9A9"  # Grey
FOOD_RADIUS = 5  # Radius of each food circle
CIRCLE_PADDING = 2  # Space between food circles

# Coordinates for the bowl
BOWL_TOP_LEFT_X = CENTER_X - BOWL_WIDTH // 2
BOWL_TOP_LEFT_Y = CENTER_Y - BOWL_HEIGHT // 2
BOWL_BOTTOM_RIGHT_X = CENTER_X + BOWL_WIDTH // 2
BOWL_BOTTOM_RIGHT_Y = CENTER_Y + BOWL_HEIGHT // 2


class BowlGUI:
    def __init__(self, root=tk.Tk()):
        self.root = root
        self.root.title(SCREEN_TITLE)

        self.canvas = tk.Canvas(
            self.root, width=SCREEN_WIDTH, height=SCREEN_HEIGHT, bg=BG_COLOR
        )
        self.canvas.pack()

        self.on_refill_cb = lambda: ...
        self.propose_new_target_weight_cb = lambda weight: ...

        self.capacity = 1  # Default capacity
        self.current_weight = 0
        self.target_weight = 0
        self.refill_state = RefillState.OFF
        self.last_visual_bowl_weight = 0

        self.init_ui()

    def init_ui(self):
        self.draw_refill_button()
        self.draw_target_weight_button()

    def set_refill_callback(self, callback: Callable[[], None]):
        self.on_refill_cb = callback

    def set_propose_new_target_weight_callback(self, callback: Callable[[int], None]):
        self.propose_new_target_weight_cb = callback

    def start_mainloop(self):
        self.init_drawing()
        # Start the tkinter main loop
        self.root.mainloop()

    def init_drawing(self) -> None:
        self.root.after(ms=0, func=self.update_visuals)
        self.root.after(ms=0, func=self.draw_bowl)

    def on_new_target_proposal_denial(self, error_message: str) -> None:
        messagebox.showerror("Error", error_message)

    def set_capacity_value(self, capacity: float):
        self.capacity = capacity
        self.root.after(ms=0, func=self.update_capacity_text)

    def set_current_weight(self, weight: float):
        self.current_weight = weight
        self.root.after(ms=0, func=self.update_current_weight_text)
        is_ascending = self.current_weight > self.last_visual_bowl_weight
        self.last_visual_bowl_weight = self.current_weight
        if is_ascending:
            self.root.after(ms=0, func=self.draw_bowl_food)
        else:
            self.root.after(ms=0, func=self.remove_food_from_bowl)

    def set_target_weight(self, weight: float):
        self.target_weight = weight
        self.root.after(ms=0, func=self.update_target_weight_text)

    def set_refill_state(self, state: RefillState):
        self.refill_state = state
        self.root.after(ms=0, func=self.update_refill_text)

    def on_refill(self):
        self.on_refill_cb()

    def set_new_target_weight(self):
        try:
            weight = int(self.target_weight_entry.get())
            self.propose_new_target_weight_cb(weight)
        except ValueError:
            self.on_new_target_proposal_denial("Invalid weight value")

    def update_visuals(self):
        self.update_capacity_text()
        self.update_current_weight_text()
        self.update_target_weight_text()
        self.update_refill_text()

    def update_refill_text(self):
        if self.refill_state == RefillState.OFF:
            color = "blue"
        elif self.refill_state == RefillState.ON:
            color = "green"
        self.canvas.delete("refill_text")
        self.canvas.create_text(
            CENTER_X, 100, fill=TEXT_COLOR, text="Refill", tags="refill_text"
        )
        self.canvas.create_oval(
            CENTER_X + 22,
            100 - 4,
            CENTER_X + 30,
            100 + 4,
            fill=color,
            outline=color,
            width=4,
        )

    def update_capacity_text(self):
        capacity_text = f"Capacity: {self.capacity} {WEIGHT_UNIT}"
        self.canvas.delete("capacity_text")
        self.canvas.create_text(
            CENTER_X, 150, fill=TEXT_COLOR, text=capacity_text, tags="capacity_text"
        )

    def update_target_weight_text(self):
        target_weight_text = f"Target Weight: {self.target_weight} {WEIGHT_UNIT}"
        self.canvas.delete("target_weight_text")
        self.canvas.create_text(
            CENTER_X,
            200,
            fill=TEXT_COLOR,
            text=target_weight_text,
            tags="target_weight_text",
        )

    def update_current_weight_text(self):
        current_weight_text = f"Current Weight: {self.current_weight} {WEIGHT_UNIT}"
        self.canvas.delete("current_weight_text")
        self.canvas.create_text(
            CENTER_X,
            250,
            fill=TEXT_COLOR,
            text=current_weight_text,
            tags="current_weight_text",
        )
        if self.current_weight == 0:
            self.canvas.delete("empty_text")
            self.canvas.create_text(
                CENTER_X,
                BOWL_BOTTOM_RIGHT_Y + 25,
                fill=EMPTY_TEXT_COLOR,
                text="EMPTY!!!",
                tags="empty_text",
            )
        else:
            self.canvas.delete("empty_text")

    def draw_bowl(self):
        # Draw the bowl with shades of grey
        for i in range(10):
            # Calculate gradient color
            shade = 230 - i * 10  # Adjust as needed for the gradient effect
            color = f"#{shade:02x}{shade:02x}{shade:02x}"  # Convert shade to hex color

            # Calculate oval coordinates
            x1 = BOWL_TOP_LEFT_X - i
            y1 = BOWL_TOP_LEFT_Y - i
            x2 = BOWL_BOTTOM_RIGHT_X + i
            y2 = BOWL_BOTTOM_RIGHT_Y + i

            # Create oval with gradient color
            self.canvas.create_oval(
                x1, y1, x2, y2, fill=color, outline=color, tags="bowl"
            )

    def draw_bowl_food(self):
        # Calculate the number of food circles based on current weight and capacity
        if self.capacity > 0:
            food_count = math.ceil(
                self.current_weight / self.capacity * 700
            )  # Adjust factor as needed
        else:
            food_count = 0

        # Get current food circles drawn in the bowl
        current_food_tags = set(self.canvas.find_withtag("bowl_food"))

        # Attempt to add new food circles if current weight is higher
        attempts = 0
        while len(current_food_tags) < food_count and attempts < 1000:
            # Generate random coordinates for new food circles within the bowl area
            x = random.randint(
                BOWL_TOP_LEFT_X + FOOD_RADIUS, BOWL_BOTTOM_RIGHT_X - FOOD_RADIUS
            )
            y = random.randint(
                BOWL_TOP_LEFT_Y + FOOD_RADIUS, BOWL_BOTTOM_RIGHT_Y - FOOD_RADIUS
            )

            # Check if the generated position is within the bowl oval and not overlapping with existing circles
            if (x - CENTER_X) ** 2 / (BOWL_WIDTH / 2) ** 2 + (y - CENTER_Y) ** 2 / (
                BOWL_HEIGHT / 2
            ) ** 2 <= 1:
                overlap = False
                for tag in current_food_tags:
                    (food_x, food_y, _, _) = self.canvas.coords(tag)
                    if (x - food_x) ** 2 + (y - food_y) ** 2 < (
                        2 * FOOD_RADIUS
                    ) ** 2:  # Check for overlap
                        overlap = True
                        break

                if not overlap:
                    food_circle = self.canvas.create_oval(
                        x - FOOD_RADIUS,
                        y - FOOD_RADIUS,
                        x + FOOD_RADIUS,
                        y + FOOD_RADIUS,
                        fill=FOOD_COLOR,
                        outline=FOOD_COLOR,
                        tags="bowl_food",
                    )
                    current_food_tags.add(food_circle)

            attempts += 1

        # Remove excess food circles if current weight is lower
        while len(current_food_tags) > food_count:
            item = current_food_tags.pop()
            self.canvas.delete(item)

    def remove_food_from_bowl(self):
        # Remove excess food circles based on current weight decrease
        if self.capacity > 0:
            food_count = math.ceil(
                self.current_weight / self.capacity * 700
            )  # Adjust as needed
        else:
            food_count = 0

        # Get current food circles drawn in the bowl
        food_items = self.canvas.find_withtag("bowl_food")

        # Remove excess food circles
        for item in food_items[food_count:]:
            self.canvas.delete(item)

    def draw_refill_button(self):
        style = ttk.Style()
        style.configure(
            "Refill.TButton",
            font=("Helvetica", 12),
            background="#E0E0E0",
            foreground=TEXT_COLOR,
            borderwidth=1,
        )
        style.map(
            "Refill.TButton",
            background=[
                ("active", "#D0D0D0"),
                ("pressed", "#C0C0C0"),
                ("hover", "#F0F0F0"),
            ],
            foreground=[
                ("active", TEXT_COLOR),
                ("pressed", TEXT_COLOR),
                ("hover", TEXT_COLOR),
            ],
            relief=[("pressed", "sunken")],
        )
        # Refill button
        refill_button = ttk.Button(
            self.root, text="Refill", command=self.on_refill, style="Refill.TButton"
        )
        self.canvas.create_window(
            CENTER_X,
            BOWL_BOTTOM_RIGHT_Y + 75,
            window=refill_button,
            tags="refill_button",
        )

        # Bind hover events to change cursor and appearance
        refill_button.bind(
            "<Enter>", lambda e: refill_button.state(["!active", "hover"])
        )
        refill_button.bind(
            "<Leave>", lambda e: refill_button.state(["!hover", "!pressed"])
        )
        refill_button.bind("<Enter>", lambda e: refill_button.config(cursor="hand2"))
        refill_button.bind("<Leave>", lambda e: refill_button.config(cursor=""))

    def draw_target_weight_button(self):
        style = ttk.Style()
        style.configure(
            "Target.TButton",
            font=("Helvetica", 12),
            background="#E0E0E0",
            foreground=TEXT_COLOR,
            borderwidth=1,
        )
        style.map(
            "Target.TButton",
            background=[
                ("active", "#D0D0D0"),
                ("pressed", "#C0C0C0"),
                ("hover", "#F0F0F0"),
            ],
            foreground=[
                ("active", TEXT_COLOR),
                ("pressed", TEXT_COLOR),
                ("hover", TEXT_COLOR),
            ],
            relief=[("pressed", "sunken")],
        )
        # New target weight input and button
        self.target_weight_entry = tk.Entry(self.root)
        self.canvas.create_window(
            CENTER_X,
            BOWL_BOTTOM_RIGHT_Y + 125,
            window=self.target_weight_entry,
            tags="target_weight_entry",
        )

        target_weight_button = ttk.Button(
            self.root,
            text="Set Target Weight",
            command=self.set_new_target_weight,
            style="Target.TButton",
        )
        self.canvas.create_window(
            CENTER_X,
            BOWL_BOTTOM_RIGHT_Y + 175,
            window=target_weight_button,
            tags="target_weight_button",
        )

        # Bind hover events to change cursor and appearance for target weight button
        target_weight_button.bind(
            "<Enter>", lambda e: target_weight_button.state(["!active", "hover"])
        )
        target_weight_button.bind(
            "<Leave>", lambda e: target_weight_button.state(["!hover", "!pressed"])
        )
        target_weight_button.bind(
            "<Enter>", lambda e: target_weight_button.config(cursor="hand2")
        )
        target_weight_button.bind(
            "<Leave>", lambda e: target_weight_button.config(cursor="")
        )
