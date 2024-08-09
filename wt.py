#!/opt/homebrew/bin/python3

##
# Work Time (like "time to work" and actually "timing" work :D)
##

from datetime import datetime as dt
from enum import StrEnum
import sys
import os

TMP_FILE_PATH = "/tmp/wt"
DT_FORMAT = "%Y-%m-%d %H-%M-%S"


class Status(StrEnum):
    Stopped = "stopped"
    Paused = "paused"
    Running = "running"


class Timer():
    def __init__(self, status=Status.Stopped, start="", pausedTime=0, totalTime=0):
        self.status: Status = status
        self.start_datetime_str: str = start
        self.paused_minutes: int = pausedTime
        self.completed_minutes: int = totalTime

    def __str__(self):
        return f"status = {self.status}\nstart_datetime = {self.start_datetime_str}\npaused_minutes = {self.paused_minutes}\ncompleted_minutes = {self.completed_minutes}"


def main():
    args = sys.argv[1:]
    if len(args) == 0:
        check()
        return

    match args[0]:
        case "start":
            start()
        case "stop":
            stop()
        case "pause":
            pause()
        case "check":
            check()
        case "set":
            if len(args) < 3:
                print("Incorrect amount of arguments.\n")
                print_help()
                return
            set_timer(args[1], args[2])
        case "reset":
            reset()
        case "new":
            new()
        case "remove":
            remove()
        case "help":
            print_help()
        case "debug":
            debug()
        case _:
            print("Invalid command.\n")
            print_help()


# TODO: PRIO 4. Maybe store tmp file elsewhere to not lose on potential mid-day system reboot? /Users/Shared?? Nice if platform agnostic. Could also auto determine based on platform.

def start():
    timer = Timer()
    if os.path.exists(TMP_FILE_PATH):
        timer = load()

    message = ""
    match timer.status:
        case Status.Running:
            print("Already running.")
            return
        case Status.Paused:
            message = "Resuming timer."
        case Status.Stopped:
            message = "Starting timer."

    now = dt.now().strftime(DT_FORMAT)
    timer.start_datetime_str = now
    timer.status = Status.Running
    save(timer)
    print(message)
    check()


def stop():
    if not os.path.exists(TMP_FILE_PATH):
        print("No timer exists.")
        return

    timer = load()
    match timer.status:
        case Status.Stopped:
            print("Timer already stopped.")
        case Status.Running | Status.Paused:
            if timer.status == Status.Running:
                timer.completed_minutes += delta_minutes(
                    dt.strptime(timer.start_datetime_str, DT_FORMAT), dt.now())

            timer.start_datetime_str = ""
            timer.completed_minutes += timer.paused_minutes
            timer.paused_minutes = 0
            timer.status = Status.Stopped
            save(timer)
            print("Timer stopped.")
            check()
        case _:
            print(f"Unhandled status: {timer.status}")


def pause():
    if not os.path.exists(TMP_FILE_PATH):
        print("No timer exists.")

    timer = load()
    match timer.status:
        case Status.Paused:
            print("Timer already paused.")
        case Status.Stopped:
            print("Cannot pause stopped timer.")
        case Status.Running:
            timer.paused_minutes += delta_minutes(dt.strptime(
                timer.start_datetime_str, DT_FORMAT), dt.now())
            timer.start_datetime_str = ""
            timer.status = Status.Paused
            save(timer)
            print(f"Timer paused.")
            check()
        case _:
            print(f"Unhandled status: {timer.status}")


def check():
    if not os.path.exists(TMP_FILE_PATH):
        print("No timer exists.")
        return

    timer = load()

    running_minutes = 0

    if timer.status == Status.Running:
        running_minutes = delta_minutes(dt.strptime(
            timer.start_datetime_str, DT_FORMAT), dt.now()) + timer.paused_minutes
    elif timer.status == Status.Paused:
        running_minutes = timer.paused_minutes

    total_minutes = running_minutes + timer.completed_minutes

    running_str = ""
    match timer.status:
        case Status.Running:
            running_str = hour_minute_str_from_minutes(running_minutes)
        case Status.Paused:
            running_str = hour_minute_str_from_minutes(timer.paused_minutes)
        case Status.Stopped:
            running_str = "--:--"
        case _:
            print(f"Unhandled status: {timer.status}.")
            return

    status_str = timer.status.upper()
    total_str = hour_minute_str_from_minutes(total_minutes)

    print(f"{running_str} {status_str} (total {total_str})")


def set_timer(type: str, time: str):
    if not os.path.exists(TMP_FILE_PATH):
        print("No timer exists.")
        return

    if type not in ["total", "current"]:
        print("Incorrect timer type. Should be 'total' or 'current'.")
        return

    if len(time) < 1 or len(time) > 4 or not time.isdigit():
        print("Incorrect time format. Should be 1-4 digit HHMM.")
        return

    timer = load()

    hour = 0
    minute = 0
    match len(time):
        case 4:
            hour = int(time[:2])
            minute = int(time[2:])
        case 3:
            hour = int(time[:1])
            minute = int(time[1:])
        case 2 | 1:
            minute = int(time)

    match type:
        case "total":
            if timer.status != Status.Stopped:
                print("Can only set total time when timer is stopped.")
                return

            timer.completed_minutes = hour_minute_to_minutes(hour, minute)
        case "current":
            if timer.status not in [Status.Running, Status.Paused, Status.Stopped]:
                print(f"Current status {timer.status} not handled.")
                return

            timer.paused_minutes = hour_minute_to_minutes(hour, minute)

            if timer.status == Status.Running:
                timer.paused_minutes += delta_minutes(dt.strptime(
                    timer.start_datetime_str, DT_FORMAT), dt.now())
                now = dt.now().strftime(DT_FORMAT)
                timer.start_datetime_str = now

            elif timer.status == Status.Stopped:
                timer.status = Status.Paused

        case _:
            print(f"Unhandled type: {type}.")
            return

    save(timer)
    print("Timer set.")
    check()


def reset():
    timer = Timer()
    save(timer)
    print("Timer reset.")
    check()


def new():
    timer = Timer()
    save(timer)
    print("New timer initialized.")
    check()


def remove():
    if not os.path.exists(TMP_FILE_PATH):
        print("Timer does not exist.")
        return

    os.remove(TMP_FILE_PATH)
    print("Timer removed.")


def debug():
    print(f"TMP_FILE_PATH = {TMP_FILE_PATH}\nDT_FORMAT = {DT_FORMAT}")
    if os.path.exists(TMP_FILE_PATH):
        timer = load(debug=True)
        print(timer)
    else:
        print(f"No file at {TMP_FILE_PATH}")


def print_help():
    print("""usage: wt <cmd> [args...]
    Work timer used to time cycles of work. Useful for pomodoro or similar
    work/break cycles. Total time is the sum of currently running/paused
    cycle and previously completed cycles. Cycles can also be thought
    of as laps in a traditional timer.
        
    Commands:
        start               Starts a new timer or continues paused timer.
        pause               Pauses currently running timer.
        stop                Stops running or paused timer, sets total time,
                            and resets current time.
        check               Prints current and total time along with status.
                            Running wt without any command does the same.
        set <type> <time>   Manually set total/current time using 1-4 digit
                            HHMM, HMM, MM, or M. Ex. wt set total 15 = 15min.
            types:
                total
                current
        reset               Stops and sets current and total timers to zero.
        new                 Creates a new timer. Alias for "reset".
        remove              Deletes the timer and related file.
        help                Prints this help message.
        debug               Prints debug info.
""")


def hour_minute_str_from_minutes(minutes: int) -> str:
    h = minutes//60
    m = minutes % 60

    return f"{h:01d}h {m:02d}m"


def delta_minutes(start: dt, now: dt) -> int:
    delta = now - start

    seconds = delta.total_seconds()
    minutes = int((seconds % 3600) // 60)

    return minutes


def total_with_paused_str(timer: Timer) -> str:
    total = timer.paused_minutes + timer.completed_minutes

    return hour_minute_str_from_minutes(total)


def hour_minute_to_minutes(hours: int, minutes: int) -> int:
    return hours * 60 + minutes


def save(timer: Timer):
    # CSV Format = status,startTime,pausedMinutes,totalMinutes
    with open(TMP_FILE_PATH, 'w') as file:
        file.write(f"{timer.status},{timer.start_datetime_str},{
                   timer.paused_minutes},{timer.completed_minutes}")


def load(debug: bool = False) -> Timer:
    # CSV Format = status,startTime,pausedMinutes,totalMinutes
    line = ""
    try:
        with open(TMP_FILE_PATH, 'r') as file:
            line = file.readline().strip('\n')
    except:
        print("No file.")

    if debug:
        print(f'CSV = "{line}"')

    csv = line.split(",")

    return Timer(Status(csv[0]), csv[1], int(csv[2]), int(csv[3]))


if __name__ == "__main__":
    main()
