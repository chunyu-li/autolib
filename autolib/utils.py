import os


def desktop_notify(title: str, info: str):
    os.system(f'osascript -e \'display notification "{info}" with title "{title}"\'')
