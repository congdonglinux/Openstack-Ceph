__author__ = 'yrabl'
#! /usr/bin/python
from hosts import CephHost
from hosts import CinderBackupHost
from hosts import CinderHost
from hosts import GlanceHost
from hosts import NovaHost

import utils
from sys import argv

if __name__ == "__main__":

    delete_pools = '--delete-pools' in argv
    reset_pools = '--reset-pools' in argv
    create_pools = '--create-pools' in argv
    create_keyrings = '--create-keyrings' in argv

    if "help" in argv:
        utils.print_help()

    if delete_pools and reset_pools:
        print "Unable to delete and reset the pools"
        utils.print_help()

    params = utils.get_config(argv[1])
    ceph_host = utils.check_ceph_host(params)

    Ceph = CephHost(params, ceph_host[0])

    if delete_pools:

        roles = argv[3:]
        Ceph.delete_pools(roles)
        exit()

    if reset_pools:
        roles = argv[3:]
        Ceph.reset_pools(roles)
        exit()

    if create_pools:
        Ceph.create_pools()
        exit()

    if create_keyrings:
        Ceph.create_client()
        exit()

    Ceph.create_pools()

    for component in Ceph.pools:
        if Ceph.pools[component] == 'y':
            Ceph.create_client(component)

    if Ceph.pools['glance'] == 'y':
        glance_hosts = utils.find_host_role(params, 'glance')
        for node in glance_hosts:
            Glance = GlanceHost(params, node)

            for rpm in Glance.parameters['packages'].split(',' ' '):
                Glance.install_software(rpm)

            Glance.set_keyring(Ceph)
            Glance.set_ceph_conf_file(Ceph)
            Glance.set_glance_conf()
            Glance.reset_services('glance')

    if Ceph.pools['cinder'] == 'y':
        cinder_hosts = utils.find_host_role(params, 'cinder')
        for node in cinder_hosts:
            Cinder = CinderHost(params, node)

            for rpm in params.get('DEFAULT', 'ceph_packages').split(','):
                Cinder.install_software(rpm)

            Cinder.set_keyring(Ceph)
            Cinder.set_ceph_conf_file(Ceph)
            Cinder.set_cinder_conf()
            Cinder.reset_services('cinder')

            nova_hosts = utils.find_host_role(params, 'nova')

            for node in nova_hosts:

                Nova = NovaHost(params, node)

                Nova.set_libvirt_secret(Ceph)
                Nova.set_user_setting()
                Nova.reset_services('nova')

    if Ceph.pools['cinder-backup'] == 'y':

        backup_hosts = utils.find_host_role(params, 'cinder-backup')

        for node in backup_hosts:
            Backup = CinderBackupHost(params, node)

            for rpm in params.get('DEFAULT', 'ceph_packages').split(','):
                Backup.install_software(rpm)

            Backup.set_keyring(Ceph)
            Backup.set_cinder_backup_conf()
            Backup.reset_services('cinder')

    nova_hosts = utils.find_host_role(params, 'nova')

    if Ceph.pools['nova'] == 'y':
        for node in nova_hosts:
            Nova = NovaHost(params, node)
            for rpm in params.get('DEFAULT', 'ceph_packages').split(','):
                    Nova.install_software(rpm)

            Nova.set_nova_conf()
            Nova.set_ceph_conf_file(Ceph)
            Nova.set_keyring(Ceph)

            Nova.reset_services('nova')

    print "Done"
