from silence_remover.silence_detector import SilenceDetector
from silence_remover.filter_generator import FilterGenerator
from silence_remover.media_editor import MediaEditor


class SilenceRemover:
    def __init__(self, input_filename, output_filename, segmented=False, segment_interval_time=-1):
        self.input_filename = input_filename
        self.output_filename = output_filename

        self.segmented = segmented
        self.segment_interval_time = segment_interval_time

        self.parsed_result = None

        self.detector = SilenceDetector(self.input_filename)
        self.generator = None
        self.editor = MediaEditor()

    def detect_silence(self, **kwargs):
        self.detector.detect(**kwargs)
        self.parsed_result = self.detector.parse(split_intervals=self.segment_interval_time, **kwargs)

        return self.parsed_result

    def generate_silence_filter(self, overwrite_prev_config=False, **kwargs):
        self.generator = FilterGenerator(self.parsed_result, segmented=self.segmented)
        self.generator.generate(**kwargs)
        print(self.generator.get_filter())
        if not self.editor.configured or overwrite_prev_config:
            self.editor.set_editor_options(self.generator.get_filter(), self.input_filename, self.output_filename)

    def export_silence_config(self, config_filename, **kwargs):
        self.generator.generate_editor_file(config_filename, self.input_filename, self.output_filename, **kwargs)

    def import_silence_config(self, config_filename):
        self.editor.load_editor_file(config_filename)

    def remove_silence(self, segment=-1):
        self.editor.edit(segment=segment)

    def combine_segments(self, output_file, re_encode=False):
        self.editor.combine(self.output_filename, output_file, re_encode=re_encode)
