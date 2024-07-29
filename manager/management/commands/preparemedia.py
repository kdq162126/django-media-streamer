from django.core.management.base import BaseCommand, CommandError
import os
import uuid
import subprocess  # Updated to use subprocess instead of commands

# Define FFMPEG options
FFMPEG_FPS_OPTS = '-r 30 -g 30'
FFMPEG_PROFILE_OPTS = '-profile:v high -level:v 4.1'
FFMPEG_CODEC_OPTS = '-codec:v libx264 -codec:a aac'

class Command(BaseCommand):
    stream_type = ''
    input_file = ''
    output_dir = ''

    def add_arguments(self, parser):
        parser.add_argument('--stream-type', type=str, required=True)
        parser.add_argument('--input-file', type=str, required=True)
        parser.add_argument('--output-dir', type=str, required=True)

    def handle(self, *args, **options):
        self._parse_params(options)
        stream_type_handlers = {
            'simple': self.handle_simple,
            'dash': self.handle_dash,
            'hls': self.handle_hls
        }
        if self.stream_type not in stream_type_handlers:
            raise CommandError('Streaming type must be simple, dash, or hls.')

        hash_name = str(uuid.uuid4().hex)
        cache_dir = self._create_cache_dir(hash_name)
        stream_type_handlers[self.stream_type](cache_dir, hash_name)

    # Stream handlers
    def handle_simple(self, cache_dir, hash_name):
        output_dir = os.path.join(cache_dir, f'{hash_name}.mp4')
        self._ffmpeg_transcode(output_dir)

    def handle_dash(self, cache_dir, hash_name):
        temp_dir = self._create_temp_dir(hash_name)
        temp_path = os.path.join(temp_dir, f'{hash_name}.mp4')
        self._ffmpeg_transcode(temp_path)
        self._mp4box_dash_segmentation(cache_dir, temp_path, hash_name)

    def handle_hls(self, cache_dir, hash_name):
        m3u8_path = os.path.join(cache_dir, f'{hash_name}.m3u8')
        ts_path = os.path.join(cache_dir, f'{hash_name}_%06d.ts')
        self._ffmpeg_transcode_and_hls_segmentation(m3u8_path, ts_path)

    # Common methods
    def _parse_params(self, opts):
        params = (opts['stream_type'], opts['input_file'], opts['output_dir'])
        if not all(params):
            raise CommandError('Invalid parameters.')

        self.stream_type, self.input_file, self.output_dir = params

    @staticmethod
    def _create_dir(path):
        if not os.path.exists(path):
            os.makedirs(path)

    def _create_cache_dir(self, hash_name):
        media_cache_dir = os.path.join(self.output_dir, hash_name)
        self._create_dir(media_cache_dir)
        return media_cache_dir

    def _create_temp_dir(self, hash_name):
        media_temp_dir = os.path.join(self.output_dir, f'../temp/{hash_name}')
        self._create_dir(media_temp_dir)
        return media_temp_dir

    def _ffmpeg_transcode(self, output_path):
        ffmpeg_cmd = f'ffmpeg -i {self.input_file} {FFMPEG_FPS_OPTS} {FFMPEG_PROFILE_OPTS} {FFMPEG_CODEC_OPTS} {output_path}'
        self.stdout.write(ffmpeg_cmd)
        result = subprocess.run(ffmpeg_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise CommandError(f'Error during ffmpeg transcoding: {result.stderr}')

    def _mp4box_dash_segmentation(self, cache_dir, temp_path, hash_name):
        output_path = os.path.join(cache_dir, hash_name)
        mp4box_cmd = f'MP4Box -dash 4000 -rap -frag-rap -profile live -url-template -segment-name {hash_name}_ -out {output_path[2:]} {temp_path}'
        self.stdout.write(mp4box_cmd)
        result = subprocess.run(mp4box_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise CommandError(f'Error during MP4Box DASH segmentation: {result.stderr}')

    def _ffmpeg_transcode_and_hls_segmentation(self, m3u8_path, ts_path):
        ffmpeg_cmd = f'ffmpeg -i {self.input_file} -map 0 {FFMPEG_PROFILE_OPTS} {FFMPEG_CODEC_OPTS} -f ssegment -segment_list {m3u8_path} -segment_list_flags +live -segment_time 4 {ts_path}'
        self.stdout.write(ffmpeg_cmd)
        result = subprocess.run(ffmpeg_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise CommandError(f'Error during ffmpeg transcoding and HLS segmentation: {result.stderr}')
