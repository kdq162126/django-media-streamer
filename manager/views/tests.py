from django.shortcuts import render
from utils.networks import get_host_ip

HOST_IP = get_host_ip()

def simple_stream(request):
    context = {
        'media_url': f'http://app.localhost:8000/streamer/53c426c98cdf4ad8ac769177578418ce.mp4'
    }
    return render(request, 'tests/simple_player.html', context)

def dash_stream(request):
    context = {
        'media_url': f'http://app.localhost:8000/streamer/b520bc595ce04d708123abcca6fdbf5e.mpd'
    }
    return render(request, 'tests/dash_player.html', context)

def hls_stream(request):
    context = {
        'media_url': f'http://app.localhost:8000/streamer/e02cd5dbe2dc4885b7a89b5ce6d699fb.m3u8'
    }
    return render(request, 'tests/hls_player.html', context)
