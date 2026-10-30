#!/usr/bin/env python3

from ev3dev2.motor import LargeMotor, OUTPUT_B, OUTPUT_C
from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.sensor import INPUT_3
from ev3dev2.button import Button
from ev3dev2.sound import Sound
from ev3dev2.display import Display
import time


# ============================================================
# HARDWARE
# ============================================================

right_motor = LargeMotor(OUTPUT_B)
left_motor = LargeMotor(OUTPUT_C)

sensor = ColorSensor(INPUT_3)

button = Button()
sound = Sound()
display = Display()


# ============================================================
# CALIBRATION
# ============================================================

BLACK_AVERAGE = 10.64
FLOOR_AVERAGE = 54.71

TARGET = (BLACK_AVERAGE + FLOOR_AVERAGE) / 2


# ============================================================
# ORIGINAL PD
# ============================================================

KP = 0.75
KD = 0.35

MAX_CORRECTION = 15


# ============================================================
# SPEED
# ============================================================

current_speed = 21

straight_counter = 0


# ============================================================
# TURBO TRACK MAP
# ============================================================
#
# Bunlar track_log.csv-dən seçilmiş
# real rahat hissələrdir.
#
# Mürəkkəb hissələrə toxunmuruq.
# Xüsusilə 17-ci saniyə ətrafı ORIGINAL qalır.
#
# format:
# (START_ENCODER, END_ENCODER, MAX_SPEED)
# ============================================================

TURBO_ZONES = [

    # İlk rahat düz hissə
    (350, 720, 46),

    # Qısa rahat hissə
    (1280, 1450, 40),

    # Çox yaxşı düz hissə
    (1690, 2020, 48),

    # 2000-3300 QƏSDƏN YOXDUR
    # 17-ci saniyə problemi buradadır

    # Orta hissədə rahat yol
    (3730, 3990, 46),

    # Digər rahat hissə
    (4730, 5000, 46),

    # 5000-6100 problemli zonaya toxunmuruq

    # Sonlara yaxın yumşaq hissə
    (6250, 6690, 42),

    # Ən yaxşı uzun hissələrdən biri
    (6690, 7100, 52),
]


# ============================================================
# STOP
# ============================================================

def stop_robot():
    left_motor.stop()
    right_motor.stop()


# ============================================================
# ORIGINAL SPEED LOGIC
# ============================================================
#
# Bu sənin 1 dəqiqəlik stabil run-da
# işləyən məntiqdir.
# ============================================================

def original_speed_logic(
    abs_error,
    abs_derivative,
    straight_counter
):

    if abs_error >= 15 or abs_derivative >= 10:
        return 15

    elif abs_error >= 11 or abs_derivative >= 7:
        return 17

    elif abs_error >= 8 or abs_derivative >= 5:
        return 19

    elif abs_error >= 6 or abs_derivative >= 3.5:
        return 23

    elif straight_counter >= 12:
        return 37

    elif straight_counter >= 6:
        return 34

    elif abs_error >= 4 or abs_derivative >= 2:
        return 29

    else:
        return 31


# ============================================================
# GET TURBO SPEED
# ============================================================

def get_turbo_speed(position):

    for start, end, speed in TURBO_ZONES:

        if start <= position < end:
            return speed

    return None


# ============================================================
# RESET ENCODERS
# ============================================================

left_motor.position = 0
right_motor.position = 0


# ============================================================
# START SCREEN
# ============================================================

display.clear()

display.text_pixels(
    "TRACK TURBO V2",
    x=10,
    y=0
)

display.text_pixels(
    "Target: {:.1f}".format(TARGET),
    x=10,
    y=25
)

display.text_pixels(
    "CENTER = START",
    x=10,
    y=50
)

display.update()


# ============================================================
# WAIT FOR START
# ============================================================

while not button.enter:
    time.sleep(0.05)

sound.beep()

while button.enter:
    time.sleep(0.05)


# ============================================================
# INITIAL VALUES
# ============================================================

previous_error = 0

last_display_time = time.monotonic()

start_time = time.monotonic()


# ============================================================
# MAIN LOOP
# ============================================================

try:

    while True:

        loop_start = time.monotonic()


        # ====================================================
        # STOP BUTTON
        # ====================================================

        if button.enter:
            break


        # ====================================================
        # TIME
        # ====================================================

        now = time.monotonic()

        elapsed_time = now - start_time


        # ====================================================
        # POSITION
        # ====================================================

        left_position = left_motor.position
        right_position = right_motor.position

        track_position = (
            abs(left_position)
            + abs(right_position)
        ) / 2.0


        # ====================================================
        # SENSOR
        # ====================================================

        sensor_value = sensor.reflected_light_intensity


        # ====================================================
        # ERROR
        # ====================================================

        error = sensor_value - TARGET

        abs_error = abs(error)


        # ====================================================
        # DERIVATIVE
        # ====================================================

        derivative = error - previous_error

        abs_derivative = abs(derivative)


        # ====================================================
        # ORIGINAL PD
        # ====================================================

        correction = (
            KP * error
            + KD * derivative
        )


        # ====================================================
        # ORIGINAL CORRECTION LIMIT
        # ====================================================

        if correction > MAX_CORRECTION:
            correction = MAX_CORRECTION

        elif correction < -MAX_CORRECTION:
            correction = -MAX_CORRECTION


        # ====================================================
        # STRAIGHT COUNTER
        # ====================================================

        if abs_error < 7 and abs_derivative < 4:

            straight_counter += 1

        else:

            straight_counter = 0


        if straight_counter > 100:
            straight_counter = 100


        # ====================================================
        # ORIGINAL TARGET SPEED
        # ====================================================

        target_speed = original_speed_logic(
            abs_error,
            abs_derivative,
            straight_counter
        )


        # ====================================================
        # TRACK TURBO
        # ====================================================

        turbo_speed = get_turbo_speed(
            track_position
        )

        turbo_active = False


        # Turbo yalnız encoder zonasında olmaqla kifayətlənmir.
        #
        # Robot REAL olaraq stabil getməlidir.
        #
        # Bu çox vacibdir.
        if turbo_speed is not None:

            if (
                abs_error < 6
                and abs_derivative < 3.5
                and abs(correction) < 6
                and straight_counter >= 3
            ):

                turbo_active = True

                target_speed = turbo_speed


        # ====================================================
        # EXTRA TURBO SAFETY
        # ====================================================
        #
        # Turbo zamanı sensor qəfil dəyişsə:
        #
        # TURBO DƏRHAL SÖNÜR.
        #
        # Robot original controller-ə qayıdır.
        # ====================================================

        if turbo_active:

            if (
                abs_derivative >= 4
                or abs_error >= 7
                or abs(correction) >= 7
            ):

                turbo_active = False

                target_speed = original_speed_logic(
                    abs_error,
                    abs_derivative,
                    straight_counter
                )


        # ====================================================
        # SPEED CONTROL
        # ====================================================
        #
        # DÖNGƏ:
        # dərhal yavaşla.
        #
        # TURBO:
        # daha sürətli acceleration.
        # ====================================================

        if target_speed < current_speed:

            current_speed = target_speed


        else:

            if turbo_active:

                # Turbo acceleration
                acceleration = 5

            else:

                # Original acceleration
                acceleration = 3


            current_speed += acceleration


            if current_speed > target_speed:

                current_speed = target_speed


        # ====================================================
        # MOTOR SPEEDS
        # ====================================================

        left_speed = (
            current_speed
            + correction
        )

        right_speed = (
            current_speed
            - correction
        )


        # ====================================================
        # SAFETY
        # ====================================================

        left_speed = max(
            0,
            min(100, left_speed)
        )

        right_speed = max(
            0,
            min(100, right_speed)
        )


        # ====================================================
        # MOTORS
        # ====================================================

        left_motor.run_direct(
            duty_cycle_sp=int(left_speed)
        )

        right_motor.run_direct(
            duty_cycle_sp=int(right_speed)
        )


        # ====================================================
        # SAVE
        # ====================================================

        previous_error = error


        # ====================================================
        # DISPLAY
        # ====================================================

        if now - last_display_time >= 0.20:

            display.clear()


            display.text_pixels(
                "T:{:.1f}".format(
                    elapsed_time
                ),
                x=0,
                y=0
            )


            display.text_pixels(
                "P:{:.0f}".format(
                    track_position
                ),
                x=0,
                y=20
            )


            display.text_pixels(
                "V:{:.0f}".format(
                    current_speed
                ),
                x=0,
                y=40
            )


            if turbo_active:

                display.text_pixels(
                    "TURBO",
                    x=0,
                    y=60
                )

            else:

                display.text_pixels(
                    "NORMAL",
                    x=0,
                    y=60
                )


            display.update()

            last_display_time = now


        # ====================================================
        # LOOP TIMING
        # ====================================================

        elapsed_loop = (
            time.monotonic()
            - loop_start
        )

        remaining = (
            0.025
            - elapsed_loop
        )

        if remaining > 0:
            time.sleep(remaining)


except KeyboardInterrupt:

    pass


except Exception:

    pass


# ============================================================
# STOP
# ============================================================

finally:

    stop_robot()

    total_time = (
        time.monotonic()
        - start_time
    )

    sound.beep()

    display.clear()

    display.text_pixels(
        "FINISH",
        x=45,
        y=15
    )

    display.text_pixels(
        "{:.2f} sec".format(
            total_time
        ),
        x=30,
        y=45
    )

    display.update()

    time.sleep(2)