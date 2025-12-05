import subprocess
import sys
import os
from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from pym3u8downloader import M3U8Downloader
from rich import print

style_green = Style.from_dict({
    '': 'fg:ansigreen'
})

def get_separator(word, color = ''):
    columns, lines = os.get_terminal_size()
    len_word = len(word)
    empty_space = columns - len_word
    left_part_len = empty_space // 2
    right_part_len = columns - (left_part_len + len_word)
    
    char = '-'
    left_part = char * left_part_len
    right_part = char * right_part_len
    
    
    separator = left_part + word + right_part
    if color:
        separator = f'[{color}]{separator}[/]'
    
    return separator

def get_path():
    # Создание путей для записи последнего просмотра
    cache = Path.home() / ".cache/Anilibria"
    global latest, latestLink
    latest = cache / "latest.txt"
    latestLink = cache / "latestLink.txt"
    
    if not cache.exists():
        cache.mkdir()
    if not latest.exists():
        latest.touch()
    if not latestLink.exists():
        latestLink.touch()
    
    return latest, latestLink

def input(question, style = None):
    try:
        answer = prompt(question, style = style)
        return answer
    except (KeyboardInterrupt, EOFError):
        print("[green]До свидания...[/]")
        sys.exit()

def get_answer(correction, condition):
    answer = input("> ", style = style_green)
    while condition(answer):
        answer = input(correction)
    return answer

def print_option_list(option_list, title = ""):
    count = 1
    if title:
        separator = get_separator(title, color = 'cyan')
        print(separator)
    for option in option_list:
        print(f"[dim white]{count}[/] {option}")
        count += 1
    

def play(link, name, player):
    if player == "mpv":
        subprocess.run(["mpv", "--save-position-on-quit", f"--title={name}", link])
    elif player == "mx":
        command = (
            "am start " +
                "-n com.mxtech.videoplayer.pro/.ActivityScreen " +
                "-a android.intent.action.VIEW " +
                f'-d "{link}" ' +
                f'-e "title"  "{name}" ' +
            "exit"
        )
        subprocess.run(command, shell = True)
    else:
        subprocess.run([player, link])


def download(link, title, name, output):
    forbiddenChars = ["<", ">", ":", '"', "/", "|", "?", "*"]
    if title == "MOVIE":
        download_path = Path.home() / output
        if not download_path.exists():
            download_path.mkdir(parents=True)
        for char in name:
            if char in forbiddenChars:
                name = name.replace(char, "_")
    else:
        for char in title:
            if char in forbiddenChars:
                title = title.replace(char, "_")
        download_path = Path.home() / output / title
        if not download_path.exists():
            download_path.mkdir(parents=True)
    fileName = download_path / name
    downloader = M3U8Downloader(
        input_file_path=link[: link.find(".m3u8") + 5], output_file_path=str(fileName)
    )
    downloader.download_playlist()


def fast(args):
    # В списке episode [0] - ссылка, [1] - название тайтла, [2] - название серии
    episode = latestLink.read_text().splitlines()
    if args.download:
        download(episode[0], episode[1], f"{episode[2]}.mp4", args.output)
    else:
        if episode[1] == "MOVIE":
            play(episode[0], episode[2], args.player)
        else:
            play(episode[0], f"{episode[1]} - {episode[2]}", args.player)

def torrent(title, args):
    torrents = title["torrents"]
    
    option_list = []
    for torrent in torrents:
        option_list.append(torrent['label'])
    print_option_list(option_list, "Доступные торренты:")
    
    answer = get_answer(
        "Слишком большой номер: ",
        lambda answer: int(answer) > len(torrents)
    )
    torrentNumber = int(answer)
    
    magnet = torrents[torrentNumber - 1]["magnet"]
    if args.magnet:
        print(magnet)
    else:
        download_path = Path.home() / args.output
        if not download_path.exists():
            download_path.mkdir(parents=True)
        subprocess.run(["aria2c", f"-d {download_path}", "--seed-time=0", magnet])
