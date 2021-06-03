DEFAULT_HTTP_PORT = 80
DEFAULT_HTTPS_PORT = 443
CR_LF = '\r\n'
HOST = "0.0.0.0"
PORT = 6969
BLOCKED_URLS = [
    "se.math.spbu.ru",
    "tiktok.com",
    "hwproj.me"
]
CONNECTION_ESTABLISHED = b'HTTP/1.1 200 Connection established\r\n\r\n'
filtered_message = """
<html>
<head>
</head>
<body>
    <h1 style="font-family:monospace;color:red">A warning from Gandalf...</h1>
    <h2 style="font-family:monospace;">Oh! This website seems to be using http.<br>
    With some magic your traffic can be easily intercepted.<br>
      Be careful, it could be a dark wizard next time!</h2>
</body>
</html>
"""
