from pathlib import Path
from app.parsers.html_parser import HTMLParser
HTML = """
<html>
<head>
<style>
body{color:red;}
</style>
<script>
alert("hello")
</script>
</head>
<body>
<h1>Apple Inc.</h1>
<p>Total Revenue</p>
<table>
<tr>
<td>2024</td>
<td>391000</td>
</tr>
</table>
</body>
</html>