import json
import tempfile
import subprocess
import os


class MediaEditor:
    def __init__(self):
        self.options = {}
        self.configured = False

    def set_editor_options(self, filter, input_media_file, output_media_file, custom_flags=""):
        self.options = {
            "filter": filter,
            "input_media_file": input_media_file,
            "output_media_file": output_media_file,
            "custom_flags": custom_flags
        }
        self.configured = True

    def load_editor_file(self, filename):
        with open(filename, "r") as f:
            self.options = json.loads(f.read())
        self.configured = True

    def __generate_temp_file(self, content, join_sequence=";\n"):
        filename = tempfile.NamedTemporaryFile().name
        with open(filename, "w+") as f:
            f.write(join_sequence.join(content))

        return filename

    def __generate_command(self, filter_filename, segment_file_suffix=""):
        command = [
            "ffmpeg",
            "-i", self.options["input_media_file"],
            "-vsync", "1", "-async", "1",
            "-safe", "0",
            "-filter_complex_script", filter_filename,
            "-y"
        ]

        if self.options["custom_flags"]:
            command.append(self.options["custom_flags"])

        if not self.options["filter"]["audio_only"]:
            command.extend([
                "-map", f'[{self.options["filter"]["output"]["video_pad"]}]'
            ])

        command.extend([
            "-map", f'[{self.options["filter"]["output"]["audio_pad"]}]',
            self.options["output_media_file"].format(segment=segment_file_suffix)
        ])

        return command

    def edit(self, segment=-1):
        if not self.options["filter"]["segmented"] or segment >= 0:
            if not self.options["filter"]["segmented"]:
                filter_filename = self.__generate_temp_file(self.options["filter"]["filter_lines"])
                command = self.__generate_command(filter_filename)
            else:
                filter_filename = self.__generate_temp_file(self.options["filter"]["filter_lines"][segment])
                command = self.__generate_command(filter_filename, segment_file_suffix=str(segment))

            console_output = subprocess.run(
                command,
                capture_output=True,
                text=True
            ).stderr

            os.remove(filter_filename)

            return console_output.split("\n")

        else:
            console_output = []
            for i, segment in enumerate(self.options["filter"]["filter_lines"]):
                filter_filename = self.__generate_temp_file(self.options["filter"]["filter_lines"][i])
                command = self.__generate_command(filter_filename, segment_file_suffix=str(i))

                console_output_part = subprocess.run(
                    command,
                    capture_output=True,
                    text=True
                ).stderr

                os.remove(filter_filename)

                console_output.append(console_output_part.split("\n"))

            return console_output

    def combine(self, segment_filename, output_file, re_encode=False):
        files = []
        for i in range(len(self.options["filter"]["filter_lines"])):
            filename = os.path.abspath(segment_filename.format(segment=i))
            files.append(f"file {filename}")

        file_list_filename = self.__generate_temp_file(files, join_sequence="\n")

        command = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", file_list_filename
        ]

        if not re_encode:
            command.extend(["-c", "copy"])

        command.append(output_file)

        console_output = subprocess.run(
            command,
            capture_output=True,
            text=True
        ).stderr

        os.remove(file_list_filename)

        return console_output.split("\n")
