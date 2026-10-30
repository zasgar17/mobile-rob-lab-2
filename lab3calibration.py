#!/usr/bin/env python3

from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.sensor import INPUT_3
from ev3dev2.sound import Sound
from ev3dev2.display import Display
from ev3dev2.button import Button

import time


# ============================================================
# LEGO EV3 - COLOR SENSOR CALIBRATION
# ============================================================

color_sensor = ColorSensor(INPUT_3)

sound = Sound()
display = Display()
button = Button()


# ============================================================
# SETTINGS
# ============================================================

CALIBRATION_TIME = 4.0

# Sensor samples every 0.05 sec
SAMPLE_DELAY = 0.05

# Print to terminal every 0.20 sec
PRINT_DELAY = 0.20


# ============================================================
# DISPLAY
# ============================================================

def show_message(line1, line2="", line3=""):

    display.clear()

    display.text_pixels(
        line1,
        clear_screen=True,
        x=5,
        y=20
    )

    if line2:
        display.text_pixels(
            line2,
            x=5,
            y=50
        )

    if line3:
        display.text_pixels(
            line3,
            x=5,
            y=80
        )

    display.update()


# ============================================================
# BUTTON
# ============================================================

def wait_for_center_button():

    while not button.enter:
        time.sleep(0.05)

    while button.enter:
        time.sleep(0.05)


# ============================================================
# CALIBRATION
# ============================================================

def calibrate_surface(surface_name):

    show_message(
        "CALIBRATION",
        surface_name,
        "Press CENTER"
    )

    print()
    print("========================================")
    print("Waiting for CENTER button")
    print("Surface:", surface_name)
    print("========================================")

    wait_for_center_button()

    sound.beep()

    show_message(
        surface_name,
        "START!",
        "Move robot..."
    )

    print()
    print("----------------------------------------")
    print("START:", surface_name)
    print("Move the robot for 4 seconds")
    print("----------------------------------------")

    values = []

    start_time = time.time()
    last_print_time = start_time

    while time.time() - start_time < CALIBRATION_TIME:

        current_time = time.time()

        value = color_sensor.reflected_light_intensity

        values.append(value)

        # Print every 0.20 seconds
        if current_time - last_print_time >= PRINT_DELAY:

            elapsed = current_time - start_time

            print(
                "Time: {:4.2f}s | "
                "Reflected: {:3d}".format(
                    elapsed,
                    value
                )
            )

            last_print_time = current_time

        time.sleep(SAMPLE_DELAY)

    sound.beep()

    # ========================================================
    # STATISTICS
    # ========================================================

    minimum = min(values)
    maximum = max(values)

    average = sum(values) / len(values)

    print()
    print("----------------------------------------")
    print("CALIBRATION FINISHED:", surface_name)
    print("----------------------------------------")

    print("Samples :", len(values))
    print("Minimum :", minimum)
    print("Maximum :", maximum)
    print("Average :", round(average, 2))

    print("----------------------------------------")
    print()

    return minimum, maximum, average


# ============================================================
# PROGRAM START
# ============================================================

print()
print("========================================")
print(" LEGO EV3 COLOR SENSOR CALIBRATION")
print("========================================")
print()


show_message(
    "LINE CALIBRATION",
    "Black + Floor",
    "Press CENTER"
)

print("Press CENTER to begin calibration...")

wait_for_center_button()


# ============================================================
# BLACK
# ============================================================

black_min, black_max, black_average = calibrate_surface(
    "BLACK TAPE"
)


show_message(
    "BLACK TAPE",
    "AVG: {:.1f}".format(black_average),
    "MIN {} MAX {}".format(
        black_min,
        black_max
    )
)

time.sleep(2)


# ============================================================
# FLOOR
# ============================================================

floor_min, floor_max, floor_average = calibrate_surface(
    "FLOOR"
)


# ============================================================
# FINAL RESULTS
# ============================================================

range_value = abs(
    floor_average - black_average
)


print()
print("========================================")
print(" FINAL CALIBRATION RESULTS")
print("========================================")

print("BLACK")
print("  Min     :", black_min)
print("  Max     :", black_max)
print("  Average :", round(black_average, 2))

print()

print("FLOOR")
print("  Min     :", floor_min)
print("  Max     :", floor_max)
print("  Average :", round(floor_average, 2))

print()

print("Difference between averages:")
print("  Range   :", round(range_value, 2))

print("========================================")
print()


display.clear()

display.text_pixels(
    "CALIBRATION DONE",
    x=5,
    y=10
)

display.text_pixels(
    "BLACK: {:.1f}".format(black_average),
    x=5,
    y=35
)

display.text_pixels(
    "FLOOR: {:.1f}".format(floor_average),
    x=5,
    y=60
)

display.text_pixels(
    "RANGE: {:.1f}".format(range_value),
    x=5,
    y=85
)

display.update()


sound.beep()
time.sleep(0.5)
sound.beep()


# ============================================================
# WAIT
# ============================================================

print("Calibration complete.")
print("Press CENTER to exit.")

while True:

    if button.enter:
        break

    time.sleep(0.1)