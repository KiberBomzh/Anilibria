import sys
import platform
import subprocess
import argparse
import json
import requests
from pathlib import Path
from pym3u8downloader import M3U8Downloader


# Создание параметров для программы
parser = argparse.ArgumentParser(description="Аниме с Анилибрии")
parser.add_argument("-s", "--search", help="Запрос для поиска")
parser.add_argument("-e", "--episode", type=int, default=0, help="Указать эпизод")
parser.add_argument("-r", "--results", type=int, default=5, help="Количество результатов поиска, по умолчанию 5")
if "android" in platform.release():
    parser.add_argument("-q", "--quality", default="480", help="Качество, по умолчанию 480")
    parser.add_argument("-p", "--player", default="mx", help="Выбор плеера")
    parser.add_argument("-o", "--output", default="storage/movies/Anilibria", help="Путь для загрузки")
else:
    parser.add_argument("-q", "--quality", default="720", help="Качество, по умолчанию 480")
    parser.add_argument("-p", "--player", default="mpv", help="Выбор плеера")
    parser.add_argument("-o", "--output", default="Anilibria", help="Путь для загрузки")
parser.add_argument("-d", "--download", action="store_true", help="Загрузка видео вместо запуска плеера")
parser.add_argument("-t", "--torrent", action="store_true", help="Загрузка торрента вместо запуска плеера")
parser.add_argument("-m", "--magnet", action="store_true", help="Вместо старта загрузки выдаёт magnet ссылку")
parser.add_argument("-l", "--latest", action="store_true", help="Открыть последний тайтл")
parser.add_argument("-f", "--fast", action="store_true", help="Открыть последнее просмотренную серию")
args = parser.parse_args()

# Создание путей для записи последнего просмотра
cache = Path.home() / ".cache/Anilibria"
latest = cache / "latest.txt"
latestLink = cache / "latestLink.txt"

if not cache.exists():
    cache.mkdir()
if not latest.exists():
    latest.touch()
if not latestLink.exists():
    latestLink.touch()


def play(link, name):
    if args.player == "mpv":
        subprocess.run(["mpv", "--save-position-on-quit", f"--title={name}", link])
    elif args.player == "mx":
        subprocess.run(["mx.sh", link, name])
    else:
        subprocess.run([args.player, link])


def downloadLink(link, title, name):
    forbiddenChars = {"<", ">", ":", '"', "/", "|", "?", "*"}
    if title == "MOVIE":
        download = Path.home() / args.output
        if not download.exists():
            download.mkdir(parents=True)
        for char in name:
            if char in forbiddenChars:
                name = name.replace(char, "_")
    else:
        for char in title:
            if char in forbiddenChars:
                title = title.replace(char, "_")
        download = Path.home() / args.output / title
        if not download.exists():
            download.mkdir(parents=True)
    fileName = download / name
    downloader = M3U8Downloader(
        input_file_path=link[: link.find(".m3u8") + 5], output_file_path=str(fileName)
    )
    downloader.download_playlist()


def main():
    if args.fast:
        # В списке episode [0] - ссылка, [1] - название тайтла, [2] - название серии
        episode = latestLink.read_text().splitlines()
        if args.download:
            downloadLink(episode[0], episode[1], f"{episode[2]}.mp4")
        else:
            if episode[1] == "MOVIE":
                play(episode[0], episode[2])
            else:
                play(episode[0], f"{episode[1]} - {episode[2]}")
        sys.exit()

    # Обработка флага -l
    if not args.latest:
        # Обработка флага -s
        if args.search:
            searchPar = {
                "limit": args.results,
                "f[search]": args.search,
                "include": "id,name.main,type.description,episodes_total",
            }
        else:
            searchPar = {
                "limit": args.results,
                "include": "id,name.main,type.description,episodes_total",
            }
        response = json.loads(
            requests.get(
                "https://api.anilibria.app/api/v1/anime/catalog/releases/?",
                params=searchPar,
            ).text
        )
        results = response["data"]

        try:
            while len(results) == 0:
                args.search = input("Ничего не найдено (⊙_⊙)\nВведите новый запрос: ")
                searchPar = {
                    "limit": args.results,
                    "f[search]": args.search,
                    "include": "id,name.main,type.description,episodes_total",
                }
                response = json.loads(
                    requests.get(
                        "https://api.anilibria.app/api/v1/anime/catalog/releases/?",
                        params=searchPar,
                    ).text
                )
                results = response["data"]
        except (KeyboardInterrupt, EOFError):
            print("До свидания...")
            sys.exit()

        # Отрисовка списка результатов
        counter = 1
        for result in results:
            print(
                counter,
                " ",
                result["name"]["main"],
                " [",
                result["type"]["description"],
                "]",
                sep="",
            )
            counter += 1

        # Запрос номера тайтла со списка
        try:
            resultNumber = int(input("Введите номер: "))
            while len(results) < resultNumber:
                resultNumber = int(input("Слишком большой номер: "))
        except (KeyboardInterrupt, EOFError):
            print("До свидания...")
            sys.exit()

        # Запрос серверу о конкретном тайтле
        titlePar = {"exclude": "poster,description,genres,members"}
        url = (
            "https://api.anilibria.app/api/v1/anime/releases/"
            + str(results[resultNumber - 1]["id"])
            + "?"
        )
        title = json.loads(requests.get(url, params=titlePar).text)
        episodes = title["episodes"]
        latest.write_text(url)
    else:
        titlePar = {"exclude": "poster,description,genres,members"}
        url = latest.read_text()
        title = json.loads(requests.get(url, params=titlePar).text)
        episodes = title["episodes"]
        if not title["type"]["description"] == "Фильм":
            print(title["name"]["main"])

    if args.torrent:
        torrents = title["torrents"]
        count = 1
        print("Доступные торренты:")
        for torrent in torrents:
            print(f"{count} {torrent['label']}")
            count += 1
        try:
            torrentNumber = int(input("Введите номер: "))
            while len(torrents) < torrentNumber:
                torrentNumber = int(input("Слишком большой номер: "))
        except (KeyboardInterrupt, EOFError):
            print("До свидания...")
            sys.exit()
        magnet = torrents[torrentNumber - 1]["magnet"]
        if args.magnet:
            print(magnet)
        else:
            download = Path.home() / args.output
            if not download.exists():
                download.mkdir(parents=True)
            subprocess.run(["aria2c", f"-d {download}", "--seed-time=0", magnet])
        sys.exit()

    # Проверка. Если выбраный тайтл - фильм, запускает просмотр
    if title["type"]["description"] == "Фильм":
        episodeLink = episodes[0]["hls_" + args.quality]
        while f"{episodeLink}" == "None":
            args.quality = input(
                f"Качество {args.quality} недоступно, введите другое: "
            )
            episodeLink = episodes[0]["hls_" + args.quality]
        if args.download:
            downloadLink(
                episodeLink, "MOVIE", f"{title['name']['main']} ({args.quality}).mp4"
            )
        else:
            play(episodeLink, title["name"]["main"])
            latestLink.write_text(
                f"{episodeLink}\nMOVIE\n{title['name']['main']} ({args.quality})"
            )

    # Если нет отрисовывает список эпизодов
    else:
        try:
            if args.episode == 0:
                for episode in episodes:
                    if f"{episode['name']}" == "None":
                        print(episode["ordinal"])
                    else:
                        print(episode["ordinal"], episode["name"])
                args.episode = int(input("Введите номер: "))

            while len(episodes) < args.episode:
                args.episode = int(input("Слишком большой номер эпизода: "))
            episodeLink = episodes[args.episode - 1]["hls_" + args.quality]
            while f"{episodeLink}" == "None":
                args.quality = input(
                    f"Качество {args.quality} недоступно, введите другое: "
                )
                episodeLink = episodes[args.episode - 1]["hls_" + args.quality]
        except (KeyboardInterrupt, EOFError):
            print("До свидания...")
            sys.exit()
        if args.download:
            downloadLink(
                episodeLink,
                title["name"]["main"],
                f"Серия {args.episode} ({args.quality}).mp4",
            )
        else:
            play(episodeLink, f"{title['name']['main']} - Серия {args.episode}")
            latestLink.write_text(
                f"{episodeLink}\n{title['name']['main']}\nСерия {args.episode} ({args.quality})"
            )


if __name__ == "__main__":
    main()
