from ets.ets_certmanager_logs_parser import CertmanagerFile as Crt_f, get_info_file, install_crl as inst_crl
from ets.ets_certificate_lib import Crl
from ets.ets_mysql_lib import MysqlConnection as Mc
from os.path import normpath, join
from datetime import datetime, timedelta
from time import sleep
from hashlib import md5
from itertools import cycle
from queries import *
import requests
from config import *

crl_f_t = 'CRL_%s.txt'
crl_for_install = 'get_by_url_%s.crl'
install_cmd = '''/opt/cprocsp/bin/amd64/certmgr -inst -crl -store mCA -f "%s"'''

temp_dir = normpath(temp_dir)

cached_dict = {}
overdue_notified_cached_dict = {}
ignored_cached_dict = {}
url_cached_dict = {}
hash_cached_dict = {}
status_cached_dict = {}

cn = Mc(connection=Mc.MS_CERT_INFO_CONNECT)


def log_add(string):
    # неудобно каждый раз добавлять в логирование AuthKeyID, проще функцией
    return ' '.join(['''%(AuthKeyID)s # ''', string, '''(%(NextUpdate)s)'''])


def get_urls(server, _auth_key, _crl, logger):
    """Добавляет список url по auth_key в url_cached_dict"""
    # если сведения по url по auth_key еще не кешировались, то кешируем
    if _auth_key not in url_cached_dict.keys():

        with cn.open():
            _urls = cn.execute_query(get_urls_query % _auth_key)
        if _urls:
            # собираем словарь
            keys = range(1, len(_urls) + 1)
            _urls = [u[0] for u in _urls]
            url_d = dict(zip(keys, _urls))
        else:
            url_d = {}

        # actual_number_iter - итератор, зацикленные номера url
        url_cached_dict[_auth_key] = {'urls': url_d,
                                      'actual_number_iter': cycle(range(1, len(_urls) + 1))
                                      }

    # вызываем загрузчик
    download_crl(server, _auth_key, _crl, logger)


def download_crl(server, _auth_key, _crl, logger):
    # получаем все значения из словаря
    urls = url_cached_dict[_auth_key]['urls']

    # если url не найдены, то игнорируем указанный AuthKeyID
    if not urls:
        ignored_cached_dict[_auth_key] = True
        logger.info(log_add('''Url not found. Dropped''') % _crl)
        return

    # получаем следующий url
    actual_number = next(url_cached_dict[_auth_key]['actual_number_iter'])
    url = urls[actual_number]

    crl_file_location = join(temp_dir, crl_for_install % server)
    try:
        response = requests.get(url, timeout=(1, None))
        if response.status_code == 200:
            crl_data = response.content
            # записываем данные в файл
            with open(crl_file_location, mode='wb') as crl_out_f:
                crl_out_f.write(crl_data)

            # собираем хэш
            h = md5()
            h.update(crl_data)
            _hash = h.hexdigest()

            # если еще не создана запись hash_cached_dict, то создаем ее
            if _auth_key not in hash_cached_dict.keys():
                hash_cached_dict[_auth_key] = {}
                # так как первое выполнение, то предыдущий хэш неизвестен, создаем пустое множество для хешей
                hash_cached_dict[_auth_key]['last_hash'] = []

            # пишем актуальный хэш
            hash_cached_dict[_auth_key]['actual_hash'] = _hash

            # если все ок, то теперь можно устанавливать
            install_crl(server, _auth_key, _crl, crl_file_location, logger)
            # и спокойно выходить
            return 0

    except requests.exceptions.RequestException:
        pass

    # если вернулась не 200 или если requests словил исключение при подключении, то больше делать нечего
    logger.info(log_add('''Bad CRL url %(url)s (%(actual_number)s)''') % {'AuthKeyID': _auth_key,
                                                                          'url': url,
                                                                          'actual_number': actual_number,
                                                                          'NextUpdate': _crl['NextUpdate']}
                )
    return


def install_crl(server, _auth_key, _crl, file, logger):

    # если еще не создана запись status_cached_dict, то создаем ее
    if _auth_key not in status_cached_dict.keys():
        status_cached_dict[_auth_key] = {'status': None, 'install_tries': 0}

    # если c таким хешом пакет уже устанавливался и ставили уже max_install_tries раз, то не будем повторяться
    if hash_cached_dict[_auth_key]['actual_hash'] in hash_cached_dict[_auth_key]['last_hash']:
        if status_cached_dict[_auth_key]['install_tries'] == max_install_tries:
            # укажем, удачно или нет завершились установки
            if status_cached_dict[_auth_key]['status']:
                logger.info(log_add('''CRL was installed early (success). Passed''') % _crl)
            else:
                logger.info(log_add('''CRL was installed early (error). Passed''') % _crl)
            return

    # если хэши не совпадают, то возобновляем установку crl
    else:
        status_cached_dict[_auth_key] = {'status': None, 'install_tries': 0}

    inst_tries = status_cached_dict[_auth_key]['install_tries']

    # получаем next_update_datetime непосредственно из файла (если получится)
    try:
        o_crl = Crl(file, timezone=timezone)
        crl_info = o_crl.compile_info_v5()
        next_update_datetime = crl_info.get_next_update_datetime()
    except:
        next_update_datetime = None

    # если не получилось определить next_update_datetime, то надо попробовать установить
    if not next_update_datetime:
        logger.info(log_add('''Can't get info about CRL. Try to install''') % _crl)

    # если скачали такой же или более старый crl, то нет смысла его устанавливать
    elif next_update_datetime <= _crl['NextUpdate']:
        logger.info(log_add('''CRL in url is overdue. Passed''') % _crl)
        return

    # во всех прочих случаях необходима установка
    else:
        logger.info(log_add('''Install CRL''') % _crl)

    # непосредственно установка
    actual_inst_status, error = inst_crl(server, file, is_local=True, test_mode=True, remote_dir=remote_dir)
#    actual_inst_status, error = True, None

    if actual_inst_status:
        status_cached_dict[_auth_key]['status'] = True
        logger.info(log_add('''Installation finished successfully''') % _crl)
    else:
        status_cached_dict[_auth_key]['status'] = False
        logger.info(log_add('''Installation finished with error "%(error)s"''') %
                    {'AuthKeyID': _crl['AuthKeyID'], 'error': error, 'NextUpdate': _crl['NextUpdate']})

    # увеличиваем количество попыток установки
    status_cached_dict[_auth_key]['install_tries'] = inst_tries + 1

    # добавляем значение хеша в last_hash
    hash_cached_dict[_auth_key]['last_hash'].append(hash_cached_dict[_auth_key]['actual_hash'])


def updater(server, _crl, logger):
    """Обновление crl"""
    auth_key = _crl['AuthKeyID']
    get_urls(server, auth_key, _crl, logger)


def main_function(server, logger):
    logger.info('''Daemon started (server: %s, search timeout: %s, drop timeout: %s)''' % (server, sleep_time, timeout))

    while True:

        # загружаем сведения
        get_info_file(server, file_type='CRL', out_dir=temp_dir, remote_dir=remote_dir)
        crl_f = join(temp_dir, crl_f_t % server)

        # установка верхнего и нижнего порога поиска
        now = datetime.now()
        end_time = now + timedelta(seconds=in_future_time)
        start_time = now - timedelta(seconds=timeout)

        # инициализация файла
        crl_o_f = Crt_f(file=crl_f, timezone=timezone)

        # формируем основные наборы данных
        crl_i = crl_o_f.get_info(key='AuthKeyID')
        crl_k = crl_i.keys()

        crl_v_all = crl_i.values()
        # получаем список AuthKeyID актуальных crl
        crl_all_id_keys = [id_key['AuthKeyID'] for id_key in crl_v_all]

        # фильтруем значения, удаляя те, где не определен NextUpdate
        crl_v = list(filter(lambda c: c['NextUpdate'], crl_v_all))

        # получаем списки словарей актуальных crl
        crl_ok = list(filter(lambda c: c['NextUpdate'] > end_time, crl_v))
        # получаем список AuthKeyID актуальных crl
        crl_ok_id_keys = [id_key['AuthKeyID'] for id_key in crl_ok]

        # получаем списки словарей просроченных crl, которые надо игнорировать
        crl_overdue_pass = list(filter(lambda c: c['NextUpdate'] < start_time, crl_v))
        # получаем список AuthKeyID просроченных crl, которые надо игнорировать
        crl_overdue_pass_keys = [id_key['AuthKeyID'] for id_key in crl_overdue_pass]

        # получаем списки словарей просроченных crl, которые нужно обработать
        crl_overdue = list(filter(lambda c: (start_time <= c['NextUpdate'] <= now) and
                                            (c['AuthKeyID'] not in ignored_cached_dict.keys()),
                                  crl_v))

        # получаем списки словарей crl, которые скоро просрочатся
        crl_overdue_in_future = list(filter(lambda c: (now < c['NextUpdate'] <= end_time) and
                                                      (c['AuthKeyID'] not in ignored_cached_dict.keys()),
                                            crl_v))

        # получаем список всех AuthKeyID, которые на данный момент кешированы
        cached_id_keys = cached_dict.keys()

        # обрабатываем все просроченные crl
        for crl in crl_overdue:
            # если найден новый AuthKeyID, то кешируем его
            if crl['AuthKeyID'] not in cached_id_keys:
                cached_dict[crl['AuthKeyID']] = crl

                # если по нему не было оповещения, то выводим оповещение, а его добавляем
                if crl['AuthKeyID'] not in overdue_notified_cached_dict:
                    overdue_notified_cached_dict[crl['AuthKeyID']] = True
                    logger.info(log_add('''(!!) CRL overdue''') % crl)

                logger.info(log_add('''CRL updating...''') % crl)
            else:
                logger.info(log_add('''Repeat CRL updating (is overdue)...''') % crl)

            # пробуем обновить
            updater(server, crl, logger)

        # обрабатываем все crl, которые скоро просрочатся
        for crl in crl_overdue_in_future:
            # если найден новый AuthKeyID, то кешируем его
            if crl['AuthKeyID'] not in cached_id_keys:
                cached_dict[crl['AuthKeyID']] = crl
                logger.info(log_add('''(!) CRL overdue for some minute''') % crl)
                logger.info(log_add('''CRL updating...''') % crl)
            else:
                logger.info(log_add('''Repeat CRL updating (wait overdue)...''') % crl)

            # пробуем обновить
            updater(server, crl, logger)

        # функция удаления ненужных сведений из словарей
        def drop_data(_key_id):
            map(lambda i: i.pop(_key_id, None),
                [overdue_notified_cached_dict,
                 url_cached_dict,
                 cached_dict,
                 hash_cached_dict,
                 status_cached_dict]
                )

        # получаем AuthKeyID, которые больше не актуальны, по ним успешно установлено
        crl_ok_inst_keys = set(cached_id_keys).intersection(set(crl_ok_id_keys))
        # выводим в лог информацию по успешно установленным crl и удаляем их из кешей
        for key_id in crl_ok_inst_keys:
            drop_data(key_id)
            logger.info(log_add('''CRL OK installed last running. Dropped''') % crl_i[key_id])

        # получаем AuthKeyID, которые больше не актуальны, по ним вышел срок установки
        crl_overtime_pass_keys = set(cached_id_keys).intersection(set(crl_overdue_pass_keys))
        # выводим в лог информацию по crl, по которым истек срок установки и удаляем их из кешей
        for key_id in crl_overtime_pass_keys:
            drop_data(key_id)
            logger.info(log_add('''CRL install time is over. Dropped''') % crl_i[key_id])

        # получаем AuthKeyID, которые в предыдущий раз были в полных сведениях, а сейчас пропали
        crl_all_id_pass_key = set(cached_id_keys).difference(set(crl_all_id_keys))
        # выводим в лог информацию по crl, которые в предыдущий раз были в полных сведениях, а сейчас пропали
        for key_id in crl_all_id_pass_key:
            drop_data(key_id)
            logger.info(log_add('''CRL status is unknown. Dropped''') % crl_i[key_id])

        sleep(sleep_time)



