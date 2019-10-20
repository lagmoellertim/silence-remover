import re


class IntervalParser:
    def __init__(self, console_output_array):
        self.console_output_array = console_output_array

        self.intervals = []
        self.media_duration = 0.0

        self.short_interval_threshold = None

    def parse_console_output(self):
        prev_time = 0
        current_interval = {}

        for i, line in enumerate(self.console_output_array):
            if line.startswith("[silencedetect"):
                capture = re.search("\[silencedetect @ [0-9xa-f]+] silence_([a-z]+): (-?[0-9]+.?[0-9]*[e-]*[0-9]*)",
                                    line)
                event = capture[1]
                time = float(capture[2])

                current_interval[event] = time
                current_interval["silent"] = True
                if event == "end":
                    current_interval["duration"] = time - prev_time
                    self.intervals.append(current_interval)
                    current_interval = {}
                prev_time = time

            elif line.startswith("  Duration"):
                capture = re.search("  Duration: ([0-9:]+.?[0-9]*)", line)
                hour, minute, second_millisecond = capture[1].split(":")
                second, millisecond = second_millisecond.split(".")
                self.media_duration = float(str(int(second) + 60 * (int(minute) + 60 * int(hour))) + "." + millisecond)

        return self

    def __add_start_interval(self):
        if self.intervals[0]["start"] != 0:
            current_interval = {
                "start": 0,
                "end": self.intervals[0]["start"],
                "duration": self.intervals[0]["start"],
                "silent": not self.intervals[0]["silent"]
            }
            self.intervals.insert(0, current_interval)

    def __add_end_interval(self):
        if self.intervals[-1]["end"] != self.media_duration:
            current_interval = {
                "start": self.intervals[-1]["end"],
                "end": self.media_duration,
                "duration": self.media_duration - self.intervals[-1]["end"],
                "silent": not self.intervals[-1]["silent"]
            }
            self.intervals.append(current_interval)

    def insert_additional_intervals(self):
        self.__add_start_interval()
        self.__add_end_interval()

        intervals = self.intervals[::]

        insert_counter = 1
        for i, interval in enumerate(self.intervals):
            if i <= len(self.intervals) - 2:
                start = interval["end"]
                end = self.intervals[i + 1]["start"]
                duration = end - start
                if duration > 0:
                    current_interval = {
                        "start": start,
                        "end": end,
                        "duration": end - start,
                        "silent": False
                    }
                    intervals.insert(i + insert_counter, current_interval)
                    insert_counter += 1

        self.intervals = intervals

        return self

    def mark_short_intervals(self, short_interval_threshold=0.3):
        self.short_interval_threshold = short_interval_threshold

        for item in self.intervals:
            if item["duration"] <= short_interval_threshold:
                item["remove"] = True

        return self

    def combine_and_remove_intervals(self):
        intervals = []
        current_interval = {"start": 0, "end": 0, "silent": None, "duration": 0}
        for interval in self.intervals:
            if "remove" in interval or current_interval["silent"] == interval["silent"]:
                current_interval["end"] = interval["end"]
                current_interval["duration"] += interval["duration"]
            else:
                if current_interval["silent"] is None:
                    current_interval["silent"] = interval["silent"]
                    current_interval["end"] = interval["end"]
                    current_interval["duration"] += interval["duration"]
                else:
                    intervals.append(current_interval)
                    current_interval = {"start": interval["start"], "end": interval["end"],
                                        "silent": interval["silent"],
                                        "duration": interval["duration"]}

        if current_interval is not None:
            if current_interval["silent"] is None:
                current_interval["silent"] = False
            intervals.append(current_interval)

        self.intervals = intervals

        return self

    def stretch_audible_intervals(self, stretch_time=0.25):
        if self.short_interval_threshold is not None and stretch_time > self.short_interval_threshold:
            raise Exception(
                "Since the ShortIntervalThreshold is larger than the StretchTime, negative Intervals are possible.\n"
                "Please choose other values.")

        stretch_time_part = stretch_time / 2
        for i, item in enumerate(self.intervals):
            new_start = item["start"] + stretch_time_part if item["silent"] else item["start"] - stretch_time_part
            new_end = item["end"] - stretch_time_part if item["silent"] else item["end"] + stretch_time_part

            if i == 0:
                new_start = item["start"]
            elif i == len(self.intervals) - 1:
                new_end = item["end"]

            item["start"] = new_start
            item["end"] = new_end
            item["duration"] = new_end - new_start

        return self

    def split_intervals(self, max_interval_time):
        interval_segments = []
        current_interval_segment = []
        current_split_time = max_interval_time

        for interval in self.intervals:
            start, end = interval["start"], interval["end"]
            
            if end < current_split_time:
                current_interval_segment.append(interval)
            elif start == current_split_time:
                current_interval_segment.append(interval)
                interval_segments.append(current_interval_segment)
                current_interval_segment = []
                current_split_time += max_interval_time
            elif start < current_split_time:
                interval["end"] = current_split_time
                interval["duration"] = current_split_time - start
                current_interval_segment.append(interval)
                interval_segments.append(current_interval_segment)
                interval = interval.copy()
                interval["start"] = current_split_time
                interval["end"] = end
                interval["duration"] = end - current_split_time
                current_interval_segment = [interval]
                current_split_time += max_interval_time
            elif start == current_split_time:
                interval_segments.append(current_interval_segment)
                current_interval_segment = [interval]
                current_split_time += max_interval_time

        interval_segments.append(current_interval_segment)

        return interval_segments


    def get_intervals(self):
        return self.intervals
