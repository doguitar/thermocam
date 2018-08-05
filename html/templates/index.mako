<%inherit file="/base.mako"/>
<%block name="js_block"><script src="${base}js/jsmpeg.min.js"></script></%block>

<canvas id="video-canvas" style="width: 95vmin; height: 95vmin;"></canvas>

<script type="text/javascript">
    var canvas = document.getElementById('video-canvas');
    var url = 'ws://${socketAddress}/';
    var player = new JSMpeg.Player(url, {canvas: canvas});
</script>