from config import language, crl_log_datetime_separator_len

translations = {
    'ENG': {'url_not_found': 'URL not found. Dropped',
            'bad_crl': 'Bad CRL url %(url)s (%(actual_number)s)',
            'success_installed_early': 'CRL was installed early (success). Passed',
            'error_installed_early': 'CRL was installed early (error). Passed',
            'cant_get_info': 'Can\'t get info about CRL. Try to install',
            'crl_is_overdue': 'CRL in url is overdue. Passed',
            'install_crl': 'Install CRL',
            'install_complete_success': 'Installation complete successfully',
            'install_complete_error': 'Installation complete with error "%(error)s"',
            'start': 'Daemon started (server: %s; wait timeout, sec: %s; drop timeout, sec: %s; search in future, sec: %s)',
            'overdue': '(!!) CRL overdue',
            'updating': 'CRL is updating...',
            'repeat_updating': 'Repeat CRL updating (is overdue)...',
            'wait_overdue': '(!) CRL will be overdue for a few minute',
            'repeat_updating_wait_overdue': 'Repeat CRL updating (wait overdue)...',
            'crl_ok_install': 'CRL OK installed',
            'crl_over_install': 'CRL install time is over. Dropped',
            'crl_status_unknown': 'CRL status is unknown. Dropped'},

    'RUS': {'url_not_found': 'URL не найден. CRL исключен из обработки',
            'bad_crl': 'Проблема с URL %(url)s (%(actual_number)s)',
            'success_installed_early': 'CRL был установлен ранее (успешно). Пропуск',
            'error_installed_early': 'CRL был установлен ранее (с ошибкой). Пропуск',
            'cant_get_info': 'Невозможно получить информацию о CRL. Попытка установки...',
            'crl_is_overdue': 'CRL в URL просрочен. Пропуск',
            'install_crl': 'Установка CRL',
            'install_complete_success': 'Установка успешно завершена',
            'install_complete_error': 'Установка завершена с ошибкой "%(error)s"',
            'start': 'Демон запущен (сервер: %s; задержка, сек: %s; лимит попыток обновления, сек: %s; предварительное обновление, сек: %s)',
            'overdue': '(!!) CRL просрочен',
            'updating': 'Обновление CRL...',
            'repeat_updating': 'Повтор обновления CRL (CRL просрочен)...',
            'wait_overdue': '(!) CRL скоро просрочится',
            'repeat_updating_wait_overdue': 'Повтор обновления CRL (CRL скоро просрочится)...',
            'crl_ok_install': 'CRL успешно установлен',
            'crl_over_install': 'Лимит времени на обновление вышел. CRL исключен из обработки',
            'crl_status_unknown': 'Статус CRL неизвестен. CRL исключен из обработки'},
}


def log_add(key, no_auth=False):
    if no_auth:
        return translations[language][key]
    else:
        return ' '.join(['''%(AuthKeyID)s # ''',
                         str(translations[language][key]).ljust(crl_log_datetime_separator_len),
                         '''(%(NextUpdate)s)'''])

