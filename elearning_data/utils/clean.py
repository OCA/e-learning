# © 2024 Open Net Sarl
# Author: Adam Bonnet <adambonnet0@gmail.com>

# This script allow to clean the content of the eLearning Data module...
# XML doesn't like special characters so this script will simply correct it...
# You just need to input the html_content when you run the script...


def escape_html(content):
    escape_dict = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }

    return "".join(escape_dict.get(c, c) for c in content)


html_content = input("Enter the HTML content: ")

escaped_content = escape_html(html_content)

print("-" * 50)  # pylint: disable=print-used

print(escaped_content)  # pylint: disable=print-used
