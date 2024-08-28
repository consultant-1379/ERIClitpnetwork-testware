"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:    April 2017
@author:   Boyan Mihovski
@summary:  Integration
            Agile: TORF-182186
"""

from litp_generic_test import GenericTest, attr
from xml_utils import XMLUtils
from lxml import etree
import test_constants
import network_test_data as data


class Story182186(GenericTest):
    """
    ENM streaming applications need to be able to configure interface buffer
    sizes on the racks running streaming applications. In order to do this,
    the LITP Networking plugin should be updated to have a new optional
    parameter that will allow us to model this value. If the value is not
    modelled, LITP should not set a default.
    """

    def setUp(self):
        super(Story182186, self).setUp()

        self.xml = XMLUtils()

        self.bond_name = data.BOND_NAME_182186

        self.ms_node = self.get_management_node_filename()
        self.peer_nodes = self.get_managed_node_filenames()
        self.node_urls = self.find(self.ms_node, '/deployments', 'node')

        self.n1_hostname = self.get_node_att(self.peer_nodes[0], 'hostname')
        self.n2_hostname = self.get_node_att(self.peer_nodes[1], 'hostname')

        self.n1_free_nics = self.verify_backup_free_nics(
            self.ms_node, self.node_urls[0], required_free_nics=3)
        self.n2_free_nics = self.verify_backup_free_nics(
            self.ms_node, self.node_urls[1], required_free_nics=2)

        self.n1_net_url = self.find(
            self.ms_node, self.node_urls[0],
            "collection-of-network-interface")[0] + '/'
        self.n2_net_url = self.find(
            self.ms_node, self.node_urls[1],
            "collection-of-network-interface")[0] + '/'

        self.vcs_host_url = self.find(
            self.ms_node, '/deployments',
            'collection-of-vcs-network-host')[0] + '/'

        self.networks_path = self.find(self.ms_node, '/infrastructure',
                                       'network', False)[0]

    def tearDown(self):
        super(Story182186, self).tearDown()

    def _get_xml_content_node(self, net_url, file_name):
        """
        Description:
            Creates exported XML file at given LITP path, asserts that it's
            valid and returns a tree of the XML.
        Args:
            net_url (str): LITP network path to export.
            file_name (str): File name of the file to be stored.
        Returns:
            XML content
        """
        self.execute_cli_export_cmd(self.ms_node, net_url, file_name)

        # run xml file and assert that it passes
        cmd = self.xml.get_validate_xml_file_cmd(file_name)
        stdout, _, _ = self.run_command(self.ms_node, cmd,
                                        default_asserts=True)
        self.assertNotEqual([], stdout)

        return etree.fromstring(''.join(stdout))

    def _xml_validate(self, xml_content, eth_dev, ring_values=None,
                      rx_only=None, tx_only=None):
        """
        Description:
            Asserts that expected rx and tx values are in given XML file. Only
            one of the ring_values rx_only and tx_only  should be set at a
            time.
        Args:
            xml_content (str): The content of xml to check.
            eth_dev (str): suffix file name of the ifcfg file.
        KwArgs:
            ring_values (tuple): Values of predefined values for rx and
                                 tx buffer size. Default value is None.
            rx_only (str): The value of rx buffer only. Default value is None.
            tx_only (str): The value of tx buffer only. Default value is None.
        """
        rx_pattern = ".//*[@id='{0}']/rx_ring_buffer/text()"
        tx_pattern = ".//*[@id='{0}']/tx_ring_buffer/text()"
        if ring_values:
            self.assertEqual(ring_values[0],
                             xml_content.xpath(rx_pattern.format(eth_dev))[0])
            self.assertEqual(ring_values[1],
                             xml_content.xpath(tx_pattern.format(eth_dev))[0])

        elif rx_only:
            self.assertEqual(rx_only,
                             xml_content.xpath(rx_pattern.format(eth_dev))[0])
        # check tx buffer only value is present
        else:
            self.assertEqual(tx_only,
                             xml_content.xpath(tx_pattern.format(eth_dev))[0])

    def _chk_ring_buffer(self, node_to_check, dev_name, ring_values=None,
                         rx_only=None, tx_only=None, act_rng_vals=None,
                         deleted=False):
        """
        Description:
            Function to query the ring buffer options values which is set
            in the ifcfg file of the specified eth NIC, check system
            applied values. Verify ETHTOOL_OPTS applied from ifcfg file
            and system applied values only for devices with assigned IP
            settings.
        Args:
            node_to_check (str): Hostname of node to be verified.
            dev_name (str): suffix file name of the ifcfg file.
        KwArgs:
            ring_values (tuple): value to be searched for when rx and tx
                 buffers are present. Default value is None.
            rx_only (str): Rx buffer value to be check. Default value is None.
            tx_only (str): Tx buffer value to be check. Default value is None.
            act_rng_vals (tuple): Buffer values default for the system if
                                  more or less are applied. Default value is
                                  None.
            deleted (bool): Switch to check deleted buffer properties. Default
                            value is False.

        """
        filepath = "{0}/ifcfg-{1}".format(
            test_constants.NETWORK_SCRIPTS_DIR, dev_name)
        stdout = self.get_file_contents(node_to_check, filepath)

        if ring_values and not deleted:
            self.assertTrue(self.is_text_in_list(
                data.RING_BUFFER_KEY + data.RING_VALUES_PROPS.format(
                    dev_name, ring_values[0], dev_name, ring_values[1]),
                stdout), 'Ring buffer values are not exposed correctly')

            ethtool_results = self._check_ring_parameters(node_to_check,
                                                          dev_name)
            if act_rng_vals:
                self.assertEquals(act_rng_vals[0], ethtool_results['RX'])
                self.assertEquals(act_rng_vals[1], ethtool_results['TX'])
            else:
                self.assertEquals(ring_values[0], ethtool_results['RX'])
                self.assertEquals(ring_values[1], ethtool_results['TX'])

        elif rx_only and not deleted:
            self.assertTrue(self.is_text_in_list(
                data.RING_BUFFER_KEY + data.RX_ONLY_PROPS.format(
                    dev_name, rx_only), stdout),
                'Ring buffer value for rx only is not exposed correctly')

            ethtool_results = self._check_ring_parameters(node_to_check,
                                                          dev_name)
            if act_rng_vals:
                self.assertEquals(act_rng_vals, ethtool_results['RX'])
            else:
                self.assertEquals(rx_only, ethtool_results['RX'])
        # check tx buffer only value is present
        elif not deleted:
            self.assertTrue(self.is_text_in_list(
                data.RING_BUFFER_KEY + data.TX_ONLY_PROPS.format(
                    dev_name, tx_only), stdout),
                'Ring buffer value for tx only is not exposed correctly')

            ethtool_results = self._check_ring_parameters(node_to_check,
                                                          dev_name)
            if act_rng_vals:
                self.assertEquals(act_rng_vals, ethtool_results['TX'])
            else:
                self.assertEquals(tx_only, ethtool_results['TX'])

        else:
            self.assertFalse(self.is_text_in_list(
                data.RING_BUFFER_KEY + data.RING_VALUES_PROPS.format(
                    dev_name, ring_values[0], dev_name, ring_values[1]),
                stdout), 'Ring buffer values are still present')

    def _check_ssh_connectivity(self, node_to_check, ip_addr):
        """
        Test TCP/IP layer 4 connectivity.
        Args:
            node_to_check (str): Hostname of node to be verified.
            ip_addr (str): IP address assigned to the bridge.
        """
        cmd = '{0} "QUIT" | nc -w 5 {1} 22'.format(test_constants.ECHO_PATH,
                                                   ip_addr)
        stdout = self.run_command(node_to_check, cmd, default_asserts=True)
        self.assertTrue(self.is_text_in_list('OpenSSH_', stdout[0]),
                        'The IP address is not reachable')

    def _set_ring_parameters(self, node_to_set, intrf, tx_val):
        """
        Set tx_ring_buffer to the
        specified interface using the ethtools cmd.
        Args:
            node_to_set (str): Hostname of node to be verified.
            intrf (str): Interface to be checked.
            tx_val (str): value to set TX too
        """
        cmd = \
            "{0} -G {1} tx {2}".format(test_constants.ETHTOOL_PATH,
                                      intrf, tx_val)

        self.run_command(node_to_set, cmd, su_root=True)

    def _check_ring_parameters(self, node_to_check, intrf):
        """
        Checks the applied values of rx_ring_buffer and tx_ring_buffer to the
        specified interface using the ethtools cmd.
        Args:
            node_to_check (str): Hostname of node to be verified.
            intrf (str): Interface to be checked.
        Returns:
            (dict): RX and TX values
        """
        cmd = \
            "{0} -g  {1} |head -n 11| {2} \"RX:|TX:\" | awk 'NR>2 " \
            "{{print $1 $2}}'".format(test_constants.ETHTOOL_PATH,
                                      intrf, test_constants.EGREP_PATH)

        stdout, _, _ = self.run_command(node_to_check, cmd,
                                        default_asserts=True)

        ethtool_values = dict([ele.split(':') for ele in stdout])

        return ethtool_values

    def _create_network_devices(self, ms_node, network_settings):
        """
        Creates network items.
            ms_node (str):  The name of the management node to execute command
                            on.
            network_settings (dict) : Contains the node urls and interface
                                      props.
        """
        for network_path, if_props in network_settings.iteritems():
            for prop in if_props:
                for iface, value in prop.iteritems():
                    node_name = value['node_name']
                    nic_name = value['nic_name']
                    mac_addr = value['MAC']
                    br_name = value['bridge']
                    bond_name = value['bond']
                    vlan_name = value['vlan']
                    ipv4_addr = value['IPv4']
                    ipv6_addr = value['IPv6']
                    network_id = value['network']
                    network_iface_path = network_path + iface

                    eth_props = "device_name={0} macaddress={1} ".format(
                        nic_name, mac_addr)

                    if ipv4_addr and not bond_name and not br_name:
                        eth_props += "network_name={0} ipaddress={1}" \
                                    " rx_ring_buffer='512'".format(
                                        network_id, ipv4_addr)

                        vcs_host_props = "network_name={0} ip={1}".format(
                            network_id, ipv4_addr)

                        self.execute_cli_create_cmd(
                            ms_node, network_iface_path, 'eth', eth_props)

                        self.execute_cli_create_cmd(ms_node,
                                                    self.vcs_host_url +
                                                    iface,
                                                    'vcs-network-host',
                                                    vcs_host_props)
                    elif ipv4_addr and not bond_name:
                        eth_props += "bridge={0} rx_ring_buffer='1024' " \
                                     "tx_ring_buffer='512'".format(br_name)

                        br_props = "ipaddress={0} device_name={1} " \
                                   "network_name={2}".format(
                                    ipv4_addr, br_name, network_id)

                        vcs_host_props = "network_name={0} ip={1}".format(
                            network_id, ipv4_addr)

                        self.execute_cli_create_cmd(
                            ms_node, network_iface_path, 'eth', eth_props)

                        self.execute_cli_create_cmd(ms_node,
                                                    network_path + br_name,
                                                    'bridge', br_props)
                        self.execute_cli_create_cmd(ms_node,
                                                    self.vcs_host_url +
                                                    br_name,
                                                    'vcs-network-host',
                                                    vcs_host_props)

                    elif ipv6_addr and not bond_name:
                        eth_props += "rx_ring_buffer='684'"

                        vlan_props = "device_name={0} ipv6address={1} " \
                                     "network_name={2} ipaddress={3}".format(
                                        nic_name + '.325', ipv6_addr,
                                        ipv4_addr, network_id)

                        vcs_host_props = "network_name={0} ip={1}".format(
                            network_id, ipv6_addr)

                        self.execute_cli_create_cmd(
                            ms_node, network_iface_path, 'eth', eth_props)

                        self.execute_cli_create_cmd(ms_node,
                                                    network_path + vlan_name,
                                                    'vlan', vlan_props)
                        self.execute_cli_create_cmd(ms_node,
                                                    self.vcs_host_url +
                                                    vlan_name,
                                                    'vcs-network-host',
                                                    vcs_host_props)
                    elif ipv6_addr and ipv4_addr:
                        eth_props += "master={0} rx_ring_buffer='1' " \
                                    "tx_ring_buffer='2147483646'".format(
                                        bond_name)

                        bridge_props = "device_name={0} network_name={1} " \
                                       "ipaddress={2} ipv6address={3}" \
                            .format(br_name, network_id, ipv4_addr, ipv6_addr)

                        bond_props = "device_name={0} bridge={1}".format(
                                bond_name, br_name)

                        vlan_props_dual = "device_name={0} bridge={1}".format(
                                bond_name + '.325', br_name)

                        vcs_host_props = "network_name={0} ip={1}".format(
                            network_id, ipv4_addr)

                        self.execute_cli_create_cmd(
                            ms_node, network_iface_path, 'eth', eth_props)

                        self.execute_cli_create_cmd(ms_node,
                                                    network_path + br_name,
                                                    'bridge', bridge_props)
                        self.execute_cli_create_cmd(ms_node,
                                                    network_path + bond_name,
                                                    'bond', bond_props)
                        self.execute_cli_create_cmd(ms_node,
                                                    network_path + vlan_name,
                                                    'vlan', vlan_props_dual)
                        self.execute_cli_create_cmd(ms_node,
                                                    self.vcs_host_url +
                                                    br_name,
                                                    'vcs-network-host',
                                                    vcs_host_props)
                    else:
                        eth_props += "master={0} rx_ring_buffer='0' " \
                                    "tx_ring_buffer='2147483647'".format(
                                        bond_name)

                        self.execute_cli_create_cmd(
                            ms_node, network_iface_path, 'eth', eth_props)

                    self.add_nic_to_cleanup(node_name, nic_name)
                    self.add_nic_to_cleanup(node_name, vlan_name)
                    self.add_nic_to_cleanup(node_name, bond_name, is_bond=True)
                    self.add_nic_to_cleanup(node_name, br_name, is_bridge=True,
                                            flush_ip=True)

    def _update_model(self, ms_node, network_settings):
        """
        Updates the previously created network items with new values for
        rx_ring_buffer and tx_ring_buffer properties.
        Args:
            ms_node (str):  The name of the management node to execute command
                            on.
            network_settings (dict) : Contains the node urls and interface
                                      props.
        """
        for network_path, if_props in network_settings.iteritems():
            for prop in if_props:
                for iface, value in prop.iteritems():
                    bond_name = value['bond']
                    ipv4_addr = value['IPv4']
                    ipv6_addr = value['IPv6']
                    br_name = value['bridge']
                    network_prop_path = network_path + iface

                    delete = False
                    if ipv4_addr and not bond_name and not br_name:
                        props = " rx_ring_buffer='1024' tx_ring_buffer='512'"

                    elif ipv4_addr and not bond_name:
                        props = 'rx_ring_buffer tx_ring_buffer'
                        delete = True

                    elif ipv6_addr and not bond_name:
                        props = " rx_ring_buffer='400'"

                    elif ipv6_addr and ipv4_addr:
                        props = " tx_ring_buffer='21474'"

                    else:
                        props = " rx_ring_buffer='2147483647' " \
                                "tx_ring_buffer='0'"

                    self.execute_cli_update_cmd(
                        ms_node, network_prop_path, props=props,
                        action_del=delete)

    def _check_values_applied(self, network_settings):
        """
        Verifies expected values defined in the model were applied
        Args:
            network_settings (dict) : Contains the node urls and interface
                                      props.
        """
        for network_path, if_props in network_settings.iteritems():
            xml_content = self._get_xml_content_node(network_path,
                                                     'xml_install_'
                                                     'story182186.xml')
            for prop in if_props:
                for net_prop, value in prop.iteritems():
                    bond_name = value['bond']
                    ipv4_addr = value['IPv4']
                    ipv6_addr = value['IPv6']
                    br_name = value['bridge']
                    host_name = value['node_name']
                    nic_name = value['nic_name']

                    if ipv4_addr and not bond_name and not br_name:
                        self._xml_validate(
                            xml_content, net_prop,
                            rx_only=data.ETH_ONLY_BUFFER_VALUE)
                        self._chk_ring_buffer(
                            host_name, nic_name,
                            rx_only=data.ETH_ONLY_BUFFER_VALUE)

                        self._check_ssh_connectivity(host_name, ipv4_addr)

                    elif ipv4_addr and not bond_name:
                        self._xml_validate(
                            xml_content, net_prop,
                            ring_values=data.BR_ETH_BUFFER_VALUES)
                        self._chk_ring_buffer(
                            host_name, nic_name,
                            ring_values=data.BR_ETH_BUFFER_VALUES)

                        self._check_ssh_connectivity(host_name, ipv4_addr)

                    elif ipv6_addr and not bond_name:
                        self._xml_validate(
                            xml_content, net_prop,
                            tx_only=data.VLAN_ETH_BUFFER_VALUE)
                        self._chk_ring_buffer(
                            host_name, nic_name,
                            tx_only=data.VLAN_ETH_BUFFER_VALUE)

                        self._check_ssh_connectivity(host_name, ipv6_addr)

                    elif ipv6_addr and ipv4_addr:
                        self._xml_validate(
                            xml_content, net_prop,
                            ring_values=data.BND_SEC_SLV_BUF_VALUES)
                        self._chk_ring_buffer(
                            host_name, nic_name,
                            ring_values=data.BND_SEC_SLV_BUF_VALUES,
                            act_rng_vals=(data.DEFAULT_MIN_BUFFER_VALUE,
                                          data.DEFAULT_MAX_BUFFER_VALUE))

                        self._check_ssh_connectivity(host_name, ipv4_addr)
                        self._check_ssh_connectivity(host_name, ipv6_addr)

                    else:
                        self._xml_validate(
                            xml_content, net_prop,
                            ring_values=data.BND_FIRST_SLV_BUF_VALUES)
                        self._chk_ring_buffer(
                            host_name, nic_name,
                            ring_values=data.BND_FIRST_SLV_BUF_VALUES,
                            act_rng_vals=(data.DEFAULT_MIN_BUFFER_VALUE,
                                          data.DEFAULT_MAX_BUFFER_VALUE))

    def _validate_after_update(self, network_settings):
        """
        Verifies updates to network items were applied.
        Args:
            network_settings (dict) : Contains the node urls and interface
                                      props.
        """
        for network_path, if_props in network_settings.iteritems():
            xml_content = self._get_xml_content_node(network_path,
                                                     'xml_update_'
                                                     'story182186.xml')
            for prop in if_props:
                for net_prop, value in prop.iteritems():
                    bond_name = value['bond']
                    ipv4_addr = value['IPv4']
                    ipv6_addr = value['IPv6']
                    br_name = value['bridge']
                    host_name = value['node_name']
                    nic_name = value['nic_name']

                    if ipv4_addr and not bond_name and not br_name:
                        self._xml_validate(
                            xml_content, net_prop,
                            ring_values=data.UPD_ETH_ONLY_BUFFER_VALUES)
                        self._chk_ring_buffer(
                            host_name, nic_name,
                            ring_values=data.UPD_ETH_ONLY_BUFFER_VALUES)
                        self._check_ssh_connectivity(host_name, ipv4_addr)
                    elif ipv4_addr and not bond_name:
                        self._chk_ring_buffer(
                            host_name, nic_name,
                            ring_values=data.BR_ETH_BUFFER_VALUES,
                            deleted=True)
                        self._check_ssh_connectivity(host_name, ipv4_addr)
                    elif ipv6_addr and not bond_name:
                        self._xml_validate(
                            xml_content, net_prop,
                            rx_only=data.UPD_VLAN_ETH_BUFFER_VALUE)
                        self._chk_ring_buffer(
                            host_name, nic_name,
                            rx_only=data.UPD_VLAN_ETH_BUFFER_VALUE)
                        self._check_ssh_connectivity(host_name, ipv6_addr)
                    elif ipv6_addr and ipv4_addr:
                        self._xml_validate(
                            xml_content, net_prop,
                            tx_only=data.UPD_BND_SEC_SLAVE_BUF_VALS)
                        self._chk_ring_buffer(
                            host_name, nic_name,
                            ring_values=('1', data.UPD_BND_SEC_SLAVE_BUF_VALS),
                            act_rng_vals=(data.DEFAULT_MIN_BUFFER_VALUE,
                                          data.DEFAULT_MAX_BUFFER_VALUE))

                        self._check_ssh_connectivity(host_name, ipv4_addr)
                        self._check_ssh_connectivity(host_name, ipv6_addr)
                    else:
                        self._xml_validate(
                            xml_content, net_prop,
                            ring_values=data.UPD_BND_FIRST_SLV_BUF_VALUES)
                        self._chk_ring_buffer(
                            host_name, nic_name,
                            ring_values=data.UPD_BND_FIRST_SLV_BUF_VALUES,
                            act_rng_vals=(data.DEFAULT_MIN_BUFFER_VALUE,
                                          data.DEFAULT_MIN_BUFFER_VALUE))

    @attr('all', 'revert', 'story182186', 'story182186_tc02')
    def test_02_p_check_boundary_values_and_idempotency(self):
        """
        @tms_id: torf_182186_tc01
        @tms_requirements_id: TORF-182186
        @tms_title: Specify, deploy and update ethernet NIC, bond, bridge
                    and vlan interfaces when rx_ring_buffer and
                    tx_ring_buffer properties are specified.
        @tms_description: With an already up and running LITP environment,
                          create 3 NICs using the two boundary values and
                          an average valid value for both properties. Then,
                          update the properties for one NIC. Check
                          idempotency forcing both creation and update
                          plans to fail and rerun them.
        @tms_test_steps:
            @step: Create network items.
            @result: Items created.
            @step: Create a ethernet NIC with IPv4 address, a bridge with
                   IPv6 address, and bond with dual stack IP configuration
                   on VLAN over bond. All of the adapters are configured
                   with rx_ring_buffer and tx_ring_buffer properties.
            @result: Items created
            @step: Run and stop plan when bond is configured.
            @result: Plan is stopped.
            @step: Restart LITP to stop plan.
            @result: LITP is restarted and plan stops successfully.
            @step: Re-create plan and verify eth item not present in new
                   plan.
            @result: Eth item is not present in the plan.
            @step: Rerun the plan.
            @result: Plan is successful.
            @step: Verify values are applied and test TCP/IP connectivity.
            @result: Items are updated and connection response is
                    successful.
            @step: Update previous values for rx_ring_buffer.
            @result: Items are updated.
            @step: Create and run plan.
            @result: Plan is successful.
            @step: Stop plan after eth configuration has completed. Restart
                   LITP to stop plan.
            @result: Plan is stopped and LITP restarts successfully.
            @step: Re-create plan and verify eth config is not in new plan.
            @result: Eth config is not in new plan.
            @step: Re-run the plan.
            @result: Plan is successful.
            @step: Verify updates were applied and test TCP/IP
                   connectivity.
            @result: Items are updated and connection response is
                     successful.
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log('info', '# 1. Create network items.')
        for interface, props in data.NETWORK_PROPS_182186.iteritems():
            interface_path = self.networks_path + interface
            self.execute_cli_create_cmd(
                self.ms_node, interface_path, 'network',
                'name={0} subnet={1}'.format(props["net_name"],
                                             props["subnet"]))

        iface0 = data.INTERFACE0
        interface_name = data.INTERFACE0.keys()[0]
        iface0[interface_name]["node_name"] = self.n1_hostname
        iface0[interface_name]["nic_name"] = \
            self.n1_free_nics[0]["NAME"]
        iface0[interface_name]["MAC"] = self.n1_free_nics[0]["MAC"]
        self._set_ring_parameters(iface0[interface_name]["node_name"],
                                  iface0[interface_name]["nic_name"],
                                  data.DEFAULT_MAX_BUFFER_VALUE)

        iface1 = data.INTERFACE1
        interface_name = data.INTERFACE1.keys()[0]
        iface1[interface_name]["node_name"] = self.n1_hostname
        iface1[interface_name]["nic_name"] = \
            self.n1_free_nics[1]["NAME"]
        iface1[interface_name]["MAC"] = self.n1_free_nics[1]["MAC"]
        self._set_ring_parameters(iface1[interface_name]["node_name"],
                                  iface1[interface_name]["nic_name"],
                                  data.DEFAULT_MAX_BUFFER_VALUE)

        iface2 = data.INTERFACE2
        interface_name = data.INTERFACE2.keys()[0]
        iface2[interface_name]["node_name"] = self.n1_hostname
        iface2[interface_name]["nic_name"] = \
            self.n1_free_nics[2]["NAME"]
        iface2[interface_name]["MAC"] = self.n1_free_nics[2]["MAC"]
        self._set_ring_parameters(iface2[interface_name]["node_name"],
                                  iface2[interface_name]["nic_name"],
                                  data.DEFAULT_MAX_BUFFER_VALUE)

        iface3 = data.INTERFACE3
        interface_name = data.INTERFACE3.keys()[0]
        iface3[interface_name]["node_name"] = self.n2_hostname
        iface3[interface_name]["nic_name"] = \
            self.n2_free_nics[0]["NAME"]
        iface3[interface_name]["MAC"] = self.n2_free_nics[0]["MAC"]
        self._set_ring_parameters(iface3[interface_name]["node_name"],
                                  iface3[interface_name]["nic_name"],
                                  data.DEFAULT_MAX_BUFFER_VALUE)

        iface4 = data.INTERFACE4
        interface_name = data.INTERFACE4.keys()[0]
        iface4[interface_name]["node_name"] = self.n2_hostname
        iface4[interface_name]["nic_name"] = \
            self.n2_free_nics[1]["NAME"]
        iface4[interface_name]["MAC"] = self.n2_free_nics[1]["MAC"]
        self._set_ring_parameters(iface4[interface_name]["node_name"],
                                  iface4[interface_name]["nic_name"],
                                  data.DEFAULT_MAX_BUFFER_VALUE)

        network_settings = {self.n1_net_url: data.NODE1_INTERFACES,
                            self.n2_net_url: data.NODE2_INTERFACES}

        self.log('info', '# 2. Create a ethernet NIC with IPv4 address, '
                         'a bridge with IPv6 address, and bond with dual '
                         'stack IP configuration on VLAN over bond. All of '
                         'the adapters are configured with rx_ring_buffer '
                         'and tx_ring_buffer properties.')
        self._create_network_devices(self.ms_node, network_settings)

        self.log('info', '# 3. Run and stop plan when bond is configured.')
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        self.log('info', '# 4. Restart litp to stop plan.')
        task = 'Configure vlan "{0}" on node'.format(self.bond_name)

        self.restart_litpd_when_task_state(
            self.ms_node, task, timeout_mins=5, task_state=0)

        self.log('info', '# 5. Re-create plan and verify eth item not present'
                         ' in new plan.')
        self.execute_cli_createplan_cmd(self.ms_node)

        stdout, _, _ = self.execute_cli_showplan_cmd(self.ms_node)
        self.assertNotEquals([], stdout)
        interface_name = data.INTERFACE1.keys()[0]
        task = 'Configure eth \"{0}\" on node \"{1}\"'.format(
                iface1[interface_name]["nic_name"],
                self.n1_hostname)

        task_error_msg = 'Previously successful task "{0}" found in ' \
                         'recreated plan:\n\n"{1}"'
        self.assertFalse(self.is_text_in_list(task, stdout),
                         task_error_msg.format(task, stdout))

        self.log('info', '# 6. Rerun the plan.')
        self.execute_cli_runplan_cmd(self.ms_node)
        plan_error_msg = 'The plan execution did not succeed'
        self.assertTrue(
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     timeout_mins=5),
            plan_error_msg)

        self.log('info', '# 7. Verify values are applied and test TCP/IP '
                         'connectivity.')
        self._check_values_applied(network_settings)

        self.log('info', '# 8. Update the previously created interfaces with'
                         ' new values for rx_ring_buffer and tx_ring_buffer'
                         ' properties.')
        self._update_model(self.ms_node, network_settings)

        self.log('info', '# 9. Create and run plan.')
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        self.log('info', '# 10. Stop plan after eth configuration has '
                         'completed. Restart LITP to stop plan.')
        interface_name = data.INTERFACE0.keys()[0]
        task = 'Update eth \"{0}\" on node \"{1}\"'.format(
            iface0[interface_name]["nic_name"], self.n1_hostname)

        self.restart_litpd_when_task_state(
            self.ms_node, task, timeout_mins=5, task_state=0)

        self.log('info', '# 11. Re-create plan and verify eth config is not in'
                         ' new plan.')
        self.execute_cli_createplan_cmd(self.ms_node)

        stdout, _, _ = self.execute_cli_showplan_cmd(self.ms_node)
        self.assertNotEquals([], stdout)
        self.assertFalse(self.is_text_in_list(task, stdout),
                         task_error_msg.format(task, stdout))

        self.log('info', '# 12. Re-run the plan.')
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     timeout_mins=5),
            plan_error_msg)

        self.log('info', '# 13. Verify updates were applied and test TCP/IP '
                         'connectivity.')
        self._validate_after_update(network_settings)
