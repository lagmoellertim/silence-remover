import subprocess

from silence_remover.silence_detector.interval_parser import IntervalParser


class SilenceDetector:
    def __init__(self, filename):
        self.filename = filename
        self.console_output_array = None
        self.detected_intervals = None

    def detect(self, silence_level_db=-35, silence_time_threshold=0.5):
        console_output = subprocess.run(
            ["ffmpeg", "-i", self.filename, "-af",
             f"silencedetect=noise={silence_level_db}dB:d={silence_time_threshold}",
             "-f", "null", "-"],
            capture_output=True,
            text=True
        ).stderr

        self.console_output_array = console_output.split("\n")

        return self.console_output_array

    def parse(self, short_interval_threshold=0.3, stretch_time=0.25, split_intervals=-1):
        parser = IntervalParser(self.console_output_array)
        parser_result = (
            parser
            .parse_console_output()
            .insert_additional_intervals()
            .mark_short_intervals(short_interval_threshold=short_interval_threshold)
            .combine_and_remove_intervals()
            .stretch_audible_intervals(stretch_time=stretch_time)
        )
        if split_intervals > 0:
            self.detected_intervals = parser_result.split_intervals(split_intervals)
        else:
            self.detected_intervals = parser_result.get_intervals()

        return self.detected_intervals
