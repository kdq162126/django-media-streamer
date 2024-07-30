from django.core.management.base import BaseCommand, CommandError
import os
import subprocess
import glob
import uuid

# Define FFMPEG options
FFMPEG_FPS_OPTS = '-r 30 -g 30'
FFMPEG_PROFILE_OPTS = '-profile:v high -level:v 4.1'
FFMPEG_CODEC_OPTS = '-codec:v libx264 -codec:a aac'
SEGMENT_DURATION = 10  # Duration of each segment in seconds

class Command(BaseCommand):
    stream_type = ''
    input_dir = ''
    output_dir = ''

    def add_arguments(self, parser):
        parser.add_argument('--stream-type', type=str, required=True)
        parser.add_argument('--input-dir', type=str, required=True)
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

    def handle_simple(self, cache_dir, hash_name):
        output_path = os.path.join(cache_dir, f'{hash_name}.mp4')
        self._ffmpeg_transcode(self.input_file, output_path)

    def handle_dash(self, cache_dir, hash_name):
        temp_dir = self._create_temp_dir(hash_name)
        temp_path = os.path.join(temp_dir, f'{hash_name}.mp4')
        self._ffmpeg_transcode(self.input_file, temp_path)
        self._mp4box_dash_segmentation(cache_dir, temp_path, hash_name)

    def handle_hls(self, cache_dir, hash_name):
        self._create_dir(cache_dir)

        ts_files = []
        segment_durations = {}
        for video_file in sorted(glob.glob(os.path.join(self.input_dir, '*.mp4'))):
            video_file_name = os.path.splitext(os.path.basename(video_file))[0]
            ts_path = os.path.join(cache_dir, f'{video_file_name}_%06d.ts')
            m3u8_path = os.path.join(cache_dir, f'{video_file_name}.m3u8')

            self._ffmpeg_transcode_and_hls_segmentation(video_file, m3u8_path, ts_path)

            ts_files.extend(sorted(glob.glob(os.path.join(cache_dir, f'{video_file_name}_*.ts'))))
            segment_durations.update(self._get_segment_durations(m3u8_path))

        self._create_master_playlist(cache_dir, ts_files, segment_durations, hash_name)

    def _parse_params(self, opts):
        params = (opts['stream_type'], opts['input_dir'], opts['output_dir'])
        if not all(params):
            raise CommandError('Invalid parameters.')

        self.stream_type, self.input_dir, self.output_dir = params

    @staticmethod
    def _create_dir(path):
        if not os.path.exists(path):
            os.makedirs(path)

    def _create_cache_dir(self, hash_name):
        media_cache_dir = os.path.join(self.output_dir, hash_name)
        self._create_dir(media_cache_dir)
        return media_cache_dir

    def _create_temp_dir(self, hash_name):
        media_temp_dir = os.path.join(self.output_dir, f'temp/{hash_name}')
        self._create_dir(media_temp_dir)
        return media_temp_dir

    def _ffmpeg_transcode(self, input_file, output_path):
        ffmpeg_cmd = f'ffmpeg -i {input_file} {FFMPEG_FPS_OPTS} {FFMPEG_PROFILE_OPTS} {FFMPEG_CODEC_OPTS} {output_path}'
        self.stdout.write(ffmpeg_cmd)
        result = subprocess.run(ffmpeg_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise CommandError(f'Error during ffmpeg transcoding: {result.stderr}')

    def _mp4box_dash_segmentation(self, cache_dir, temp_path, hash_name):
        output_path = os.path.join(cache_dir, f'{hash_name}.mpd')
        mp4box_cmd = f'MP4Box -dash 4000 -rap -frag-rap -profile live -url-template -segment-name {hash_name}_ -out {output_path} {temp_path}'
        self.stdout.write(mp4box_cmd)
        result = subprocess.run(mp4box_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise CommandError(f'Error during MP4Box DASH segmentation: {result.stderr}')

    def _ffmpeg_transcode_and_hls_segmentation(self, input_file, m3u8_path, ts_path):
        ffmpeg_cmd = (
            f'ffmpeg -i {input_file} {FFMPEG_FPS_OPTS} {FFMPEG_PROFILE_OPTS} {FFMPEG_CODEC_OPTS} '
            f'-f hls -hls_playlist_type vod -hls_segment_filename {ts_path} '
            f'-hls_list_size 0 -hls_time {SEGMENT_DURATION} -hls_segment_type mpegts -hls_flags split_by_time '
            f'{m3u8_path}'
        )
        self.stdout.write(ffmpeg_cmd)
        result = subprocess.run(ffmpeg_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise CommandError(f'Error during ffmpeg HLS segmentation: {result.stderr}')

    def _get_segment_durations(self, m3u8_path):
        durations = {}
        with open(m3u8_path, 'r') as file:
            lines = file.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('#EXTINF:'):
                duration = float(line.split(':')[1].split(',')[0])
                if i + 1 < len(lines):
                    segment_file = lines[i + 1].strip()
                    durations[segment_file] = duration
                i += 2
            else:
                i += 1

        return durations

    def _create_master_playlist(self, cache_dir, ts_files, segment_durations, hash_name):
        master_playlist_path = os.path.join(cache_dir, f'{hash_name}.m3u8')
        with open(master_playlist_path, 'w') as f:
            f.write('#EXTM3U\n')
            f.write('#EXT-X-VERSION:3\n')
            f.write('#EXT-X-ALLOW-CACHE:YES\n')

            # Calculate target duration based on the longest segment
            target_duration = max(segment_durations.values(), default=SEGMENT_DURATION)
            f.write(f'#EXT-X-TARGETDURATION:{int(round(target_duration))}\n')

            # Write segments in the order they were generated
            for ts_file in sorted(ts_files):
                base_name = os.path.basename(ts_file)
                duration = segment_durations.get(base_name, SEGMENT_DURATION)
                f.write(f'#EXTINF:{duration},\n')
                f.write(f'{base_name}\n')

            f.write('#EXT-X-ENDLIST\n')
