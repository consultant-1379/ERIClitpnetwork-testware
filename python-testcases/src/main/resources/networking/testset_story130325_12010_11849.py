'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     February 2017
@author:    Boyan Mihovski
@summary:   Integration
            Agile: STORY-130325, 12010, 11849, TORF-159450
'''

from litp_generic_test import GenericTest, attr
from xml_utils import XMLUtils
import test_constants


class Story130325(GenericTest):

    """
    As a LITP administrator I want additional properties for multicast on the
     bridge so I can block multicast traffic from the bridge
    """

    def setUp(self):
        super(Story130325, self).setUp()

        # Set up variables used in the test
        self.ms_node = self.get_management_node_filename()
        self.xml = XMLUtils()
        # Defining test constants
        self.node_urls = self.find(self.ms_node, '/deployments', 'node')
        n1_vpath = \
            self.get_node_filename_from_url(self.ms_node, self.node_urls[0])
        self.n1_hostname = \
            self.get_node_att(n1_vpath, 'hostname')
        n2_vpath = \
            self.get_node_filename_from_url(self.ms_node, self.node_urls[1])
        self.n2_hostname = \
            self.get_node_att(n2_vpath, 'hostname')
        self.n1_net_url = self.node_urls[0] + '/network_interfaces/'
        self.n2_net_url = self.node_urls[1] + '/network_interfaces/'
        n1_free_nics = \
            self.verify_backup_free_nics(self.ms_node, self.node_urls[0],
                                         required_free_nics=3)
        n2_free_nics = \
            self.verify_backup_free_nics(self.ms_node, self.node_urls[1])
        self.network_settings = {
                self.n1_net_url:
                {'if_130325_0': {
                    'node_name': self.n1_hostname,
                    'nic_name': n1_free_nics[0]['NAME'],
                    'MAC': n1_free_nics[0]['MAC'],
                    'IPv4': '26.26.26.2',
                    'IPv6': None,
                    'network': 'test130325_1',
                    'bridge': 'br_130325_3',
                    'bond': None,
                    'vlan': None,
                    'autcnfg': None
                        },
                 'if_130325_1': {
                    'node_name': self.n1_hostname,
                    'nic_name': n1_free_nics[1]['NAME'],
                    'MAC': n1_free_nics[1]['MAC'],
                    'IPv4': None,
                    'IPv6': '2001:2200:82a1:25::164',
                    'network': 'test130325_2',
                    'bridge': 'br_130325_0',
                    'bond': None,
                    'vlan': None,
                    'autcnfg': None
                        },
                 'if_159450': {
                    'node_name': self.n1_hostname,
                    'nic_name': n1_free_nics[2]['NAME'],
                    'MAC': n1_free_nics[2]['MAC'],
                    'IPv4': '25.25.25.1',
                    'IPv6': '2001:2200:82a1:25::264',
                    'network': 'test130325_3',
                    'bridge': 'br_130325_1',
                    'bond': 'bond_130325',
                    'vlan': 'vlan_130325',
                    'autcnfg': True
                        }
                 },
                self.n2_net_url:
                {'if_130325_3': {
                    'node_name': self.n2_hostname,
                    'nic_name': n2_free_nics[0]['NAME'],
                    'MAC': n2_free_nics[0]['MAC'],
                    'IPv4': '27.27.27.3',
                    'IPv6': '2001:2200:82a1:25::365',
                    'network': 'test159450',
                    'bridge': 'br_159450',
                    'bond': 'bond_159450',
                    'vlan': 'vlan_159450',
                    'autcnfg': False
                    }
                 }
                            }

    def tearDown(self):
        super(Story130325, self).tearDown()

    def xml_validate(self, node_url, file_name):
        """
        Description:
        checks that ie xml file created is valid
        """

        # XML TEST ARTIFACT
        # EXPORT CREATED PROFILE ITEM
        network_url = "{0}/network_interfaces".format(node_url)
        self.execute_cli_export_cmd(self.ms_node, network_url, file_name)

        # run xml file and assert that it passes
        cmd = self.xml.get_validate_xml_file_cmd(file_name)
        stdout, stderr, exit_code = self.run_command(self.ms_node, cmd)
        self.assertNotEqual([], stdout)
        self.assertEqual(0, exit_code)
        self.assertEqual([], stderr)

    def chk_applied_autoconf(self, node_to_check, br_name, exp_val):
        """
        Description:
            Function to query the system applied ipv6_autoconf values.
        Args:
            node_to_check (str): Hostname of node to be verified.
            br_name (str): Bridge name to verify.
            exp_val (3-tuple): Values of autoconf, accept_redirects,
             accept_ra to verify
        """
        ipv6_conf_dir = '/proc/sys/net/ipv6/conf'
        stdout = \
            self.get_file_contents(node_to_check,
                                   '{0}/{1}/autoconf'.
                                   format(ipv6_conf_dir, br_name))
        self.assertEqual(exp_val[0], stdout[0])
        stdout = \
            self.get_file_contents(node_to_check,
                                   '{0}/{1}/accept_redirects'.
                                   format(ipv6_conf_dir, br_name))
        self.assertEqual(exp_val[1], stdout[0])
        stdout = \
            self.get_file_contents(node_to_check,
                                   '{0}/{1}/accept_ra'.
                                   format(ipv6_conf_dir, br_name))
        self.assertEqual(exp_val[2], stdout[0])

    def chk_multicast_br_opt_ip6_autcon_on_node(self, node_to_check, dev_name,
                                                ipv6_autoconf, br_prop=None):
        """
        Description:
            Function to query the multicast options values which is set
            in the ifcfg file of the specified bridge, check system
             applied values. Verify IPV6_AUTOCONF applied from ifcfg file
             and system applied values only for devices with assigned IP
             settings.
        Args:
            node_to_check (str): Hostname of node to be verified.
            dev_name (str): suffix file name of the ifcfg file.
            br_prop (str): value to be searched for.
            ipv6_autoconf (str): key specifying type autoconf used
        """
        filepath = test_constants.NETWORK_SCRIPTS_DIR + \
            '/ifcfg-{0}'.format(dev_name)
        stdout = self.get_file_contents(node_to_check, filepath)
        ipv6_autoconf_key = 'IPV6_AUTOCONF='
        enable_ipv6_autoconf = ipv6_autoconf_key + 'yes'
        disable_ipv6_autoconf = ipv6_autoconf_key + 'no'
        if ipv6_autoconf == 'enabled':
            self.assertTrue(self.is_text_in_list(enable_ipv6_autoconf, stdout),
                            'Autoconf have been not enabled correctly')
            if br_prop:
                self.chk_applied_autoconf(node_to_check, dev_name,
                                          ('1', '1', '1'))
        elif ipv6_autoconf == 'disabled':
            self.assertTrue(self.is_text_in_list(disable_ipv6_autoconf,
                                                 stdout),
                            'Autoconf have been not disabled correctly')
            if br_prop:
                self.chk_applied_autoconf(node_to_check, dev_name,
                                          ('0', '0', '0'))
        elif ipv6_autoconf == 'default_ipv4':
            self.assertFalse(self.is_text_in_list(ipv6_autoconf_key,
                                                  stdout),
                             'Autoconf should be not present by default')
            if br_prop:
                self.chk_applied_autoconf(node_to_check, dev_name,
                                          ('1', '0', '0'))
        elif ipv6_autoconf == 'default_ipv6':
            self.assertFalse(self.is_text_in_list(ipv6_autoconf_key,
                                                  stdout),
                             'Autoconf should be not present by default')
            if br_prop:
                self.chk_applied_autoconf(node_to_check, dev_name,
                                          ('1', '1', '1'))
        if br_prop:
            option_str = 'BRIDGING_OPTS="{0}'.format(br_prop)
            self.assertTrue(self.is_text_in_list(option_str, stdout),
                            'The bridge options are not correct')
            br_options = dict(pairs.split('=') for pairs in
                              br_prop.split(' '))

            for option in br_options.keys():
                stdout = \
                    self.get_file_contents(node_to_check,
                                           '/sys/class/net/{0}/bridge/'
                                           '{1}'.
                                           format(dev_name, option))
                self.assertEqual(br_options[option], stdout[0])

    def check_ssh_connectivity_bridge(self, node_to_check, ip_addr):
        """
        Function to test TCP/IP layer 4 connectivity using ssh port.
        Args:
            node_to_check (str): Hostname of node to be verified.
            ip_addr (str): IP address assigned to the bridge.
        """
        stdout = self.run_command(node_to_check,
                                  'echo "QUIT" | nc -w 5 {0} 22'.
                                  format(ip_addr), default_asserts=True)
        self.assertTrue(self.is_text_in_list('OpenSSH_', stdout[0]),
                        'Bridge ip address is not reachable')

    def call_connectivity_check(self):
        """
        Function which calling and executing connectivity check per used
         IP address.
        Args: None
        Returns: None
        """
        for node_path in (self.n1_net_url, self.n2_net_url):
            node_data = self.network_settings[node_path]
            for _, if_opt in node_data.iteritems():
                ipv4_addr = if_opt['IPv4']
                ipv6_addr = if_opt['IPv6']
                host_to_check = if_opt['node_name']
                if if_opt['IPv6']:
                    self.check_ssh_connectivity_bridge(host_to_check,
                                                       ipv6_addr)
                else:
                    self.check_ssh_connectivity_bridge(host_to_check,
                                                       ipv4_addr)

    def add_intf_to_clean_up(self, node_name, eth, vlan, bridge, bond):
        """
        Function which adding used interfaces to teardown.
        Args:
            node_name (str): Hostname of node to be verified.
            eth (str): Ethernet interface name.
            vlan (str): Vlan interface name.
            bridge (str): Bridge interface name.
            bond (str): Bond interface name.
        Returns: None
        """
        intfs_to_clean_up = (eth, vlan, bridge, bond)
        for idx, intrf in enumerate(intfs_to_clean_up):
            if idx == 2:
                self.add_nic_to_cleanup(node_name,
                                        intrf,
                                        is_bridge=True, flush_ip=True)
            elif idx == 3:
                self.add_nic_to_cleanup(node_name,
                                        intrf, is_bond=True)
            else:
                self.add_nic_to_cleanup(node_name,
                                        intrf)

    @attr('manual-test', 'revert', 'story130325_12010_11849',
          'story130325_12010_11849_tc01')
    def test_01_p_add_update_bridge_options_ipv4_ipv6(self):
        """
            @tms_id:
                torf_130325_tc01
            @tms_requirements_id:
                TORF-130325, LITPCDS-12010, LITPCDS-11849, TORF-159450
            @tms_title:
                Specify, deploy and update a bridge and vlan over bridge and
                 bond when querier_multicast, hash_max, hash_elasticity,
                  ipv6_autoconf and multicast_snooping properties are present.
            @tms_description:
                Validate that it is possible to specify, deploy and update a
                 bridge and vlan over bridge and bond when querier_multicast,
                 hash_max, hash_elasticity, ipv6_autoconf
                  and multicast_snooping properties are present.
                 The test will configure three bridges with IPv4, IPv6 and
                 dual stack IP configuration. Note: The test combining
                 the scenarios in order to save KGB execution time.
                 Tested values are min and maximum values
            NOTE: also verifies bug LITPCDS-11849, story LITPCDS-12010 and
                 task TORF-159450
            @tms_test_steps:
            @step: Create a bridge with IPv4 address, a bridge with IPv6
                 address, and bridges with dual stack IP configuration on
                 VLAN over bond. All of the bridges are configured with
                 multicast_querier, multicast_router, hash_max hash_elasticity,
                  ipv6_autoconf and multicast_snooping properties.
            @result: The Litp items are created.
            @step: Create a bridge with dual stack IP configuration on VLAN
                 over bond with default properties and ipv6_autoconf=false
            @result: The Litp items are created.
            @step: Create, run the plan and stop it after the bridge
                 configuration ipv6_autoconf=true is applied.
                 Then recreate the plan
            @result: The applied bridge tasks are not present.
            @step: Rerun the plan.
            @result: The plan is successful.
            @step: Ensure bridge configuration and other settings are applied.
            @result: The config files and applied configuration matching to
                 the litp model.
            @step: Ensure the connectivity on TCP/IP layer 4 level.
            @result: The connection response is successful.
            @step: Validate the generated xml after model export.
            @result: The generated xml has correct structure.
            @step: Update the previously created bridges with new values for
                 multicast_querier, multicast_router, hash_elasticity,
                  hash_max and multicast_snooping properties.
            @result: The Litp items are updated.
            @step: Delete multicast_querier, multicast_router, hash_max,
                 hash_elasticity, ipv6_autoconf and
                  multicast_snooping properties on the bridge.
            @result: The Litp items are updated.
            @step: Create and run plan.
            @result: The plan is successful.
            @step: Ensure bridge configuration and other settings are applied.
            @result: The config files and applied configuration matching to
                 the litp model.
            @step: Ensure the connectivity on TCP/IP layer 4 level.
            @result: The connection response is successful.
            @step: Validate the generated xml after model export.
            @result: The generated xml has correct structure.
            @tms_test_precondition: NA
            @tms_execution_type: Automated
        """
        self.log('info', '# 1.Create a bridge with IPv4 address, a bridge with'
                 ' IPv6 address, and a bridge with dual stack IP configuration'
                 ' on VLAN over bond. All of the bridges are configured with'
                 ' multicast_querier, multicast_router, hash_max and'
                 ' multicast_snooping properties.')
        subnets = ['27.27.27.', 'ipv6', '25.25.25.', '26.26.26.']
        networks_names = ['test159450', 'test130325_2', 'test130325_3',
                          'test130325_1']
        vcs_cluster_url = self.find(self.ms_node, '/deployments',
                                    'vcs-cluster')[-1]
        vcs_host_url = vcs_cluster_url + '/network_hosts/'

        self.log('info', 'Get network path and create test networks')
        networks_path = self.find(self.ms_node, '/infrastructure',
                                  'network', False)[0]
        index = 0
        for subnet, name in zip(subnets, networks_names):
            index += 1
            network_url = networks_path + "/test_network130325" + str(index)
            if subnet == 'ipv6':
                props = 'name=' + name
            else:
                props = "name='{0}' subnet='{1}0/24'".format(name, subnet)
            self.execute_cli_create_cmd(self.ms_node, network_url,
                                        "network", props)
        self.log('info', 'Create test interfaces for IPv4 and IPv6'
                 ' only scenarious')

        br_opts_template = "multicast_snooping={0} multicast_querier={1} " +\
                           "multicast_router={2} hash_max={3} " +\
                           "hash_elasticity={4}"
        eth_props_bond_slave_template = "device_name={0} macaddress={1} " +\
            "master={2} ipv6_autoconf={3}"
        eth_props_br_template = "device_name={0} macaddress={1} bridge={2}"
        bond_props_template = "device_name={0} miimon='100' bridge={1} " +\
                              "ipv6_autoconf={2}"
        br_props_template = "ipaddress={0} device_name={1} " +\
                            "ipv6address='{2}/128' network_name='{3}' " +\
                            "{4} ipv6_autoconf={5}"
        vlan_props_template = "device_name={0} bridge={1} ipv6_autoconf={2}"
        ipv6_only_br_opts = br_opts_template.format('1', '1', '2',
                                                    '262144', '4')
        ipv4_only_br_opts = br_opts_template.format('1', '1', '1',
                                                    '4096', '4')
        dual_stack_br_opts = br_opts_template.format('0', '0', '0',
                                                     '1', '64')
        br_opts_deflt = br_opts_template.format('1', '0', '1',
                                                '512', '4')
        ipv6_only_br_opts_upd = br_opts_template.format('0', '0', '2',
                                                        '131072',
                                                        '4294967295')
        ipv4_only_br_opts_upd = br_opts_template.format('1', '0', '2',
                                                        '32768', '0')
        for node_path in (self.n1_net_url, self.n2_net_url):
            node_data = self.network_settings[node_path]
            ipv4_only_br, \
            ipv6_only_br, \
            n1_dlstack_bond, \
            n1_dlstack_eth, \
            n1_dualstack_br, \
            n1_vlan_name, \
            n2_dlstck_bond, \
            n2_dlstck_eth, \
            n2_dualstack_br, \
            n2_vlan_name = self.extract_network_props(node_path)

            for iface, if_opt in node_data.iteritems():
                node_name = if_opt['node_name']
                nic_name = if_opt['nic_name']
                mac_addr = if_opt['MAC']
                br_name = if_opt['bridge']
                bond_name = if_opt['bond']
                vlan_name = if_opt['vlan']
                ipv4_addr = if_opt['IPv4']
                ipv6_addr = if_opt['IPv6']
                network_id = if_opt['network']
                ipv6_autocfg = if_opt['autcnfg']
                if ipv4_addr and not bond_name:
                    eth_props = eth_props_br_template.format(nic_name,
                                                             mac_addr,
                                                             br_name)
                    br_props = ("device_name='{0}' ipaddress='{1}' "
                                "network_name='{2}' {3}".
                                format(br_name, ipv4_addr,
                                       network_id,
                                       ipv4_only_br_opts))
                    self.execute_cli_create_cmd(self.ms_node,
                                                node_path + iface,
                                                'eth', eth_props)
                    self.execute_cli_create_cmd(self.ms_node,
                                                node_path + br_name,
                                                'bridge', br_props)
                    vcs_host_props = "network_name={0} ip='{1}'".\
                        format(network_id, ipv4_addr)
                    self.execute_cli_create_cmd(self.ms_node,
                                                vcs_host_url +
                                                br_name,
                                                'vcs-network-host',
                                                vcs_host_props)
                    self.add_intf_to_clean_up(node_name, nic_name, vlan_name,
                                              br_name, bond_name)
                elif ipv6_addr and not bond_name:
                    eth_props = eth_props_br_template.format(nic_name,
                                                             mac_addr,
                                                             br_name)
                    br_props = ("device_name='{0}' ipv6address='{1}/128' "
                                "network_name='{2}' {3}".
                                format(br_name, ipv6_addr,
                                       network_id,
                                       ipv6_only_br_opts))
                    self.execute_cli_create_cmd(self.ms_node,
                                                node_path + iface,
                                                'eth', eth_props)
                    self.execute_cli_create_cmd(self.ms_node,
                                                node_path + br_name,
                                                'bridge', br_props)
                    vcs_host_props = "network_name={0} ip='{1}'".\
                        format(network_id, ipv6_addr)
                    self.execute_cli_create_cmd(self.ms_node,
                                                vcs_host_url +
                                                br_name,
                                                'vcs-network-host',
                                                vcs_host_props)
                    self.add_intf_to_clean_up(node_name, nic_name, vlan_name,
                                              br_name, bond_name)
                elif(ipv6_addr and ipv4_addr and
                        ipv6_autocfg):
                    eth_props = eth_props_bond_slave_template.format(nic_name,
                                                                     mac_addr,
                                                                     bond_name,
                                                                     'true')
                    br_props = br_props_template.format(ipv4_addr,
                                                        br_name,
                                                        ipv6_addr,
                                                        network_id,
                                                        dual_stack_br_opts,
                                                        'true')
                    vlan_props = vlan_props_template.format(n1_vlan_name,
                                                            br_name,
                                                            'true')
                    bond_props = bond_props_template.format(bond_name,
                                                            br_name,
                                                            'true')
                    self.execute_cli_create_cmd(self.ms_node,
                                                node_path + iface,
                                                'eth', eth_props)
                    self.execute_cli_create_cmd(self.ms_node,
                                                node_path + br_name,
                                                'bridge', br_props)
                    self.execute_cli_create_cmd(self.ms_node,
                                                node_path + bond_name,
                                                'bond', bond_props)
                    self.execute_cli_create_cmd(self.ms_node,
                                                node_path + vlan_name,
                                                'vlan', vlan_props)
                    vcs_host_props = "network_name={0} ip='{1}'".\
                        format(network_id, ipv4_addr)
                    self.execute_cli_create_cmd(self.ms_node,
                                                vcs_host_url +
                                                br_name,
                                                'vcs-network-host',
                                                vcs_host_props)
                    self.add_intf_to_clean_up(node_name, nic_name, vlan_name,
                                              br_name, bond_name)
                elif(ipv6_addr and ipv4_addr and
                        not ipv6_autocfg):
                    self.log('info', '# 2.Create a bridge with dual stack IP '
                             'configuration on VLAN over bond with default '
                             'properties and ipv6_autoconf=false')
                    eth_props = eth_props_bond_slave_template.format(nic_name,
                                                                     mac_addr,
                                                                     bond_name,
                                                                     'false')
                    br_props = br_props_template.format(ipv4_addr,
                                                        br_name,
                                                        ipv6_addr,
                                                        network_id,
                                                        '',
                                                        'false')
                    vlan_props = vlan_props_template.format(n2_vlan_name,
                                                            br_name,
                                                            'false')
                    bond_props = bond_props_template.format(bond_name,
                                                            br_name,
                                                            'false')
                    self.execute_cli_create_cmd(self.ms_node,
                                                node_path + iface,
                                                'eth', eth_props)
                    self.execute_cli_create_cmd(self.ms_node,
                                                node_path + br_name,
                                                'bridge', br_props)
                    self.execute_cli_create_cmd(self.ms_node,
                                                node_path + bond_name,
                                                'bond', bond_props)
                    self.execute_cli_create_cmd(self.ms_node,
                                                node_path + vlan_name,
                                                'vlan', vlan_props)
                    vcs_host_props = "network_name={0} ip='{1}'".\
                        format(network_id, ipv4_addr)
                    self.execute_cli_create_cmd(self.ms_node,
                                                vcs_host_url +
                                                br_name,
                                                'vcs-network-host',
                                                vcs_host_props)
                    self.add_intf_to_clean_up(node_name, nic_name, vlan_name,
                                              br_name, bond_name)
        self.log('info', '# 3. Create, run the plan and stop it after the '
                 'bridge configuration ipv6_autoconf=true is applied.')
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        phase_2_br3_success = 'Create VCS service group for NIC "br_130325_1"'
        self.assertTrue(self.wait_for_task_state(self.ms_node,
                                                 phase_2_br3_success,
                                                 test_constants.
                                                 PLAN_TASKS_SUCCESS,
                                                 False),
                        'The peer node is is not updated'
                        )
        self.log('info', 'Restart LITP in order to stop the plan '
                 'in selected phase')
        self.restart_litpd_service(self.ms_node)
        self.log('info', 'Recreate the plan and verify the applied bridge'
                 ' configuration is not present.')
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        phase_2_br1_not_present = \
            'Configure bridge "br_130325_1" on node \"{0}\"'.\
            format(self.n1_hostname)
        self.assertEqual(test_constants.CMD_ERROR,
                         self.get_task_state(self.ms_node,
                                             phase_2_br1_not_present,
                                             False))
        self.execute_cli_runplan_cmd(self.ms_node)

        self.assertTrue(self.wait_for_plan_state(self.ms_node,
                                                 test_constants.
                                                 PLAN_COMPLETE),
                        'The plan execution did not succeed'
                        )
        self.log('info', '# 4. Ensure bridge configuration and other settings '
                 'are applied.')
        self.chk_multicast_br_opt_ip6_autcon_on_node(self.n1_hostname,
                                                     ipv6_only_br,
                                                     'default_ipv6',
                                                     ipv6_only_br_opts)
        self.chk_multicast_br_opt_ip6_autcon_on_node(self.n1_hostname,
                                                     ipv4_only_br,
                                                     'default_ipv4',
                                                     ipv4_only_br_opts)
        self.chk_multicast_br_opt_ip6_autcon_on_node(self.n1_hostname,
                                                     n1_dualstack_br,
                                                     'enabled',
                                                     dual_stack_br_opts)
        self.chk_multicast_br_opt_ip6_autcon_on_node(self.n2_hostname,
                                                     n2_dualstack_br,
                                                     'disabled',
                                                     br_opts_deflt)
        self.chk_multicast_br_opt_ip6_autcon_on_node(self.n1_hostname,
                                                     n1_dlstack_eth, 'enabled')
        self.chk_multicast_br_opt_ip6_autcon_on_node(self.n1_hostname,
                                                     n1_dlstack_bond,
                                                     'enabled')
        self.chk_multicast_br_opt_ip6_autcon_on_node(self.n1_hostname,
                                                     n1_vlan_name,
                                                     'enabled')
        self.chk_multicast_br_opt_ip6_autcon_on_node(self.n2_hostname,
                                                     n2_dlstck_eth, 'disabled')
        self.chk_multicast_br_opt_ip6_autcon_on_node(self.n2_hostname,
                                                     n2_dlstck_bond,
                                                     'disabled')
        self.chk_multicast_br_opt_ip6_autcon_on_node(self.n2_hostname,
                                                     n2_vlan_name,
                                                     'disabled')
        self.log('info', '# 5. Ensure the connectivity on TCP/IP '
                 'layer 4 level.')
        self.call_connectivity_check()
        self.log('info', '# 6. Validate the generated xml after model export.')
        self.xml_validate(self.node_urls[0],
                          'xml_expected_install_story130325.xml')
        self.xml_validate(self.node_urls[1],
                          'xml_expected_install_story159450.xml')
        self.log('info', '# 7. Update the previously created bridges with new'
                 ' values for multicast_querier, multicast_router, hash_max'
                 ' and multicast_snooping properties.')
        self.execute_cli_update_cmd(self.ms_node, self.n1_net_url +
                                    ipv6_only_br,
                                    ipv6_only_br_opts_upd)
        self.execute_cli_update_cmd(self.ms_node, self.n1_net_url +
                                    ipv4_only_br,
                                    ipv4_only_br_opts_upd)
        self.execute_cli_update_cmd(self.ms_node, self.n1_net_url +
                                    n1_dualstack_br,
                                    action_del=True,
                                    props=('multicast_snooping '
                                           'multicast_querier '
                                           'multicast_router hash_max '
                                           'hash_elasticity '
                                           'ipv6_autoconf'))
        self.log('info', '# 8. Create and run plan.')
        self.run_and_check_plan(self.ms_node,
                                test_constants.PLAN_COMPLETE, 5)

        self.log('info', '# 9. Ensure bridge configuration and other settings '
                 'are applied.')
        self. \
            chk_multicast_br_opt_ip6_autcon_on_node(self.n1_hostname,
                                                    ipv6_only_br,
                                                    'default_ipv6',
                                                    ipv6_only_br_opts_upd)
        self. \
            chk_multicast_br_opt_ip6_autcon_on_node(self.n1_hostname,
                                                    ipv4_only_br,
                                                    'default_ipv4',
                                                    ipv4_only_br_opts_upd)
        self.chk_multicast_br_opt_ip6_autcon_on_node(self.n1_hostname,
                                                     n1_dualstack_br,
                                                     'default_ipv6',
                                                     br_opts_deflt)
        self.chk_multicast_br_opt_ip6_autcon_on_node(self.n2_hostname,
                                                     n2_dualstack_br,
                                                     'disabled',
                                                     br_opts_deflt)
        self.chk_multicast_br_opt_ip6_autcon_on_node(self.n1_hostname,
                                                     n1_dlstack_eth, 'enabled')
        self.chk_multicast_br_opt_ip6_autcon_on_node(self.n1_hostname,
                                                     n1_dlstack_bond,
                                                     'enabled')
        self.chk_multicast_br_opt_ip6_autcon_on_node(self.n1_hostname,
                                                     n1_vlan_name,
                                                     'enabled')
        self.log('info', '# 10. Ensure the connectivity on TCP/IP '
                 'layer 4 level.')
        self.call_connectivity_check()
        self.log('info', '# 11. Validate the generated xml after '
                 'model export.')
        self.xml_validate(self.node_urls[0],
                          'xml_expected_update_story130325.xml')
        self.xml_validate(self.node_urls[1],
                          'xml_expected_update_story159450.xml')

    def extract_network_props(self, node_path):
        """
        Function extracts network properties from the network settings
            dictionary
        Args:

        Returns: (
               ipv4_only_br
               ipv6_only_br
               n1_dlstack_bond
               n1_dlstack_eth
               n1_dualstack_br
               n1_vlan_name
               n2_dlstck_bond
               n2_dlstck_eth
               n2_dualstack_br
               n2_vlan_name
               )
        """
        if 'if_130325_0' in self.network_settings[node_path]:
            ipv4_only_br = (self.network_settings[node_path]
                            ['if_130325_0']['bridge'])
        if 'if_130325_1' in self.network_settings[node_path]:
            ipv6_only_br = (self.network_settings[node_path]
                            ['if_130325_1']['bridge'])
        if 'if_159450' in self.network_settings[node_path]:
            n1_dlstack_eth = (self.network_settings[node_path]
                              ['if_159450']['nic_name'])
            n1_dualstack_br = (self.network_settings[node_path]
                               ['if_159450']['bridge'])
            n1_dlstack_bond = (self.network_settings[node_path]
                               ['if_159450']['bond'])
            n1_vlan_name = (self.network_settings[node_path]['if_159450']
                            ['bond'] + '.325')
        if 'if_130325_3' in self.network_settings[node_path]:
            n2_dlstck_eth = (self.network_settings[node_path]
                             ['if_130325_3']['nic_name'])
            n2_dualstack_br = (self.network_settings[node_path]
                               ['if_130325_3']['bridge'])
            n2_dlstck_bond = (self.network_settings[node_path]
                              ['if_130325_3']['bond'])
            n2_vlan_name = (self.network_settings[node_path]['if_130325_3']
                            ['bond'] + '.325')
        return ipv4_only_br,\
               ipv6_only_br,\
               n1_dlstack_bond,\
               n1_dlstack_eth,\
               n1_dualstack_br,\
               n1_vlan_name,\
               n2_dlstck_bond,\
               n2_dlstck_eth,\
               n2_dualstack_br,\
               n2_vlan_name
