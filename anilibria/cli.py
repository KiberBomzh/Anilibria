import platform
import argparse

from anilibria.functions import input, get_answer, print_option_list, play, download, style_green, get_path, fast, torrent, get_link
from anilibria.api_anilibria import catalog_request, get_title
from anilibria.config import config as config

from rich.traceback import install
install(show_locals=True)


# Создание параметров для программы
parser = argparse.ArgumentParser(description="Аниме с Анилибрии")
parser.add_argument("-s", "--search", help="Запрос для поиска")
parser.add_argument("-e", "--episode", type=int, default=0, help="Указать эпизод")
parser.add_argument("-r", "--results", type=int, default=5, help="Количество результатов поиска, по умолчанию 5")
parser.add_argument("-q", "--quality", default="", help="Качество, по умолчанию 720 (480 для android)")
parser.add_argument("-p", "--player", default="", help="Выбор плеера")
parser.add_argument("-o", "--output", default="", help="Путь для загрузки")

parser.add_argument("-d", "--download", action="store_true", help="Загрузка видео вместо запуска плеера")
parser.add_argument("-t", "--torrent", action="store_true", help="Загрузка торрента вместо запуска плеера")
parser.add_argument("-m", "--magnet", action="store_true", help="Вместо старта загрузки выдаёт magnet ссылку")
parser.add_argument("-l", "--latest", action="store_true", help="Открыть последний тайтл")
parser.add_argument("-f", "--fast", action="store_true", help="Открыть последнее просмотренную серию")
args = parser.parse_args()

if config:
    if 'search_results' in config and not args.results:
        args.results = config['search_results']
    if 'quality' in config and not args.quality:
        args.quality = config['quality']
    if 'player' in config and not args.player:
        args.player = config['player']
    if 'download_path' in config and not args.output:
        args.output = config['download_path']


if "android" in platform.release():
    args.quality = "480" if not args.quality else args.quality
    args.player = "next-android" if not args.player else args.player
    args.output = "storage/movies/Anilibria" if not args.output else args.output
else:
    args.quality = "720" if not args.quality else args.quality
    args.player = "mpv" if not args.player else args.player
    args.output = "Anilibria" if not args.output else args.output

latest, latestLink = get_path()


def main():
    if args.fast:
        fast(args)
        return

    # Обработка флага -l
    if not args.latest:
        results = catalog_request(args.search, args.results)
        while not results:
            args.search = input("Ничего не найдено (⊙_⊙)\nВведите новый запрос: ")
            results = catalog_request()

        # Отрисовка списка результатов
        option_list = []
        for result in results:
            option_list.append(
                result["name"]["main"] +
                f" [blue][{result["type"]["description"]}][/]"
            )
        print_option_list(option_list)

        # Запрос номера тайтла со списка
        answer = get_answer(
            "Слишком большой номер: ",
            lambda answer: int(answer) > len(results)
        )
        resultNumber = int(answer)
        title_id = str(results[resultNumber - 1]["id"])
    else:
        title_id = None
        

    # Запрос серверу о конкретном тайтле
    title, episodes = get_title(title_id)

    if args.torrent:
        torrent(title, args)
        return

    # Проверка. Если выбраный тайтл - фильм, запускает просмотр
    if title["type"]["description"] == "Фильм":
        episodeLink = get_link(episodes, args.quality)
        
        if args.download:
            download(
                episodeLink, 
                "MOVIE", 
                f"{title['name']['main']} ({args.quality}).mp4",
                args.output
            )
        else:
            play(episodeLink, title["name"]["main"], args.player)
            
            latestLink.write_text(f"{episodeLink}\nMOVIE\n{title['name']['main']} ({args.quality})")

    # Если нет отрисовывает список эпизодов
    else:
        if args.episode == 0:
            option_list = []
            for episode in episodes:
                if episode['name'] is None:
                    option_list.append(f"Эпизод {episode["ordinal"]}")
                else:
                    option_list.append(f"Эпизод {episode["ordinal"]}. {episode["name"]}")
            
            print_option_list(option_list, title['name']['main'])
            args.episode = int(input("> ", style = style_green))

        while len(episodes) < args.episode:
            args.episode = int(input("Слишком большой номер эпизода: "))
        
        episodeLink = get_link(episodes, args.quality, args.episode)
        
        if args.download:
            download(
                episodeLink,
                title["name"]["main"],
                f"Серия {args.episode} ({args.quality}).mp4",
                args.output
            )
        else:
            play(episodeLink, f"{title['name']['main']} - Серия {args.episode}", args.player)
            latestLink.write_text(
                f"{episodeLink}\n{title['name']['main']}\nСерия {args.episode} ({args.quality})"
            )


if __name__ == "__main__":
    main()
