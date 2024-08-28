"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     November 2014
@author:    Carlos Novo, Kieran Duggan, Boyan Mihovski
@summary:   Integration
            Agile: STORY-6629
"""
from xml_utils import XMLUtils
from litp_generic_test import GenericTest, attr
import test_constants as const
import network_test_data as data


class Story6629(GenericTest):
    """
    As a LITP administrator I want to configure a bridge that uses a
    configured bond or vlan on the host as an underlying interface,
    so that I can connect guest VMs to external networks.
    """
    test_node_if1 = None
    test_node_if2 = None
    test_n1_if1 = None
    test_ms_if1 = None
    test_node2_if1 = None

    def setUp(self):
        """
        Runs before every single test
        """
        # 1. Call super class setup
        super(Story6629, self).setUp()

        # 2. Set up variables used in the test
        self.ms_node = self.get_management_node_filename()
        self.managed_nodes = self.get_managed_node_filenames()
        self.all_nodes = [self.ms_node] + self.managed_nodes

        self.vcs_cluster_url = \
            self.find(self.ms_node, "/deployments", "vcs-cluster")[-1]

        self.ms_url = "/ms"
        self.node_urls = self.find(self.ms_node, self.vcs_cluster_url, "node")

        self.network_host_url = self.find(self.ms_node, self.vcs_cluster_url,
                                          "collection-of-vcs-network-host")[-1]

        self.networks_path = self.find(self.ms_node, "/infrastructure",
                                       "network", False)[0]

        self.ms_net_url = self.find(self.ms_node, self.ms_url,
                                    "collection-of-network-interface")[0]
        self.node1_net_url = self.find(self.ms_node, self.node_urls[0],
                                       "collection-of-network-interface")[0]
        self.node2_net_url = self.find(self.ms_node, self.node_urls[1],
                                       "collection-of-network-interface")[0]

        self.xml = XMLUtils()

    def tearDown(self):
        """
        Run after each test and performs the following:
        """
        super(Story6629, self).tearDown()

    def create_vcs_net_host(self, url_id, host_props):
        """
        Description:
            Function to create a vcs network host with the provided
            properties.
        Args:
            url_id (str): ID of the url
            host_props (str): Properties to be used in the creation.
        """
        net_host_url = self.network_host_url + "/" + url_id
        self.execute_cli_create_cmd(self.ms_node, net_host_url,
                                    "vcs-network-host", host_props)

    def chk_applied_bond_prim(self, node_to_check, bnd_name, exp_val):
        """
        Description:
            Assert primary and primary_select bond files have given values on
            specified node
        Args:
            node_to_check (str): Hostname of node to be verified.
            bnd_name (str): Bond name to verify.
            exp_val (2-tuple): primary_reselect value to verify
        """
        bnd_sys_class = '/sys/class/net/' + bnd_name + '/bonding/'
        file_content = self.get_file_contents(
            node_to_check, bnd_sys_class + 'primary_reselect')
        self.assertEqual(exp_val[1], file_content[0])

    def check_ssh_connectivity_bridge(self, node_to_check, ips_to_check):
        """
        Function to test TCP/IP layer 4 connectivity using ssh port.
        Args:
            node_to_check (str): Hostname of node to be verified.
            ips_to_check (list): IP addresses assigned to the bridges.
        """
        for ip_addr in ips_to_check:
            command = '{0} "QUIT" | nc -w 5 {1} 22'.format(const.ECHO_PATH,
                                                           ip_addr)
            stdout = self.run_command(node_to_check, command,
                                      default_asserts=True)[0]

            self.assertTrue(self.is_text_in_list('OpenSSH_', stdout),
                            'Bridge IP address ({0}) is not reachable'.format(
                                                                    ip_addr))

    def xml_validate(self, node_url, file_name):
        """
        Description:
            Asserts that XML export of network interface model on given node
            is valid.
        Args:
            node_url(str): Modeled node to export the network_interface path of
            file_name(str): Name of XML file to create
        """
        network_url = self.find(self.ms_node, node_url,
                                "collection-of-network-interface")[0]
        self.execute_cli_export_cmd(self.ms_node, network_url, file_name)

        cmd = self.xml.get_validate_xml_file_cmd(file_name)
        stdout = self.run_command(self.ms_node, cmd, default_asserts=True)[0]
        self.assertNotEqual([], stdout)

    def create_network_items(self, props):
        """
        Description:
            Creates a number of network items from the provided list of props
        Args:
            props(list): A list of dictionaries that each contain the
            information needed
        """
        for prop in props:
            self.execute_cli_create_cmd(self.ms_node, prop["url"],
                                        prop["type"], prop["props"])

    def check_ifcfg(self, node, path, props, negative_props=None):
        """
        Description:
            Checks the contents of the bridge ifcfg file for the specified
            information
        Args:
            node(str): Node the ifcfg file is on
            path(str): Path to the ifcfg file to check
            props(list): List of properties to ensure exist in the ifcfg file
        KwArgs:
            negative_props(list): List of properties to ensure don't exist in
                the ifcfg file. Defaults to None
        """
        dir_contents = self.list_dir_contents(node, path)
        self.assertNotEqual([], dir_contents)

        stdout = self.get_file_contents(node, path)
        for prop in props:
            self.assertTrue(self.is_text_in_list(prop, stdout),
                            "'{0}' was not found in ifcfg file".format(prop))
        if negative_props:
            for prop in negative_props:
                self.assertFalse(self.is_text_in_list(prop, stdout),
                                 "'{0}' was found in ifcfg file".format(prop))

    @attr('all', 'revert', 'story6629', 'story6629_tc01')
    def test_01_n_create_bridged_vlan_remove_bridge(self):
        """
        @tms_id: litpcds_6629_tc01
        @tms_requirements_id: LITPCDS-6629
        @tms_title: create bridged vlan remove bridge
        @tms_description: Verify removing a bridge item results in an error
            at create plan
        @tms_test_steps:
            @step: Create network item under 'infrastructure'
            @result: Item created
            @step: Create eth item on ms, node1 and node2
            @result: Item created
            @step: Create bridge item on ms, node1 and node2
            @result: Item created
            @step: Create vlan item on ms, node1 and node2
            @result: Item created
            @step: Create and run plan
            @result: Plan executes successfully
            @step: Ping ms, node1 and node2
            @result: Ms, node1 and node2 are pingable
            @step: Execute "cat ifcfg" on ms, node1 and node2 on each vlan
                and bridge
            @result: Ms, node1 and node2 contain correct information
            @step: Remove bridge items from ms, node1 and node2
            @result: Items set to ForRemoval
            @step: Create and run plan
            @result: Error thrown: ValidationError
            @result: Is not a valid bridge as it has state 'ForRemoval'
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log('info', "1. Create deployment")
        self.test_ms_if1 = self.verify_backup_free_nics(
            self.ms_node, self.ms_url)[0]
        self.test_node_if1 = self.verify_backup_free_nics(
            self.ms_node, self.node_urls[0])[0]
        self.test_node2_if1 = self.verify_backup_free_nics(
            self.ms_node, self.node_urls[1])[0]

        network_url = self.networks_path + "/test_network2069"
        props = "name='test2' subnet='10.10.10.0/24'"
        self.execute_cli_create_cmd(self.ms_node, network_url,
                                    "network", props)

        # Store bridge urls as they are needed at the end of the test
        bridge_url_ms = self.ms_net_url + "/br629"
        bridge_url_n1 = self.node1_net_url + "/br629"
        bridge_url_n2 = self.node2_net_url + "/br629"
        net_props = [
            # ms
            {
                "type": "eth",
                "url": self.ms_net_url + "/eth629",
                "props": "device_name='{0}' macaddress='{1}'".format(
                                                    self.test_ms_if1["NAME"],
                                                    self.test_ms_if1["MAC"])
            },
            {
                "type": "bridge",
                "url": bridge_url_ms,
                "props": "ipaddress='10.10.10.21' device_name='br6629' \
                        ipv6address='fe05::1' network_name='test2'"
            },
            {
                "type": "vlan",
                "url": self.ms_net_url + "/vlan629",
                "props": "device_name='{0}.629' bridge='br6629'".format(
                                                    self.test_ms_if1["NAME"])
            },
            # node1
            {
                "type": "eth",
                "url": self.node1_net_url + "/eth_629",
                "props": "device_name='{0}' macaddress='{1}'".format(
                                                    self.test_node_if1["NAME"],
                                                    self.test_node_if1["MAC"])
            },
            {
                "type": "bridge",
                "url": bridge_url_n1,
                "props": "ipaddress='10.10.10.22' device_name='br6629' \
                            ipv6address='fe05::2' network_name='test2'"
            },
            {
                "type": "vlan",
                "url": self.node1_net_url + "/vlan629",
                "props": "device_name='{0}.629' bridge='br6629'".format(
                                                    self.test_node_if1["NAME"])
            },
            # node2
            {
                "type": "eth",
                "url": self.node2_net_url + "/eth_629",
                "props": "device_name='{0}' macaddress='{1}'".format(
                                                self.test_node2_if1["NAME"],
                                                self.test_node2_if1["MAC"])
            },
            {
                "type": "bridge",
                "url": bridge_url_n2,
                "props": "ipaddress='10.10.10.23' device_name='br6629' \
                            ipv6address='fe05::3' network_name='test2'"
            },
            {
                "type": "vlan",
                "url": self.node2_net_url + "/vlan629",
                "props": "device_name='{0}.629' bridge='br6629'".format(
                                                self.test_node2_if1["NAME"])
            },
        ]
        for net_item in net_props:
            self.execute_cli_create_cmd(self.ms_node, net_item["url"],
                                        net_item["type"], net_item["props"])

        # Setup further nics cleaning in teardown
        self.add_nic_to_cleanup(self.ms_node, 'br6629', is_bridge=True)
        self.add_nic_to_cleanup(self.ms_node, '{0}.629'.
                                format(self.test_ms_if1["NAME"]))

        self.add_nic_to_cleanup(self.managed_nodes[0],
                                'br6629', is_bridge=True)
        self.add_nic_to_cleanup(self.managed_nodes[0], '{0}.629'.
                                format(self.test_node_if1["NAME"]))

        self.add_nic_to_cleanup(self.managed_nodes[1],
                                'br6629', is_bridge=True)
        self.add_nic_to_cleanup(self.managed_nodes[1], '{0}.629'.
                                format(self.test_node2_if1["NAME"]))

        self.log('info', "2. Create VCS network hosts")
        host_props = data.TEST01_HOST_PROPS
        for url, props in host_props.iteritems():
            self.create_vcs_net_host(url, props)

        self.log('info', "3. Create and run plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 20)

        self.log('info', "4. Check ifcfg-files")
        props = data.TEST01_MS_BR_PROPS
        path = "{0}/ifcfg-br6629".format(const.NETWORK_SCRIPTS_DIR)
        self.check_ifcfg(self.ms_node, path, props)

        props = data.TEST01_N1_BR_PROPS
        self.check_ifcfg(self.managed_nodes[0], path, props)

        props = data.TEST01_N2_BR_PROPS
        self.check_ifcfg(self.managed_nodes[1], path, props)

        self.log('info', "5. Check VLAN ifcfg file content")
        props = data.TEST01_MS_VLAN_PROPS
        path = "{0}/ifcfg-{1}.629".format(const.NETWORK_SCRIPTS_DIR,
                                          self.test_ms_if1["NAME"])
        self.check_ifcfg(self.ms_node, path, props)

        props = data.TEST01_N1_VLAN_PROPS
        path = "{0}/ifcfg-{1}.629".format(const.NETWORK_SCRIPTS_DIR,
                                          self.test_node_if1["NAME"])
        self.check_ifcfg(self.managed_nodes[0], path, props)

        props = data.TEST01_N2_VLAN_PROPS
        path = "{0}/ifcfg-{1}.629".format(const.NETWORK_SCRIPTS_DIR,
                                          self.test_node2_if1["NAME"])
        self.check_ifcfg(self.managed_nodes[0], path, props)

        self.log('info', "6. Remove bridge")
        self.execute_cli_remove_cmd(self.ms_node, bridge_url_ms)
        self.execute_cli_remove_cmd(self.ms_node, bridge_url_n1)
        self.execute_cli_remove_cmd(self.ms_node, bridge_url_n2)

        std_err = self.execute_cli_createplan_cmd(self.ms_node,
                                                  expect_positive=False)[1]

        self.assertTrue(self.is_text_in_list("ValidationError", std_err))
        msg = "is not a valid bridge as it has state 'ForRemoval'"
        self.assertTrue(self.is_text_in_list(msg, std_err))

    @attr('all', 'revert', 'story6629', 'story6629_tc02')
    def test_02_p_create_bridged_bond_with_multiple_eths(self):
        """
        @tms_id: litpcds_6629_tc02
        @tms_requirements_id: LITPCDS-6629
        @tms_title: create bridged bond with multiple eths
        @tms_description: Create a deployment with two eths attached
            to a bond where the bond is bridged on the ms and nodes.
            Verify applied primary_reselect and primary properties.
        NOTE: also verifies task TORF-161584
        @tms_test_steps:
            @step: Create network item under 'infrastructure'
            @result: Item created
            @step: Create one eth item on ms and two eth items on node1 and
                   node2
            @result: Items created
            @step: Create bridge item on ms, node1 and node2
            @result: Items created
            @step: Create bond item on ms, node1 and node2
            @result: Items created
            @step: Create, run the plan and stop it after the bond
                   configuration primary_reselect and primary is applied
            @result: Plan is stopped
            @step: Recreate the plan and verify the applied bond configuration
                is not present
            @result: The applied bond tasks are not present
            @step: Rerun the plan
            @result: The plan is successful
            @step: Execute "cat ifcfg" on ms, node1 and node2 on each bond
            @result: Ms, node1 and node2 contain correct information
            @step: Verify primary and primary_reselect system applied settings
                  on node1
            @result: Node1 bond settings are correct
            @step: Ensure the connectivity on TCP/IP layer 4 level
            @result: The connection response is successful
            @step: Validate the generated xml after model export
            @result: The generated xml has correct structure
            @step: Delete primary and primary_reselect on node1 bond
            @result: The Litp items are updated
            @step: Create and run plan
            @result: The plan is successful
            @step: Ensure bond configuration are applied
            @result: The config files and applied configuration matching to
                the litp model
            @step: Ensure the connectivity on TCP/IP layer 4 level
            @result: The connection response is successful
            @step: Validate the generated xml after model export
            @result: The generated xml has correct structure
            @step: Remove bridge items from ms,node1 and node2
            @result: Items set to ForRemoval
            @step: Create plan
            @result: error thrown: ValidationError
            @result: is not a valid bridge as it has state 'ForRemoval'
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """

        self.log('info', "1. Create deployment")
        self.test_ms_if1 = self.verify_backup_free_nics(
            self.ms_node, self.ms_url, specific_nics=data.MS_STORAGE_NICS)[0]
        free_nics_n1 = self.verify_backup_free_nics(
            self.ms_node, self.node_urls[0], required_free_nics=2,
            specific_nics=data.MN_STORAGE_NICS)
        free_nics_n2 = self.verify_backup_free_nics(
            self.ms_node, self.node_urls[1], required_free_nics=2,
            specific_nics=data.MN_STORAGE_NICS)

        ord_free_nics_n1 = dict([(nic['NAME'], nic) for nic in free_nics_n1])
        ord_free_nics_n2 = dict([(nic['NAME'], nic) for nic in free_nics_n2])
        nic_node1 = None
        for nic, nic_node1 in ord_free_nics_n1.iteritems():
            try:
                nic_node2 = ord_free_nics_n2[nic]
                used_key = nic
            except KeyError:
                pass
        nic_2_node1 = [nic for key, nic in ord_free_nics_n1.iteritems()
                       if key != used_key][0]
        nic_2_node2 = [nic for key, nic in ord_free_nics_n2.iteritems()
                       if key != used_key][0]
        if not nic_node2:
            self.fail('There is no free nics from the same network')

        network_url = self.networks_path + "/test_network2069"
        props = "name='test2' subnet='10.10.10.0/24'"
        self.execute_cli_create_cmd(self.ms_node, network_url, "network",
                                    props)

        net_props = [
            # ms
            {
                "type": "eth",
                "url": self.ms_net_url + "/eth629",
                "props": "device_name='{0}' macaddress='{1}' "
                         "master='bond629'".format(self.test_ms_if1["NAME"],
                                                   self.test_ms_if1["MAC"])
            },
            {
                "type": "bridge",
                "url": self.ms_net_url + "/br629",
                "props": data.TEST02_MS_BRIDGE
            },
            {
                "type": "bond",
                "url": self.ms_net_url + "/b629",
                "props": "device_name='bond629' bridge='br6629' miimon='100'"
            },
            # node1
            {
                "type": "eth",
                "url": self.node1_net_url + "/eth_629",
                "props": "device_name='{0}' macaddress='{1}' "
                         "master='bond629'".format(nic_node1["NAME"],
                                                   nic_node1["MAC"])
            },
            {
                "type": "eth",
                "url": self.node1_net_url + "/eth_730",
                "props": "device_name='{0}' macaddress='{1}' "
                         "master='bond629'".format(nic_2_node1["NAME"],
                                                   nic_2_node1["MAC"])
            },
            {
                "type": "bridge",
                "url": self.node1_net_url + "/br629",
                "props": data.TEST02_N1_BRIDGE
            },
            {
                "type": "bond",
                "url": self.node1_net_url + "/b629",
                "props": data.TEST02_N1_BOND.format(nic_node1["NAME"])
            },
            # node2
            {
                "type": "eth",
                "url": self.node2_net_url + "/eth_629",
                "props": "device_name='{0}' macaddress='{1}' "
                         "master='bond629'".format(nic_node2["NAME"],
                                                   nic_node2["MAC"])
            },
            {
                "type": "eth",
                "url": self.node2_net_url + "/eth_730",
                "props": "device_name='{0}' macaddress='{1}' "
                         "master='bond629'".format(nic_2_node2["NAME"],
                                                   nic_2_node2["MAC"])
            },
            {
                "type": "bridge",
                "url": self.node2_net_url + "/br629",
                "props": data.TEST02_N2_BRIDGE.format('10.10.10.23', 'fe05::3')
            },
            {
                "type": "bond",
                "url": self.node2_net_url + "/b629",
                "props": data.TEST02_N2_BOND.format(nic_2_node2["NAME"])
            }
        ]
        self.create_network_items(net_props)

        # Setup further nics cleaning in teardown
        for node in self.all_nodes:
            self.add_nic_to_cleanup(node, 'br6629', is_bridge=True)
            self.add_nic_to_cleanup(node, 'bond629', is_bond=True)

        self.log('info', "2. Create VCS network hosts")
        for url_id, props in data.TEST02_HOST_PROPS.iteritems():
            self.create_vcs_net_host(url_id, props)

        self.log('info', "3. Create, run the plan and stop it after the bond "
                         "configuration primary_reselect and primary is "
                         "applied")
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        # Assert VCS unlock phase from the plan, we need that in order
        # to stop the plan when all of the phases for this node are completed.
        phase_4_node_unlock_success = 'Unlock VCS on node "{0}"'.format(
                                                        self.managed_nodes[0])
        self.restart_litpd_when_task_state(self.ms_node,
                                           phase_4_node_unlock_success)

        self.log('info', "4. Recreate the plan and verify the applied bond "
                         "configuration is not present")
        self.execute_cli_createplan_cmd(self.ms_node)

        stdout = self.execute_cli_showplan_cmd(self.ms_node)[0]
        task = 'Configure bond "bond629" on node "{0}"'.format(
                                                        self.managed_nodes[0])
        self.assertFalse(self.is_text_in_list(task, stdout),
                         'Previously successful task "{0}" '
                         'found in recreated plan:\n\n"{1}"'.format(
                             task, stdout))
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(self.ms_node,
                                                 const.PLAN_COMPLETE),
                        'The plan execution did not succeed')
        self.log('info', "5. Check bond attached bridge connectivity")
        self.chk_applied_bond_prim(self.managed_nodes[0], 'bond629',
                                   (nic_node1["NAME"], 'better 1'))
        self.check_ssh_connectivity_bridge(self.managed_nodes[0],
                                           ['10.10.10.23', 'fe05::3'])

        self.log('info', "6. Validate the generated xml after model export")
        self.xml_validate(self.node_urls[0],
                          'xml_expected_install_story161584.xml')

        self.log('info', "7. Check ifcfg files")
        path = "{0}/ifcfg-br6629".format(const.NETWORK_SCRIPTS_DIR)
        props = {
            self.ms_node: data.TEST02_MS_BR_PROPS,
            self.managed_nodes[0]: data.TEST02_N1_BR_PROPS,
            self.managed_nodes[1]: data.TEST02_N2_BR_PROPS
        }
        for node, prop in props.iteritems():
            self.check_ifcfg(node, path, prop)

        path = "{0}/ifcfg-bond629".format(const.NETWORK_SCRIPTS_DIR)
        n1_bond_props = [
            'DEVICE="bond629"',
            'TYPE="Bonding"',
            'BRIDGE="br6629"',
            "miimon=100 mode=1 primary={0} primary_reselect=1".format(
                                                        nic_node1["NAME"]),
        ]
        props = {
            self.ms_node: data.TEST02_MS_BOND_PROPS,
            self.managed_nodes[0]: n1_bond_props,
            self.managed_nodes[1]: data.TEST02_N2_BOND_PROPS
        }
        for node, prop in props.iteritems():
            self.check_ifcfg(node, path, prop)

        self.log('info', "8. Check eth ifcfg files")
        props = [
            'SLAVE="yes"',
            'MASTER="bond629"'
        ]
        path = "{0}/ifcfg-{1}".format(const.NETWORK_SCRIPTS_DIR,
                                      self.test_ms_if1["NAME"])
        self.check_ifcfg(self.ms_node, path, props)

        path = "{0}/ifcfg-{1}".format(const.NETWORK_SCRIPTS_DIR,
                                      nic_node1["NAME"])
        self.check_ifcfg(self.managed_nodes[0], path, props)

        path = "{0}/ifcfg-{1}".format(const.NETWORK_SCRIPTS_DIR,
                                      nic_2_node1["NAME"])
        self.check_ifcfg(self.managed_nodes[1], path, props)

        path = "{0}/ifcfg-{1}".format(const.NETWORK_SCRIPTS_DIR,
                                      nic_node2["NAME"])
        self.check_ifcfg(self.managed_nodes[1], path, props)

        path = "{0}/ifcfg-{1}".format(const.NETWORK_SCRIPTS_DIR,
                                      nic_2_node2["NAME"])
        self.check_ifcfg(self.managed_nodes[1], path, props)

        default_primary_reselect = 'always 0'
        bond_url_n1 = self.node1_net_url + "/b629"
        self.execute_cli_update_cmd(self.ms_node, bond_url_n1,
                                    action_del=True,
                                    props='primary_reselect primary')

        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 5)
        self.chk_applied_bond_prim(self.managed_nodes[0], 'bond629',
                                   ([], default_primary_reselect))
        self.check_ssh_connectivity_bridge(self.managed_nodes[0],
                                           ['10.10.10.23', 'fe05::3'])

        props = data.TEST02_UPDATED_N1_BOND_PROPS
        path = "{0}/ifcfg-bond629".format(const.NETWORK_SCRIPTS_DIR)
        self.check_ifcfg(self.managed_nodes[0], path, props)

        self.log('info', "9. Remove the bridge")
        bridge_urls = [
            self.ms_net_url + "/br629",
            self.node1_net_url + "/br629",
            self.node2_net_url + "/br629"
        ]
        for bridge in bridge_urls:
            self.execute_cli_remove_cmd(self.ms_node, bridge)

        std_err = self.execute_cli_createplan_cmd(self.ms_node,
                                                  expect_positive=False)[1]

        msg = "is not a valid bridge as it has state 'ForRemoval'"
        self.assertTrue(self.is_text_in_list("ValidationError", std_err))
        self.assertTrue(self.is_text_in_list(msg, std_err))

    @attr('all', 'revert', 'story6629', 'story6629_tc03')
    def test_03_p_create_update_bond_on_bridged_vlan_multiple_eths(self):
        """
        @tms_id: litpcds_6629_tc03
        @tms_requirements_id: LITPCDS-6629
        @tms_title: create update bond on bridged vlan multiple eths
        @tms_description: Create and update a deployment with one eth attached
        to a bond, where there is a VLAN on the bond and the vlan is bridged
        @tms_test_steps:
            @step: Create network item under 'infrastructure'
            @result: Item created
            @step: Create one eth item on ms, node1 and node2
            @result: Items created
            @step: Create bridge item on ms, node1 and node2
            @result: Items created
            @step: Create bond item on ms, node1 and node2
            @result: Items created
            @step: Create vlan item on ms, node1 and node2
            @result: Items created
            @step: Create and run plan
            @result: Plan executes successfully
            @step: Execute "cat ifcfg" on ms, node1 and node2
            @result: Ms, node1 and node2 contain correct information
            @step: Update mode, miimon properties on bond item on ms
            @result: Item update
            @step: Update ipaddress, stp and forwarding_delay properties on
            bridge Item on ms
            @result: Item update
            @step: Create and run plan
            @result: Plan executes successfully
            @step: Execute "cat ifcfg" on ms
            @result: Ms contain correct information
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log('info', "1. Create deployment")
        network_url = self.networks_path + "/test_network2069"
        props = "name='test2' subnet='10.10.10.0/24'"
        self.execute_cli_create_cmd(self.ms_node, network_url,
                                    "network", props)

        free_nics_ms = self.verify_backup_free_nics(self.ms_node,
                                                    self.ms_url,
                                                    required_free_nics=1)[0]
        free_nics_mn1 = self.verify_backup_free_nics(self.ms_node,
                                                     self.node_urls[0],
                                                     required_free_nics=1)[0]
        free_nics_mn2 = self.verify_backup_free_nics(self.ms_node,
                                                     self.node_urls[1],
                                                     required_free_nics=1)[0]

        net_props = [
            # ms
            {
                "type": "eth",
                "url": self.ms_net_url + "/eth629",
                "props": "device_name='{0}' macaddress='{1}' "
                         "master='bond629'".format(free_nics_ms["NAME"],
                                                   free_nics_ms["MAC"])
            },
            {
                "type": "bridge",
                "url": self.ms_net_url + "/br629",
                "props": data.TEST03_MS_BR
            },
            {
                "type": "bond",
                "url": self.ms_net_url + "/bond629",
                "props": "device_name='bond629' miimon='100'"
            },
            {
                "type": "vlan",
                "url": self.ms_net_url + "/vlan_629",
                "props": "device_name='bond629.629' bridge='br629'"
            },
            # node1
            {
                "type": "eth",
                "url": self.node1_net_url + "/eth629",
                "props": "device_name='{0}' macaddress='{1}' "
                         "master='bond629'".format(free_nics_mn1["NAME"],
                                                   free_nics_mn1["MAC"])
            },
            {
                "type": "bridge",
                "url": self.node1_net_url + "/br629",
                "props": data.TEST03_N1_BR
            },
            {
                "type": "bond",
                "url": self.node1_net_url + "/bond629",
                "props": "device_name='bond629' miimon='100'"
            },
            {
                "type": "vlan",
                "url": self.node1_net_url + "/vlan_629",
                "props": "device_name='bond629.629' bridge='br629'"
            },
            # node2
            {
                "type": "eth",
                "url": self.node2_net_url + "/eth629",
                "props": "device_name='{0}' macaddress='{1}' "
                         "master='bond629'".format(free_nics_mn2["NAME"],
                                                   free_nics_mn2["MAC"])
            },
            {
                "type": "bridge",
                "url": self.node2_net_url + "/br629",
                "props": data.TEST03_N2_BR
            },
            {
                "type": "bond",
                "url": self.node2_net_url + "/bond629",
                "props": "device_name='bond629' miimon='100'"
            },
            {
                "type": "vlan",
                "url": self.node2_net_url + "/vlan_629",
                "props": "device_name='bond629.629' bridge='br629'"
            }
        ]
        self.create_network_items(net_props)

        # Setup further nics cleaning in teardown
        self.add_nic_to_cleanup(self.ms_node, 'bond629', is_bond=True)
        self.add_nic_to_cleanup(self.ms_node, 'bond629.629')
        self.add_nic_to_cleanup(self.ms_node, 'br629', is_bridge=True)
        for node_index in range(0, 2):
            self.add_nic_to_cleanup(self.managed_nodes[node_index],
                                    'bond629',
                                    is_bond=True)
            self.add_nic_to_cleanup(self.managed_nodes[node_index],
                                    'bond629.629')
            self.add_nic_to_cleanup(self.managed_nodes[node_index],
                                    'br629', is_bridge=True)

        self.log('info', "2. Create and run the plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 20)

        self.log('info', "3. Check ifcfg files")
        path = "{0}/ifcfg-br629".format(const.NETWORK_SCRIPTS_DIR)
        self.check_ifcfg(self.ms_node, path, data.TEST03_BR_PROPS)

        path = "{0}/ifcfg-bond629.629".format(const.NETWORK_SCRIPTS_DIR)
        self.check_ifcfg(self.ms_node, path, data.TEST03_VLAN_PROPS)

        path = "{0}/ifcfg-bond629".format(const.NETWORK_SCRIPTS_DIR)
        self.check_ifcfg(self.ms_node, path, data.TEST03_BOND_PROPS)

        path = "{0}/ifcfg-{1}".format(
            const.NETWORK_SCRIPTS_DIR, free_nics_ms['NAME'])
        self.check_ifcfg(self.ms_node, path, data.TEST03_ETH_PROPS)

        self.log('info', "4. Update bond")
        props = "mode=6 miimon=200"
        dev_url = self.ms_net_url + '/bond629'
        self.execute_cli_update_cmd(self.ms_node, dev_url, props)

        self.log('info', "5. Update bridge")
        props = "ipaddress='10.10.10.30' stp='true' forwarding_delay='25'"
        dev_url = self.ms_net_url + '/br629'
        self.execute_cli_update_cmd(self.ms_node, dev_url, props)

        self.log('info', "6. Create and run the plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 20)

        self.log('info', "7. Check ifcfg files")
        path = "{0}/ifcfg-br629".format(const.NETWORK_SCRIPTS_DIR)
        self.check_ifcfg(self.ms_node, path, data.TEST03_UPDATED_BR)

        path = "{0}/ifcfg-bond629".format(const.NETWORK_SCRIPTS_DIR)
        self.check_ifcfg(self.ms_node, path, data.TEST03_UPDATED_BOND)

    @attr('all', 'revert', 'story6629', 'story6629_tc04')
    def test_04_p_create_bridged_eth_vlan_tagged(self):
        """
        @tms_id: litpcds_6629_tc04
        @tms_requirements_id: LITPCDS-6629
        @tms_title: create bridged eth vlan tagged
        @tms_description: Create a deployment with an eth which is both vlan
            tagged and has a "bridge" property set
        @tms_test_steps:
            @step: Create two network item under 'infrastructure'
            @result: Item created
            @step: Create one eth item on ms, node1 and node2
            @result: Items created
            @step: Create bridge item on ms, node1 and node2
            @result: Items created
            @step: Create vlan item on ms, node1 and node2
            @result: Items created
            @step: Create and run plan
            @result: Plan executes successfully
            @step: Execute "cat ifcfg" on ms, node1 and node2
            @result: Ms, node1 and node2 contain correct information
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log('info', "1. Create deployment")
        network_url = self.networks_path + "/test_network2069"
        props = "name='test2' subnet='10.10.10.0/24'"
        self.execute_cli_create_cmd(self.ms_node, network_url,
                                    "network", props)

        network_url = self.networks_path + "/test_network20692"
        props = "name='test3' subnet='10.10.20.0/24'"
        self.execute_cli_create_cmd(self.ms_node, network_url,
                                    "network", props)

        free_nics_ms = self.verify_backup_free_nics(
            self.ms_node, self.ms_url, required_free_nics=1)[0]
        free_nics_mn1 = self.verify_backup_free_nics(
            self.ms_node, self.node_urls[0], required_free_nics=1)[0]
        free_nics_mn2 = self.verify_backup_free_nics(
            self.ms_node, self.node_urls[1], required_free_nics=1)[0]

        net_props = [
            # ms
            {
                "type": "eth",
                "url": self.ms_net_url + "/eth629",
                "props": "device_name='{0}' macaddress='{1}' "
                         "bridge='br629'".format(free_nics_ms["NAME"],
                                                 free_nics_ms["MAC"])
            },
            {
                "type": "bridge",
                "url": self.ms_net_url + "/br629",
                "props": data.TEST04_MS_BR
            },
            {
                "type": "vlan",
                "url": self.ms_net_url + "/vlan_629",
                "props": data.TEST04_MS_VLAN.format(free_nics_ms["NAME"])
            },
            # node1
            {
                "type": "eth",
                "url": self.node1_net_url + "/eth629",
                "props": "device_name='{0}' macaddress='{1}' "
                         "bridge='br629'".format(free_nics_mn1["NAME"],
                                                 free_nics_mn1["MAC"])
            },
            {
                "type": "bridge",
                "url": self.node1_net_url + "/br629",
                "props": data.TEST04_N1_BR
            },
            {
                "type": "vlan",
                "url": self.node1_net_url + "/vlan_629",
                "props": data.TEST04_N1_VLAN.format(free_nics_mn1["NAME"])
            },
            # node2
            {
                "type": "eth",
                "url": self.node2_net_url + "/eth629",
                "props": "device_name='{0}' macaddress='{1}' "
                         "bridge='br629'".format(free_nics_mn1["NAME"],
                                                 free_nics_mn2["MAC"])
            },
            {
                "type": "bridge",
                "url": self.node2_net_url + "/br629",
                "props": data.TEST04_N2_BR
            },
            {
                "type": "vlan",
                "url": self.node2_net_url + "/vlan_629",
                "props": data.TEST04_N2_VLAN.format(free_nics_mn2["NAME"])
            }
        ]
        self.create_network_items(net_props)

        # # Setup further nics cleaning in teardown
        self.add_nic_to_cleanup(self.ms_node, 'br629', is_bridge=True)
        self.add_nic_to_cleanup(self.ms_node, '{0}.629'.
                                format(free_nics_ms['NAME']))

        self.add_nic_to_cleanup(self.managed_nodes[0], 'br629', is_bridge=True)
        self.add_nic_to_cleanup(self.managed_nodes[0], '{0}.629'.
                                format(free_nics_mn1['NAME']))

        self.add_nic_to_cleanup(self.managed_nodes[1], 'br629', is_bridge=True)
        self.add_nic_to_cleanup(self.managed_nodes[1], '{0}.629'.
                                format(free_nics_mn2['NAME']))

        self.log('info', "2. Create and run the plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 20)

        self.log('info', "3. Check ifcfg files")
        path = "{0}/ifcfg-br629".format(const.NETWORK_SCRIPTS_DIR)
        props = data.TEST04_BR_PROPS
        self.check_ifcfg(self.ms_node, path, props)

        path = "{0}/ifcfg-{1}.629".format(
            const.NETWORK_SCRIPTS_DIR, free_nics_ms['NAME'])
        props = data.TEST04_VLAN_PROPS
        self.check_ifcfg(self.ms_node, path, props)

        path = "{0}/ifcfg-{1}".format(
            const.NETWORK_SCRIPTS_DIR, free_nics_ms['NAME'])
        self.check_ifcfg(self.ms_node, path, ['BRIDGE="br629"'])

    @attr('all', 'revert', 'story6629', 'story6629_tc05')
    def test_05_p_create_update_bridge_no_ip(self):
        """
        @tms_id: litpcds_6629_tc05
        @tms_requirements_id: LITPCDS-6629
        @tms_title: create update bridge no ip
        @tms_description: Create a bridge item with no ipv4 or ipv6 address
            and then update with ipv6 property
        @tms_test_steps:
            @step: Create one network item under 'infrastructure'
            @result: Item created
            @step: Create one eth item and one bridge item on ms
            @result: Items created
            @step: Create and run plan
            @result: Plan executes successfully
            @step: Execute "cat ifcfg" on ms, node1 and node2
            @result: Command executes - IF info for each system is obtained
            @step: Update bridge item on ms with ipv6 property
            @result: Items updated
            @step: Create and run plan
            @result: Plan executes successfully
            @step: Execute "cat ifcfg" on ms, node1 and node2
            @result: Ms contain correct information
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log('info', "1. Create deployment")
        network_url = self.networks_path + "/test_network2069"
        props = "name='test2'"
        self.execute_cli_create_cmd(self.ms_node, network_url,
                                    "network", props)

        free_nics_ms = self.verify_backup_free_nics(self.ms_node,
                                                    self.ms_url,
                                                    required_free_nics=1)

        # Bridge must be used in plan so we create an network interface
        # eth0 and bridge it.
        bridge_url = self.ms_net_url + "/br629"
        net_props = [
            {
                "type": "eth",
                "url": self.ms_net_url + '/eth629',
                "props": "device_name='{0}' macaddress='{1}' "
                         "bridge='br629'".format(free_nics_ms[0]["NAME"],
                                                 free_nics_ms[0]["MAC"])
            },
            {
                "type": "bridge",
                "url": bridge_url,
                "props": "device_name='br629' network_name='test2'"
            }
        ]
        self.create_network_items(net_props)

        # # Setup further nics cleaning in teardown
        self.add_nic_to_cleanup(self.ms_node, 'br629', is_bridge=True)

        self.log('info', "2. Create and run the plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 20)

        self.log('info', "3. Check bridge is properly configured")
        path = "{0}/ifcfg-br629".format(const.NETWORK_SCRIPTS_DIR)
        props = data.TEST05_BR_PROPS
        n_props = data.TEST05_BR_N_PROPS
        self.check_ifcfg(self.ms_node, path, props, negative_props=n_props)

        self.log('info', "4. Add IPV6 to existing bridge")
        ipaddress = "fdda:4d7a:d471::835:0105:0101"
        props = "ipv6address={0}/64".format(ipaddress)
        self.execute_cli_update_cmd(self.ms_node, bridge_url, props)

        self.run_and_check_plan(self.ms_node, const.PLAN_TASKS_SUCCESS, 10)

        stdout = self.get_file_contents(self.ms_node, path)
        self.assertTrue(self.is_text_in_list(
            'IPV6ADDR="{0}/64"'.format(ipaddress), stdout))

        self.log('info', "5. Check bridge ipv6 is pingable")
        cmd = self.net.get_ping6_cmd(ipaddress, 2)
        ret_code = self.run_command(self.ms_node, cmd)[2]
        self.assertEqual(0, ret_code)

    @attr('all', 'revert', 'story6629', 'story6629_tc06')
    def test_06_p_check_bridge_mgmt_net(self):
        """
        @tms_id: litpcds_6629_tc06
        @tms_requirements_id: LITPCDS-6629
        @tms_title: check_bridge_mgmt_net
        @tms_description: Check that the bridged eth on a mgmt network is
            configured correctly.(bridge is created in initial deployment.)
        @tms_test_steps:
            @step: Check model for bridge
            @result: Bridge items are configured correctly
            @step: Execute "cat ifcfg" on initial deployment nodes
            @result: Nodes contain correct information
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log('info', "1. Check ifcfg files")
        mgmt_network_name = self.get_management_network_name(self.ms_node)

        mgmt_bridge = None
        bridges = self.find(self.ms_node, self.node_urls[0], 'bridge')
        for bridge in bridges:
            bridge_props = self.get_props_from_url(self.ms_node, bridge)
            if mgmt_network_name == bridge_props.get('network_name'):
                mgmt_bridge = bridge
                break
        self.assertNotEqual(None, mgmt_bridge)

        path = "{0}/ifcfg-{1}".format(const.NETWORK_SCRIPTS_DIR,
                                      bridge_props.get('device_name'))
        props = data.TEST06_BR_PROPS
        ipv4 = bridge_props.get('ipaddress')
        ipv6 = bridge_props.get('ipv6address')
        if ipv4:
            props.append('IPADDR="{0}"'.format(ipv4))
        if ipv6:
            props.append('IPV6ADDR="{0}"'.format(ipv6))

        self.check_ifcfg(self.managed_nodes[0], path, props)

        self.log('info', "2. Check bridged interface")
        bridged_eth = None
        eths = self.find(self.ms_node, self.node_urls[0], 'eth')
        for eth in eths:
            eth_props = self.get_props_from_url(self.ms_node, eth)
            if bridge_props.get('device_name') and \
               bridge_props.get('device_name') == eth_props.get('bridge'):
                bridged_eth = eth
                break
        self.assertNotEqual(None, bridged_eth)

        self.log('info', "3. Check eth ifcfg file")
        path = "{0}/ifcfg-{1}".format(const.NETWORK_SCRIPTS_DIR,
                                      eth_props.get('device_name'))
        props = ['BRIDGE="{0}"'.format(bridge_props.get('device_name'))]
        n_props = data.TEST06_ETH_N_PROPS
        self.check_ifcfg(self.managed_nodes[0], path, props,
                         negative_props=n_props)

    # attr('all', 'non-revert', 'story6629', 'story6629_tc07')
    def obsolete_07_n_validate_invalid_combinations(self):
        """
        Converted to "test_07_n_validate_invalid_combinations.at" in network

        #tms_id: litpcds_6629_tc07
        #tms_requirements_id: LITPCDS-6629
        #tms_title: validate invalid combinations
        #tms_description: Verify invalid property combinations results
            in a validation error
        #tms_test_steps:
        #step: Create a bond with both bridge and network_name props specified
        #result: error thrown: ValidationError
        #step: Create a bond with both bridge and ipaddress props
            specified(without specifying network_name)
        #result: error thrown: ValidationError
        #step: Create a bond with both bridge and ipv6address props
            specified(without specifying network_name)
        #result: error thrown: ValidationError
        #step: Create a vlan with both bridge and network_name props specified
        #result: error thrown: ValidationError
        #step: Create a vlan with both bridge and ipaddress props
            specified(without specifying network_name)
        #result: error thrown: ValidationError
        #step: Create a vlan with both bridge and ipv6address props
            specified(without specifying network_name)
        #result: error thrown: ValidationError
        #step: Create a vlan with invalid bridge
        #result: error thrown: ValidationError
        #step: Create a bond with invalid bridge
        #result: error thrown: ValidationError
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'revert', 'story6629', 'story6629_tc08')
    def test_08_p_create_bridge_no_ip_idempotent_plan(self):
        """
        @tms_id: litpcds_6629_tc08
        @tms_requirements_id: LITPCDS-6629
        @tms_title: create bridge no ip idempotent plan
        @tms_description: Creates a bridge on the MS and also an invalid item
        on a MN. The plan is expected to fail at the MN item creation.
        It then tests that recreated plan doesn't include the previously
        successful bridge creation task.
        @tms_test_steps:
            @step: Create network item under 'infrastructure'
            @result: Item created
            @step: Create one eth item on ms
            @result: Item created
            @step: Create bridge item on ms
            @result: Item created
            @step: Create one eth on node1
            @result: Items created
            @step: Create and run plan
            @result: Plan fails to test idempotency
            @step: Re-create and run plan to ensure that the previously
                   successful tasks aren't run.
            @result: The plan fails.
            @step: Execute ifcfg on nodes
            @result: Bridge is configured correctly
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log('info', "1. Create deployment")
        network_url = self.networks_path + "/test_network2069"
        props = "name='test2'"
        self.execute_cli_create_cmd(self.ms_node, network_url,
                                    "network", props)

        free_nics_ms = self.verify_backup_free_nics(
            self.ms_node, self.ms_url, required_free_nics=1)[0]
        test_n1_if1 = self.verify_backup_free_nics(
            self.ms_node, self.node_urls[0], required_free_nics=1)[0]

        net_props = [
            # ms
            {
                "type": "eth",
                "url": self.ms_net_url + '/eth629',
                "props": "device_name='{0}' macaddress='{1}' "
                         "bridge='br629'".format(free_nics_ms["NAME"],
                                                 free_nics_ms["MAC"])
            },
            {
                "type": "bridge",
                "url": self.ms_net_url + "/br629",
                "props": "device_name='br629' network_name='test2'"
            },
            # node1
            {
                "type": "eth",
                "url": self.node1_net_url + '/eth629',
                "props": data.TEST08_ETH_N1.format(test_n1_if1["NAME"])
            }
        ]
        self.create_network_items(net_props)

        # Setup further nics cleaning in teardown
        self.add_nic_to_cleanup(self.ms_node, 'br629', is_bridge=True)

        self.log('info', "2. Create and run the plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_FAILED, 20)

        self.log('info', "3. Check bridge is properly configured")
        path = "{0}/ifcfg-br629".format(const.NETWORK_SCRIPTS_DIR)
        props = data.TEST08_BR_PROPS
        n_props = data.TEST08_BR_N_PROPS
        self.check_ifcfg(self.ms_node, path, props, negative_props=n_props)

        node1_hostname = self.managed_nodes[0]
        # assure the completed phase is visualised correctly
        phase_1_1 = 'Configure bridge "br629" on node "{0}"'.format(
            self.ms_node)
        phase_1_2 = 'Configure eth "{0}" on node "{1}"'.format(
            free_nics_ms["NAME"], self.ms_node)
        phase_3_1 = 'Configure eth "{0}" on node "{1}"'.format(
            test_n1_if1["NAME"], node1_hostname)
        phases = {
            phase_1_1: const.PLAN_TASKS_SUCCESS,
            phase_1_2: const.PLAN_TASKS_SUCCESS,
            phase_3_1: const.PLAN_TASKS_FAILED
        }
        for phase, state in phases.iteritems():
            self.assertEqual(state, self.get_task_state(
                self.ms_node, phase, False))

        self.log('info', "4. Create and run the plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_FAILED, 20)

        self.log('info', "5. Check bridge is properly configured")
        path = "{0}/ifcfg-br629".format(const.NETWORK_SCRIPTS_DIR)
        self.check_ifcfg(self.ms_node, path, props)

        # assure that already completed phases are not executed again
        phases = {
            phase_1_1: const.CMD_ERROR,
            phase_1_2: const.CMD_ERROR,
            phase_3_1: const.PLAN_TASKS_FAILED
        }
        for phase, state in phases.iteritems():
            self.assertEqual(state, self.get_task_state(
                self.ms_node, phase, False))
