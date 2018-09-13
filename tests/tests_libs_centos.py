
from novaagent.libs import centos
from .fixtures import xen_data
from .fixtures import network


import logging
import glob
import sys
import os


if sys.version_info[:2] >= (2, 7):
    from unittest import TestCase
else:
    from unittest2 import TestCase


try:
    from unittest import mock
except ImportError:
    import mock


class TestHelpers(TestCase):
    def setUp(self):
        logging.disable(logging.ERROR)

    def tearDown(self):
        logging.disable(logging.NOTSET)
        file_searches = [
            '/tmp/route-*',
            '/tmp/ifcfg-eth*',
            '/tmp/hostname*',
            '/tmp/network*',
            '/tmp/ifcfg-lo*'
        ]
        for search in file_searches:
            route_files = glob.glob(search)
            for item in route_files:
                os.remove(item)

    def setup_temp_route(self):
        with open('/tmp/route-eth1', 'a+') as f:
            f.write('This is a test file')

    def setup_temp_interface_config(self, interface):
        with open('/tmp/ifcfg-{0}'.format(interface), 'a+') as f:
            f.write(
                'IPADDR=2.2.2.2\n'
                'IPADDR999=1.1.1.1\n'
                'ZONE=TestFirewalldZone\n'
                'NETMASK=255.255.255.0\n'
                'NETMASK12345=255.255.0.0\n'
                'DNS1=9.9.9.9\n'
                'DNS2=10.10.10.10\n'
                '# Comment in file\n'
                ' Starts with a space\n'
                '      # Mulitple spaces\n'
                'TEST_OPTION=TEST_VALUE\n'
            )

    def setup_temp_hostname(self):
        with open('/tmp/hostname', 'a+') as f:
            f.write('test.hostname.local')

    def setup_temp_network(self):
        with open('/tmp/network', 'a+') as f:
            f.write('This is a test file')

    def test_initialization(self):
        temp = centos.ServerOS()
        self.assertEqual(
            temp.netconfig_dir,
            '/etc/sysconfig/network-scripts',
            'Network scripts directory was not expected value'
        )
        self.assertEqual(
            temp.interface_file_prefix,
            'ifcfg',
            'Network scripts prefix is not expected value'
        )
        self.assertEqual(
            temp.route_file_prefix,
            'route',
            'Route script prefix is not expected value'
        )
        self.assertEqual(
            temp.hostname_file,
            '/etc/hostname',
            'Hostname file is not expected value'
        )
        self.assertEqual(
            temp.network_file,
            '/etc/sysconfig/network',
            'Network file location is not expected value'
        )

    def test_reset_network_hostname_failure(self):
        self.setup_temp_route()
        self.setup_temp_interface_config('eth1')
        self.setup_temp_interface_config('lo')
        self.setup_temp_network()
        temp = centos.ServerOS()
        temp.netconfig_dir = '/tmp'
        temp.network_file = '/tmp/network'
        with mock.patch(
            'novaagent.libs.centos.ServerOS._setup_hostname'
        ) as hostname:
            hostname.return_value = 1, 'temp.hostname'
            with mock.patch('novaagent.utils.list_xenstore_macaddrs') as mac:
                mac.return_value = ['BC764E206C5B']
                with mock.patch('novaagent.utils.list_hw_interfaces') as hwint:
                    hwint.return_value = ['eth1', 'lo']
                    mock_response = mock.Mock()
                    mock_response.side_effect = [
                        'BC764E206C5B',
                        None
                    ]
                    with mock.patch(
                        'novaagent.utils.get_hw_addr',
                        side_effect=mock_response
                    ):
                        with mock.patch(
                            'novaagent.utils.get_interface'
                        ) as inter:
                            inter.return_value = (
                                xen_data.check_network_interface()
                            )
                            with mock.patch(
                                'novaagent.utils.get_ifcfg_files_to_remove'
                            ) as ifcfg_files:
                                ifcfg_files.return_value = ['/tmp/ifcfg-eth1']
                                with mock.patch(
                                    'novaagent.libs.centos.ServerOS.'
                                    '_check_for_extra_settings'
                                ) as check:
                                    check.return_value = []
                                    with mock.patch(
                                        'novaagent.libs.centos.Popen'
                                    ) as p:
                                        p.return_value.communicate.return_value = ('out', 'error')  # noqa
                                        p.return_value.returncode = 0
                                        result = temp.resetnetwork(
                                            'name',
                                            'value',
                                            'dummy_client'
                                        )

        self.assertEqual(
            result,
            ('0', ''),
            'Result was not the expected value'
        )
        network_files = glob.glob('/tmp/network*')
        self.assertEqual(
            len(network_files),
            2,
            'Incorrect number of network files'
        )
        ifcfg_files = glob.glob('/tmp/ifcfg-eth*')
        self.assertEqual(
            len(ifcfg_files),
            2,
            'Incorrect number of ifcfg files'
        )
        route_files = glob.glob('/tmp/route*')
        self.assertEqual(
            len(route_files),
            2,
            'Incorrect number of route files'
        )
        localhost = glob.glob('/tmp/ifcfg-lo')
        self.assertEqual(
            len(localhost),
            1,
            'Localhost ifcfg file was moved out of the way and should not have'
        )

    def test_reset_network_flush_failure(self):
        self.setup_temp_route()
        self.setup_temp_interface_config('eth1')
        self.setup_temp_interface_config('lo')
        self.setup_temp_network()
        temp = centos.ServerOS()
        temp.netconfig_dir = '/tmp'
        temp.network_file = '/tmp/network'
        with mock.patch(
            'novaagent.libs.centos.ServerOS._setup_hostname'
        ) as hostname:
            hostname.return_value = 0, 'temp.hostname'
            with mock.patch('novaagent.utils.list_xenstore_macaddrs') as mac:
                mac.return_value = ['BC764E206C5B']
                with mock.patch('novaagent.utils.list_hw_interfaces') as hwint:
                    hwint.return_value = ['eth1', 'lo']
                    mock_response = mock.Mock()
                    mock_response.side_effect = [
                        'BC764E206C5B',
                        None
                    ]
                    with mock.patch(
                        'novaagent.utils.get_hw_addr',
                        side_effect=mock_response
                    ):
                        with mock.patch(
                            'novaagent.utils.get_interface'
                        ) as inter:
                            inter.return_value = (
                                xen_data.check_network_interface()
                            )
                            with mock.patch(
                                'novaagent.utils.get_ifcfg_files_to_remove'
                            ) as ifcfg_files:
                                ifcfg_files.return_value = ['/tmp/ifcfg-eth1']
                                with mock.patch(
                                    'novaagent.libs.centos.ServerOS.'
                                    '_check_for_extra_settings'
                                ) as check:
                                    check.return_value = []
                                    mock_popen = mock.Mock()
                                    mock_comm = mock.Mock()
                                    mock_comm.return_value = ('out', 'error')
                                    mock_popen.side_effect = [
                                        mock.Mock(
                                            returncode=1,
                                            communicate=mock_comm
                                        ),
                                        mock.Mock(
                                            returncode=0,
                                            communicate=mock_comm
                                        )
                                    ]
                                    with mock.patch(
                                        'novaagent.libs.centos.Popen',
                                        side_effect=mock_popen
                                    ):
                                        result = temp.resetnetwork(
                                            'name',
                                            'value',
                                            'dummy_client'
                                        )

        self.assertEqual(
            result,
            ('0', ''),
            'Result was not the expected value'
        )
        network_files = glob.glob('/tmp/network*')
        self.assertEqual(
            len(network_files),
            2,
            'Incorrect number of network files'
        )
        ifcfg_files = glob.glob('/tmp/ifcfg-eth*')
        self.assertEqual(
            len(ifcfg_files),
            2,
            'Incorrect number of ifcfg files'
        )
        route_files = glob.glob('/tmp/route*')
        self.assertEqual(
            len(route_files),
            2,
            'Incorrect number of route files'
        )
        localhost = glob.glob('/tmp/ifcfg-lo')
        self.assertEqual(
            len(localhost),
            1,
            'Localhost ifcfg file was moved out of the way and should not have'
        )

    def test_reset_network_success(self):
        self.setup_temp_route()
        self.setup_temp_interface_config('eth1')
        self.setup_temp_interface_config('lo')
        self.setup_temp_network()
        temp = centos.ServerOS()
        temp.netconfig_dir = '/tmp'
        temp.network_file = '/tmp/network'
        with mock.patch(
            'novaagent.libs.centos.ServerOS._setup_hostname'
        ) as hostname:
            hostname.return_value = 0, 'temp.hostname'
            with mock.patch('novaagent.utils.list_xenstore_macaddrs') as mac:
                mac.return_value = ['BC764E206C5B']
                with mock.patch('novaagent.utils.list_hw_interfaces') as hwint:
                    hwint.return_value = ['eth1', 'lo']
                    mock_response = mock.Mock()
                    mock_response.side_effect = [
                        'BC764E206C5B',
                        None
                    ]
                    with mock.patch(
                        'novaagent.utils.get_hw_addr',
                        side_effect=mock_response
                    ):
                        with mock.patch(
                            'novaagent.utils.get_interface'
                        ) as inter:
                            inter.return_value = (
                                xen_data.check_network_interface()
                            )
                            with mock.patch(
                                'novaagent.utils.get_ifcfg_files_to_remove'
                            ) as ifcfg_files:
                                ifcfg_files.return_value = ['/tmp/ifcfg-eth1']
                                with mock.patch(
                                    'novaagent.libs.centos.ServerOS.'
                                    '_check_for_extra_settings'
                                ) as check:
                                    check.return_value = []
                                    with mock.patch(
                                        'novaagent.libs.centos.Popen'
                                    ) as p:
                                        p.return_value.communicate.return_value = ('out', 'error')  # noqa
                                        p.return_value.returncode = 0
                                        result = temp.resetnetwork(
                                            'name',
                                            'value',
                                            'dummy_client'
                                        )

        self.assertEqual(
            result,
            ('0', ''),
            'Result was not the expected value'
        )
        network_files = glob.glob('/tmp/network*')
        self.assertEqual(
            len(network_files),
            2,
            'Incorrect number of network files'
        )
        ifcfg_files = glob.glob('/tmp/ifcfg-eth*')
        self.assertEqual(
            len(ifcfg_files),
            2,
            'Incorrect number of ifcfg files'
        )
        route_files = glob.glob('/tmp/route*')
        self.assertEqual(
            len(route_files),
            2,
            'Incorrect number of route files'
        )
        localhost = glob.glob('/tmp/ifcfg-lo')
        self.assertEqual(
            len(localhost),
            1,
            'Localhost ifcfg file was moved out of the way and should not have'
        )

    def test_reset_network_error(self):
        self.setup_temp_route()
        self.setup_temp_interface_config('eth1')
        self.setup_temp_interface_config('lo')
        self.setup_temp_network()
        temp = centos.ServerOS()
        temp.netconfig_dir = '/tmp'
        temp.network_file = '/tmp/network'
        with mock.patch(
            'novaagent.libs.centos.ServerOS._setup_hostname'
        ) as hostname:
            hostname.return_value = 0, 'temp.hostname'
            with mock.patch('novaagent.utils.list_xenstore_macaddrs') as mac:
                mac.return_value = ['BC764E206C5B']
                with mock.patch('novaagent.utils.list_hw_interfaces') as hwint:
                    hwint.return_value = ['eth1']
                    with mock.patch('novaagent.utils.get_hw_addr') as addr:
                        addr.return_value = 'BC764E206C5B'
                        with mock.patch(
                            'novaagent.utils.get_interface'
                        ) as inter:
                            inter.return_value = (
                                xen_data.check_network_interface()
                            )
                            with mock.patch(
                                'novaagent.utils.get_ifcfg_files_to_remove'
                            ) as ifcfg_files:
                                ifcfg_files.return_value = ['/tmp/ifcfg-eth1']
                                with mock.patch(
                                    'novaagent.libs.centos.ServerOS.'
                                    '_check_for_extra_settings'
                                ) as check:
                                    check.return_value = []
                                    with mock.patch(
                                        'novaagent.libs.centos.Popen'
                                    ) as p:
                                        p.return_value.communicate.return_value = ('out', 'error')  # noqa
                                        p.return_value.returncode = 1
                                        result = temp.resetnetwork(
                                            'name',
                                            'value',
                                            'dummy_client'
                                        )

        self.assertEqual(
            result,
            ('1', 'Error restarting network'),
            'Result was not the expected value'
        )
        network_files = glob.glob('/tmp/network*')
        self.assertEqual(
            len(network_files),
            2,
            'Incorrect number of network files'
        )
        ifcfg_files = glob.glob('/tmp/ifcfg-eth*')
        self.assertEqual(
            len(ifcfg_files),
            2,
            'Incorrect number of ifcfg files'
        )
        route_files = glob.glob('/tmp/route*')
        self.assertEqual(
            len(route_files),
            2,
            'Incorrect number of route files'
        )
        localhost = glob.glob('/tmp/ifcfg-lo')
        self.assertEqual(
            len(localhost),
            1,
            'Localhost ifcfg file was moved out of the way and should not have'
        )

    def test_reset_network_success_systemctl(self):
        self.setup_temp_route()
        self.setup_temp_interface_config('eth1')
        self.setup_temp_interface_config('lo')
        self.setup_temp_network()
        temp = centos.ServerOS()
        temp.netconfig_dir = '/tmp'
        temp.network_file = '/tmp/network'

        mock_response = mock.Mock()
        mock_response.side_effect = [
            True, True, False, True, True
        ]
        with mock.patch(
            'novaagent.libs.centos.os.path.exists',
            mock_response
        ):
            with mock.patch(
                'novaagent.libs.centos.ServerOS._setup_hostname'
            ) as hostname:
                hostname.return_value = 0, 'temp.hostname'
                with mock.patch(
                    'novaagent.utils.list_xenstore_macaddrs'
                ) as mac:
                    mac.return_value = ['BC764E206C5B']
                    with mock.patch(
                        'novaagent.utils.list_hw_interfaces'
                    ) as hwint:
                        hwint.return_value = ['eth1']
                        with mock.patch(
                            'novaagent.utils.get_hw_addr'
                        ) as hw_addr:
                            hw_addr.return_value = 'BC764E206C5B'
                            with mock.patch(
                                'novaagent.utils.get_interface'
                            ) as inter:
                                inter.return_value = (
                                    xen_data.check_network_interface()
                                )
                                with mock.patch(
                                    'novaagent.utils.get_ifcfg_files_to_remove'
                                ) as ifcfg_files:
                                    ifcfg_files.return_value = [
                                        '/tmp/ifcfg-eth1'
                                    ]
                                    with mock.patch(
                                        'novaagent.libs.centos.ServerOS.'
                                        '_check_for_extra_settings'
                                    ) as check:
                                        check.return_value = []
                                        with mock.patch(
                                            'novaagent.libs.centos.Popen'
                                        ) as p:
                                            p.return_value.communicate.return_value = ('out', 'error')  # noqa
                                            p.return_value.returncode = 0
                                            result = temp.resetnetwork(
                                                'name',
                                                'value',
                                                'dummy_client'
                                            )

        self.assertEqual(
            result,
            ('0', ''),
            'Result was not the expected value'
        )
        network_files = glob.glob('/tmp/network*')
        self.assertEqual(
            len(network_files),
            2,
            'Incorrect number of network files'
        )
        ifcfg_files = glob.glob('/tmp/ifcfg-eth*')
        self.assertEqual(
            len(ifcfg_files),
            2,
            'Incorrect number of ifcfg files'
        )
        route_files = glob.glob('/tmp/route*')
        self.assertEqual(
            len(route_files),
            2,
            'Incorrect number of route files'
        )
        localhost = glob.glob('/tmp/ifcfg-lo')
        self.assertEqual(
            len(localhost),
            1,
            'Localhost ifcfg file was moved out of the way and should not have'
        )

    def test_reset_network_error_systemctl(self):
        self.setup_temp_route()
        self.setup_temp_interface_config('eth1')
        self.setup_temp_interface_config('lo')
        self.setup_temp_network()
        temp = centos.ServerOS()
        temp.netconfig_dir = '/tmp'
        temp.network_file = '/tmp/network'
        mock_response = mock.Mock()
        mock_response.side_effect = [
            True, True, False, True, True
        ]
        with mock.patch(
            'novaagent.libs.centos.os.path.exists',
            mock_response
        ):
            with mock.patch(
                'novaagent.libs.centos.ServerOS._setup_hostname'
            ) as hostname:
                hostname.return_value = 0, 'temp.hostname'
                with mock.patch(
                    'novaagent.utils.list_xenstore_macaddrs'
                ) as mac:
                    mac.return_value = ['BC764E206C5B']
                    with mock.patch(
                        'novaagent.utils.list_hw_interfaces'
                    ) as hwint:
                        hwint.return_value = ['eth1']
                        with mock.patch(
                            'novaagent.utils.get_hw_addr'
                        ) as hw_addr:
                            hw_addr.return_value = 'BC764E206C5B'
                            with mock.patch(
                                'novaagent.utils.get_interface'
                            ) as inter:
                                inter.return_value = (
                                    xen_data.check_network_interface()
                                )
                                with mock.patch(
                                    'novaagent.utils.get_ifcfg_files_to_remove'
                                ) as ifcfg_files:
                                    ifcfg_files.return_value = [
                                        '/tmp/ifcfg-eth1'
                                    ]
                                    with mock.patch(
                                        'novaagent.libs.centos.ServerOS.'
                                        '_check_for_extra_settings'
                                    ) as check:
                                        check.return_value = []
                                        with mock.patch(
                                            'novaagent.libs.centos.Popen'
                                        ) as p:
                                            p.return_value.communicate.return_value = ('out', 'error')  # noqa
                                            p.return_value.returncode = 1
                                            result = temp.resetnetwork(
                                                'name',
                                                'value',
                                                'dummy_client'
                                            )

        self.assertEqual(
            result,
            ('1', 'Error restarting network'),
            'Result was not the expected value'
        )
        network_files = glob.glob('/tmp/network*')
        self.assertEqual(
            len(network_files),
            2,
            'Incorrect number of network files'
        )
        ifcfg_files = glob.glob('/tmp/ifcfg-eth*')
        self.assertEqual(
            len(ifcfg_files),
            2,
            'Incorrect number of ifcfg files'
        )
        route_files = glob.glob('/tmp/route*')
        self.assertEqual(
            len(route_files),
            2,
            'Incorrect number of route files'
        )
        localhost = glob.glob('/tmp/ifcfg-lo')
        self.assertEqual(
            len(localhost),
            1,
            'Localhost ifcfg file was moved out of the way and should not have'
        )

    def test_check_extra_args(self):
        self.setup_temp_interface_config('eth1')
        temp = centos.ServerOS()
        interface_file = '/tmp/ifcfg-eth1'

        extra_args = temp._check_for_extra_settings(interface_file)
        self.assertEqual(
            len(extra_args),
            2,
            'Did not get proper number of arguments from check'
        )
        self.assertEqual(
            extra_args,
            ['ZONE=TestFirewalldZone', 'TEST_OPTION=TEST_VALUE'],
            'Did not get proper extra arguments from check'
        )

    def test_check_extra_args_no_file(self):
        temp = centos.ServerOS()
        interface_file = '/tmp/ifcfg-eth1'

        extra_args = temp._check_for_extra_settings(interface_file)
        self.assertEqual(
            len(extra_args),
            0,
            'Did not get proper number of arguments from check'
        )
        self.assertEqual(
            extra_args,
            [],
            'Did not get proper extra arguments from check'
        )

    def test_setup_routes(self):
        self.setup_temp_route()
        temp = centos.ServerOS()
        temp.netconfig_dir = '/tmp'
        temp_iface = xen_data.check_network_interface()
        temp._setup_routes('eth1', temp_iface)
        files = glob.glob('/tmp/route-eth1*')
        self.assertEqual(
            len(files),
            2,
            'Did not find correct number of files'
        )
        with open('/tmp/route-eth1') as f:
            written_data = f.readlines()

        for index, line in enumerate(written_data):
            self.assertEqual(
                line,
                network.CENTOS_ROUTE_FILE[index],
                'Written file did not match expected value'
            )

    def test_setup_interfaces_eth0(self):
        self.setup_temp_interface_config('eth0')
        temp = centos.ServerOS()
        temp.netconfig_dir = '/tmp'
        temp_iface = network.ETH0_INTERFACE
        temp._setup_interface('eth0', temp_iface)

        files = glob.glob('/tmp/ifcfg-eth0*')
        self.assertEqual(
            len(files),
            2,
            'Did not find correct number of files'
        )
        with open('/tmp/ifcfg-eth0') as f:
            written_data = f.readlines()

        for index, line in enumerate(written_data):
            self.assertEqual(
                line,
                network.CENTOS_IFCFG_ETH0[index],
                'Written file did not match expected value'
            )

    def test_setup_interfaces_eth1(self):
        self.setup_temp_interface_config('eth1')
        temp = centos.ServerOS()
        temp.netconfig_dir = '/tmp'
        temp_iface = xen_data.check_network_interface()
        temp._setup_interface('eth1', temp_iface)

        files = glob.glob('/tmp/ifcfg-eth1*')
        self.assertEqual(
            len(files),
            2,
            'Did not find correct number of files'
        )
        with open('/tmp/ifcfg-eth1') as f:
            written_data = f.readlines()

        for index, line in enumerate(written_data):
            self.assertEqual(
                line,
                network.CENTOS_IFCFG_ETH1[index],
                'Written file did not match expected value'
            )

    def test_setup_hostname_hostname_success(self):
        self.setup_temp_hostname()
        temp = centos.ServerOS()
        temp.hostname_file = '/tmp/hostname'
        test_hostname = 'test.hostname'
        with mock.patch('novaagent.utils.get_hostname') as hostname:
            hostname.return_value = test_hostname
            with mock.patch('novaagent.libs.os.path.exists') as exists:
                exists.return_value = False
                with mock.patch('novaagent.libs.Popen') as popen:
                    popen.return_value.communicate.return_value = (
                        ('out', 'err')
                    )
                    popen.return_value.returncode = 0
                    return_code, hostname = temp._setup_hostname(
                        'dummy_client'
                    )

        self.assertEqual(
            hostname,
            test_hostname,
            'Did not receive expected host from function'
        )
        self.assertEqual(
            return_code,
            0,
            'Return code received was not expected value'
        )

    def test_setup_hostname_hostname_failure(self):
        self.setup_temp_hostname()
        temp = centos.ServerOS()
        temp.hostname_file = '/tmp/hostname'
        test_hostname = 'test.hostname'
        with mock.patch('novaagent.utils.get_hostname') as hostname:
            hostname.return_value = test_hostname
            with mock.patch('novaagent.libs.os.path.exists') as exists:
                exists.return_value = False
                with mock.patch('novaagent.libs.Popen') as popen:
                    popen.return_value.communicate.return_value = (
                        ('out', 'err')
                    )
                    popen.return_value.returncode = 1
                    return_code, hostname = temp._setup_hostname(
                        'dummy_client'
                    )

        self.assertEqual(
            hostname,
            test_hostname,
            'Did not receive expected host from function'
        )
        self.assertEqual(
            return_code,
            1,
            'Return code received was not expected value'
        )

    def test_setup_hostname_hostnamectl_success(self):
        self.setup_temp_hostname()
        temp = centos.ServerOS()
        temp.hostname_file = '/tmp/hostname'
        test_hostname = 'test.hostname'
        with mock.patch('novaagent.utils.get_hostname') as hostname:
            hostname.return_value = test_hostname
            with mock.patch('novaagent.libs.os.path.exists') as exists:
                exists.return_value = True
                with mock.patch('novaagent.libs.Popen') as popen:
                    popen.return_value.communicate.return_value = (
                        ('out', 'err')
                    )
                    popen.return_value.returncode = 0
                    return_code, hostname = temp._setup_hostname(
                        'dummy_client'
                    )

        self.assertEqual(
            hostname,
            test_hostname,
            'Did not receive expected host from function'
        )
        self.assertEqual(
            return_code,
            0,
            'Return code received was not expected value'
        )

    def test_setup_hostname_hostnamectl_failure(self):
        self.setup_temp_hostname()
        temp = centos.ServerOS()
        temp.hostname_file = '/tmp/hostname'
        test_hostname = 'test.hostname'
        with mock.patch('novaagent.utils.get_hostname') as hostname:
            hostname.return_value = test_hostname
            with mock.patch('novaagent.libs.os.path.exists') as exists:
                exists.return_value = True
                with mock.patch('novaagent.libs.Popen') as popen:
                    popen.return_value.communicate.return_value = (
                        ('out', 'err')
                    )
                    popen.return_value.returncode = 1
                    return_code, hostname = temp._setup_hostname(
                        'dummy_client'
                    )

        self.assertEqual(
            hostname,
            test_hostname,
            'Did not receive expected host from function'
        )
        self.assertEqual(
            return_code,
            1,
            'Return code received was not expected value'
        )
