from flask import request
import re


def seen(element, manga=False):
    read = 0

    if manga:
        available_matches = re.search(r"\[<a href=\".*\">(\d+)</a>\]|\[(\d+)\]", element)
        read_matches = re.search(r"</a> (\d+) <a href=\"/anilist", element)

        if read_matches:
            read = int(read_matches.group(1))

        if available_matches:
            return int(available_matches.group(1) or re.sub(r"[\[\]]", '', available_matches.group(0))) - read
        else:
            return 0

    available_matches = re.findall(r"\d+\]|\[\d+", element)
    seen_matches = re.search(
        r"\s(\d+)*?(<span style=\"opacity: 50%\">/(\d+)</span>)*\s", element
    )

    if seen_matches:
        read = int(seen_matches.group(1))

    if len(available_matches) > 1:
        return int(available_matches[1].strip("[]")) - read
    elif len(available_matches) == 1:
        return int(available_matches[0].strip("[]")) - read
    else:
        return 0


def page(main_content, footer):
    message = '<blockquote>Slow loads? If your media hasn\'t been cached in a while, the first load will take a couple seconds longer than the rest. Subsequent requests on cached media should be faster. <a href="/?hide_message">Hide <i>forever</i></a></blockquote>'

    if request.cookies.get("hide_message") == "1":
        message = ""

    return f"""
<!DOCTYPE html>
<html>
    <head>
        <title>期限</title>

        <link rel="stylesheet" type="text/css" href="https://latex.now.sh/style.css">
        <link rel="stylesheet" type="text/css" href="https://skybox.sh/css/palettes/base16-light.css">
        <link rel="stylesheet" type="text/css" href="https://skybox.sh/css/risotto.css">
        <!-- <link rel="stylesheet" type="text/css" href="https://skybox.sh/css/custom.css"> -->
        <link rel="shortcut icon" type="image/x-icon" href="https://ps.fuwn.me/-tePaWtKW2y/angry-miku-nakano.ico">
    </head>

    <body>
        <style>text-align: center;</style>

        <h1><a href="/">期限</a></h1>

        {main_content}

        <p></p>

        <hr>

        <p>{footer}</p>

        {message}
    </body>
</html>
"""
