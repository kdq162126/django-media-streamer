var session = null;

// Initialize Cast API
if (!chrome.cast || !chrome.cast.isAvailable) {
  setTimeout(initializeCastApi, 1000);
}

function initializeCastApi() {
  var appID = '90CA4506';   // chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID;
  var sessionRequest = new chrome.cast.SessionRequest(appID);
  var apiConfig = new chrome.cast.ApiConfig(sessionRequest, sessionListener, receiverListener);

  chrome.cast.initialize(apiConfig, onInitSuccess, onError);
}

function launchApp() {
  chrome.cast.requestSession(onRequestSessionSuccess, onLaunchError);
}

function doChromecast() {
  var videoElement = document.getElementById('sample-video-src');
  var videoSrc = videoElement.querySelector('source').getAttribute('src')

  if (videoSrc) {
    loadAndPlayMedia(videoSrc);
  } else {
    console.error('Video source URL is missing.');
  }
}

function getContentType(url) {
  var contentType = 'video/mp4';
  var parts = url.split('.');
  if (!(parts.length === 1 || (parts[0] === '' && parts.length === 2))) {
    var extension = parts.pop().toLowerCase();
    if (extension === 'mpd') {
      contentType = 'application/dash+xml';
    } else if (extension === 'm3u8') {
      contentType = 'application/x-mpegurl';
    }
  }
  return contentType;
}

function loadAndPlayMedia(mediaURL) {
  if (session === null) {
    console.error('No active session found. Please launch the app first.');
    return;
  }

  var mediaInfo = new chrome.cast.media.MediaInfo(mediaURL);
  mediaInfo.metadata = new chrome.cast.media.GenericMediaMetadata();
  mediaInfo.metadata.metadataType = chrome.cast.media.MetadataType.GENERIC;
  mediaInfo.metadata.title = 'Hello World';
  mediaInfo.metadata.subtitle = 'Sub Title Here';
  mediaInfo.metadata.images = [new chrome.cast.Image('https://goo.gl/ZRMjjO')];
  mediaInfo.contentType = getContentType(mediaURL);

  var request = new chrome.cast.media.LoadRequest(mediaInfo);
  request.autoplay = true;
  request.currentTime = 0;

  session.loadMedia(request).then(onMediaSuccess).catch(onMediaError);
}

// Callbacks
function onInitSuccess() {
  console.log('Cast API initialized successfully.');
}

function onError(e) {
  console.error('Error:', e);
}

function sessionListener(e) {
  session = e;
  console.log('Session started:', session);
}

function receiverListener(e) {
  console.log('Receiver listener event:', e);
}

function onMediaSuccess() {
  console.log('Media loaded successfully.');
}

function onMediaError(e) {
  console.error('Media loading error:', e);
}

function onRequestSessionSuccess(e) {
  session = e;
  console.log('Session established:', session);
}

function onLaunchError(e) {
  console.error('Error launching app:', e);
}
