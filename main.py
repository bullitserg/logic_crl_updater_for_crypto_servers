import argparse
from os.path import normpath, join
from logger_module import logger, init_log_config
from config import server_list, log_dir, log_name_mask
from functions import main_function

PROGNAME = 'CRL server updater'
DESCRIPTION = '''Скрипт для обновления CRL на серверах'''
VERSION = '1.0'
AUTHOR = 'Belim S.'
RELEASE_DATE = '2018-04-25'


def show_version():
    print(PROGNAME, VERSION, '\n', DESCRIPTION, '\nAuthor:', AUTHOR, '\nRelease date:', RELEASE_DATE)


# обработчик параметров командной строки
def create_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument('-v', '--version', action='store_true',
                        help="Показать версию программы")

    parser.add_argument('-s', '--server', type=int, choices=server_list,
                        help="Установить номер сервера")
    return parser

if __name__ == '__main__':
        # парсим аргументы командной строки
        my_parser = create_parser()
        namespace = my_parser.parse_args()

        if namespace.version:
            show_version()
            exit(0)
        if namespace.server:
            try:
                # инициируем лог-файл
                log_file = join(normpath(log_dir), log_name_mask % namespace.server)
                init_log_config(log_file)
                logger_name = 'SERVER_%s' % namespace.server
                logger = logger(logger_name)

                # запускаем основной процесс
                main_function(namespace.server, logger)

            # если при исполнении будут исключения - кратко выводим на терминал, остальное - в лог
            except Exception as e:
                logger.fatal('Fatal error! Exit', exc_info=True)
                print('Critical error: %s' % e)
                print('More information in log file')
                exit(1)
        else:
            show_version()
            print('For more information run use --help')

exit(0)



