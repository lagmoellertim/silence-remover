import json

class FilterGenerator:
    def __init__(self, intervals, segmented=False):
        self.intervals = intervals
        self.segmented = segmented

        self.final_filter_lines = []
        self.filter_lines = []
        self.media_components = []
        self.current_component_index = 0

    def generate(self, **kwargs):
        self.options = {
            "audible": {
                "speed": kwargs.get("audible_speed", 1.0),
                "volume": kwargs.get("audible_volume", 1.0)
            },
            "silent": {
                "speed": kwargs.get("silent_speed", 6.0),
                "volume": kwargs.get("silent_volume", 0.5)
            },
            "output": {
                "video_pad": kwargs.get("video_output_pad", "vout"),
                "audio_pad": kwargs.get("audio_output_pad", "aout")
            },
            "audio_only": kwargs.get("audio_only", False)
        }

        if self.segmented:
            for segmented_intervals in self.intervals:
                for interval in segmented_intervals:
                    self.__add_media_component(interval["start"], interval["end"], interval["silent"])

                self.__concat_media_components()
                self.final_filter_lines.append(self.filter_lines)
                self.filter_lines = []
                self.media_components = []
                self.current_component_index = 0
        else:
            for interval in self.intervals:
                self.__add_media_component(interval["start"], interval["end"], interval["silent"])

            self.__concat_media_components()
            self.final_filter_lines = self.filter_lines

    def __add_media_component(self, start_time, end_time, silent):
        speed = self.options["silent"]["speed"] if silent else self.options["audible"]["speed"]

        if speed > 0:
            rounded_start_time = round(start_time, 4)
            rounded_end_time = round(end_time, 4)

            if not self.options["audio_only"]:
                self.__add_video_component(rounded_start_time, rounded_end_time, speed)

            self.__add_audio_component(rounded_start_time, rounded_end_time, speed, silent)

            self.current_component_index += 1

    def __add_video_component(self, start_time, end_time, speed):
        self.filter_lines.append(
            f"[0:v]trim=start={start_time}:end={end_time},setpts=PTS-STARTPTS[v{self.current_component_index}]"
        )

        video_filter = f"setpts={round(1 / speed, 4)}*PTS" if speed != 1.0 else ""

        if video_filter == "":
            self.media_components.append(
                f"[v{self.current_component_index}]"
            )

        else:
            self.filter_lines.append(
                f"[v{self.current_component_index}]{video_filter}[vf{self.current_component_index}]"
            )

            self.media_components.append(
                f"[vf{self.current_component_index}]"
            )


    def __add_audio_component(self, start_time, end_time, speed, silent):
        volume = self.options["silent"]["volume"] if silent else self.options["audible"]["volume"]

        self.filter_lines.append(
            f"[0:a]atrim=start={start_time}:end={end_time},asetpts=PTS-STARTPTS[a{self.current_component_index}]"
        )

        audio_filter_list = [
            f"atempo={round(speed, 4)}" if speed != 1.0 else "",
            f"volume={volume}" if volume != 1.0 else ""
        ]

        audio_filter = ','.join(x for x in audio_filter_list if x)

        if audio_filter == "":
            self.media_components.append(
                f"[a{self.current_component_index}]"
            )

        else:
            self.filter_lines.append(
                f"[a{self.current_component_index}]{audio_filter}[af{self.current_component_index}]"
            )

            self.media_components.append(
                f"[af{self.current_component_index}]"
            )

    def __concat_media_components(self):
        media_components_string = "".join(self.media_components)

        if self.options["audio_only"]:
            self.filter_lines.append(
                f"{media_components_string}"
                f"concat=n={self.current_component_index}:v=0:a=1"
                f"[{self.options['output']['audio_pad']}]"
            )

        else:
            self.filter_lines.append(
                f"{media_components_string}"
                f"concat=n={self.current_component_index}:v=1:a=1"
                f"[{self.options['output']['video_pad']}]"
                f"[{self.options['output']['audio_pad']}]"
            )

    def get_filter(self):
        return {
            "filter_lines":self.final_filter_lines,
            "audio_only":self.options["audio_only"],
            "output":self.options["output"],
            "segmented":self.segmented
        }

    def generate_editor_file(self, output_config_file, input_media_file, output_media_file, custom_flags=""):
        output = {
            "filter": self.get_filter(),
            "input_media_file": input_media_file,
            "output_media_file": output_media_file,
            "custom_flags": custom_flags
        }

        with open(output_config_file, "w+") as f:
            f.write(json.dumps(output))