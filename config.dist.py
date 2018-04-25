timezone = +3           # часовой пояс (от UTC)
timeout = 3600          # время после истечения next_update, в течение которого необходимо пытаться обновить, seconds
in_future_time = 600    # время до истечения next_update, в течение которого необходимо пытаться обновить, seconds
sleep_time = 10         # время задержки выполнения, seconds
max_install_tries = 2   # максимальное количество попыток установки одного и того же crl
server_list = [1, 2, 4, 5]

temp_dir = 'C:/Users/belim/PycharmProjects/Crl updater for crypto servers/temp'
remote_dir = '/home/application/crl_updater/'

log_dir = 'C:/Users/belim/PycharmProjects/Crl updater for crypto servers/'
log_name_mask = 'crl_updater_server_%s.log'

