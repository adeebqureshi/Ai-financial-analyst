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
"""


def test_parse_text():

    parser = HTMLParser()

    result = parser.parse_text(HTML)

    assert "Apple Inc." in result

    assert "Revenue" in result

    assert "alert" not in result

    assert "color:red" not in result


def test_parse_file(tmp_path: Path):

    file = tmp_path / "sample.html"

    file.write_text(HTML)

    parser = HTMLParser()

    result = parser.parse_file(file)

    assert "Apple Inc." in result
    