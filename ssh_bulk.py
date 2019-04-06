import paramiko
import os
import multiprocessing


def ssh_bulk(host, port, conn_user_list, src_file, dst_path, cmd_list):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    for index, user in enumerate(conn_user_list):
        try:
            ssh.connect(hostname=host,
                        port=port,
                        username=user['user'],
                        password=user['pwd'])
            print('Succeed user:{} pwd:{} for {}'.format(user['user'], user['pwd'], host))
            break
        except paramiko.ssh_exception.AuthenticationException:
            # print('Failed for user:{} pwd:{} for {}'.format(user['user'], user['pwd'], host))
            if index == (len(conn_user_list) - 1):
                return 'All login failed.'

    sftp = paramiko.SFTPClient.from_transport(ssh.get_transport())
    ssh.open_sftp()
    sftp.put(src_file, os.path.join(dst_path, src_file))

    for cmd in cmd_list:
        print(cmd)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        # if 'install.sh' in cmd:
        #     stdin.write('yes\n')
        #     stdin.flush()
        err = stderr.read()
        if err:
            print(err)
        else:
            print('CMD OK')

    ssh.close()
    return 'Done: {}'.format(host)


def get_host_list(path):
    host_list = list()

    try:
        with open(path, 'r') as user_f:
            for line in user_f:
                host_dict = dict()
                host_dict['host'] = line.split(':')[0].strip()
                host_dict['port'] = line.split(':')[1].strip()
                host_list.append(host_dict)
    except Exception as err:
        print(err)
        exit(-1)

    return host_list


def get_user_list(path):
    user_list = list()
    try:
        with open(path, 'r') as user_f:
            for line in user_f:
                user_dict = dict()
                user_dict['user'] = line.split(':')[0].strip()
                user_dict['pwd'] = line.split(':')[1].strip()
                user_list.append(user_dict)
    except Exception as err:
        print(err)
    finally:
        return user_list


def get_cmd_list(path):
    cmd_list = list()
    try:
        with open(path, 'r') as user_f:
            for line in user_f:
                cmd_list.append(line.strip())
    except Exception:
        print('It will not execute any commands.')

    return cmd_list


if __name__ == '__main__':
    threads = []
    cmd = []
    local_file = './cdrom.tar.gz'
    remote_path = '/tmp/'

    conf_host_list = get_host_list('./ssh_host')
    conf_user_list = get_user_list('./user_dict')
    conf_cmd_list = get_cmd_list('./cmd')
    print(conf_user_list)

    pool = multiprocessing.Pool(processes=50)

    result_list = []

    for host in conf_host_list:
        result = pool.apply_async(ssh_bulk,
                                  (host['host'], host['port'], conf_user_list, local_file, remote_path, conf_cmd_list))
        result_list.append(result)

    print('Start processing ...')
    pool.close()
    pool.join()

    for result in result_list:
        print(result.get())

    print('All done ...')
